import logging
import csv
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Sum, Max
from django.db import transaction, models
from django.db.models.functions import Coalesce, TruncMonth
from django.conf import settings
import os
from xsdata.models.datatype import XmlDate
from ..models import MonthlyConsolidation, CompanySettings, NotaFiscal, NfseLog
from utils.taxes import get_applicable_bracket, get_minimum_salary, calculate_inss
from .. import signals as _signals
import requests

logger = logging.getLogger(__name__)

from ..models import *

def calculate_irrf(pro_labore_amount, reference_date):
    inss_deduction = calculate_inss(pro_labore_amount, reference_date)
    base_calc = pro_labore_amount - inss_deduction

    logger.debug(
        "Calculating IRRF for Pró-labore: %s, INSS Deduction: %s, Base Calc: %s",
        pro_labore_amount,
        inss_deduction,
        base_calc,
    )

    try:
        bracket = get_applicable_bracket("IRRF", base_calc, reference_date)
        nominal_rate = bracket.nominal_rate / Decimal("100")
        irrf = (base_calc * nominal_rate) - bracket.deduction
        return max(Decimal("0.00"), irrf).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    except ValueError as e:
        logger.debug(
            "No applicable IRRF bracket found for base calculation %s on %s. Returning 0.00. Error: %s",
            base_calc,
            reference_date,
            e,
        )
        return Decimal("0.00")



def calculate_rbt12_and_fator_r(target_month_year):
    """Calculate trailing 12-month revenue (RBT12) and Fator R for a given month.

    Fator R for Month X is based on payroll and revenue of the 12 preceding months (X-12 to X-1).
    For < 12 months of operation, uses the proportional annualization formula.
    For the very first month, uses current month's values × 12.
    """
    company = CompanySettings.objects.first()
    if not company:
        raise ValueError("Company settings not configured.")

    start_date = target_month_year - relativedelta(months=12)
    end_date = target_month_year - relativedelta(months=1)

    months_active = (target_month_year.year - company.opening_date.year) * 12 + (
        target_month_year.month - company.opening_date.month
    )

    past_consolidations = MonthlyConsolidation.objects.filter(
        month_year__gte=start_date, month_year__lte=end_date
    )

    # Use Coalesce to avoid None + None TypeError when no rows match
    agg = past_consolidations.aggregate(
        rev_int=Coalesce(Sum("total_revenue_internal"), Decimal("0.00")),
        rev_exp=Coalesce(Sum("total_revenue_export"), Decimal("0.00")),
    )
    sum_revenue = agg["rev_int"] + agg["rev_exp"]

    payroll_agg = past_consolidations.aggregate(
        pl=Coalesce(Sum("actual_pro_labore_paid"), Decimal("0.00"))
    )

    # Filter CPP by start date
    if (
        hasattr(settings, "CPP_ACCUMULATION_START_DATE")
        and settings.CPP_ACCUMULATION_START_DATE
    ):
        cpp_qs = past_consolidations.filter(
            month_year__gte=settings.CPP_ACCUMULATION_START_DATE
        )
    else:
        cpp_qs = past_consolidations

    cpp_agg = cpp_qs.aggregate(cpp=Coalesce(Sum("das_cpp_tax"), Decimal("0.00")))

    sum_payroll = payroll_agg["pl"] + cpp_agg["cpp"]

    # Specific rule for 1st Month Exception (§3.4)
    current = None
    if months_active == 0:
        current = MonthlyConsolidation.objects.filter(
            month_year=target_month_year
        ).first()
        if current:
            logger.debug(
                "Calculating RBT12 and Fator R for %s (1st month exception)",
                target_month_year,
            )
            rev = current.total_revenue_internal + current.total_revenue_export
            logger.debug("  Current Month Revenue: %s", rev)
            sum_revenue = rev * 12
            sum_payroll = (current.actual_pro_labore_paid + current.das_cpp_tax) * 12
        else:
            sum_revenue = Decimal("0.00")
            sum_payroll = Decimal("0.00")
            logger.debug(
                "No consolidation found for %s. Assuming zero revenue and payroll.",
                target_month_year,
            )

    elif months_active < 12:
        # Proportional annualization for bracket lookup
        sum_revenue = (sum_revenue / months_active) * 12
        sum_payroll = (sum_payroll / months_active) * 12

    pl_sum = payroll_agg["pl"]
    cpp_sum = cpp_agg["cpp"]

    if months_active == 0 and current:
        pl_sum = current.actual_pro_labore_paid * 12
        cpp_sum = current.das_cpp_tax * 12
    elif 0 < months_active < 12:
        pl_sum = (pl_sum / months_active) * 12
        cpp_sum = (cpp_sum / months_active) * 12

    if sum_revenue > 0:
        fator_r = ((sum_payroll / sum_revenue) * Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    else:
        fator_r = Decimal("0.00")

    sum_revenue = sum_revenue.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    logger.debug(
        "RBT12/Fator R for %s: Revenue=%s, Payroll=%s, Fator R=%s%%",
        target_month_year,
        sum_revenue,
        sum_payroll,
        fator_r,
    )

    return sum_revenue, fator_r, pl_sum, cpp_sum



def calculate_ideal_pro_labore(target_month, estimated_current_revenue=None):
    """Calculate the minimum Pró-labore needed in the current month so that
    next month's Fator R >= 28% (qualifying for Annex III).

    The Fator R for Month X+1 uses payroll and revenue from months X-11 to X.
    So we need: (sum_payroll_trailing_11 + current_month_pl) / (sum_revenue_trailing_11 + current_month_rev) >= 0.28
    Solving: ideal_pl = 0.28 * (sum_rev_11 + current_rev) - sum_payroll_11
    """
    company = CompanySettings.objects.first()
    if not company:
        raise ValueError("Company settings not configured.")

    # For next month's Fator R, the window is target_month-11 to target_month
    # (the 12 months preceding target_month+1)
    start_date = target_month - relativedelta(months=11)
    end_date = target_month - relativedelta(months=1)

    # Sum the trailing 11 months (excluding current month)
    past_consolidations = MonthlyConsolidation.objects.filter(
        month_year__gte=start_date, month_year__lte=end_date
    )

    agg = past_consolidations.aggregate(
        rev_int=Coalesce(Sum("total_revenue_internal"), Decimal("0.00")),
        rev_exp=Coalesce(Sum("total_revenue_export"), Decimal("0.00")),
        payroll=Coalesce(Sum("actual_pro_labore_paid"), Decimal("0.00")),
    )
    sum_revenue_11 = agg["rev_int"] + agg["rev_exp"]

    # Accumulate CPP from the past 11 months, filtering by start date if set
    if (
        hasattr(settings, "CPP_ACCUMULATION_START_DATE")
        and settings.CPP_ACCUMULATION_START_DATE
    ):
        cpp_qs = past_consolidations.filter(
            month_year__gte=settings.CPP_ACCUMULATION_START_DATE
        )
    else:
        cpp_qs = past_consolidations

    cpp_agg = cpp_qs.aggregate(cpp=Coalesce(Sum("das_cpp_tax"), Decimal("0.00")))

    sum_payroll_11 = agg["payroll"] + cpp_agg["cpp"]

    # Current month's revenue: use provided estimate, or look up from existing consolidation/NFs
    if estimated_current_revenue is not None:
        current_revenue = Decimal(str(estimated_current_revenue))
    else:
        # Try to get from existing consolidation or sum NFs
        current_cons = MonthlyConsolidation.objects.filter(
            month_year=target_month.replace(day=1)
        ).first()
        if (
            current_cons
            and (
                current_cons.total_revenue_internal + current_cons.total_revenue_export
            )
            > 0
        ):
            current_revenue = (
                current_cons.total_revenue_internal + current_cons.total_revenue_export
            )
        else:
            nfs = NotaFiscal.objects.filter(
                issue_date__year=target_month.year, issue_date__month=target_month.month
            ).exclude(models.Q(is_canceled=True) | models.Q(invoice__status="CANCELED"))
            current_revenue = nfs.aggregate(
                total=Coalesce(Sum("amount_brl"), Decimal("0.00"))
            )["total"]

    total_revenue = sum_revenue_11 + current_revenue
    total_payroll = sum_payroll_11

    # Solve: (total_payroll + ideal_pl) / total_revenue >= 0.28
    # ideal_pl = 0.28 * total_revenue - total_payroll
    if total_revenue <= 0:
        return Decimal("0.00")

    # Estimate current month's CPP assuming Annex III
    current_rbt12, _, _, _ = calculate_rbt12_and_fator_r(target_month)
    _, current_cpp = calculate_simples_tax(
        Decimal("0.00"), current_revenue, current_rbt12, "ANNEX_III", target_month
    )

    if (
        hasattr(settings, "CPP_ACCUMULATION_START_DATE")
        and settings.CPP_ACCUMULATION_START_DATE
    ):
        if target_month < settings.CPP_ACCUMULATION_START_DATE:
            current_cpp = Decimal("0.00")

    ideal_pl = (Decimal("0.28") * total_revenue) - total_payroll - current_cpp

    return max(Decimal("0.00"), ideal_pl + 1).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )



