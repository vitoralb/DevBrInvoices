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
from .. import signals as _signals
import requests

logger = logging.getLogger(__name__)

from .tax_calculations import *
def consolidate_month(month_year, actual_pro_labore=None):
    """Aggregates data, determines Annex III vs V, and locks in taxes for a month.

    When first consolidating (no prior pró-labore set and none provided),
    the system auto-sets the pró-labore to the ideal amount needed for Fator R >= 28%.
    """
    _signals.set_consolidation_in_progress(True)
    try:
        return _consolidate_month_inner(month_year, actual_pro_labore)
    finally:
        _signals.set_consolidation_in_progress(False)



@transaction.atomic
def _consolidate_month_inner(month_year, actual_pro_labore=None):
    """Inner implementation of consolidate_month, runs with signal guard active."""
    nfs = NotaFiscal.objects.filter(
        issue_date__year=month_year.year, issue_date__month=month_year.month
    ).exclude(models.Q(is_canceled=True) | models.Q(invoice__status="CANCELED"))
    revenue_export = nfs.filter(is_export=True).aggregate(
        total=Coalesce(Sum("amount_brl"), Decimal("0.00"))
    )["total"]
    revenue_internal = nfs.filter(is_export=False).aggregate(
        total=Coalesce(Sum("amount_brl"), Decimal("0.00"))
    )["total"]

    first_day = month_year.replace(day=1)
    consolidation, created = MonthlyConsolidation.objects.get_or_create(
        month_year=first_day
    )

    if actual_pro_labore is not None:
        consolidation.actual_pro_labore_paid = Decimal(str(actual_pro_labore))
    elif created or consolidation.actual_pro_labore_paid == Decimal("0.00"):
        # Auto-set to ideal pró-labore when first consolidating this month
        current_revenue = revenue_internal + revenue_export
        ideal_pl = calculate_ideal_pro_labore(
            first_day, estimated_current_revenue=current_revenue
        )

        if ideal_pl > Decimal("0.00"):
            consolidation.actual_pro_labore_paid = ideal_pl
            logger.info(
                "Auto-set pró-labore for %s to ideal value: R$ %s", first_day, ideal_pl
            )
        else:
            # No revenue — fall back to minimum salary
            try:
                min_salary = get_minimum_salary(first_day)
                consolidation.actual_pro_labore_paid = min_salary
                logger.info(
                    "Auto-set pró-labore for %s to minimum salary: R$ %s",
                    first_day,
                    min_salary,
                )
            except ValueError:
                logger.warning(
                    "No minimum salary configured for %s, leaving pró-labore at 0",
                    first_day,
                )

    # Save revenue first so RBT12 calculation can see it
    consolidation.total_revenue_internal = revenue_internal
    consolidation.total_revenue_export = revenue_export
    consolidation.save()

    rbt12, fator_r, pl_sum, cpp_sum = calculate_rbt12_and_fator_r(first_day)
    applied_annex = "ANNEX_III" if fator_r >= Decimal("28.00") else "ANNEX_V"

    das_tax, das_cpp_tax = calculate_simples_tax(
        revenue_internal, revenue_export, rbt12, applied_annex, month_year
    )
    inss_tax = calculate_inss(consolidation.actual_pro_labore_paid, month_year)
    irrf_tax = calculate_irrf(consolidation.actual_pro_labore_paid, month_year)

    consolidation.status = "CONSOLIDATED"
    consolidation.rbt12 = rbt12
    consolidation.fator_r_ratio = fator_r
    consolidation.fator_r_payroll_sum = pl_sum
    consolidation.fator_r_cpp_sum = cpp_sum
    consolidation.applied_annex = applied_annex
    consolidation.das_tax = das_tax
    consolidation.das_cpp_tax = das_cpp_tax
    consolidation.inss_tax = inss_tax
    consolidation.irrf_tax = irrf_tax
    consolidation.save()

    return consolidation



