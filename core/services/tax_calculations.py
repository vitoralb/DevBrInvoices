import logging
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Sum
from django.db import transaction, models
from django.db.models.functions import Coalesce
from django.conf import settings
from ..models import MonthlyConsolidation, CompanySettings, NotaFiscal
from utils.taxes import (
    get_applicable_bracket,
    get_minimum_salary,
    calculate_inss,
    get_active_table,
)
from .. import signals as _signals

logger = logging.getLogger(__name__)


def calculate_irrf(pro_labore_amount, reference_date):
    inss_deduction = calculate_inss(pro_labore_amount, reference_date)
    base_calc = (Decimal(str(pro_labore_amount)) - inss_deduction).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    logger.debug(
        "Calculating IRRF for Pró-labore: %s, INSS Deduction: %s, Base Calc: %s",
        pro_labore_amount,
        inss_deduction,
        base_calc,
    )

    if base_calc <= Decimal("0.00"):
        return Decimal("0.00")

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


def calculate_rbt12_and_fator_r(target_month_year, use_ideal_pro_labore=False):
    """Calculate trailing 12-month revenue (RBT12) and Fator R for a given month.

    Fator R for Month X is based on payroll and revenue of the 12 preceding months (X-12 to X-1).
    For < 12 months of operation, uses the proportional annualization formula.
    For the very first month, uses current month's values × 12.
    """
    company = CompanySettings.load()
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

    if use_ideal_pro_labore and sum_revenue > 0:
        target_payroll = (sum_revenue * Decimal("0.28")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if sum_payroll < target_payroll:
            pl_sum += target_payroll - sum_payroll
            sum_payroll = target_payroll

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
    company = CompanySettings.load()
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
    cpp_tax = (
        (revenue_internal + revenue_export) * effective_rate * cpp_allocation
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return total_tax, cpp_tax


def is_month_closed(month_year: date, today: date | None = None) -> bool:
    """Retorna True se o mês for considerado fechado:
    - Qualquer mês anterior ao mês passado (month_year < prev_month)
    - O mês passado (month_year == prev_month) se today.day > 7
    """
    if today is None:
        from django.utils import timezone
        today = timezone.localdate()
    first_day = month_year.replace(day=1)
    current_month = today.replace(day=1)
    prev_month = current_month - relativedelta(months=1)
    if first_day < prev_month:
        return True
    if first_day == prev_month and today.day > 7:
        return True
    return False


def get_unsynced_prior_months_for_ideal_pl(target_month: date, all_cons_dict: dict | None = None) -> list[date]:
    """Retorna lista de meses anteriores na janela de cálculo do pró-labore ideal
    (últimos 11 meses até target_month-1, respeitando a data de abertura da empresa)
    que ainda não foram sincronizados com o eSocial.
    """
    company = CompanySettings.load()
    if not company:
        return []

    start_date = target_month.replace(day=1) - relativedelta(months=11)
    if company.opening_date and company.opening_date.replace(day=1) > start_date:
        start_date = company.opening_date.replace(day=1)

    end_date = target_month.replace(day=1) - relativedelta(months=1)
    if start_date > end_date:
        return []

    unsynced = []
    curr = start_date
    while curr <= end_date:
        if all_cons_dict is not None:
            c = all_cons_dict.get(curr)
            if not c or not getattr(c, "esocial_synced", False):
                unsynced.append(curr)
        else:
            c = MonthlyConsolidation.objects.filter(month_year=curr).first()
            if not c or not c.esocial_synced:
                unsynced.append(curr)
        curr += relativedelta(months=1)

    return unsynced


def attach_recommended_pl(consolidation, all_cons_dict=None):
    """Computes and attaches Fator R projection attributes to a MonthlyConsolidation instance.

    Calculates the ideal pró-labore, rolling 11-month revenue/payroll sums, and
    projected Fator R. Results are attached as transient attributes on the consolidation
    object (not persisted to the DB) for display in the dashboard.

    Args:
        consolidation: A MonthlyConsolidation instance.
        all_cons_dict: Optional dict mapping month_year → consolidation for bulk lookups.
                       When provided, avoids extra DB queries per consolidation.
    """
    pl_total = calculate_ideal_pro_labore(
        consolidation.month_year, estimated_current_revenue=consolidation.total_revenue
    )
    consolidation.recommended_pl = pl_total
    consolidation.is_closed = is_month_closed(consolidation.month_year)
    consolidation.unsynced_prior_months = get_unsynced_prior_months_for_ideal_pl(
        consolidation.month_year, all_cons_dict
    )
    consolidation.has_incomplete_esocial_window = bool(consolidation.unsynced_prior_months)
    consolidation.net_pro_labore = max(
        Decimal("0.00"),
        (consolidation.actual_pro_labore_paid or Decimal("0.00"))
        - (consolidation.inss_tax or Decimal("0.00"))
        - (consolidation.irrf_tax or Decimal("0.00")),
    )

    start_date = consolidation.month_year - relativedelta(months=11)
    end_date = consolidation.month_year - relativedelta(months=1)

    if all_cons_dict is not None:
        rev_int = Decimal("0.00")
        rev_exp = Decimal("0.00")
        payroll = Decimal("0.00")
        cpp_sum = Decimal("0.00")
        curr = start_date
        while curr <= end_date:
            past_cons = all_cons_dict.get(curr)
            if past_cons:
                rev_int += past_cons.total_revenue_internal
                rev_exp += past_cons.total_revenue_export
                payroll += past_cons.actual_pro_labore_paid
                if (
                    not hasattr(settings, "CPP_ACCUMULATION_START_DATE")
                    or not settings.CPP_ACCUMULATION_START_DATE
                    or curr >= settings.CPP_ACCUMULATION_START_DATE
                ):
                    cpp_sum += past_cons.das_cpp_tax
            curr += relativedelta(months=1)

        consolidation.proj_rbt12 = rev_int + rev_exp + consolidation.total_revenue
        consolidation.proj_pl_sum = payroll + consolidation.actual_pro_labore_paid
        consolidation.proj_prev_cpp = cpp_sum
    else:
        past = MonthlyConsolidation.objects.filter(
            month_year__gte=start_date, month_year__lte=end_date
        )
        agg = past.aggregate(
            rev_int=Coalesce(Sum("total_revenue_internal"), Decimal("0.00")),
            rev_exp=Coalesce(Sum("total_revenue_export"), Decimal("0.00")),
            payroll=Coalesce(Sum("actual_pro_labore_paid"), Decimal("0.00")),
        )
        consolidation.proj_rbt12 = (
            agg["rev_int"] + agg["rev_exp"] + consolidation.total_revenue
        )

        if (
            hasattr(settings, "CPP_ACCUMULATION_START_DATE")
            and settings.CPP_ACCUMULATION_START_DATE
        ):
            cpp_qs = past.filter(month_year__gte=settings.CPP_ACCUMULATION_START_DATE)
        else:
            cpp_qs = past

        cpp_agg = cpp_qs.aggregate(cpp=Coalesce(Sum("das_cpp_tax"), Decimal("0.00")))
        consolidation.proj_pl_sum = (
            agg["payroll"] + consolidation.actual_pro_labore_paid
        )
        consolidation.proj_prev_cpp = cpp_agg["cpp"]

    # Current CPP
    current_rbt12, _, _, _ = calculate_rbt12_and_fator_r(consolidation.month_year)
    _, current_cpp = calculate_simples_tax(
        Decimal("0.00"),
        consolidation.total_revenue,
        current_rbt12,
        "ANNEX_III",
        consolidation.month_year,
    )

    if (
        hasattr(settings, "CPP_ACCUMULATION_START_DATE")
        and settings.CPP_ACCUMULATION_START_DATE
    ):
        if consolidation.month_year < settings.CPP_ACCUMULATION_START_DATE:
            current_cpp = Decimal("0.00")

    consolidation.proj_cpp = current_cpp

    if consolidation.proj_rbt12 > 0:
        consolidation.proj_fator_r = (
            (consolidation.proj_pl_sum + consolidation.proj_prev_cpp + current_cpp)
            / consolidation.proj_rbt12
            * 100
        ).quantize(Decimal("0.01"))
    else:
        consolidation.proj_fator_r = Decimal("0.00")
