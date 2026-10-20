import logging
import uuid
import io
from datetime import date, datetime
from django.utils import timezone
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Q, Sum, Min, Max, Count
from django.db.models.functions import Coalesce
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    FileResponse,
    JsonResponse,
)
from django.utils.html import escape
from django.utils.http import url_has_allowed_host_and_scheme
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from urllib.parse import parse_qs, quote, urlencode, urlsplit, urlunsplit
from django.views.decorators.http import require_GET, require_POST

from .forms import (
    InvoiceForm,
    InvoiceItemForm,
    EmailTemplateForm,
    InvoiceTemplateForm,
    InvoiceTemplateItemFormSet,
    CompanySettingsForm,
    ClientForm,
    InvoiceDraftMetadataForm,
)
from .models import (
    Client,
    CompanySettings,
    Invoice,
    InvoiceItem,
    MonthlyConsolidation,
    NotaFiscal,
    EmailTemplate,
    InvoiceTemplate,
    InvoiceTemplateItem,
    DEFAULT_NFSE_DESCRIPTION_TEMPLATE,
)
from .pdf_service import generate_pdf_bytes
from .services import (
    audit_consolidations,
    attach_recommended_pl,
    fetch_exchange_rate,
    is_month_closed,
    reconsolidate_with_prior,
)

logger = logging.getLogger(__name__)


def _redirect_with_next(request, default_view, *args, **kwargs):
    """Safely redirects to next param (GET or POST) if internal, otherwise default_view."""
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect(default_view, *args, **kwargs)


def _get_safe_next_url(request, default_url=None):
    """Safely returns validated next param (GET or POST) if internal, otherwise default_url."""
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return default_url


# --- Dashboard & Consolidation ---


@login_required
def dashboard_view(request):
    """Monthly detail dashboard view (landing page).

    Displays detailed financial information for a selected month (defaults to current month):
    - Block 1: Revenue & monthly metrics (RBT12, Fator R, Annex)
    - Block 2: Amounts to pay this month (taxes & pró-labore from previous month)
    - Block 3: Forecast for next month (ideal pró-labore, projected taxes & Fator R)
    - Block 4: List of Invoices and NFS-es issued in the month
    """
    today = timezone.localdate()
    current_month_first = today.replace(day=1)

    month_str = request.GET.get("month", "").strip()
    target_month = current_month_first
    if month_str:
        try:
            target_month = datetime.strptime(month_str, "%Y-%m").date().replace(day=1)
        except ValueError:
            target_month = current_month_first

    company = CompanySettings.load()
    start_date = (
        company.opening_date.replace(day=1)
        if company and company.opening_date
        else current_month_first
    )
    min_nf_date = NotaFiscal.objects.aggregate(Min("issue_date"))["issue_date__min"]
    if min_nf_date and min_nf_date.replace(day=1) < start_date:
        start_date = min_nf_date.replace(day=1)

    # Ensure target consolidation exists and is up to date
    cons = MonthlyConsolidation.objects.filter(month_year=target_month).first()
    if not cons or cons.status == "OUTDATED":
        cons = reconsolidate_with_prior(target_month)

    # Build all consolidations dict for ideal PL calculations
    all_cons_dict = {c.month_year: c for c in MonthlyConsolidation.objects.all()}
    attach_recommended_pl(cons, all_cons_dict)

    # Previous month (M-1) for amounts to pay this month (M)
    prev_month = target_month - relativedelta(months=1)
    prev_cons = all_cons_dict.get(prev_month)
    if prev_cons and prev_cons.status == "OUTDATED":
        prev_cons = reconsolidate_with_prior(prev_month)
        all_cons_dict[prev_month] = prev_cons
    if prev_cons:
        attach_recommended_pl(prev_cons, all_cons_dict)

    # Next month (M+1) for navigation
    next_month = target_month + relativedelta(months=1)

    # Invoices / Notas Fiscais in target month
    nfs = (
        NotaFiscal.objects.filter(
            issue_date__year=target_month.year,
            issue_date__month=target_month.month,
        )
        .select_related("invoice", "invoice__client")
        .order_by("-issue_date", "-created_at")
    )

    pending_invoices = (
        Invoice.objects.filter(
            issue_date__year=target_month.year,
            issue_date__month=target_month.month,
            nota_fiscal__isnull=True,
        )
        .select_related("client")
        .order_by("issue_date", "invoice_number")
    )

    # Build list of available months for navigation dropdown
    max_month = max(current_month_first, target_month)
    available_months = []
    curr = max_month
    while curr >= start_date:
        available_months.append(curr)
        curr -= relativedelta(months=1)

    has_prev = prev_month >= start_date
    has_next = target_month < max_month

    return render(
        request,
        "core/mes_detail.html",
        {
            "consolidation": cons,
            "prev_consolidation": prev_cons,
            "target_month": target_month,
            "prev_month": prev_month,
            "next_month": next_month,
            "current_month_first": current_month_first,
            "notas_fiscais": nfs,
            "pending_invoices": pending_invoices,
            "available_months": available_months,
            "has_prev": has_prev,
            "has_next": has_next,
            "company": company,
        },
    )


