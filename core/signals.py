import logging
import threading
from django.db.models.signals import pre_save, post_save, post_delete
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


@receiver(pre_save, sender=NotaFiscal)
def track_nf_pre_save(sender, instance, **kwargs):
    """Tracks previous values of NotaFiscal before saving to detect if financial/status fields change."""
    if kwargs.get("raw", False) or is_consolidation_in_progress():
        return

    if not instance.pk:
        instance._nf_existed_in_db = False
        return

    try:
        old = (
            NotaFiscal.objects.filter(pk=instance.pk)
            .values("amount_brl", "is_canceled", "issue_date", "is_export")
            .first()
        )
        if old is not None:
            instance._nf_existed_in_db = True
            instance._old_amount_brl = old["amount_brl"]
            instance._old_is_canceled = old["is_canceled"]
            instance._old_issue_date = old["issue_date"]
            instance._old_is_export = old["is_export"]
        else:
            instance._nf_existed_in_db = False
    except Exception:
        instance._nf_existed_in_db = False


@receiver(post_save, sender=NotaFiscal)
@receiver(post_delete, sender=NotaFiscal)
def handle_nf_changes(sender, instance, **kwargs):
    """When an NF is created, modified, or deleted, flag affected months as OUTDATED."""
    if kwargs.get("raw", False):
        return
    if is_consolidation_in_progress():
        return

    # Deletion handling
    if "created" not in kwargs:
        if not instance.is_canceled:
            flag_months_outdated(instance.issue_date)
        return

    created = kwargs.get("created", False)

    # Creation handling: only flag if active (adds revenue)
    if created:
        if not instance.is_canceled:
            flag_months_outdated(instance.issue_date)
        return

    # Update handling: check if financial or status fields changed
    if getattr(instance, "_nf_existed_in_db", False):
        update_fields = kwargs.get("update_fields")
        relevant_fields = {"amount_brl", "is_canceled", "issue_date", "is_export"}

        # If update_fields was explicitly provided and none of the relevant fields are present, skip
        if update_fields is not None and not (relevant_fields & set(update_fields)):
            return

        old_amount = getattr(instance, "_old_amount_brl", None)
        old_canceled = getattr(instance, "_old_is_canceled", None)
        old_date = getattr(instance, "_old_issue_date", None)
        old_export = getattr(instance, "_old_is_export", None)

        amount_changed = (old_amount is not None) and (old_amount != instance.amount_brl)
        canceled_changed = (old_canceled is not None) and (old_canceled != instance.is_canceled)
        date_changed = (old_date is not None) and (old_date != instance.issue_date)
        export_changed = (old_export is not None) and (old_export != instance.is_export)

        if not (amount_changed or canceled_changed or date_changed or export_changed):
            # No financially relevant field changed
            return

        if date_changed and old_date:
            flag_months_outdated(old_date)

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


@receiver(pre_save, sender=Invoice)
def track_invoice_pre_save(sender, instance, **kwargs):
    """Tracks previous status of Invoice to only flag when transitioning to CANCELED."""
    if kwargs.get("raw", False) or is_consolidation_in_progress():
        return
    if not instance.pk:
        return
    try:
        old = Invoice.objects.filter(pk=instance.pk).values("status").first()
        if old is not None:
            instance._old_status = old["status"]
    except Exception:
        pass


@receiver(post_save, sender=Invoice)
def handle_invoice_changes(sender, instance, **kwargs):
    """When an invoice status changes (e.g. to CANCELED), flag affected months."""
    if kwargs.get("raw", False):
        return
    if is_consolidation_in_progress():
        return

    # Only matters if the invoice has a Nota Fiscal and is affecting totals
    if hasattr(instance, "nota_fiscal") and instance.nota_fiscal:
        old_status = getattr(instance, "_old_status", None)
        # Optimization: Only trigger if status changed to CANCELED
        if instance.status == "CANCELED" and old_status != "CANCELED":
            flag_months_outdated(instance.issue_date)

