import re
from django.test import TestCase
from django import forms
from core.models import CompanySettings, Client, Invoice, InvoiceItem
from core.forms import CompanySettingsForm
from core.utils.formatters import format_cnpj, validate_cnpj
from core.esocial.client import EsocialClient
from core.nfse.paulistana.mock import _format_cnpj as paulistana_format_cnpj
from core.nfse.paulistana.rps_signer import assinar_rps_v1
from core.nfse.paulistana.schemas_v1.tipos_nfe_v01 import (
    TpChaveRps as TpChaveRpsV1,
    TpCpfcnpj as TpCpfcnpjV1,
    TpRps as TpRpsV1,
)
from core.nfse.nacional.provider import NacionalProvider
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from datetime import date


class AlphanumericCnpjValidationTests(TestCase):
    def test_validate_cnpj_classic_numeric(self):
        # Valid classic numeric CNPJ (synthetic test)
        self.assertTrue(validate_cnpj("12.345.678/0001-95"))
        self.assertTrue(validate_cnpj("12345678000195"))

        # Invalid classic numeric CNPJ
        self.assertFalse(validate_cnpj("12.345.678/0001-99"))
        self.assertFalse(validate_cnpj("12345678000100"))

    def test_validate_cnpj_alphanumeric_official_spec(self):
        # Official example from Serpro / Receita Federal IN RFB nº 2.229/2024:
        # Base: 12.ABC.345/01DE -> DV: 35
        self.assertTrue(validate_cnpj("12.ABC.345/01DE-35"))
        self.assertTrue(validate_cnpj("12ABC34501DE35"))
        # Case insensitive input
        self.assertTrue(validate_cnpj("12.abc.345/01de-35"))
        self.assertTrue(validate_cnpj("12abc34501de35"))

        # Invalid check digits for alphanumeric
        self.assertFalse(validate_cnpj("12.ABC.345/01DE-34"))
        self.assertFalse(validate_cnpj("12.ABC.345/01DE-00"))

    def test_validate_cnpj_check_digits_must_be_numeric(self):
        # Positions 13 and 14 must be numeric digits [0-9]
        self.assertFalse(validate_cnpj("12.ABC.345/01DE-AA"))
        self.assertFalse(validate_cnpj("12.ABC.345/01DE-3A"))

    def test_validate_cnpj_edge_cases(self):
        self.assertFalse(validate_cnpj(None))
        self.assertFalse(validate_cnpj(""))
        self.assertFalse(validate_cnpj("123"))
        self.assertFalse(validate_cnpj("12.ABC.345/01DE-35111"))  # too long
        self.assertFalse(validate_cnpj("12.ABC.345/01D@-35"))  # invalid character @


class AlphanumericCnpjFormattingTests(TestCase):
    def test_format_cnpj_numeric_and_alphanumeric(self):
        self.assertEqual(format_cnpj("12345678000195"), "12.345.678/0001-95")
        self.assertEqual(format_cnpj("12ABC34501DE35"), "12.ABC.345/01DE-35")
        self.assertEqual(format_cnpj("12abc34501de35"), "12.ABC.345/01DE-35")

    def test_format_cnpj_edge_cases(self):
        self.assertEqual(format_cnpj(None), "")
        self.assertEqual(format_cnpj(""), "")
        self.assertEqual(format_cnpj("12345"), "12345")