@login_required
def consolidation_history_view(request):
    """Historical multi-month consolidation table view with filters."""
    qs = MonthlyConsolidation.objects.all()
    today = timezone.localdate()

    if "quick_filter" in request.GET or "start_date" in request.GET:
        quick_filter = request.GET.get("quick_filter", "")
        start_date_val = request.GET.get("start_date", "")
        end_date_val = request.GET.get("end_date", "")
    else:
        quick_filter = str(today.year)
        start_date_val = f"{today.year}-01-01"
        end_date_val = f"{today.year}-12-31"

    if quick_filter == "past_6_months":
        end = (today.replace(day=1) + relativedelta(months=1)) - relativedelta(days=1)
        start = today.replace(day=1) - relativedelta(months=6)
        qs = qs.filter(month_year__gte=start, month_year__lte=end)
        start_date_val = start.strftime("%Y-%m-%d")
        end_date_val = end.strftime("%Y-%m-%d")
    elif quick_filter == "past_12_months":
        end = (today.replace(day=1) + relativedelta(months=1)) - relativedelta(days=1)
        start = today.replace(day=1) - relativedelta(months=12)
        qs = qs.filter(month_year__gte=start, month_year__lte=end)
        start_date_val = start.strftime("%Y-%m-%d")
        end_date_val = end.strftime("%Y-%m-%d")
    elif quick_filter and quick_filter.isdigit():
        year = int(quick_filter)
        qs = qs.filter(month_year__year=year)
        start_date_val = f"{year}-01-01"
        end_date_val = f"{year}-12-31"
    else:
        if start_date_val:
            try:
                sd = datetime.strptime(start_date_val, "%Y-%m-%d").date()
                qs = qs.filter(month_year__gte=sd)
            except ValueError:
                pass
        if end_date_val:
            try:
                ed = datetime.strptime(end_date_val, "%Y-%m-%d").date()
                qs = qs.filter(month_year__lte=ed)
            except ValueError:
                pass

    consolidations = list(qs.order_by("-month_year"))
    all_cons_dict = {c.month_year: c for c in MonthlyConsolidation.objects.all()}
    for c in consolidations:
        attach_recommended_pl(c, all_cons_dict)

    total_revenue = sum(c.total_revenue for c in consolidations)
    total_tax = sum(c.total_tax for c in consolidations)
    total_pl = sum(c.actual_pro_labore_paid for c in consolidations)
    net_profit = total_revenue - total_tax - total_pl

    available_years = list(
        MonthlyConsolidation.objects.dates("month_year", "year")
        .values_list("month_year__year", flat=True)
        .distinct()
    )
    available_years.sort(reverse=True)
    if today.year not in available_years:
        available_years.insert(0, today.year)

    return render(
        request,
        "core/dashboard.html",
        {
            "consolidations": consolidations,
            "total_revenue": total_revenue,
            "total_tax": total_tax,
            "total_pl": total_pl,
            "net_profit": net_profit,
            "available_years": available_years,
            "quick_filter": quick_filter,
            "start_date": start_date_val,
            "end_date": end_date_val,
            "current_month_first": today.replace(day=1),
        },
    )


@login_required
@require_POST
def htmx_reconsolidate_month(request, pk):
    consolidation = get_object_or_404(MonthlyConsolidation, pk=pk)

    actual_pl_str = request.POST.get("actual_pro_labore_paid", "").strip()
    actual_pl = None
    force_pl = False
    if actual_pl_str:
        if is_month_closed(consolidation.month_year):
            return HttpResponseBadRequest(
                "Meses passados são sincronizados via eSocial e não permitem edição manual."
            )
        try:
            actual_pl = Decimal(actual_pl_str.replace(",", "."))
            force_pl = True
        except Exception:
            return HttpResponseBadRequest("Valor de pró-labore inválido.")

    try:
        consolidation = reconsolidate_with_prior(
            consolidation.month_year,
            actual_pro_labore=actual_pl,
            force_actual_pro_labore=force_pl,
        )
        next_url = request.GET.get("next") or request.POST.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            if not request.headers.get("HX-Request"):
                messages.success(
                    request,
                    f"Mês {consolidation.month_year.strftime('%m/%Y')} recalculado com sucesso.",
                )
                return redirect(next_url)
            else:
                response = HttpResponse()
                response["HX-Redirect"] = next_url
                return response

        if request.headers.get("HX-Request"):
            response = HttpResponse()
            response["HX-Refresh"] = "true"
            return response

        attach_recommended_pl(consolidation)
        return render(
            request,
            "core/partials/consolidation_row.html",
            {
                "consolidation": consolidation,
                "current_month_first": timezone.localdate().replace(day=1),
            },
        )
    except Exception as e:
        logger.error("Error reconsolidating month %s: %s", consolidation.month_year, e)
        return HttpResponseBadRequest(
            "Erro ao reconsolidar. Verifique os logs para detalhes."
        )


@login_required
@staff_member_required
@require_POST
def run_audit(request):
    try:
        findings = audit_consolidations()
        fixed = findings.get("total_fixed", 0)
        if fixed > 0:
            messages.success(
                request, f"Auditoria concluída: {fixed} registro(s) corrigido(s)."
            )
        else:
            messages.info(request, "Auditoria concluída: nenhuma diferença encontrada.")
    except Exception as e:
        logger.error("Audit failed: %s", e)
        messages.error(request, "Erro ao executar a auditoria. Verifique os logs.")
    return _redirect_with_next(request, "dashboard")


@login_required
@staff_member_required
@require_POST
def sync_esocial_view(request):
    try:
        from core.services.esocial_services import sync_esocial_payroll

        count, msg = sync_esocial_payroll(force=True)
        if count > 0:
            messages.success(request, msg)
        else:
            messages.info(request, msg)
    except Exception as e:
        logger.error("eSocial sync failed: %s", e)
        messages.error(request, f"Erro ao sincronizar com o eSocial: {str(e)}")
    return _redirect_with_next(request, "dashboard")


