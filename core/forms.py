import datetime
from decimal import Decimal
import re
from django import forms
from django.core.exceptions import ValidationError
from .models import (
    Client,
    Invoice,
    InvoiceItem,
    EmailTemplate,
    InvoiceTemplate,
    InvoiceTemplateItem,
)
from django.forms import inlineformset_factory

VALID_INVOICE_MACROS = {
    "{{ invoice_date }}",
    "{{ prev_month_start }}",
    "{{ prev_month_end }}",
    "{{ prev_month_name }}",
    "{{ prev_month_year }}",
    "{{ invoice_number }}",
    "{{ currency }}",
    "{{ client_name }}",
    "{{ value_original }}",
    "{{ value_brl }}",
    "{{ company_cnpj }}",
    "{{ exchange_rate }}",
    "{{ effective_tax_rate }}",
    "{{ nominal_tax_rate }}",
}

VALID_NFSE_MACROS = VALID_INVOICE_MACROS

VALID_EMAIL_MACROS = VALID_INVOICE_MACROS | {
    "{{ error }}",
    "{{ month_info }}",
    "{{ failsafe_reason }}",
    "{{ nf_number }}",
    "{{ amount_brl }}",
    "{{ verification_code }}",
}


def validate_macros(text, valid_macros):
    if not text:
        return text
    matches = re.findall(r"\{\{.*?\}\}|\{.*?\}", text)
    for match in matches:
        if match not in valid_macros:
            raise ValidationError(f"Macro inválida: {match}")
    return text


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            "client",
            "invoice_number",
            "issue_date",
            "currency",
            "bank_details",
            "nfse_description",
            "codigo_tributacao_nacional",
            "codigo_servico_municipio",
            "codigo_nbs",
            "cst_ibs_cbs",
            "c_class_trib_ibs_cbs",
            "c_ind_op_ibs_cbs",
        ]
        labels = {
            "client": "Cliente",
            "invoice_number": "Número da Invoice",
            "issue_date": "Data de Emissão",
            "currency": "Moeda",
            "bank_details": "Dados Bancários",
            "nfse_description": "Descrição da NFS-e",
            "codigo_tributacao_nacional": "Cód. Tributação Nacional",
            "codigo_servico_municipio": "Cód. Serviço Município",
            "codigo_nbs": "Cód. NBS",
            "cst_ibs_cbs": "CST IBS/CBS",
            "c_class_trib_ibs_cbs": "Classificação IBS/CBS (cClassTrib)",
            "c_ind_op_ibs_cbs": "Indicador da Operação (cIndOp)",
        }
        widgets = {
            "issue_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "client": forms.Select(attrs={"class": "form-select"}),
            "invoice_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "ex: 2026-001"}
            ),
            "currency": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "CAD, USD, EUR, etc."}
            ),
            "bank_details": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Dados bancários (suporta Markdown)...",
                }
            ),
            "nfse_description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": "Texto / discriminação dos serviços para a NFS-e...",
                }
            ),
            "codigo_tributacao_nacional": forms.TextInput(
                attrs={"class": "form-control font-monospace", "placeholder": "ex: 010101"}
            ),
            "codigo_servico_municipio": forms.TextInput(
                attrs={"class": "form-control font-monospace", "placeholder": "ex: 001"}
            ),
            "codigo_nbs": forms.TextInput(
                attrs={"class": "form-control font-monospace", "placeholder": "ex: 115029000"}
            ),
            "cst_ibs_cbs": forms.TextInput(
                attrs={"class": "form-control font-monospace", "placeholder": "ex: 410"}
            ),
            "c_class_trib_ibs_cbs": forms.TextInput(
                attrs={"class": "form-control font-monospace", "placeholder": "ex: 410004"}
            ),
            "c_ind_op_ibs_cbs": forms.TextInput(
                attrs={"class": "form-control font-monospace", "placeholder": "ex: 100301"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["codigo_servico_municipio"].required = False
        self.fields["cst_ibs_cbs"].required = False
        self.fields["c_class_trib_ibs_cbs"].required = False
        self.fields["c_ind_op_ibs_cbs"].required = False
        if not self.instance.pk and not self.initial.get("issue_date"):
            self.fields["issue_date"].initial = datetime.date.today

    def clean_currency(self):
        curr = self.cleaned_data.get("currency", "CAD")
        return curr.strip().upper() if curr else "CAD"

    def clean_nfse_description(self):
        desc = self.cleaned_data.get("nfse_description", "")
        if not desc or not desc.strip():
            raise ValidationError("A descrição da NFS-e é obrigatória.")
        return validate_macros(desc.strip(), VALID_INVOICE_MACROS)

    def clean_codigo_tributacao_nacional(self):
        val = (self.cleaned_data.get("codigo_tributacao_nacional") or "").strip()
        if not val:
            raise ValidationError("O Código de Tributação Nacional é obrigatório.")
        return val

    def clean_codigo_nbs(self):
        val = (self.cleaned_data.get("codigo_nbs") or "").strip()
        if not val:
            raise ValidationError("O Código NBS é obrigatório.")
        return val

    def clean_codigo_servico_municipio(self):
        return (self.cleaned_data.get("codigo_servico_municipio") or "").strip()

    def clean_cst_ibs_cbs(self):
        return (self.cleaned_data.get("cst_ibs_cbs") or "").strip()

    def clean_c_class_trib_ibs_cbs(self):
        return (self.cleaned_data.get("c_class_trib_ibs_cbs") or "").strip()

    def clean_c_ind_op_ibs_cbs(self):
        return (self.cleaned_data.get("c_ind_op_ibs_cbs") or "").strip()


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ["description", "quantity", "unit_price_foreign"]
        labels = {
            "description": "Descrição",
            "quantity": "Quantidade",
            "unit_price_foreign": "Preço Unitário",
        }
        widgets = {
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Descrição do serviço prestado...",
                }
            ),
            "quantity": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0.01"}
            ),
            "unit_price_foreign": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0.00"}
            ),
        }


