import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from django.db import models
from core.fields import EncryptedTextField
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils import timezone

numeric_series_validator = RegexValidator(
    r"^\d{1,5}$", "A série deve conter apenas dígitos numéricos (1 a 5 dígitos)."
)


ALLOWED_PROVIDERS_BY_IBGE = {
    "3550308": ["PAULISTANA", "NACIONAL"],
}


def get_allowed_providers(ibge_code):
    return ALLOWED_PROVIDERS_BY_IBGE.get(str(ibge_code), ["NACIONAL"])


class CompanySettings(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_name = models.CharField(max_length=255)
    cnpj = models.CharField(max_length=20)
    inscricao_municipal = models.CharField(max_length=20)
    opening_date = models.DateField()

    address_tipo_logradouro = models.CharField(max_length=10, blank=True, default="")
    address_line1 = models.CharField(max_length=50, blank=True, default="")
    address_number = models.CharField(max_length=10, blank=True, default="")
    address_line2 = models.CharField(max_length=30, blank=True, default="")
    address_neighborhood = models.CharField(max_length=30, blank=True, default="")
    address_uf = models.CharField(max_length=2, blank=True, default="")
    address_cep = models.CharField(max_length=8, blank=True, default="")
    address_city = models.CharField(max_length=60, blank=True, default="")

    email = models.EmailField()

    next_document_number = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Next RPS/DPS number to be used for new invoices",
    )
    nfse_provider = models.CharField(
        max_length=20,
        choices=[("PAULISTANA", "Paulistana"), ("NACIONAL", "Sefin Nacional")],
        default="NACIONAL",
    )
    document_series = models.CharField(
        max_length=5,
        default="1",
        validators=[numeric_series_validator],
        help_text="Série numérica do RPS/DPS (1 a 5 dígitos)",
    )

    address_city_ibge = models.CharField(
        max_length=7,
        default="3550308",
        help_text="Código IBGE do município emissor (ex: 3550308 para São Paulo)",
    )
    default_codigo_tributacao_nacional = models.CharField(
        max_length=6,
        default="010101",
        help_text="Código de tributação nacional do ISSQN (LC 116)",
    )
    default_codigo_nbs = models.CharField(
        max_length=9,
        blank=True,
        default="",
        help_text="Código NBS correspondente ao serviço",
    )

    pfx_cert_pem = models.TextField(
        blank=True, null=True, help_text="Certificado Público em formato PEM"
    )
    pfx_key_pem = EncryptedTextField(
        blank=True, null=True, help_text="Chave Privada em formato PEM"
    )
    certificate_valid_until = models.DateTimeField(
        blank=True, null=True, help_text="Data de validade do certificado"
    )

    debug_email = models.EmailField(
        blank=True,
        null=True,
        help_text="If set, all emails are redirected here for debugging.",
    )
    debug_mode = models.BooleanField(
        default=False,
        help_text="Enable debug mode (routes emails to debug email and uses test NFS-e API)",
    )

    auto_finalize_invoices = models.BooleanField(
        default=False,
        help_text="Automatically finalize DRAFT invoices on their issue date.",
    )
    auto_send_emails = models.BooleanField(
        default=False,
        help_text="Automatically send emails after finalizing an invoice.",
    )
    auto_emit_nfse = models.BooleanField(
        default=False,
        help_text="Automatically emit NFS-e after finalizing an invoice.",
    )
    auto_invoice_hour = models.IntegerField(
        default=9,
        validators=[MinValueValidator(0), MaxValueValidator(23)],
        help_text="Hour of the day (0-23) to run the automatic invoice finalization.",
    )

    class Meta:
        verbose_name = "Configuração da Empresa"
        verbose_name_plural = "Configurações da Empresa"

    def clean(self):
        super().clean()
        if not self.pk and CompanySettings.objects.exists():
            raise ValidationError("Só pode existir uma configuração de empresa.")

    @property
    def allowed_providers(self):
        return get_allowed_providers(self.address_city_ibge)

    @classmethod
    def load(cls):
        return cls.objects.first()

    def __str__(self):
        return self.company_name