@login_required
@staff_member_required
def export_esocial_backup_view(request):
    try:
        from core.services.esocial_services import export_esocial_backup

        zip_bytes, filename = export_esocial_backup()
        response = HttpResponse(zip_bytes, content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        logger.error("Failed to export eSocial backup: %s", e)
        messages.error(request, f"Erro ao exportar backup do eSocial: {str(e)}")
        return _redirect_with_next(request, "dashboard")


@login_required
@staff_member_required
@require_POST
def import_esocial_backup_view(request):
    uploaded_files = request.FILES.getlist("backup_file")
    if not uploaded_files:
        messages.warning(
            request,
            "Nenhum arquivo enviado. Selecione um ou mais arquivos ZIP ou XML do eSocial.",
        )
        return _redirect_with_next(request, "dashboard")

    try:
        from core.services.esocial_services import import_esocial_backup

        files_payload = [(f.read(), f.name) for f in uploaded_files]
        res = import_esocial_backup(files_payload)
        if res.get("count", 0) > 0:
            messages.success(
                request, res.get("message", "Importação realizada com sucesso.")
            )
        else:
            messages.warning(
                request, res.get("message", "Nenhum dado importado.")
            )
    except Exception as e:
        logger.error("Failed to import eSocial backup: %s", e)
        messages.error(request, f"Falha ao processar arquivo(s) do eSocial: {str(e)}")

    return _redirect_with_next(request, "dashboard")


# --- Invoices Management ---


@login_required
def invoice_list(request):
    client_id = request.GET.get("client_id", "")
    status = request.GET.get("status", "")
    year = (
        request.GET.get("year", "") if "year" in request.GET else str(date.today().year)
    )
    company = CompanySettings.load()

    invoices = Invoice.objects.select_related("client", "nota_fiscal").all()

    if client_id:
        invoices = invoices.filter(client_id=client_id)
    if status:
        invoices = invoices.filter(status=status)
    if year and year.isdigit():
        invoices = invoices.filter(issue_date__year=int(year))

    invoices = invoices.order_by("-issue_date")
    clients = Client.objects.all()

    available_years = list(
        Invoice.objects.dates("issue_date", "year")
        .values_list("issue_date__year", flat=True)
        .distinct()
    )
    available_years.sort(reverse=True)
    if date.today().year not in available_years:
        available_years.insert(0, date.today().year)

    return render(
        request,
        "core/invoice_list.html",
        {
            "invoices": invoices,
            "clients": clients,
            "available_years": available_years,
            "selected_client": client_id,
            "selected_status": status,
            "selected_year": year,
            "debug_mode": company.debug_mode if company else False,
        },
    )


@login_required
@transaction.atomic
def invoice_create(request):
    from .forms import InvoiceItemFormSet

    safe_next = _get_safe_next_url(request, None)

    if request.method == "POST":
        form = InvoiceForm(request.POST)
        formset = InvoiceItemFormSet(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            formset.instance = invoice
            if formset.is_valid():
                invoice.save()
                items = formset.save()

                from .utils.macros import apply_invoice_macros

                for item in items:
                    item.description = apply_invoice_macros(
                        item.description, invoice, language="en"
                    )
                    item.save()

                messages.success(request, "Invoice criada com sucesso.")
                detail_url = reverse("invoice_detail", kwargs={"pk": invoice.id})
                if safe_next:
                    return redirect(f"{detail_url}?next={quote(safe_next)}")
                return redirect(detail_url)
    else:
        initial = {"nfse_description": DEFAULT_NFSE_DESCRIPTION_TEMPLATE}
        client_id = request.GET.get("client_id")
        if client_id:
            initial["client"] = client_id
        form = InvoiceForm(initial=initial)
        formset = InvoiceItemFormSet()

    invoice_templates = InvoiceTemplate.objects.all()
    return render(
        request,
        "core/invoice_form.html",
        {
            "form": form,
            "formset": formset,
            "invoice_templates": invoice_templates,
            "next_url": safe_next or "",
        },
    )


@login_required
def invoice_detail(request, pk, extra_context=None):
    invoice = get_object_or_404(Invoice, pk=pk)
    item_form = InvoiceItemForm()
    company = CompanySettings.load()

    suggested_exchange_rate = None
    if invoice.status == "FINALIZED" and (
        not hasattr(invoice, "nota_fiscal") or not invoice.nota_fiscal
    ):
        try:
            suggested_exchange_rate = fetch_exchange_rate(
                invoice.issue_date, invoice.currency
            )
        except Exception:
            pass

    latest_nfse_log = invoice.nfse_logs.order_by("-created_at").first()
    nfse_logs = invoice.nfse_logs.order_by("-created_at")[:10]
    back_url = _get_safe_next_url(request, reverse("invoice_list"))

    context = {
        "invoice": invoice,
        "item_form": item_form,
        "company": company,
        "suggested_exchange_rate": suggested_exchange_rate,
        "latest_nfse_log": latest_nfse_log,
        "nfse_logs": nfse_logs,
        "all_clients": Client.objects.all(),
        "back_url": back_url,
    }
    if extra_context:
        context.update(extra_context)

    return render(
        request,
        "core/invoice_detail.html",
        context,
    )


@login_required
@require_POST
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if invoice.status == "DRAFT":
        invoice.delete()
        messages.success(request, "Invoice excluída com sucesso.")
    else:
        messages.error(request, "Apenas invoices em rascunho podem ser excluídas.")
    return _redirect_with_next(request, "invoice_list")


@login_required
@require_POST
def revert_invoice_to_draft(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    has_nfse = hasattr(invoice, "nota_fiscal") and invoice.nota_fiscal is not None
    if invoice.status == "FINALIZED" and not has_nfse:
        invoice.status = "DRAFT"
        invoice.save()
        messages.success(request, "Invoice revertida para rascunho.")
    else:
        messages.error(
            request,
            "Apenas invoices finalizadas sem NFS-e podem ser revertidas para rascunho.",
        )
    return _redirect_with_next(request, "invoice_detail", pk=invoice.id)


@login_required
@require_POST
def htmx_add_invoice_item(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if invoice.status != "DRAFT":
        return HttpResponseForbidden(
            "Apenas invoices em rascunho podem ser modificadas."
        )
    form = InvoiceItemForm(request.POST)
    if form.is_valid():
        item = form.save(commit=False)
        item.invoice = invoice

        from .utils.macros import apply_invoice_macros

        item.description = apply_invoice_macros(
            item.description, invoice, language="en"
        )

        item.save()
        response = render(
            request, "core/partials/invoice_item_list.html", {"invoice": invoice}
        )
        response["HX-Trigger"] = "itemAdded"
        return response
    else:
        return HttpResponseBadRequest("Dados do formulário inválidos.")


@login_required
def htmx_edit_invoice_item(request, item_pk):
    item = get_object_or_404(InvoiceItem.objects.select_related("invoice"), pk=item_pk)
    invoice = item.invoice
    if invoice.status != "DRAFT":
        return HttpResponseForbidden(
            "Apenas itens de invoices em rascunho podem ser editados."
        )

    if request.method == "POST":
        form = InvoiceItemForm(request.POST, instance=item)
        if form.is_valid():
            item = form.save(commit=False)
            from .utils.macros import apply_invoice_macros

            item.description = apply_invoice_macros(
                item.description, invoice, language="en"
            )
            item.save()
            response = render(
                request,
                "core/partials/invoice_item_list.html",
                {"invoice": invoice},
            )
            response["HX-Trigger"] = "itemUpdated"
            return response
        else:
            return HttpResponseBadRequest("Dados do formulário inválidos.")

    # GET request - return inline edit row
    return render(
        request,
        "core/partials/invoice_item_row_edit.html",
        {"item": item, "invoice": invoice},
    )


@login_required
@require_POST
def htmx_delete_invoice_item(request, item_pk):
    item = get_object_or_404(InvoiceItem, pk=item_pk)
    invoice = item.invoice
    if invoice.status == "DRAFT":
        item.delete()
    return render(request, "core/partials/invoice_item_list.html", {"invoice": invoice})


@login_required
@require_POST
def htmx_update_invoice_metadata(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if invoice.status != "DRAFT":
        return HttpResponseForbidden(
            "Apenas invoices em rascunho podem ser modificadas."
        )
    form = InvoiceDraftMetadataForm(request.POST, instance=invoice)
    metadata_form_invalid = False
    metadata_errors = None
    metadata_saved = False
    if form.is_valid():
        form.save()
        metadata_saved = True
    else:
        metadata_form_invalid = True
        metadata_errors = form.errors

    if request.headers.get("HX-Request"):
        return invoice_detail(
            request,
            pk,
            extra_context={
                "metadata_form_invalid": metadata_form_invalid,
                "metadata_errors": metadata_errors,
                "metadata_saved": metadata_saved,
            },
        )
    return _redirect_with_next(request, "invoice_detail", pk=pk)


@login_required
@require_POST
def htmx_update_invoice_number(request, pk):
    from django.http import HttpResponse, HttpResponseBadRequest

    invoice = get_object_or_404(Invoice, pk=pk)
    if invoice.status == "DRAFT":
        new_number = request.POST.get("invoice_number", "").strip()
        if new_number:
            if (
                Invoice.objects.filter(invoice_number=new_number)
                .exclude(pk=invoice.pk)
                .exists()
            ):
                return HttpResponseBadRequest("Este número de invoice já existe.")
            invoice.invoice_number = new_number
            invoice.save()
            return HttpResponse(new_number)
    return HttpResponseBadRequest("Inválido.")


@login_required
@require_POST
def htmx_update_bank_details(request, pk):
    from django.http import HttpResponseBadRequest

    invoice = get_object_or_404(Invoice, pk=pk)
    if invoice.status == "DRAFT":
        invoice.bank_details = request.POST.get("bank_details", "").strip()
        invoice.save(update_fields=["bank_details", "updated_at"])
        return render(
            request,
            "core/partials/invoice_bank_details.html",
            {"invoice": invoice},
        )
    return HttpResponseBadRequest(
        "Apenas invoices em rascunho podem ter dados bancários alterados."
    )


@login_required
@require_POST
def htmx_update_nfse_description(request, pk):
    from django.http import HttpResponseBadRequest
    from .forms import VALID_INVOICE_MACROS, validate_macros
    from django.core.exceptions import ValidationError

    invoice = get_object_or_404(Invoice, pk=pk)
    if invoice.status != "DRAFT":
        return HttpResponseBadRequest(
            "Apenas invoices em rascunho podem ter a descrição da NFS-e alterada."
        )

    new_text = request.POST.get("nfse_description", "").strip()
    error_message = None
    if not new_text:
        error_message = "A descrição da NFS-e é obrigatória."
    else:
        try:
            validate_macros(new_text, VALID_INVOICE_MACROS)
        except ValidationError as e:
            error_message = e.message

    if error_message:
        return render(
            request,
            "core/partials/invoice_nfse_description.html",
            {
                "invoice": invoice,
                "error_message": error_message,
                "draft_text": new_text,
                "is_editing": True,
            },
            status=400,
        )

    invoice.nfse_description = new_text
    invoice.save(update_fields=["nfse_description", "updated_at"])
    return render(
        request,
        "core/partials/invoice_nfse_description.html",
        {"invoice": invoice},
    )


@login_required
@require_POST
def htmx_update_fiscal_codes(request, pk):
    from django.http import HttpResponseBadRequest

    invoice = get_object_or_404(Invoice, pk=pk)
    if invoice.status != "DRAFT":
        return HttpResponseBadRequest(
            "Apenas invoices em rascunho podem ter os códigos fiscais alterados."
        )

    trib_nac = request.POST.get("codigo_tributacao_nacional", "").strip()
    serv_mun = request.POST.get("codigo_servico_municipio", "").strip()
    nbs = request.POST.get("codigo_nbs", "").strip()

    cst_ibs = request.POST.get("cst_ibs_cbs", "").strip()
    c_class = request.POST.get("c_class_trib_ibs_cbs", "").strip()
    c_ind = request.POST.get("c_ind_op_ibs_cbs", "").strip()

    error_message = None
    if not trib_nac:
        error_message = "O Código de Tributação Nacional é obrigatório."
    elif not nbs:
        error_message = "O Código NBS é obrigatório."
    elif len(cst_ibs) > 3:
        error_message = "O CST do IBS/CBS deve ter no máximo 3 caracteres."
    elif len(c_class) > 6:
        error_message = "A Classificação IBS/CBS (cClassTrib) deve ter no máximo 6 caracteres."
    elif len(c_ind) > 6:
        error_message = "O Indicador da Operação (cIndOp) deve ter no máximo 6 caracteres."

    if error_message:
        return render(
            request,
            "core/partials/invoice_fiscal_codes.html",
            {
                "invoice": invoice,
                "error_message": error_message,
                "draft_trib_nac": trib_nac,
                "draft_serv_mun": serv_mun,
                "draft_nbs": nbs,
                "draft_cst_ibs": cst_ibs,
                "draft_c_class": c_class,
                "draft_c_ind": c_ind,
                "is_editing": True,
            },
            status=400,
        )

    invoice.codigo_tributacao_nacional = trib_nac
    invoice.codigo_servico_municipio = serv_mun
    invoice.codigo_nbs = nbs
    update_fields = [
        "codigo_tributacao_nacional",
        "codigo_servico_municipio",
        "codigo_nbs",
        "updated_at",
    ]
    if "cst_ibs_cbs" in request.POST:
        invoice.cst_ibs_cbs = cst_ibs
        update_fields.append("cst_ibs_cbs")
    if "c_class_trib_ibs_cbs" in request.POST:
        invoice.c_class_trib_ibs_cbs = c_class
        update_fields.append("c_class_trib_ibs_cbs")
    if "c_ind_op_ibs_cbs" in request.POST:
        invoice.c_ind_op_ibs_cbs = c_ind
        update_fields.append("c_ind_op_ibs_cbs")

    invoice.save(update_fields=update_fields)
    return render(
        request,
        "core/partials/invoice_fiscal_codes.html",
        {"invoice": invoice},
    )


@login_required
@require_POST
def finalize_invoice(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)

    if invoice.status != "DRAFT":
        messages.error(request, "Apenas invoices em rascunho podem ser finalizadas.")
        return _redirect_with_next(request, "invoice_detail", pk=invoice.id)

    send_to_client = request.POST.get("send_to_client") == "on"
    send_to_company = request.POST.get("send_to_company") == "on"

    invoice.status = "PROCESSING"
    from .tasks import finalize_invoice_task

    task = finalize_invoice_task.delay(
        invoice.id, send_to_client=send_to_client, send_to_company=send_to_company
    )
    invoice.task_id = task.id
    invoice.save(update_fields=["status", "task_id", "updated_at"])

    messages.success(request, "Processo de finalização iniciado em segundo plano.")
    return _redirect_with_next(request, "invoice_detail", pk=invoice.id)


@login_required
@require_POST
def cancel_invoice(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)

    if invoice.status == "CANCELED":
        messages.error(request, "Esta invoice já foi cancelada.")
        return _redirect_with_next(request, "invoice_detail", pk=invoice.id)

    if invoice.status == "DRAFT":
        messages.error(
            request, "Invoices em rascunho devem ser excluídas, não canceladas."
        )
        return _redirect_with_next(request, "invoice_detail", pk=invoice.id)

    if (
        hasattr(invoice, "nota_fiscal")
        and invoice.nota_fiscal
        and not invoice.nota_fiscal.can_be_canceled
    ):
        messages.error(
            request,
            "A NFS-e vinculada a esta invoice foi autorizada há mais de 24 horas e não pode ser cancelada diretamente pelo sistema.",
        )
        return _redirect_with_next(request, "invoice_detail", pk=invoice.id)

    invoice.status = "PROCESSING"
    from .tasks import cancel_invoice_task

    task = cancel_invoice_task.delay(invoice.id)
    invoice.task_id = task.id
    invoice.save(update_fields=["status", "task_id", "updated_at"])

    messages.success(request, "Processo de cancelamento iniciado em segundo plano.")
    return _redirect_with_next(request, "invoice_detail", pk=invoice.id)


@login_required
@require_POST
def issue_nfse(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)

    if invoice.status != "FINALIZED":
        messages.error(request, "Apenas invoices finalizadas podem ter NFS-e emitida.")
        return _redirect_with_next(request, "invoice_detail", pk=invoice.id)

    exchange_rate_str = request.POST.get("exchange_rate")
    if not exchange_rate_str:
        messages.error(request, "A taxa de câmbio é obrigatória para emissão da NFS-e.")
        return _redirect_with_next(request, "invoice_detail", pk=invoice.id)

    try:
        exchange_rate = Decimal(exchange_rate_str.replace(",", "."))
        if exchange_rate <= 0:
            raise ValueError()
    except Exception:
        messages.error(request, "Taxa de câmbio inválida.")
        return _redirect_with_next(request, "invoice_detail", pk=invoice.id)

    send_to_company = request.POST.get("send_to_company") == "on"
    send_to_client = request.POST.get("send_to_client") == "on"

    invoice.status = "PROCESSING"
    from .tasks import issue_nfse_task

    task = issue_nfse_task.delay(
        invoice.id,
        str(exchange_rate),
        send_to_company=send_to_company,
        send_to_client=send_to_client,
    )
    invoice.task_id = task.id
    invoice.save(update_fields=["status", "task_id", "updated_at"])

    messages.success(request, "Processo de emissão da NFS-e iniciado em segundo plano.")
    return _redirect_with_next(request, "invoice_detail", pk=invoice.id)


@login_required
def generate_invoice_pdf(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    company = CompanySettings.load()

    if not company:
        messages.error(
            request,
            "Configurações da empresa não encontradas. Por favor, configure-as no painel admin.",
        )
        return redirect("invoice_detail", pk=invoice.id)

    pdf = generate_pdf_bytes(invoice, company)
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{invoice.invoice_number}.pdf"'
    return response


@login_required
def download_nfse_pdf(request, pk):
    """Backward-compatible wrapper for downloading an invoice's NFS-e PDF, delegating to nfse_download_pdf."""
    invoice = get_object_or_404(Invoice, pk=pk)
    nf = getattr(invoice, "nota_fiscal", None)
    if not nf:
        messages.error(request, "Nenhuma NFS-e associada a esta invoice.")
        return redirect("invoice_detail", pk=invoice.id)
    return nfse_download_pdf(request, pk=nf.id, redirect_view="invoice_detail")



@login_required
@require_POST
@transaction.atomic
def clone_invoice(request, pk):
    original = get_object_or_404(Invoice, pk=pk)
    new_invoice = Invoice.objects.create(
        client=original.client,
        invoice_number=f"CLONE-{uuid.uuid4().hex[:6]}",
        issue_date=date.today(),
        currency=original.currency,
        bank_details=original.bank_details,
        nfse_description=original.nfse_description,
        codigo_tributacao_nacional=original.codigo_tributacao_nacional,
        codigo_servico_municipio=original.codigo_servico_municipio,
        codigo_nbs=original.codigo_nbs,
        cst_ibs_cbs=original.cst_ibs_cbs,
        c_class_trib_ibs_cbs=original.c_class_trib_ibs_cbs,
        c_ind_op_ibs_cbs=original.c_ind_op_ibs_cbs,
    )
    for item in original.items.all():
        InvoiceItem.objects.create(
            invoice=new_invoice,
            description=item.description,
            quantity=item.quantity,
            unit_price_foreign=item.unit_price_foreign,
        )
    messages.success(
        request, "Invoice clonada com sucesso. Por favor, atualize o número da invoice."
    )
    return redirect("invoice_detail", pk=new_invoice.id)


@login_required
@require_POST
def email_invoice(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    company = CompanySettings.load()

    send_to_company = request.POST.get("send_to_company") == "on"
    send_to_client = request.POST.get("send_to_client") == "on"
    include_nfse = request.POST.get("include_nfse") == "on"

    if not (send_to_company or send_to_client):
        messages.error(request, "Nenhum destinatário selecionado.")
        return redirect("invoice_detail", pk=invoice.id)

    if not company:
        messages.error(request, "Configurações da empresa não encontradas.")
        return redirect("invoice_detail", pk=invoice.id)

    invoice.status = "PROCESSING"
    from .tasks import email_invoice_task

    task = email_invoice_task.delay(
        invoice.id,
        send_to_company=send_to_company,
        send_to_client=send_to_client,
        include_nfse=include_nfse,
    )
    invoice.task_id = task.id
    invoice.save(update_fields=["status", "task_id", "updated_at"])

    messages.success(request, "Envio de e-mail iniciado em segundo plano.")
    return redirect("invoice_detail", pk=invoice.id)


@login_required
@require_GET
def htmx_fetch_exchange_rate(request):
    date_str = request.GET.get("conversion_date")
    currency = request.GET.get("currency", "CAD")

    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            target_date = date.today()
    else:
        target_date = date.today()

    rate = fetch_exchange_rate(target_date, currency)
    return render(
        request,
        "core/partials/exchange_rate_input.html",
        {"currency": currency, "rate": rate},
    )


@login_required
@staff_member_required
def tasks_view(request):
    from celery import current_app

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "purge":
            current_app.control.purge()
            messages.success(request, "Fila do Celery limpa com sucesso.")
        elif action == "revoke":
            task_id = request.POST.get("task_id")
            if task_id:
                current_app.control.revoke(task_id, terminate=True)
                messages.success(request, f"Tarefa {task_id} revogada.")
        elif action == "cancel_retry":
            invoice_id = request.POST.get("invoice_id")
            invoice = get_object_or_404(Invoice, id=invoice_id)
            if invoice.task_id:
                current_app.control.revoke(invoice.task_id, terminate=True)
            invoice.task_id = ""
            invoice.task_retry_count = 0
            invoice.status = "FINALIZED"
            invoice.save(update_fields=["task_id", "task_retry_count", "status", "updated_at"])
            messages.success(
                request,
                f"Tentativas canceladas para a invoice {invoice.invoice_number}.",
            )
        return redirect("tasks_view")

    try:
        inspector = current_app.control.inspect()
        active = inspector.active() or {}
        reserved = inspector.reserved() or {}
        scheduled = inspector.scheduled() or {}
    except Exception as e:
        active, reserved, scheduled = {}, {}, {}
        logger.warning("Could not connect to Celery broker: %s", e)
        messages.error(request, f"Não foi possível conectar ao Celery broker: {e}")

    retrying_invoices = Invoice.objects.filter(task_retry_count__gt=0)

    context = {
        "active_tasks": active,
        "reserved_tasks": reserved,
        "scheduled_tasks": scheduled,
        "retrying_invoices": retrying_invoices,
    }
    return render(request, "core/tasks_list.html", context)


@login_required
@staff_member_required
@require_POST
def force_process_daily_invoices(request):
    from .tasks import process_daily_invoices_task

    process_daily_invoices_task.delay(force=True)
    messages.success(
        request, "Processamento diário de invoices iniciado em segundo plano."
    )
    return _redirect_with_next(request, "invoice_list")


from django.http import HttpResponse
from celery.result import AsyncResult
from .tasks import import_nfses_task


@login_required
def nfse_list(request):
    query = request.GET.get("q", "").strip()
    provider_filter = request.GET.get("provider", "").strip().upper()
    status_filter = request.GET.get("status", "").strip().upper()

    notas_qs = (
        NotaFiscal.objects.select_related("invoice", "invoice__client")
        .all()
        .order_by(
            F("data_hora_autorizacao").desc(nulls_last=True),
            "-issue_date",
            "-created_at",
        )
    )

    if query:
        notas_qs = notas_qs.filter(
            Q(nf_number__icontains=query)
            | Q(chave_acesso_nacional__icontains=query)
            | Q(verification_code__icontains=query)
            | Q(description__icontains=query)
            | Q(invoice__invoice_number__icontains=query)
            | Q(invoice__client__name__icontains=query)
        )

    if provider_filter == "NACIONAL":
        notas_qs = notas_qs.filter(chave_acesso_nacional__regex=r"^\d{7}2")
    elif provider_filter == "PAULISTANA":
        notas_qs = notas_qs.exclude(chave_acesso_nacional__regex=r"^\d{7}2")

    if status_filter == "ACTIVE":
        notas_qs = notas_qs.filter(is_canceled=False)
    elif status_filter == "CANCELED":
        notas_qs = notas_qs.filter(is_canceled=True)

    paginator = Paginator(notas_qs, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    company = CompanySettings.load()
    return render(
        request,
        "core/nfse_list.html",
        {
            "page_obj": page_obj,
            "notas": page_obj,
            "query": query,
            "selected_provider": provider_filter,
            "selected_status": status_filter,
            "company": company,
        },
    )


@login_required
@require_POST
def nfse_import(request):
    provider = request.POST.get("provider")

    # Trigger Celery Task
    task = import_nfses_task.delay(provider)

    # Return HTMX polling snippet
    return render(
        request,
        "core/partials/import_status.html",
        {"state": "pending", "task_id": task.id},
    )


@login_required
def htmx_import_status(request, task_id):
    res = AsyncResult(task_id)
    if res.ready():
        if res.successful():
            result_data = res.result
            msg = result_data.get("message", "Importação concluída.")
            return render(
                request,
                "core/partials/import_status.html",
                {
                    "state": "success",
                    "message": msg,
                },
            )
        else:
            return render(
                request,
                "core/partials/import_status.html",
                {
                    "state": "error",
                    "message": str(res.result),
                },
            )

    return render(
        request,
        "core/partials/import_status.html",
        {
            "state": "pending",
            "task_id": task_id,
        },
    )


@login_required
def nfse_detail(request, pk):
    nf = get_object_or_404(
        NotaFiscal.objects.select_related("invoice", "invoice__client"), pk=pk
    )
    invoices = (
        Invoice.objects.filter(nota_fiscal__isnull=True)
        .select_related("client")
        .order_by("-issue_date")
        if not nf.invoice
        else []
    )
    nfse_logs = list(nf.nfse_logs.order_by("-created_at")[:20])
    if not nfse_logs and nf.invoice:
        nfse_logs = list(nf.invoice.nfse_logs.order_by("-created_at")[:20])
    nf_events = list(nf.events.order_by("-created_at"))

    is_canceling = False
    if not nf.is_canceled:
        if cache.get(f"nfse_canceling_{nf.pk}"):
            is_canceling = True
        elif nf.invoice and nf.invoice.status == "PROCESSING":
            is_canceling = True
    else:
        cache.delete(f"nfse_canceling_{nf.pk}")

    has_errors = any(not log.is_success or bool(log.display_error) for log in nfse_logs)
    back_url = _get_safe_next_url(request, reverse("nfse_list"))

    return render(
        request,
        "core/nfse_detail.html",
        {
            "nf": nf,
            "invoices": invoices,
            "nfse_logs": nfse_logs,
            "nf_events": nf_events,
            "is_canceling": is_canceling,
            "back_url": back_url,
            "has_errors": has_errors,
        },
    )


@login_required
@require_POST
def nfse_refresh(request, pk):
    from core.services.nfse_services import sync_nota_fiscal

    nf = get_object_or_404(NotaFiscal, pk=pk)
    success, msg = sync_nota_fiscal(nf)
    if success:
        messages.success(request, msg)
    else:
        messages.error(request, msg)
    return _redirect_with_next(request, "nfse_detail", pk=pk)


@login_required
@require_POST
@transaction.atomic
def nfse_link_invoice(request, pk):
    nf = get_object_or_404(NotaFiscal, pk=pk)
    invoice_id = request.POST.get("invoice_id")
    if invoice_id:
        # Check if already linked
        invoice = get_object_or_404(Invoice, pk=invoice_id)
        existing_nf = getattr(invoice, "nota_fiscal", None)
        if existing_nf and existing_nf.pk != nf.pk:
            messages.error(request, "Esta invoice já possui uma NFS-e vinculada.")
        else:
            nf.invoice = invoice
            nf.save()
            messages.success(request, "Invoice vinculada com sucesso.")
    return _redirect_with_next(request, "nfse_detail", pk=pk)


@login_required
@require_POST
def nfse_cancel(request, pk):
    nf = get_object_or_404(NotaFiscal, pk=pk)

    if nf.is_canceled:
        messages.error(request, "Esta NFS-e já está cancelada.")
        return _redirect_with_next(request, "nfse_detail", pk=pk)

    if not nf.can_be_canceled:
        messages.error(
            request,
            "Esta NFS-e foi autorizada há mais de 24 horas e não pode ser cancelada diretamente pelo sistema.",
        )
        return _redirect_with_next(request, "nfse_detail", pk=pk)

    if nf.invoice:
        # If there's an invoice, trigger the invoice cancel workflow which cancels both
        from .tasks import cancel_invoice_task

        nf.invoice.status = "PROCESSING"
        task = cancel_invoice_task.delay(nf.invoice.id)
        nf.invoice.task_id = task.id
        nf.invoice.save(update_fields=["status", "task_id", "updated_at"])
        messages.success(
            request,
            "Processo de cancelamento da Invoice e NFS-e iniciado em segundo plano.",
        )
    else:
        # Standalone cancel
        from .tasks import cancel_nfse_standalone_task

        cancel_nfse_standalone_task.delay(nf.id)
        messages.success(
            request,
            "Processo de cancelamento da NFS-e avulsa iniciado em segundo plano.",
        )

    cache.set(f"nfse_canceling_{nf.pk}", True, timeout=60)
    return _redirect_with_next(request, "nfse_detail", pk=pk)


@login_required
def nfse_download_pdf(request, pk, redirect_view="nfse_detail"):
    nf = get_object_or_404(NotaFiscal, pk=pk)

    if nf.danfse_pdf:
        try:
            if nf.danfse_pdf.storage.exists(nf.danfse_pdf.name):
                return FileResponse(
                    nf.danfse_pdf.open("rb"),
                    content_type="application/pdf",
                    as_attachment=False,
                    filename=f"NFS-e_{nf.nf_number}.pdf",
                )
        except Exception as e:
            logger.warning("Erro ao acessar PDF local da NFS-e %s: %s", nf.nf_number, e)

    from core.nfse.provider_factory import get_provider
    from core.services.nfse_services import fetch_and_save_nfse_pdf

    target = getattr(nf, "invoice", None) or nf

    try:
        provider = get_provider(target)
        pdf_bytes = fetch_and_save_nfse_pdf(target, provider)

        if pdf_bytes and nf.danfse_pdf and nf.danfse_pdf.storage.exists(nf.danfse_pdf.name):
            return FileResponse(
                nf.danfse_pdf.open("rb"),
                content_type="application/pdf",
                as_attachment=False,
                filename=f"NFS-e_{nf.nf_number}.pdf",
            )
    except Exception as e:
        logger.error(
            "Erro ao buscar PDF da NFS-e junto ao provedor para nf %s: %s",
            nf.nf_number,
            e,
        )

    messages.warning(
        request,
        "O PDF da NFS-e ainda não está disponível para visualização ou download.",
    )
    if redirect_view == "invoice_detail" and nf.invoice_id:
        return redirect("invoice_detail", pk=nf.invoice_id)
    return redirect("nfse_detail", pk=pk)



@login_required
def nfse_download_xml(request, pk):
    nf = get_object_or_404(NotaFiscal, pk=pk)

    if nf.xml_autorizacao:
        try:
            if nf.xml_autorizacao.storage.exists(nf.xml_autorizacao.name):
                return FileResponse(
                    nf.xml_autorizacao.open("rb"),
                    content_type="application/xml",
                    as_attachment=False,
                    filename=f"NFSe_{nf.nf_number}.xml",
                )
        except Exception as e:
            logger.warning("Erro ao acessar XML local da NFS-e %s: %s", nf.nf_number, e)

    from core.services.nfse_services import sync_nota_fiscal

    sync_nota_fiscal(nf)
    nf.refresh_from_db()

    if nf.xml_autorizacao:
        try:
            return FileResponse(
                nf.xml_autorizacao.open("rb"),
                content_type="application/xml",
                as_attachment=False,
                filename=f"NFSe_{nf.nf_number}.xml",
            )
        except Exception as e:
            logger.error("Erro ao servir XML da NFS-e %s: %s", nf.nf_number, e)

    messages.warning(
        request,
        "O XML da NFS-e ainda não está disponível para visualização ou download.",
    )
    return redirect("nfse_detail", pk=pk)



@login_required
def email_template_list(request):
    active_tab = request.GET.get("tab", "emails")
    invoice_templates = InvoiceTemplate.objects.prefetch_related("items").all()
    email_templates = EmailTemplate.objects.all().order_by("name")
    return render(
        request,
        "core/email_template_list.html",
        {
            "invoice_templates": invoice_templates,
            "email_templates": email_templates,
            "active_tab": active_tab,
        },
    )


@login_required
def invoice_template_list(request):
    active_tab = request.GET.get("tab", "invoices")
    invoice_templates = InvoiceTemplate.objects.prefetch_related("items").all()
    email_templates = EmailTemplate.objects.all().order_by("name")
    return render(
        request,
        "core/invoice_template_list.html",
        {
            "invoice_templates": invoice_templates,
            "email_templates": email_templates,
            "active_tab": active_tab,
        },
    )


@login_required
def email_template_update(request, pk):
    template = get_object_or_404(EmailTemplate, pk=pk)
    if request.method == "POST":
        form = EmailTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, "Modelo de e-mail atualizado com sucesso.")
            return redirect("email_template_list")
    else:
        form = EmailTemplateForm(instance=template)
    return render(request, "core/email_template_form.html", {"form": form})


@login_required
def invoice_template_create(request):
    if request.method == "POST":
        form = InvoiceTemplateForm(request.POST)
        formset = InvoiceTemplateItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            template = form.save()
            formset.instance = template
            formset.save()
            messages.success(request, "Modelo de invoice criado com sucesso.")
            return redirect("invoice_template_list")
    else:
        form = InvoiceTemplateForm(
            initial={"nfse_description": DEFAULT_NFSE_DESCRIPTION_TEMPLATE}
        )
        formset = InvoiceTemplateItemFormSet()
    return render(
        request, "core/invoice_template_form.html", {"form": form, "formset": formset}
    )


@login_required
def invoice_template_update(request, pk):
    template = get_object_or_404(InvoiceTemplate, pk=pk)
    if request.method == "POST":
        form = InvoiceTemplateForm(request.POST, instance=template)
        formset = InvoiceTemplateItemFormSet(request.POST, instance=template)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Modelo de invoice atualizado com sucesso.")
            return redirect("invoice_template_list")
    else:
        form = InvoiceTemplateForm(instance=template)
        formset = InvoiceTemplateItemFormSet(instance=template)
    return render(
        request, "core/invoice_template_form.html", {"form": form, "formset": formset}
    )


@login_required
def invoice_template_delete(request, pk):
    template = get_object_or_404(InvoiceTemplate, pk=pk)
    if request.method == "POST":
        template.delete()
        messages.success(request, "Modelo de invoice excluído com sucesso.")
        return redirect("invoice_template_list")
    return redirect("invoice_template_list")


@login_required
def htmx_get_invoice_template(request, pk):
    template = get_object_or_404(InvoiceTemplate, pk=pk)
    items = list(
        template.items.all().values("description", "quantity", "unit_price_foreign")
    )
    # Decimal objects need to be converted to str for JSON serialization
    for item in items:
        item["quantity"] = str(item["quantity"])
        item["unit_price_foreign"] = str(item["unit_price_foreign"])
    return JsonResponse(
        {
            "currency": template.currency,
            "bank_details": template.bank_details,
            "nfse_description": template.nfse_description,
            "codigo_tributacao_nacional": template.codigo_tributacao_nacional,
            "codigo_servico_municipio": template.codigo_servico_municipio,
            "codigo_nbs": template.codigo_nbs,
            "cst_ibs_cbs": template.cst_ibs_cbs,
            "c_class_trib_ibs_cbs": template.c_class_trib_ibs_cbs,
            "c_ind_op_ibs_cbs": template.c_ind_op_ibs_cbs,
            "items": items,
        }
    )


@login_required
@require_POST
def remove_certificate_view(request):
    company = CompanySettings.load()
    if not company:
        messages.error(request, "Configurações da empresa não encontradas.")
        return _redirect_with_next(request, "company_settings")

    company.pfx_cert_pem = None
    company.pfx_key_pem = None
    company.certificate_valid_until = None
    company.save()
    messages.success(request, "Certificado digital removido com sucesso.")
    return _redirect_with_next(request, "company_settings")


@login_required
def company_settings_view(request):
    company = CompanySettings.load()
    safe_next = _get_safe_next_url(request, None)
    if request.method == "POST":
        form = CompanySettingsForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            form.save()
            from core.middleware import COMPANY_SETTINGS_CACHE_KEY
            cache.delete(COMPANY_SETTINGS_CACHE_KEY)
            messages.success(request, "Configurações da empresa atualizadas.")
            return _redirect_with_next(request, "company_settings")
    else:
        form = CompanySettingsForm(instance=company)
    return render(
        request,
        "core/company_settings_form.html",
        {"form": form, "next_url": safe_next or ""},
    )


import requests


@login_required
def api_cep_view(request, cep):
    try:
        response = requests.get(f"https://cep.awesomeapi.com.br/json/{cep}", timeout=5)
        if response.status_code == 200:
            return JsonResponse(response.json())
        elif response.status_code in [400, 404]:
            return JsonResponse(
                {"error": "CEP não encontrado ou inválido."},
                status=response.status_code,
            )
        response.raise_for_status()
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def api_cnpj_view(request, cnpj):
    try:
        clean_cnpj = re.sub(r"[^0-9a-zA-Z]", "", cnpj).upper()
        response = requests.get(f"https://minhareceita.org/{clean_cnpj}", timeout=5)
        if response.status_code == 200:
            return JsonResponse(response.json())
        elif response.status_code in [400, 404]:
            return JsonResponse(
                {"error": "CNPJ não encontrado ou inválido."},
                status=response.status_code,
            )
        response.raise_for_status()
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# --- Client Management ---


@login_required
def client_list(request):
    clients = Client.objects.annotate(invoices_count=Count("invoices")).order_by("name")
    return render(request, "core/client_list.html", {"clients": clients})


@login_required
def client_create(request):
    safe_next = _get_safe_next_url(request, None)
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            messages.success(request, f"Cliente '{client.name}' cadastrado com sucesso.")
            if safe_next:
                parsed = urlsplit(safe_next)
                qs = parse_qs(parsed.query, keep_blank_values=True)
                qs["client_id"] = [str(client.id)]
                new_query = urlencode(qs, doseq=True)
                target = urlunsplit(
                    (parsed.scheme, parsed.netloc, parsed.path, new_query, parsed.fragment)
                )
                return redirect(target)
            return redirect("client_list")
    else:
        form = ClientForm()
    return render(
        request, "core/client_form.html", {"form": form, "next_url": safe_next or ""}
    )


@login_required
def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)
    safe_next = _get_safe_next_url(request, None)
    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            client = form.save()
            messages.success(request, f"Cliente '{client.name}' atualizado com sucesso.")
            if safe_next:
                return redirect(safe_next)
            return redirect("client_list")
    else:
        form = ClientForm(instance=client)
    return render(
        request,
        "core/client_form.html",
        {"form": form, "client": client, "next_url": safe_next or ""},
    )


@login_required
@require_POST
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    invoice_count = client.invoices.count()
    if invoice_count > 0:
        messages.error(
            request,
            f"Não é possível excluir o cliente '{client.name}' porque ele possui "
            f"{invoice_count} invoice(s) vinculada(s).",
        )
    else:
        client.delete()
        messages.success(request, f"Cliente '{client.name}' excluído com sucesso.")
    return _redirect_with_next(request, "client_list")