InvoiceItemFormSet = inlineformset_factory(
    Invoice, InvoiceItem, form=InvoiceItemForm, extra=0, can_delete=True
)


class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = ["subject", "body", "language"]
        widgets = {
            "subject": forms.TextInput(attrs={"class": "form-control"}),
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "language": forms.Select(attrs={"class": "form-select"}),
        }

    def clean_subject(self):
        subject = self.cleaned_data.get("subject")
        return validate_macros(subject, VALID_EMAIL_MACROS)

    def clean_body(self):
        body = self.cleaned_data.get("body")
        return validate_macros(body, VALID_EMAIL_MACROS)


class InvoiceTemplateForm(forms.ModelForm):
    class Meta:
        model = InvoiceTemplate
        fields = [
            "name",
            "currency",
            "bank_details",
            "nfse_description",
            "codigo_tributacao_nacional",
            "codigo_servico_municipio",
            "codigo_nbs",
            "cst_ibs_cbs",
            "c_class_trib_ibs_cbs",
            "c_ind_op_ibs_cbs",
        ]
        labels = {
            "name": "Nome",
            "currency": "Moeda",
            "bank_details": "Dados Bancários",
            "nfse_description": "Descrição da NFS-e",
            "codigo_tributacao_nacional": "Cód. Tributação Nacional",
            "codigo_servico_municipio": "Cód. Serviço Município",
            "codigo_nbs": "Cód. NBS",
            "cst_ibs_cbs": "CST IBS/CBS",
            "c_class_trib_ibs_cbs": "Classificação IBS/CBS (cClassTrib)",
            "c_ind_op_ibs_cbs": "Indicador da Operação (cIndOp)",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "currency": forms.TextInput(attrs={"class": "form-control"}),
            "bank_details": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Dados bancários (suporta Markdown)...",
                }
            ),
            "nfse_description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": "Texto / discriminação dos serviços para a NFS-e...",
                }
            ),
            "codigo_tributacao_nacional": forms.TextInput(
                attrs={"class": "form-control font-monospace", "placeholder": "ex: 010101"}
            ),
            "codigo_servico_municipio": forms.TextInput(
                attrs={"class": "form-control font-monospace", "placeholder": "ex: 001"}
            ),
            "codigo_nbs": forms.TextInput(
                attrs={"class": "form-control font-monospace", "placeholder": "ex: 115029000"}
            ),
            "cst_ibs_cbs": forms.TextInput(
                attrs={"class": "form-control font-monospace", "placeholder": "ex: 410"}
            ),
            "c_class_trib_ibs_cbs": forms.TextInput(
                attrs={"class": "form-control font-monospace", "placeholder": "ex: 410004"}
            ),
            "c_ind_op_ibs_cbs": forms.TextInput(
                attrs={"class": "form-control font-monospace", "placeholder": "ex: 100301"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["codigo_servico_municipio"].required = False
        self.fields["cst_ibs_cbs"].required = False
        self.fields["c_class_trib_ibs_cbs"].required = False
        self.fields["c_ind_op_ibs_cbs"].required = False

    def clean_nfse_description(self):
        desc = self.cleaned_data.get("nfse_description", "")
        if not desc or not desc.strip():
            raise ValidationError("A descrição da NFS-e é obrigatória.")
        return validate_macros(desc.strip(), VALID_INVOICE_MACROS)

    def clean_codigo_tributacao_nacional(self):
        val = (self.cleaned_data.get("codigo_tributacao_nacional") or "").strip()
        if not val:
            raise ValidationError("O Código de Tributação Nacional é obrigatório.")
        return val

    def clean_codigo_nbs(self):
        val = (self.cleaned_data.get("codigo_nbs") or "").strip()
        if not val:
            raise ValidationError("O Código NBS é obrigatório.")
        return val

    def clean_codigo_servico_municipio(self):
        return (self.cleaned_data.get("codigo_servico_municipio") or "").strip()

    def clean_cst_ibs_cbs(self):
        return (self.cleaned_data.get("cst_ibs_cbs") or "").strip()

    def clean_c_class_trib_ibs_cbs(self):
        return (self.cleaned_data.get("c_class_trib_ibs_cbs") or "").strip()

    def clean_c_ind_op_ibs_cbs(self):
        return (self.cleaned_data.get("c_ind_op_ibs_cbs") or "").strip()


class InvoiceTemplateItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceTemplateItem
        fields = ["description", "quantity", "unit_price_foreign"]
        widgets = {
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "quantity": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0.01"}
            ),
            "unit_price_foreign": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0.00"}
            ),
        }

    def clean_description(self):
        description = self.cleaned_data.get("description")
        return validate_macros(description, VALID_INVOICE_MACROS)


