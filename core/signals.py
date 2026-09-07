import logging
import threading
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from dateutil.relativedelta import relativedelta
from .models import NotaFiscal, MonthlyConsolidation

logger = logging.getLogger(__name__)

# Thread-local guard to prevent recursive signal firing during consolidation
_state = threading.local()


def is_consolidation_in_progress():
    return getattr(_state, "consolidation_in_progress", False)


def set_consolidation_in_progress(value: bool):
    _state.consolidation_in_progress = value


# Module-level backward-compatible proxy object
class _ConsolidationGuard:
    def __bool__(self):
        return is_consolidation_in_progress()


_consolidation_in_progress = _ConsolidationGuard()


def flag_months_outdated(target_date):
    """Flag the target month and the next 12 months as OUTDATED.

    Per §3.7: Changing Month X alters taxes for X+1 through X+12 because
    RBT12 uses 12 months of history. We flag exactly 13 months total
    (the changed month + the next 12).
    """
    first_day_of_month = target_date.replace(day=1)
    end_boundary = first_day_of_month + relativedelta(months=12)

    # Ensure a consolidation record exists for the target month
    MonthlyConsolidation.objects.get_or_create(
        month_year=first_day_of_month, defaults={"status": "OUTDATED"}
    )

    # Flag the target month and up to the next 12 months
    MonthlyConsolidation.objects.filter(
        month_year__gte=first_day_of_month, month_year__lte=end_boundary
    ).update(status="OUTDATED")


@receiver(post_save, sender=NotaFiscal)
@receiver(post_delete, sender=NotaFiscal)
def handle_nf_changes(sender, instance, **kwargs):
    """When an NF is created, modified, or deleted, flag affected months as OUTDATED."""
    if kwargs.get("raw", False):
        return
    if is_consolidation_in_progress():
        return

    first_day_of_month = instance.issue_date.replace(day=1)

    from .services import calculate_ideal_pro_labore, get_minimum_salary
    from decimal import Decimal
    from django.db.models import Sum
    from django.db.models.functions import Coalesce

    # Ensure a consolidation record exists for the target month
    cons, _ = MonthlyConsolidation.objects.get_or_create(
        month_year=first_day_of_month, defaults={"status": "OUTDATED"}
    )

    flag_months_outdated(instance.issue_date)


@receiver(post_save, sender=MonthlyConsolidation)
def handle_consolidation_pro_labore_change(sender, instance, **kwargs):
    """When a consolidation's pró-labore changes outside of the consolidation
    process (e.g., via admin), flag the next month and subsequent 12 months
    as OUTDATED since it affects Fator R calculations.
    """
    if kwargs.get("raw", False):
        return
    # Skip all signal processing during consolidation to prevent recursion
    if is_consolidation_in_progress():
        return

    # Newly created placeholders don't have a changed pró-labore, so don't cascade.
    # This also prevents infinite recursion from flag_months_outdated's get_or_create.
    if kwargs.get("created", False):
        return

    # If update_fields was provided, only react to pró-labore changes
    update_fields = kwargs.get("update_fields")
    if update_fields is not None and "actual_pro_labore_paid" not in update_fields:
        return

    next_month = instance.month_year + relativedelta(months=1)
    flag_months_outdated(next_month)


from .models import Invoice


@receiver(post_save, sender=Invoice)
def handle_invoice_changes(sender, instance, **kwargs):
    """When an invoice status changes (e.g. to CANCELED), flag affected months."""
    if kwargs.get("raw", False):
        return
    if is_consolidation_in_progress():
        return

    # Only matters if the invoice has a Nota Fiscal and is affecting totals
    if hasattr(instance, "nota_fiscal") and instance.nota_fiscal:
        # Optimization: We only strictly need to trigger this if the status is CANCELED
        # because normal finalized invoices are already covered by NotaFiscal post_save.
        if instance.status == "CANCELED":
            flag_months_outdated(instance.issue_date)
