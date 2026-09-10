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
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Q, Sum
from django.db.models.functions import Coalesce
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    FileResponse,
    JsonResponse,
)
from django.utils.html import escape
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from .forms import (
    InvoiceForm,
    InvoiceItemForm,
    EmailTemplateForm,
    InvoiceTemplateForm,
    InvoiceTemplateItemFormSet,
    CompanySettingsForm,
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
)
from .pdf_service import generate_pdf_bytes
from .services import (
    audit_consolidations,
    attach_recommended_pl,
    calculate_ideal_pro_labore,
    calculate_rbt12_and_fator_r,
    calculate_simples_tax,
    fetch_exchange_rate,
    reconsolidate_with_prior,
)

logger = logging.getLogger(__name__)


# --- Dashboard & Consolidation ---


@login_required
def dashboard_view(request):
    qs = MonthlyConsolidation.objects.all()
    today = date.today()

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

    # Calculate ideal pró-labore for next month
    current_month = today.replace(day=1)
    ideal_pro_labore = None
    try:
        ideal_pro_labore = calculate_ideal_pro_labore(current_month)
    except Exception as e:
        logger.debug("Could not calculate ideal pro labore for next month: %s", e)

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
            "ideal_pro_labore": ideal_pro_labore,
            "current_month": current_month,
        },
    )


@login_required
@require_POST
def htmx_reconsolidate_month(request, pk):
    consolidation = get_object_or_404(MonthlyConsolidation, pk=pk)

    actual_pl_str = request.POST.get("actual_pro_labore_paid", "").strip()
    actual_pl = None
    if actual_pl_str:
        try:
            actual_pl = Decimal(actual_pl_str.replace(",", "."))
        except Exception:
            return HttpResponseBadRequest("Valor de pró-labore inválido.")

    try:
        consolidation = reconsolidate_with_prior(
            consolidation.month_year, actual_pro_labore=actual_pl
        )
        attach_recommended_pl(consolidation)
        return render(
            request,
            "core/partials/consolidation_row.html",
            {"consolidation": consolidation},
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
    from core.services import audit_consolidations

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
    return redirect("dashboard")


# --- Invoices Management ---


@login_required
def invoice_list(request):
    client_id = request.GET.get("client_id", "")
    status = request.GET.get("status", "")
    year = (
        request.GET.get("year", "") if "year" in request.GET else str(date.today().year)
    )
    company = CompanySettings.load()

    invoices = Invoice.objects.select_related("client").all()

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
            "debug_mode": company.debug_mode,
        },
    )


@login_required
@transaction.atomic
def invoice_create(request):
    from .forms import InvoiceItemFormSet

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
                return redirect("invoice_detail", pk=invoice.id)
    else:
        form = InvoiceForm()
        formset = InvoiceItemFormSet()

    invoice_templates = InvoiceTemplate.objects.all()
    return render(
        request,
        "core/invoice_form.html",
        {"form": form, "formset": formset, "invoice_templates": invoice_templates},
    )