class AlphanumericCnpjFormAndModelTests(TestCase):
    def setUp(self):
        self.company = CompanySettings.objects.create(
            company_name="Alpha Tech Consulting Ltda",
            cnpj="12.ABC.345/01DE-35",
            inscricao_municipal="12345678",
            opening_date=date(2026, 1, 1),
            email="financeiro@synthetic.local",
            address_city_ibge="3550308",
            address_neighborhood="Centro",
        )

    def test_company_settings_cnpj_clean_property(self):
        self.assertEqual(self.company.cnpj_clean, "12ABC34501DE35")

    def test_company_settings_form_clean_cnpj_alphanumeric(self):
        form = CompanySettingsForm(
            data={
                "company_name": "Alpha Tech Consulting Ltda",
                "cnpj": "12.ABC.345/01DE-35",
                "inscricao_municipal": "12345678",
                "opening_date": "01/01/2026",
                "email": "financeiro@synthetic.local",
                "address_city_ibge": "3550308",
                "address_neighborhood": "Centro",
                "nfse_provider": "NACIONAL",
                "document_series": "4242",
                "next_document_number": 1,
                "auto_invoice_hour": 9,
            },
            instance=self.company,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["cnpj"], "12ABC34501DE35")

    def test_company_settings_form_clean_cnpj_invalid_alphanumeric(self):
        form = CompanySettingsForm(
            data={
                "company_name": "Alpha Tech Consulting Ltda",
                "cnpj": "12.ABC.345/01DE-99",  # Wrong DV
                "inscricao_municipal": "12345678",
                "opening_date": "01/01/2026",
                "email": "financeiro@synthetic.local",
                "address_city_ibge": "3550308",
                "address_neighborhood": "Centro",
                "nfse_provider": "NACIONAL",
                "document_series": "4242",
                "next_document_number": 1,
                "auto_invoice_hour": 9,
            },
            instance=self.company,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("cnpj", form.errors)
        self.assertIn("CNPJ inválido.", form.errors["cnpj"][0])


class AlphanumericCnpjIntegrationTests(TestCase):
    def test_esocial_extract_cnpj_base_alphanumeric(self):
        base = EsocialClient._extract_cnpj_base("12.ABC.345/01DE-35")
        self.assertEqual(base, "12ABC345")

    def test_paulistana_format_cnpj_alphanumeric(self):
        res = paulistana_format_cnpj("12ABC34501DE35")
        self.assertEqual(res, "12.ABC.345/01DE-35")

    def test_paulistana_rps_signer_alphanumeric(self):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        key_pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )

        rps = TpRpsV1(
            assinatura="",
            chave_rps=TpChaveRpsV1(inscricao_prestador=12345678, serie_rps="A", numero_rps=1),
            tipo_rps="RPS",
            data_emissao="2026-10-20",
            status_rps="N",
            tributacao_rps="T",
            valor_servicos="100.00",
            valor_deducoes="0.00",
            codigo_servico=2675,
            aliquota_servicos="0.05",
            issretido=False,
            cpfcnpjtomador=TpCpfcnpjV1(cnpj="12ABC34501DE35"),
            discriminacao="Consulting Service",
        )
        signature = assinar_rps_v1(rps, key_pem)
        self.assertTrue(isinstance(signature, str))
        self.assertTrue(len(signature) > 50)

    def test_nacional_id_dps_generation_alphanumeric(self):
        from decimal import Decimal
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from datetime import datetime, timezone, timedelta

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        key_pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")
        subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "synthetic.local")])
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(timezone.utc) - timedelta(days=1))
            .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
            .sign(key, hashes.SHA256())
        )
        cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")

        company = CompanySettings.objects.create(
            company_name="Alpha Tech Consulting Ltda",
            cnpj="12.ABC.345/01DE-35",
            inscricao_municipal="12345678",
            opening_date=date(2026, 1, 1),
            email="financeiro@synthetic.local",
            address_city_ibge="3550308",
            address_neighborhood="Centro",
            pfx_cert_pem=cert_pem,
            pfx_key_pem=key_pem,
        )
        client = Client.objects.create(
            name="Foreign Client Inc",
            address_neighborhood="Downtown",
            address_country_code="US",
        )
        invoice = Invoice.objects.create(
            client=client,
            invoice_number="INV-ALPHA-01",
            currency="USD",
            exchange_rate_to_brl=Decimal("5.0000"),
            codigo_tributacao_nacional="010101",
            codigo_nbs="1.0101",
            issue_date=date(2026, 10, 1),
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            description="Consulting Service",
            quantity=1,
            unit_price_foreign=Decimal("500.00"),
        )
        invoice.status = "FINALIZED"
        invoice.save()

        provider = NacionalProvider()
        dps, signed_xml, id_dps = provider._build_and_sign_dps(
            invoice, company, numero_dps=1, serie_dps="4242"
        )
        # Expected ID DPS length: "DPS" (3) + cMun (7) + tpInsc (1) + CNPJ (14) + serie (5) + nDPS (15) = 45
        self.assertEqual(len(id_dps), 45)
        self.assertIn("12ABC34501DE35", id_dps)
        self.assertTrue(id_dps.startswith("DPS3550308212ABC34501DE35"))
