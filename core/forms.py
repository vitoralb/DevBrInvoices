from decimal import Decimal
import re
from django import forms
from django.core.exceptions import ValidationError
from .models import (
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
    "{start_date}",
    "{end_date}",
    "{{ company_cnpj }}",
}

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
        ]
        labels = {
            "client": "Cliente",
            "invoice_number": "Número da Invoice",
            "issue_date": "Data de Emissão",
            "currency": "Moeda",
            "bank_details": "Dados Bancários",
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
        }

    def clean_currency(self):
        curr = self.cleaned_data.get("currency", "CAD")
        return curr.strip().upper() if curr else "CAD"


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
        fields = ["name", "currency", "bank_details"]
        labels = {
            "name": "Nome",
            "currency": "Moeda",
            "bank_details": "Dados Bancários",
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
        }


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
                "class": "form-control",
                "style": "pointer-events: none; background-color: #e9ecef;",
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
        }
        widgets = {
            "company_name": forms.TextInput(
                attrs={
                    "readonly": "readonly",
                    "class": "form-control",
                    "style": "pointer-events: none; background-color: #e9ecef;",
                }
            ),
            "address_city_ibge": forms.HiddenInput(),
            "address_tipo_logradouro": forms.TextInput(
                attrs={
                    "readonly": "readonly",
                    "class": "form-control",
                    "style": "pointer-events: none; background-color: #e9ecef;",
                }
            ),
            "address_line1": forms.TextInput(
                attrs={
                    "readonly": "readonly",
                    "class": "form-control",
                    "style": "pointer-events: none; background-color: #e9ecef;",
                }
            ),
            "address_cep": forms.TextInput(
                attrs={
                    "readonly": "readonly",
                    "class": "form-control",
                    "style": "pointer-events: none; background-color: #e9ecef;",
                }
            ),
            "address_number": forms.TextInput(
                attrs={
                    "readonly": "readonly",
                    "class": "form-control",
                    "style": "pointer-events: none; background-color: #e9ecef;",
                }
            ),
            "address_line2": forms.TextInput(
                attrs={
                    "readonly": "readonly",
                    "class": "form-control",
                    "style": "pointer-events: none; background-color: #e9ecef;",
                }
            ),
            "address_neighborhood": forms.TextInput(
                attrs={
                    "readonly": "readonly",
                    "class": "form-control",
                    "style": "pointer-events: none; background-color: #e9ecef;",
                }
            ),
            "address_uf": forms.TextInput(
                attrs={
                    "readonly": "readonly",
                    "class": "form-control",
                    "style": "pointer-events: none; background-color: #e9ecef;",
                }
            ),
            "address_city": forms.TextInput(
                attrs={
                    "readonly": "readonly",
                    "class": "form-control",
                    "style": "pointer-events: none; background-color: #e9ecef;",
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
        cnpj = re.sub(r"[^0-9]", "", cnpj)
        if len(cnpj) != 14:
            raise forms.ValidationError("CNPJ deve conter 14 dígitos numéricos.")

        # Validate modulo-11 checksum
        def calc_digit(cnpj_digits, weights):
            total = sum(d * w for d, w in zip(cnpj_digits, weights))
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder

        digits = [int(c) for c in cnpj]
        w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        w2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        if (
            calc_digit(digits[:12], w1) != digits[12]
            or calc_digit(digits[:13], w2) != digits[13]
        ):
            raise forms.ValidationError("CNPJ inválido.")
        return cnpj