@login_required
def invoice_detail(request, pk):
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

    return render(
        request,
        "core/invoice_detail.html",
        {
            "invoice": invoice,
            "item_form": item_form,
            "company": company,
            "suggested_exchange_rate": suggested_exchange_rate,
            "latest_nfse_log": latest_nfse_log,
        },
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
    return redirect("invoice_list")


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
    return redirect("invoice_detail", pk=invoice.id)


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
@require_POST
def htmx_delete_invoice_item(request, item_pk):
    item = get_object_or_404(InvoiceItem, pk=item_pk)
    invoice = item.invoice
    if invoice.status == "DRAFT":
        item.delete()
    return render(request, "core/partials/invoice_item_list.html", {"invoice": invoice})


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
def finalize_invoice(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)

    if invoice.status != "DRAFT":
        messages.error(request, "Apenas invoices em rascunho podem ser finalizadas.")
        return redirect("invoice_detail", pk=invoice.id)

    send_to_client = request.POST.get("send_to_client") == "on"
    send_to_company = request.POST.get("send_to_company") == "on"

    invoice.status = "PROCESSING"
    from .tasks import finalize_invoice_task

    task = finalize_invoice_task.delay(
        invoice.id, send_to_client=send_to_client, send_to_company=send_to_company
    )
    invoice.task_id = task.id
    invoice.save()

    messages.success(request, "Processo de finalização iniciado em segundo plano.")
    return redirect("invoice_detail", pk=invoice.id)


@login_required
@require_POST
def cancel_invoice(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)

    if invoice.status == "CANCELED":
        messages.error(request, "Esta invoice já foi cancelada.")
        return redirect("invoice_detail", pk=invoice.id)

    if invoice.status == "DRAFT":
        messages.error(
            request, "Invoices em rascunho devem ser excluídas, não canceladas."
        )
        return redirect("invoice_detail", pk=invoice.id)

    if (
        hasattr(invoice, "nota_fiscal")
        and invoice.nota_fiscal
        and not invoice.nota_fiscal.can_be_canceled
    ):
        messages.error(
            request,
            "A NFS-e vinculada a esta invoice foi autorizada há mais de 24 horas e não pode ser cancelada diretamente pelo sistema.",
        )
        return redirect("invoice_detail", pk=invoice.id)

    invoice.status = "PROCESSING"
    from .tasks import cancel_invoice_task

    task = cancel_invoice_task.delay(invoice.id)
    invoice.task_id = task.id
    invoice.save()

    messages.success(request, "Processo de cancelamento iniciado em segundo plano.")
    return redirect("invoice_detail", pk=invoice.id)


@login_required
@require_POST
def issue_nfse(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)

    if invoice.status != "FINALIZED":
        messages.error(request, "Apenas invoices finalizadas podem ter NFS-e emitida.")
        return redirect("invoice_detail", pk=invoice.id)

    exchange_rate_str = request.POST.get("exchange_rate")
    if not exchange_rate_str:
        messages.error(request, "A taxa de câmbio é obrigatória para emissão da NFS-e.")
        return redirect("invoice_detail", pk=invoice.id)

    try:
        exchange_rate = Decimal(exchange_rate_str.replace(",", "."))
        if exchange_rate <= 0:
            raise ValueError()
    except Exception:
        messages.error(request, "Taxa de câmbio inválida.")
        return redirect("invoice_detail", pk=invoice.id)

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
    invoice.save()

    messages.success(request, "Processo de emissão da NFS-e iniciado em segundo plano.")
    return redirect("invoice_detail", pk=invoice.id)


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
    invoice = get_object_or_404(Invoice, pk=pk)
    nf = getattr(invoice, "nota_fiscal", None)

    if not nf:
        messages.error(request, "Nenhuma NFS-e associada a esta invoice.")
        return redirect("invoice_detail", pk=invoice.id)

    # 1. Check if PDF is already stored locally
    if nf.danfse_pdf:
        try:
            if nf.danfse_pdf.storage.exists(nf.danfse_pdf.name):
                return FileResponse(
                    nf.danfse_pdf.open("rb"),
                    content_type="application/pdf",
                    as_attachment=False,
                    filename=f"NFSe_{nf.nf_number}.pdf",
                )
        except Exception as e:
            logger.warning(
                "Erro ao acessar arquivo local do PDF da NFS-e para invoice %s: %s",
                invoice.invoice_number,
                e,
            )

    # 2. If not present locally, fetch via provider
    from core.nfse.provider_factory import get_provider
    from django.core.files.base import ContentFile

    try:
        provider = get_provider(invoice)
        pdf_bytes = provider.baixar_pdf(invoice)
        if pdf_bytes:
            nf.danfse_pdf.save(f"NFSe_{nf.nf_number}.pdf", ContentFile(pdf_bytes))
            return FileResponse(
                nf.danfse_pdf.open("rb"),
                content_type="application/pdf",
                as_attachment=False,
                filename=f"NFSe_{nf.nf_number}.pdf",
            )
    except Exception as e:
        logger.error(
            "Erro ao buscar PDF da NFS-e junto ao provedor para invoice %s: %s",
            invoice.invoice_number,
            e,
        )

    messages.warning(
        request,
        "O PDF da NFS-e ainda não está disponível para visualização ou download.",
    )
    return redirect("invoice_detail", pk=invoice.id)


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
    invoice.save()

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
            invoice.save()
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
    return redirect("invoice_list")


from django.http import HttpResponse
from celery.result import AsyncResult
from .tasks import import_nfses_task


@login_required
def nfse_list(request):
    query = request.GET.get("q", "").strip()
    notas_qs = NotaFiscal.objects.all().order_by(
        F("data_hora_autorizacao").desc(nulls_last=True),
        "-issue_date",
        "-created_at",
    )
    if query:
        notas_qs = notas_qs.filter(
            Q(nf_number__icontains=query)
            | Q(chave_acesso_nacional__icontains=query)
            | Q(verification_code__icontains=query)
            | Q(description__icontains=query)
        )

    paginator = Paginator(notas_qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    company = CompanySettings.load()
    today = timezone.now().date()
    return render(
        request,
        "core/nfse_list.html",
        {
            "page_obj": page_obj,
            "notas": page_obj,
            "query": query,
            "today": today.isoformat(),
            "company": company,
            "opening_date": (
                company.opening_date.isoformat()
                if company and company.opening_date
                else ""
            ),
        },
    )


@login_required
@require_POST
def nfse_import(request):
    provider = request.POST.get("provider")

    # Trigger Celery Task
    task = import_nfses_task.delay(provider)

    # Return HTMX polling snippet
    return HttpResponse(f"""
        <div class="modal-content" id="importModalContent">
            <div class="modal-body text-center py-5">
                <div class="spinner-border text-primary mb-3" role="status"></div>
                <h5>Importando NFS-es...</h5>
                <p class="text-muted" hx-get="/nfse/import/status/{task.id}/" hx-trigger="every 2s" hx-target="#importModalContent" hx-swap="outerHTML">
                    Aguarde enquanto consultamos o provedor. Pode levar alguns minutos.
                </p>
            </div>
        </div>
    """)


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
    nf = get_object_or_404(NotaFiscal, pk=pk)
    invoices = Invoice.objects.all().order_by("-issue_date")
    return render(
        request,
        "core/nfse_detail.html",
        {
            "nf": nf,
            "invoices": invoices,
        },
    )


@login_required
@require_POST
def nfse_link_invoice(request, pk):
    nf = get_object_or_404(NotaFiscal, pk=pk)
    invoice_id = request.POST.get("invoice_id")
    if invoice_id:
        # Check if already linked
        existing_nf = getattr(Invoice.objects.get(pk=invoice_id), "nota_fiscal", None)
        if existing_nf and existing_nf.pk != nf.pk:
            messages.error(request, "Esta invoice já possui uma NFS-e vinculada.")
        else:
            nf.invoice_id = invoice_id
            nf.save()
            messages.success(request, "Invoice vinculada com sucesso.")
    return redirect("nfse_detail", pk=pk)


@login_required
@require_POST
def nfse_cancel(request, pk):
    nf = get_object_or_404(NotaFiscal, pk=pk)

    if nf.is_canceled:
        messages.error(request, "Esta NFS-e já está cancelada.")
        return redirect("nfse_detail", pk=pk)

    if not nf.can_be_canceled:
        messages.error(
            request,
            "Esta NFS-e foi autorizada há mais de 24 horas e não pode ser cancelada diretamente pelo sistema.",
        )
        return redirect("nfse_detail", pk=pk)

    if nf.invoice:
        # If there's an invoice, trigger the invoice cancel workflow which cancels both
        from .tasks import cancel_invoice_task

        nf.invoice.status = "PROCESSING"
        task = cancel_invoice_task.delay(nf.invoice.id)
        nf.invoice.task_id = task.id
        nf.invoice.save()
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

    return redirect("nfse_detail", pk=pk)


@login_required
def nfse_download_pdf(request, pk):
    nf = get_object_or_404(NotaFiscal, pk=pk)

    if nf.danfse_pdf:
        try:
            if nf.danfse_pdf.storage.exists(nf.danfse_pdf.name):
                return FileResponse(
                    nf.danfse_pdf.open("rb"),
                    content_type="application/pdf",
                    as_attachment=False,
                    filename=f"NFSe_{nf.nf_number}.pdf",
                )
        except Exception as e:
            logger.warning("Erro ao acessar PDF local da NFS-e %s: %s", nf.nf_number, e)

    from core.nfse.provider_factory import get_provider
    from django.core.files.base import ContentFile

    class DummyInvoice:
        def __init__(self, nota_fiscal):
            self.nota_fiscal = nota_fiscal

    dummy = DummyInvoice(nf)

    try:
        provider = get_provider(dummy)
        pdf_bytes = provider.baixar_pdf(dummy)
        if pdf_bytes:
            nf.danfse_pdf.save(f"NFSe_{nf.nf_number}.pdf", ContentFile(pdf_bytes))
            return FileResponse(
                nf.danfse_pdf.open("rb"),
                content_type="application/pdf",
                as_attachment=False,
                filename=f"NFSe_{nf.nf_number}.pdf",
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
    return redirect("nfse_detail", pk=pk)


@login_required
def email_template_list(request):
    email_templates = EmailTemplate.objects.all()
    return render(
        request,
        "core/email_template_list.html",
        {
            "email_templates": email_templates,
        },
    )


@login_required
def invoice_template_list(request):
    invoice_templates = InvoiceTemplate.objects.all()
    return render(
        request,
        "core/invoice_template_list.html",
        {"invoice_templates": invoice_templates},
    )


@login_required
def email_template_update(request, pk):
    template = get_object_or_404(EmailTemplate, pk=pk)
    if request.method == "POST":
        form = EmailTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, "Email template updated.")
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
            messages.success(request, "Invoice template created.")
            return redirect("invoice_template_list")
    else:
        form = InvoiceTemplateForm()
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
            messages.success(request, "Invoice template updated.")
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
        messages.success(request, "Invoice template deleted.")
        return redirect("invoice_template_list")
    return render(
        request, "core/invoice_template_confirm_delete.html", {"template": template}
    )


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
            "items": items,
        }
    )


@login_required
@require_POST
def remove_certificate_view(request):
    company = CompanySettings.load()
    company.pfx_cert_pem = None
    company.pfx_key_pem = None
    company.certificate_valid_until = None
    company.save()
    from django.contrib import messages

    messages.success(request, "Certificado digital removido com sucesso.")
    return redirect("company_settings")


@login_required
def company_settings_view(request):
    company = CompanySettings.load()
    if request.method == "POST":
        form = CompanySettingsForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, "Configurações da empresa atualizadas.")
            return redirect("company_settings")
    else:
        form = CompanySettingsForm(instance=company)
    return render(request, "core/company_settings_form.html", {"form": form})


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
        response = requests.get(f"https://minhareceita.org/{cnpj}", timeout=5)
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