@transaction.atomic
def reconsolidate_with_prior(month_year, actual_pro_labore=None):
    """Reconsolidate a specific month, automatically reconsolidating
    any prior OUTDATED months first (oldest to newest) to ensure
    correct cascading RBT12 and Fator R values.
    """
    first_day = month_year.replace(day=1)

    # Find all OUTDATED months prior to (and including) the target
    outdated_prior = MonthlyConsolidation.objects.select_for_update().filter(
        month_year__lt=first_day, status="OUTDATED"
    ).order_by("month_year")

    # Reconsolidate each prior OUTDATED month chronologically
    for prior in outdated_prior:
        logger.info("Auto-reconsolidating prior OUTDATED month: %s", prior.month_year)
        consolidate_month(prior.month_year, prior.actual_pro_labore_paid)

    # Now reconsolidate the target month
    return consolidate_month(first_day, actual_pro_labore)



def audit_consolidations():
    """Audit all consolidation data for incoherences and fix them.

    Checks for:
    1. Months with NFs but no MonthlyConsolidation record (e.g. deleted via admin)
    2. Recalculates ALL consolidations chronologically and finds differences
       between previous values and newly calculated values.

    Returns a dict summarizing findings and actions taken.
    """
    findings = {
        "missing_months": [],
        "differences": [],
        "total_fixed": 0,
    }

    company = CompanySettings.objects.first()
    if not company:
        return findings

    start_date = company.opening_date.replace(day=1)

    # Get max month from NFs just in case there's an NF in the future
    max_nf_date = NotaFiscal.objects.aggregate(Max("issue_date"))["issue_date__max"]

    today = date.today()
    end_date = today.replace(day=1)
    if max_nf_date and max_nf_date.replace(day=1) > end_date:
        end_date = max_nf_date.replace(day=1)

    expected_months = set()
    current = start_date
    while current <= end_date:
        expected_months.add(current)
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    existing_months = set(
        MonthlyConsolidation.objects.values_list("month_year", flat=True)
    )

    missing_months = sorted(expected_months - existing_months)

    for month in missing_months:
        findings["missing_months"].append(month)
        logger.info(
            "Audit: Missing consolidation for %s — creating and consolidating", month
        )
        consolidate_month(month)
        findings["total_fixed"] += 1

    # 2. Re-calculate ALL consolidations chronologically
    all_cons = MonthlyConsolidation.objects.all().order_by("month_year")

    for cons in all_cons:
        # Store old values
        old_vals = {
            "DAS": cons.das_tax,
            "INSS": cons.inss_tax,
            "IRRF": cons.irrf_tax,
            "Pró-labore": cons.actual_pro_labore_paid,
            "RBT12": cons.rbt12,
            "Fator R (%)": cons.fator_r_ratio,
            "Annex": cons.get_applied_annex_display(),
        }

        # Reconsolidate (this saves the new values)
        updated_cons = consolidate_month(cons.month_year, cons.actual_pro_labore_paid)

        # Compare
        changes = []
        new_vals = {
            "DAS": updated_cons.das_tax,
            "INSS": updated_cons.inss_tax,
            "IRRF": updated_cons.irrf_tax,
            "Pró-labore": updated_cons.actual_pro_labore_paid,
            "RBT12": updated_cons.rbt12,
            "Fator R (%)": updated_cons.fator_r_ratio,
            "Annex": updated_cons.get_applied_annex_display(),
        }

        for k in old_vals:
            if old_vals[k] != new_vals[k]:
                old_str = (
                    f"{old_vals[k]:.2f}"
                    if isinstance(old_vals[k], Decimal)
                    else old_vals[k]
                )
                new_str = (
                    f"{new_vals[k]:.2f}"
                    if isinstance(new_vals[k], Decimal)
                    else new_vals[k]
                )
                changes.append(f"{k} changed from {old_str} to {new_str}")

        # If there were any changes (and we didn't just create it as a missing month)
        if changes and cons.month_year not in findings["missing_months"]:
            findings["differences"].append(
                {"month": cons.month_year, "changes": changes}
            )
            findings["total_fixed"] += 1

    logger.info(
        "Audit complete: %d missing, %d differences, %d total fixed",
        len(findings["missing_months"]),
        len(findings["differences"]),
        findings["total_fixed"],
    )

    return findings