class Client(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    address_line1 = models.CharField(max_length=50, blank=True, default="")
    address_number = models.CharField(max_length=10, blank=True, default="")
    address_line2 = models.CharField(max_length=30, blank=True, default="")
    address_neighborhood = models.CharField(max_length=30, blank=True, default="")

    # Nacional fields for foreign addresses
    address_country_code = models.CharField(
        max_length=2,
        blank=True,
        default="",
        help_text="ISO 3166-1 alpha-2 code (e.g. CA)",
    )
    country = models.CharField(max_length=100, blank=True, default="")

    address_postal_code = models.CharField(max_length=11, blank=True, default="")
    address_city = models.CharField(max_length=60, blank=True, default="")
    address_state_province = models.CharField(max_length=50, blank=True, default="")

    email = models.EmailField(blank=True, null=True)
    email_cc = models.TextField(
        blank=True, default="", help_text="Comma-separated list of CC emails"
    )

    def clean(self):
        if not self.address_neighborhood:
            raise ValidationError(
                {"address_neighborhood": "Bairro is mandatory for NFS-e Nacional."}
            )
        super().clean()

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Invoice(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Rascunho"
        PROCESSING = "PROCESSING", "Processando"
        FINALIZED = "FINALIZED", "Finalizado"
        CANCELED = "CANCELED", "Cancelado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(
        Client, on_delete=models.PROTECT, related_name="invoices"
    )
    invoice_number = models.CharField(max_length=50, unique=True)
    issue_date = models.DateField(db_index=True)
    currency = models.CharField(max_length=10, default="CAD")
    exchange_rate_to_brl = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.0001"))],
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True
    )

    task_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_index=True,
        help_text="ID of the celery task currently processing this invoice.",
    )
    task_retry_count = models.PositiveSmallIntegerField(
        default=0, help_text="Number of times the current task has been retried."
    )

    document_number = models.IntegerField(
        null=True, blank=True, help_text="RPS/DPS Number"
    )
    document_series = models.CharField(
        max_length=5,
        default="1",
        blank=True,
        validators=[numeric_series_validator],
        help_text="Série numérica do RPS/DPS (1 a 5 dígitos)",
    )
    protocolo_envio = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Protocol returned when batch is sent to prefeitura",
    )
    bank_details = models.TextField(
        blank=True,
        default="",
        help_text="Dados bancários / instruções de pagamento (suporta Markdown).",
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Fatura"
        verbose_name_plural = "Faturas"
        ordering = ["-issue_date"]
        indexes = [
            models.Index(fields=["status", "issue_date"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["document_number", "document_series"],
                name="unique_document",
                condition=models.Q(document_number__isnull=False),
            )
        ]

    @property
    def total_foreign(self):
        return sum(item.total_price_foreign for item in self.items.all())

    @property
    def total_brl(self):
        if self.exchange_rate_to_brl:
            return (self.total_foreign * self.exchange_rate_to_brl).quantize(
                Decimal("0.01")
            )
        return None

    @property
    def is_draft(self):
        return self.status == "DRAFT"

    @property
    def is_finalized(self):
        return self.status == "FINALIZED"

    @property
    def is_canceled(self):
        return self.status == "CANCELED"

    @property
    def can_be_canceled(self):
        if self.status in ["CANCELED", "DRAFT", "PROCESSING"]:
            return False
        if hasattr(self, "nota_fiscal") and self.nota_fiscal:
            return self.nota_fiscal.can_be_canceled
        return True

    @property
    def nfse_provider_type(self):
        if hasattr(self, "nota_fiscal") and self.nota_fiscal:
            return self.nota_fiscal.provider_type
        company = CompanySettings.objects.first()
        return company.nfse_provider if company else "PAULISTANA"

    @property
    def bank_details_html(self):
        if not self.bank_details:
            return ""
        from core.templatetags.core_tags import render_markdown_text

        return render_markdown_text(self.bank_details)

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.client.name}"


class InvoiceItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    description = models.TextField()
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("1.00"),
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    unit_price_foreign = models.DecimalField(
        max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )

    @property
    def total_price_foreign(self):
        return (self.quantity * self.unit_price_foreign).quantize(Decimal("0.01"))

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def clean(self):
        if (
            self.invoice_id
            and hasattr(self, "invoice")
            and self.invoice
            and self.invoice.status != "DRAFT"
        ):
            raise ValidationError(
                "Itens só podem ser alterados em invoices em rascunho."
            )
        super().clean()

    def delete(self, *args, **kwargs):
        if self.invoice.status != "DRAFT":
            raise ValidationError(
                "Não é possível remover itens de uma fatura que não está em rascunho."
            )
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = "Item de Fatura"
        verbose_name_plural = "Itens de Fatura"
        ordering = ["id"]

    def __str__(self):
        return self.description


class NotaFiscal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.OneToOneField(
        Invoice,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="nota_fiscal",
    )

    nf_number = models.CharField(max_length=50, unique=True)
    issue_date = models.DateField(db_index=True)
    amount_brl = models.DecimalField(
        max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )
    is_export = models.BooleanField(
        default=True, help_text="Exempts PIS, COFINS, ISS from DAS"
    )
    description = models.TextField()
    verification_code = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Código de Verificação retornado pela prefeitura",
    )

    # Metadados Fiscais
    chave_acesso_nacional = models.CharField(max_length=100, blank=True, default="")
    data_hora_autorizacao = models.DateTimeField(blank=True, null=True)

    # Serviço
    codigo_tributacao_nacional = models.CharField(max_length=50, blank=True, default="")
    codigo_servico_municipio = models.CharField(max_length=50, blank=True, default="")
    codigo_nbs = models.CharField(max_length=20, blank=True, default="")

    # Financeiro e Impostos
    aliquota_iss = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    valor_iss = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )

    # Camada de Arquivos (Blob Storage)
    xml_autorizacao = models.FileField(upload_to="nfs_e/xmls/", blank=True, null=True)
    danfse_pdf = models.FileField(upload_to="nfs_e/pdfs/", blank=True, null=True)

    is_canceled = models.BooleanField(
        default=False, help_text="Indicates if the NFS-e has been canceled."
    )
    cancelation_date = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Nota Fiscal"
        verbose_name_plural = "Notas Fiscais"
        ordering = ["-issue_date"]
        indexes = [
            models.Index(fields=["issue_date", "is_canceled"]),
        ]

    @property
    def can_be_canceled(self):
        if self.is_canceled:
            return False
        auth_time = self.data_hora_autorizacao or self.created_at
        if not auth_time and self.issue_date:
            auth_time = timezone.make_aware(
                datetime.combine(self.issue_date, datetime.min.time())
            )
        if auth_time:
            if timezone.is_naive(auth_time):
                auth_time = timezone.make_aware(auth_time)
            if timezone.now() - auth_time > timedelta(hours=24):
                return False
        return True

    @property
    def provider_type(self):
        if self.verification_code:
            return "PAULISTANA"
        if self.chave_acesso_nacional:
            return "NACIONAL"
        company = CompanySettings.objects.first()
        return company.nfse_provider if company else "PAULISTANA"

    def __str__(self):
        return f"NF {self.nf_number} - R$ {self.amount_brl}"