def calculate_simples_tax(
    revenue_internal, revenue_export, rbt12, annex_type, reference_date
):
    try:
        bracket = get_applicable_bracket(annex_type, rbt12, reference_date)
    except ValueError:
        return Decimal("0.00"), Decimal("0.00")

    if not bracket or rbt12 == 0:
        return Decimal("0.00"), Decimal("0.00")

    nominal_rate = bracket.nominal_rate / Decimal("100")
    effective_rate = ((rbt12 * nominal_rate) - bracket.deduction) / rbt12

    tax_internal = revenue_internal * effective_rate

    # Export exemption: Remove PIS, COFINS, and ISS percentages
    export_exemptions = (
        bracket.pis_allocation + bracket.cofins_allocation + bracket.iss_allocation
    ) / Decimal("100")
    effective_export_rate = effective_rate * (Decimal("1.00") - export_exemptions)
    tax_export = revenue_export * effective_export_rate

    total_tax = (tax_internal + tax_export).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    # Calculate CPP portion
    cpp_allocation = bracket.cpp_allocation / Decimal("100")
    cpp_tax_internal = tax_internal * cpp_allocation
    # Assuming export revenue still pays CPP. The CPP allocation is based on the normal effective_rate, not export.
    # Actually, the percentage is applied to the gross tax before deductions?
    # Usually the Simples apportionment applies the percentage to the tax collected.
    cpp_tax_export = (
        tax_export * (cpp_allocation / (Decimal("1.00") - export_exemptions))
        if export_exemptions < 1
        else Decimal("0.00")
    )
    # Wait, it's easier: CPP allocation is a fixed % of the full tax amount before export deductions, but export just exempts some other taxes.
    # So CPP is collected on both at the same nominal rate? No, the formula is: revenue * effective_rate * cpp_allocation.
    cpp_tax = (
        (revenue_internal + revenue_export) * effective_rate * cpp_allocation
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return total_tax, cpp_tax



