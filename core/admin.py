from django.contrib import admin
from .models import (
    CompanySettings,
    Client,
    Invoice,
    InvoiceItem,
    NotaFiscal,
    
    
    MonthlyConsolidation,
    NfseLog,
    ApiLog,
)


@admin.action(description="Buscar / Atualizar PDF da NFS-e")
def buscar_pdf_nfse_action(modeladmin, request, queryset):
    from .tasks import fetch_nfse_pdf_task

    dispatched = 0
    for obj in queryset:
        if isinstance(obj, Invoice):
            fetch_nfse_pdf_task.delay(invoice_id=obj.id)
            dispatched += 1
        else:
            # It's a NotaFiscal
            invoice = getattr(obj, "invoice", None)
            if invoice:
                fetch_nfse_pdf_task.delay(invoice_id=invoice.id)
            else:
                fetch_nfse_pdf_task.delay(nf_id=obj.id)
            dispatched += 1
    modeladmin.message_user(
        request, f"Busca de PDF agendada para {dispatched} nota(s)/invoice(s)."
    )


@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    list_display = (
        "company_name",
        "cnpj",
        "opening_date",
        "nfse_provider",
        "document_series",
        "address_city_ibge",
        "debug_mode",
    )

    def has_add_permission(self, request):
        return not CompanySettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    ordering = ("-created_at",)
    list_display = ("name", "country", "email")
    search_fields = ("name", "email")


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1

    def has_delete_permission(self, request, obj=None):
        if obj and obj.status != "DRAFT":
            return False
        return super().has_delete_permission(request, obj)


class NfseLogInline(admin.TabularInline):
    model = NfseLog
    extra = 0
    can_delete = False
    readonly_fields = (
        "created_at",
        "origem",
        "erro_mensagem",
        "payload_enviado",
        "payload_retorno",
    )
    fields = (
        "created_at",
        "origem",
        "erro_mensagem",
        "payload_enviado",
        "payload_retorno",
    )

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    ordering = ("-created_at",)
    list_display = (
        "invoice_number",
        "client",
        "issue_date",
        "currency",
        "status",
        "document_number",
        "document_series",
    )
    list_filter = ("status", "currency", "issue_date")
    search_fields = ("invoice_number", "client__name", "=document_number")
    autocomplete_fields = ("client",)
    inlines = [InvoiceItemInline, NfseLogInline]
    actions = [buscar_pdf_nfse_action]


@admin.register(NotaFiscal)
class NotaFiscalAdmin(admin.ModelAdmin):
    ordering = ("-created_at",)
    list_display = (
        "nf_number",
        "issue_date",
        "amount_brl",
        "is_export",
        "chave_acesso_nacional",
        "verification_code",
    )
    list_filter = ("is_export", "issue_date")
    search_fields = (
        "nf_number",
        "invoice__invoice_number",
        "verification_code",
        "chave_acesso_nacional",
        "description",
    )
    autocomplete_fields = ("invoice",)
    actions = [buscar_pdf_nfse_action]



@admin.register(MonthlyConsolidation)
class MonthlyConsolidationAdmin(admin.ModelAdmin):
    ordering = ("-month_year",)
    list_display = (
        "month_year",
        "status",
        "rbt12",
        "fator_r_ratio",
        "applied_annex",
        "das_tax",
        "actual_pro_labore_paid",
    )
    list_filter = ("status", "applied_annex")
    search_fields = ()
    readonly_fields = (
        "rbt12",
        "fator_r_ratio",
        "applied_annex",
        "fator_r_payroll_sum",
        "fator_r_cpp_sum",
        "inss_tax",
        "irrf_tax",
        "das_tax",
        "das_cpp_tax",
    )


@admin.register(NfseLog)
class NfseLogAdmin(admin.ModelAdmin):
    ordering = ("-created_at",)
    list_display = ("invoice", "created_at", "origem")
    list_filter = ("created_at",)
    search_fields = ("invoice__invoice_number", "erro_mensagem", "origem")
    readonly_fields = (
        "invoice",
        "payload_enviado",
        "payload_retorno",
        "erro_mensagem",
        "origem",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

@admin.register(ApiLog)
class ApiLogAdmin(admin.ModelAdmin):
    ordering = ("-created_at",)
    list_display = ("created_at", "method", "endpoint", "status_code")
    list_filter = ("method", "status_code", "created_at")
    search_fields = ("endpoint", "request_payload", "response_payload")
    readonly_fields = ("id", "created_at", "method", "endpoint", "status_code", "request_payload", "response_payload")

    def has_add_permission(self, request):
        return False