class MonthlyConsolidation(models.Model):
    class Status(models.TextChoices):
        CONSOLIDATED = "CONSOLIDATED", "Consolidado"
        OUTDATED = "OUTDATED", "Desatualizado - Requer Recálculo"

    class Annex(models.TextChoices):
        ANNEX_III = "ANNEX_III", "Anexo III (Fator R >= 28%)"
        ANNEX_V = "ANNEX_V", "Anexo V (Fator R < 28%)"

    month_year = models.DateField(unique=True, help_text="First day of the month")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OUTDATED
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    total_revenue_internal = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0.00")
    )
    total_revenue_export = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0.00")
    )

    @property
    def total_revenue(self):
        return self.total_revenue_internal + self.total_revenue_export

    rbt12 = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0.00")
    )
    fator_r_ratio = models.DecimalField(
        max_digits=7, decimal_places=2, default=Decimal("0.00")
    )
    fator_r_payroll_sum = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0.00")
    )
    fator_r_cpp_sum = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0.00")
    )

    actual_pro_labore_paid = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0.00")
    )
    applied_annex = models.CharField(
        max_length=20, choices=Annex.choices, null=True, blank=True
    )

    inss_tax = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0.00")
    )
    irrf_tax = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0.00")
    )
    das_tax = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0.00")
    )
    das_cpp_tax = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0.00")
    )

    @property
    def total_tax(self):
        return self.das_tax + self.inss_tax + self.irrf_tax

    def clean(self):
        super().clean()
        if self.month_year and self.month_year.day != 1:
            raise ValidationError(
                {"month_year": "O campo month_year deve ser o primeiro dia do mês."}
            )

    class Meta:
        ordering = ["-month_year"]

    def __str__(self):
        return f"Consolidação: {self.month_year.strftime('%B %Y')} - {self.status}"


class NfseLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.SET_NULL,
        related_name="nfse_logs",
        null=True,
        blank=True,
    )
    nota_fiscal = models.ForeignKey(
        "NotaFiscal",
        on_delete=models.SET_NULL,
        related_name="nfse_logs",
        null=True,
        blank=True,
    )
    payload_enviado = models.TextField(blank=True, default="")
    payload_retorno = models.TextField(blank=True, default="")
    erro_mensagem = models.TextField(blank=True, default="")
    origem = models.CharField(
        max_length=255, blank=True, default="", help_text="Origin (User/IP)"
    )
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        verbose_name = "Log NFS-e"
        verbose_name_plural = "Logs NFS-e"
        ordering = ["-created_at"]

    def __str__(self):
        target = (
            self.invoice.invoice_number
            if self.invoice
            else (self.nota_fiscal.nf_number if self.nota_fiscal else "Unknown")
        )
        return f"Log for {target} at {self.created_at}"


class ApiLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    endpoint = models.URLField(max_length=2000)
    method = models.CharField(max_length=10)
    request_payload = models.TextField(blank=True, null=True)
    response_payload = models.TextField(blank=True, null=True)
    status_code = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    def __str__(self):
        return f"{self.method} {self.endpoint} - {self.status_code}"


class EmailTemplate(models.Model):
    TEMPLATE_TYPE_CHOICES = [
        ("CLIENT_INVOICE_ISSUED", "Client: Invoice Issued"),
        ("COMPANY_INVOICE_ISSUED", "Company: Invoice Issued"),
        ("COMPANY_CANCEL_FAILED", "Company: Cancel Failed"),
        ("COMPANY_FAILSAFE_TRIGGERED", "Company: Failsafe Triggered"),
        ("COMPANY_NFSE_ISSUED", "Company: NFS-e Issued"),
        ("COMPANY_NFSE_FAILED", "Company: NFS-e Failed"),
    ]
    LANGUAGE_CHOICES = [
        ("en", "English"),
        ("pt-br", "Portuguese (Brazil)"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template_type = models.CharField(
        max_length=50,
        unique=True,
        choices=TEMPLATE_TYPE_CHOICES,
        help_text="Internal identifier for the email type",
    )
    name = models.CharField(max_length=255, help_text="Human-readable name")
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default="en")
    subject = models.CharField(max_length=255)
    body = models.TextField(
        help_text="Use {{ macros }} like {{ invoice_date }}, {{ prev_month_start }}, etc."
    )

    class Meta:
        verbose_name = "Template de E-mail"
        verbose_name_plural = "Templates de E-mail"

    def __str__(self):
        return f"[{self.get_template_type_display()}] {self.name}"

    def delete(self, *args, **kwargs):
        raise ValidationError("Email templates cannot be deleted.")


class InvoiceTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    currency = models.CharField(max_length=10, default="CAD")
    bank_details = models.TextField(
        blank=True,
        default="",
        help_text="Dados bancários / instruções de pagamento (suporta Markdown).",
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name = "Template de Fatura"
        verbose_name_plural = "Templates de Fatura"
        ordering = ["name"]

    @property
    def bank_details_html(self):
        if not self.bank_details:
            return ""
        from core.templatetags.core_tags import render_markdown_text

        return render_markdown_text(self.bank_details)

    def __str__(self):
        return self.name


class InvoiceTemplateItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        InvoiceTemplate, on_delete=models.CASCADE, related_name="items"
    )
    description = models.TextField(
        help_text="Can contain macros like {{ prev_month_start }}"
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("1.00"),
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    unit_price_foreign = models.DecimalField(
        max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )

    @property
    def total_price_foreign(self):
        return (self.quantity * self.unit_price_foreign).quantize(Decimal("0.01"))

    def __str__(self):
        return self.description