InvoiceTemplateItemFormSet = inlineformset_factory(
    InvoiceTemplate,
    InvoiceTemplateItem,
    form=InvoiceTemplateItemForm,
    extra=0,
    can_delete=True,
)

from .models import CompanySettings


class CompanySettingsForm(forms.ModelForm):
    pfx_file = forms.FileField(
        required=False,
        label="Certificado Digital (PFX)",
        help_text="Faça o upload do seu certificado A1 (.pfx) caso deseje atualizá-lo.",
    )
    pfx_password_input = forms.CharField(
        required=False,
        label="Senha do Certificado PFX",
        widget=forms.PasswordInput(render_value=False),
        help_text="Informe a senha se estiver enviando um novo arquivo PFX.",
    )
    opening_date = forms.DateField(
        input_formats=["%d/%m/%Y", "%Y-%m-%d"],
        widget=forms.DateInput(
            format="%d/%m/%Y",
            attrs={
                "type": "text",
                "readonly": "readonly",
                "class": "form-control bg-body-secondary text-body-secondary",
                "style": "pointer-events: none;",
            },
        ),
    )

    class Meta:
        model = CompanySettings
        exclude = [
            "debug_mode",
            "pfx_cert_pem",
            "pfx_key_pem",
            "certificate_valid_until",
            "last_adn_nsu",
        ]
        labels = {
            "address_cep": "CEP",
            "address_tipo_logradouro": "Tipo de Logradouro",
            "address_line1": "Logradouro",
            "address_number": "Número",
            "address_line2": "Complemento",
            "address_neighborhood": "Bairro",
            "address_uf": "UF",
            "address_city": "Cidade",
            "auto_finalize_invoices": "Finalizar Invoices Automaticamente",
            "auto_send_emails": "Enviar E-mails Automaticamente",
            "auto_emit_nfse": "Emitir NFS-e Automaticamente",
            "auto_invoice_hour": "Hora do Processamento Automático",
            "debug_email": "E-mail de Depuração",
            "phone_number": "Telefone",
            "enable_cbs_ibs": "Ativar Grupo IBS/CBS na DPS Nacional",
        }
        help_texts = {
            "auto_finalize_invoices": "Finaliza automaticamente invoices em rascunho na data de emissão.",
            "auto_send_emails": "Envia e-mails automaticamente após a finalização da invoice.",
            "auto_emit_nfse": "Emite a NFS-e automaticamente após a finalização da invoice.",
            "auto_invoice_hour": "Hora do dia (0 a 23) para executar o processamento automático.",
            "debug_email": "Se preenchido, todos os e-mails são redirecionados para este endereço de teste.",
            "phone_number": "Telefone de contato da empresa.",
            "enable_cbs_ibs": "Habilita o preenchimento do grupo IBS/CBS na DPS Nacional (Reforma Tributária - LC 214/2025). Mantenha desativado até a vigência oficial ou adesão voluntária.",
        }
        widgets = {
            "enable_cbs_ibs": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "phone_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "(11) 99999-9999",
                }
            ),
            "company_name": forms.TextInput(
                attrs={
                    "readonly": "readonly",
                    "class": "form-control bg-body-secondary text-body-secondary",
                    "style": "pointer-events: none;",
                }
            ),
            "address_city_ibge": forms.HiddenInput(),
            "address_tipo_logradouro": forms.TextInput(
                attrs={
                    "readonly": "readonly",
                    "class": "form-control bg-body-secondary text-body-secondary",
                    "style": "pointer-events: none;",
                }
            ),
            "address_line1": forms.TextInput(
                attrs={
                    "readonly": "readonly",
                    "class": "form-control bg-body-secondary text-body-secondary",
                    "style": "pointer-events: none;",
                }
            ),
            "address_cep": forms.TextInput(
                attrs={
                    "readonly": "readonly",
                    "class": "form-control bg-body-secondary text-body-secondary",
                    "style": "pointer-events: none;",
                }
            ),
            "address_number": forms.TextInput(
                attrs={
                    "readonly": "readonly",
                    "class": "form-control bg-body-secondary text-body-secondary",
                    "style": "pointer-events: none;",
                }
            ),
            "address_line2": forms.TextInput(
                attrs={
                    "readonly": "readonly",
                    "class": "form-control bg-body-secondary text-body-secondary",
                    "style": "pointer-events: none;",
                }
            ),
            "address_neighborhood": forms.TextInput(
                attrs={
                    "readonly": "readonly",
                    "class": "form-control bg-body-secondary text-body-secondary",
                    "style": "pointer-events: none;",
                }
            ),
            "address_uf": forms.TextInput(
                attrs={
                    "readonly": "readonly",
                    "class": "form-control bg-body-secondary text-body-secondary",
                    "style": "pointer-events: none;",
                }
            ),
            "address_city": forms.TextInput(
                attrs={
                    "readonly": "readonly",
                    "class": "form-control bg-body-secondary text-body-secondary",
                    "style": "pointer-events: none;",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.is_bound and self.data.get("address_city_ibge"):
            ibge = self.data.get("address_city_ibge")
        elif self.instance and self.instance.pk:
            ibge = self.instance.address_city_ibge
        else:
            ibge = None

        if ibge:
            from core.models import get_allowed_providers

            allowed = get_allowed_providers(ibge)
            self.fields["nfse_provider"].choices = [
                (k, v) for k, v in self.fields["nfse_provider"].choices if k in allowed
            ]
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = (
                    field.widget.attrs.get("class", "") + " form-check-input"
                )
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = (
                    field.widget.attrs.get("class", "") + " form-select"
                )
            elif not isinstance(field.widget, forms.HiddenInput):
                field.widget.attrs["class"] = (
                    field.widget.attrs.get("class", "") + " form-control"
                )

    def clean_nfse_provider(self):
        provider = self.cleaned_data.get("nfse_provider")
        if provider == "PAULISTANA":
            from core.models import paulistana_emission_blocked

            if paulistana_emission_blocked():
                raise forms.ValidationError(
                    "ME/EPP do Simples Nacional devem emitir pelo Emissor Nacional desde 01/11/2026."
                )
        return provider

    def clean(self):
        cleaned_data = super().clean()
        pfx_file = cleaned_data.get("pfx_file")
        pfx_password = cleaned_data.get("pfx_password_input")

        if pfx_file:
            if not pfx_password:
                self.add_error(
                    "pfx_password_input",
                    "A senha é obrigatória ao enviar um arquivo PFX.",
                )
            else:
                try:
                    from core.nfse.cert import carregar_certificado_pfx_bytes

                    pfx_data = pfx_file.read()
                    key_pem, cert_pem, exp = carregar_certificado_pfx_bytes(
                        pfx_data, pfx_password
                    )
                    cleaned_data["pfx_cert_pem"] = cert_pem.decode("utf-8")
                    cleaned_data["pfx_key_pem"] = key_pem.decode("utf-8")
                    cleaned_data["certificate_valid_until"] = exp
                except Exception as e:
                    self.add_error("pfx_file", f"Erro ao validar certificado: {str(e)}")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get("pfx_cert_pem"):
            instance.pfx_cert_pem = self.cleaned_data["pfx_cert_pem"]
            instance.pfx_key_pem = self.cleaned_data["pfx_key_pem"]
            instance.certificate_valid_until = self.cleaned_data[
                "certificate_valid_until"
            ]
        if commit:
            instance.save()
        return instance

    def clean_cnpj(self):
        cnpj = self.cleaned_data.get("cnpj")
        if not cnpj:
            return cnpj
        from core.utils.formatters import validate_cnpj
        cleaned = re.sub(r"[^0-9a-zA-Z]", "", cnpj).upper()
        if len(cleaned) != 14:
            raise forms.ValidationError("CNPJ deve conter 14 caracteres alfanuméricos.")
        if not validate_cnpj(cleaned):
            raise forms.ValidationError("CNPJ inválido.")
        return cleaned


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            "name",
            "nif",
            "email",
            "email_cc",
            "address_line1",
            "address_number",
            "address_line2",
            "address_neighborhood",
            "address_city",
            "address_state_province",
            "address_postal_code",
            "address_country_code",
            "country",
        ]
        labels = {
            "name": "Nome / Razão Social",
            "nif": "NIF (Número de Identificação Fiscal / Tax ID)",
            "email": "E-mail Principal",
            "email_cc": "E-mails em Cópia (separados por vírgula)",
            "address_line1": "Logradouro / Endereço",
            "address_number": "Número",
            "address_line2": "Complemento / Sala / Suíte",
            "address_neighborhood": "Bairro / Distrito",
            "address_city": "Cidade",
            "address_state_province": "Estado / Província",
            "address_postal_code": "Código Postal / CEP",
            "address_country_code": "Código do País (ISO 2 letras, ex: CA, US)",
            "country": "País (ex: Canada, United States)",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nome ou Razão Social"}),
            "nif": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: 123456789"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "financeiro@cliente.com"}),
            "email_cc": forms.TextInput(attrs={"class": "form-control", "placeholder": "diretoria@cliente.com, contatofin@cliente.com"}),
            "address_line1": forms.TextInput(attrs={"class": "form-control", "placeholder": "Rua / Avenida"}),
            "address_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "100"}),
            "address_line2": forms.TextInput(attrs={"class": "form-control", "placeholder": "Suite 400"}),
            "address_neighborhood": forms.TextInput(attrs={"class": "form-control", "placeholder": "Bairro / Distrito"}),
            "address_city": forms.TextInput(attrs={"class": "form-control", "placeholder": "Cidade"}),
            "address_state_province": forms.TextInput(attrs={"class": "form-control", "placeholder": "Estado / Província"}),
            "address_postal_code": forms.TextInput(attrs={"class": "form-control", "placeholder": "Postal Code / Zip"}),
            "address_country_code": forms.TextInput(attrs={"class": "form-control", "placeholder": "CA"}),
            "country": forms.TextInput(attrs={"class": "form-control", "placeholder": "Canada"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["address_neighborhood"].required = True

    def clean_nif(self):
        nif = self.cleaned_data.get("nif", "")
        return nif.strip() if nif else ""

    def clean_address_country_code(self):
        code = self.cleaned_data.get("address_country_code", "")
        return code.strip().upper() if code else ""

    def clean_country(self):
        country = self.cleaned_data.get("country", "")
        return country.strip() if country else ""


class InvoiceDraftMetadataForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ["invoice_number", "client", "issue_date", "currency"]
        labels = {
            "invoice_number": "Número da Invoice",
            "client": "Cliente",
            "issue_date": "Data de Emissão",
            "currency": "Moeda",
        }
        widgets = {
            "invoice_number": forms.TextInput(attrs={"class": "form-control font-monospace"}),
            "client": forms.Select(attrs={"class": "form-select"}),
            "issue_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "currency": forms.TextInput(attrs={"class": "form-control", "placeholder": "CAD, USD, EUR, etc."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["invoice_number"].required = False

    def clean_invoice_number(self):
        inv_num = (self.cleaned_data.get("invoice_number") or "").strip()
        if not inv_num and "invoice_number" not in self.data and self.instance and self.instance.pk:
            return self.instance.invoice_number
        if not inv_num:
            raise forms.ValidationError("O número da invoice é obrigatório.")
        qs = Invoice.objects.filter(invoice_number=inv_num)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Já existe uma invoice com este número.")
        return inv_num

    def clean_currency(self):
        curr = self.cleaned_data.get("currency", "CAD")
        return curr.strip().upper() if curr else "CAD"

