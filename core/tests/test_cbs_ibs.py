import os
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import patch, MagicMock
from lxml import etree
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography import x509
from cryptography.x509.oid import NameOID

from django.conf import settings
from django.test import TestCase, Client as HttpClient
from django.urls import reverse
from django.contrib.auth.models import User

from core.models import (
    CompanySettings,
    Client,
    Invoice,
    InvoiceItem,
    InvoiceTemplate,
    InvoiceTemplateItem,
    NotaFiscal,
)
from core.forms import (
    CompanySettingsForm,
    InvoiceForm,
    InvoiceTemplateForm,
)
from core.nfse.base import EmitResult
from core.nfse.nacional.provider import NacionalProvider, _parse_decompressed_nfse_xml
from core.services.nfse_services import enviar_nfe_para_prefeitura, import_nfses


class CbsIbsModelAndTemplateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.client_http = HttpClient()
        self.client_http.login(username="testuser", password="password")

        self.company = CompanySettings.objects.create(
            company_name="Synthetic IT Services Ltda",
            cnpj="12.345.678/0001-90",
            inscricao_municipal="123456",
            opening_date=date(2024, 1, 1),
            email="financeiro@synthetic.local",
            pfx_cert_pem="cert",
            pfx_key_pem="key",
            next_document_number=1,
            document_series="1",
            address_city_ibge="3550308",
            enable_cbs_ibs=False,
        )

        self.client_obj = Client.objects.create(
            name="Acme International LLC",
            email="billing@acme.example",
            address_country_code="US",
            address_city="New York",
            address_state_province="NY",
            address_postal_code="10001",
            address_line1="100 Broadway",
            address_number="500",
            address_neighborhood="Manhattan",
        )

    def test_company_settings_enable_cbs_ibs_defaults_to_false(self):
        self.assertFalse(self.company.enable_cbs_ibs)
        self.company.enable_cbs_ibs = True
        self.company.save()
        reloaded = CompanySettings.objects.get(pk=self.company.pk)
        self.assertTrue(reloaded.enable_cbs_ibs)

    def test_invoice_and_template_default_cbs_ibs_fields(self):
        template = InvoiceTemplate.objects.create(
            name="Standard IT Template",
            currency="USD",
            bank_details="Bank instructions here",
            nfse_description="Development services",
            codigo_tributacao_nacional="010101",
            codigo_servico_municipio="001",
            codigo_nbs="115029000",
        )
        self.assertEqual(template.cst_ibs_cbs, "410")
        self.assertEqual(template.c_class_trib_ibs_cbs, "410004")
        self.assertEqual(template.c_ind_op_ibs_cbs, "100301")

        invoice = Invoice.objects.create(
            client=self.client_obj,
            invoice_number="INV-CBS-001",
            issue_date=date(2026, 10, 1),
            currency="USD",
        )
        self.assertEqual(invoice.cst_ibs_cbs, "410")
        self.assertEqual(invoice.c_class_trib_ibs_cbs, "410004")
        self.assertEqual(invoice.c_ind_op_ibs_cbs, "100301")

    def test_nota_fiscal_cbs_ibs_fields_default_blank(self):
        nf = NotaFiscal.objects.create(
            nf_number="123",
            issue_date=date(2026, 10, 1),
            amount_brl=Decimal("1000.00"),
            description="NFS-e description",
        )
        self.assertEqual(nf.cst_ibs_cbs, "")
        self.assertEqual(nf.c_class_trib_ibs_cbs, "")
        self.assertEqual(nf.c_ind_op_ibs_cbs, "")

    def test_create_from_template_copies_cbs_ibs_fields_and_items(self):
        template = InvoiceTemplate.objects.create(
            name="Custom CBS/IBS Template",
            currency="CAD",
            bank_details="Interac e-Transfer",
            nfse_description="Software programming",
            codigo_tributacao_nacional="010203",
            codigo_servico_municipio="002",
            codigo_nbs="115022999",
            cst_ibs_cbs="410",
            c_class_trib_ibs_cbs="410004",
            c_ind_op_ibs_cbs="100301",
        )
        InvoiceTemplateItem.objects.create(
            template=template,
            description="Sprint 42",
            quantity=Decimal("2.00"),
            unit_price_foreign=Decimal("500.00"),
        )

        inv = Invoice.create_from_template(
            template=template,
            client=self.client_obj,
            issue_date=date(2026, 10, 15),
            invoice_number="INV-FROM-TMPL-1",
        )
        self.assertEqual(inv.invoice_number, "INV-FROM-TMPL-1")
        self.assertEqual(inv.currency, "CAD")
        self.assertEqual(inv.cst_ibs_cbs, "410")
        self.assertEqual(inv.c_class_trib_ibs_cbs, "410004")
        self.assertEqual(inv.c_ind_op_ibs_cbs, "100301")
        self.assertEqual(inv.codigo_tributacao_nacional, "010203")
        self.assertEqual(inv.codigo_servico_municipio, "002")
        self.assertEqual(inv.codigo_nbs, "115022999")
        self.assertEqual(inv.items.count(), 1)
        self.assertEqual(inv.items.first().description, "Sprint 42")

        # Also test via template.create_invoice helper
        inv2 = template.create_invoice(
            client=self.client_obj,
            issue_date=date(2026, 10, 16),
            invoice_number="INV-FROM-TMPL-2",
        )
        self.assertEqual(inv2.cst_ibs_cbs, "410")
        self.assertEqual(inv2.c_class_trib_ibs_cbs, "410004")
        self.assertEqual(inv2.c_ind_op_ibs_cbs, "100301")
        self.assertEqual(inv2.items.count(), 1)

    def test_clone_invoice_copies_cbs_ibs_fields(self):
        original = Invoice.objects.create(
            client=self.client_obj,
            invoice_number="INV-ORIG-CBS",
            issue_date=date(2026, 9, 1),
            currency="USD",
            bank_details="Wire details",
            nfse_description="Original dev services",
            codigo_tributacao_nacional="010101",
            codigo_servico_municipio="001",
            codigo_nbs="115029000",
            cst_ibs_cbs="410",
            c_class_trib_ibs_cbs="410004",
            c_ind_op_ibs_cbs="100301",
        )
        InvoiceItem.objects.create(
            invoice=original,
            description="Item 1",
            quantity=1,
            unit_price_foreign=Decimal("2000.00"),
        )

        resp = self.client_http.post(reverse("clone_invoice", args=[original.id]))
        self.assertEqual(resp.status_code, 302)

        cloned = Invoice.objects.exclude(id=original.id).first()
        self.assertIsNotNone(cloned)
        self.assertEqual(cloned.cst_ibs_cbs, "410")
        self.assertEqual(cloned.c_class_trib_ibs_cbs, "410004")
        self.assertEqual(cloned.c_ind_op_ibs_cbs, "100301")

    def test_htmx_template_details_endpoint_returns_cbs_ibs_fields(self):
        template = InvoiceTemplate.objects.create(
            name="JSON Test Template",
            currency="USD",
            bank_details="Details",
            nfse_description="Desc",
            codigo_tributacao_nacional="010101",
            codigo_servico_municipio="001",
            codigo_nbs="115029000",
            cst_ibs_cbs="410",
            c_class_trib_ibs_cbs="410004",
            c_ind_op_ibs_cbs="100301",
        )
        resp = self.client_http.get(f"/htmx/template-details/{template.id}/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["cst_ibs_cbs"], "410")
        self.assertEqual(data["c_class_trib_ibs_cbs"], "410004")
        self.assertEqual(data["c_ind_op_ibs_cbs"], "100301")

    def test_htmx_update_fiscal_codes_updates_cbs_ibs_fields(self):
        inv = Invoice.objects.create(
            client=self.client_obj,
            invoice_number="INV-HTMX-EDIT",
            issue_date=date(2026, 10, 1),
            currency="USD",
            codigo_tributacao_nacional="010101",
            codigo_nbs="115029000",
            cst_ibs_cbs="410",
            c_class_trib_ibs_cbs="410004",
            c_ind_op_ibs_cbs="100301",
            status="DRAFT",
        )
        resp = self.client_http.post(
            reverse("htmx_update_fiscal_codes", args=[inv.id]),
            data={
                "codigo_tributacao_nacional": "010203",
                "codigo_servico_municipio": "001",
                "codigo_nbs": "115022999",
                "cst_ibs_cbs": "410",
                "c_class_trib_ibs_cbs": "410004",
                "c_ind_op_ibs_cbs": "100301",
            },
        )
        self.assertEqual(resp.status_code, 200)
        inv.refresh_from_db()
        self.assertEqual(inv.codigo_tributacao_nacional, "010203")
        self.assertEqual(inv.cst_ibs_cbs, "410")
        self.assertEqual(inv.c_class_trib_ibs_cbs, "410004")
        self.assertEqual(inv.c_ind_op_ibs_cbs, "100301")
        self.assertIn("CST IBS/CBS", resp.content.decode("utf-8"))

    def test_htmx_update_fiscal_codes_rejects_overlong_codes(self):
        inv = Invoice.objects.create(
            client=self.client_obj,
            invoice_number="INV-HTMX-OVERLONG",
            issue_date=date(2026, 10, 1),
            currency="USD",
            codigo_tributacao_nacional="010101",
            codigo_nbs="115029000",
            status="DRAFT",
        )
        resp = self.client_http.post(
            reverse("htmx_update_fiscal_codes", args=[inv.id]),
            data={
                "codigo_tributacao_nacional": "010203",
                "codigo_servico_municipio": "001",
                "codigo_nbs": "115022999",
                "cst_ibs_cbs": "4100",  # 4 chars > max 3
                "c_class_trib_ibs_cbs": "410004",
                "c_ind_op_ibs_cbs": "100301",
            },
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("CST do IBS/CBS deve ter no máximo 3 caracteres", resp.content.decode("utf-8"))


class CbsIbsDpsGenerationAndXsdTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.test_key_pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        subject = issuer = x509.Name(
            [x509.NameAttribute(NameOID.COMMON_NAME, "synthetic.local")]
        )
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
        cls.test_cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode(
            "utf-8"
        )

    def setUp(self):
        self.company = CompanySettings.objects.create(
            company_name="Synthetic IT Services Ltda",
            cnpj="12.345.678/0001-90",
            inscricao_municipal="123456",
            opening_date=date(2024, 1, 1),
            email="financeiro@synthetic.local",
            pfx_cert_pem=self.test_cert_pem,
            pfx_key_pem=self.test_key_pem,
            next_document_number=1,
            document_series="1",
            address_city_ibge="3550308",
            enable_cbs_ibs=False,
        )

        self.client_obj = Client.objects.create(
            name="Foreign Test Client LLC",
            email="client@example.com",
            address_country_code="US",
            address_city="New York",
            address_state_province="NY",
            address_postal_code="10001",
            address_line1="123 Broadway",
            address_number="100",
            address_neighborhood="Manhattan",
        )

        self.invoice = Invoice.objects.create(
            invoice_number="INV-DPS-001",
            client=self.client_obj,
            issue_date=date.today(),
            currency="USD",
            exchange_rate_to_brl=Decimal("5.0000"),
            codigo_tributacao_nacional="010101",
            codigo_nbs="115029000",
            codigo_servico_municipio="001",
            cst_ibs_cbs="410",
            c_class_trib_ibs_cbs="410004",
            c_ind_op_ibs_cbs="100301",
            status="DRAFT",
        )
        InvoiceItem.objects.create(
            invoice=self.invoice,
            description="Consulting Services",
            quantity=1,
            unit_price_foreign=Decimal("100.00"),
        )
        self.invoice.status = "FINALIZED"
        self.invoice.save()

    def test_dps_xml_omits_ibscbs_when_toggle_is_disabled(self):
        self.company.enable_cbs_ibs = False
        self.company.save()

        provider = NacionalProvider()
        dps, signed_xml, id_dps = provider._build_and_sign_dps(
            self.invoice, self.company, 1, "4242"
        )
        self.assertNotIn("<IBSCBS>", signed_xml)
        self.assertNotIn("cClassTrib", signed_xml)
        self.assertNotIn("cIndOp", signed_xml)

    def test_dps_xml_includes_ibscbs_when_toggle_is_enabled(self):
        self.company.enable_cbs_ibs = True
        self.company.save()

        provider = NacionalProvider()
        dps, signed_xml, id_dps = provider._build_and_sign_dps(
            self.invoice, self.company, 1, "4242"
        )
        self.assertIn("<IBSCBS>", signed_xml)
        self.assertIn("<finNFSe>0</finNFSe>", signed_xml)
        self.assertIn("<indDest>0</indDest>", signed_xml)
        self.assertIn("<CST>410</CST>", signed_xml)
        self.assertIn("<cClassTrib>410004</cClassTrib>", signed_xml)
        # For CST 410 (export/immunity), cIndOp is omitted to satisfy Sefin Rule E0859
        self.assertNotIn("<cIndOp>", signed_xml)
        self.assertIn("</IBSCBS>", signed_xml)

    def test_dps_xml_with_custom_cbs_ibs_values(self):
        self.company.enable_cbs_ibs = True
        self.company.save()

        # For a taxable CST (e.g. 000 / 000001), cIndOp must be present
        self.invoice.cst_ibs_cbs = "000"
        self.invoice.c_class_trib_ibs_cbs = "000001"
        self.invoice.c_ind_op_ibs_cbs = "100301"
        self.invoice.save()

        provider = NacionalProvider()
        dps, signed_xml, _ = provider._build_and_sign_dps(
            self.invoice, self.company, 2, "4242"
        )
        self.assertIn("<CST>000</CST>", signed_xml)
        self.assertIn("<cClassTrib>000001</cClassTrib>", signed_xml)
        self.assertIn("<cIndOp>100301</cIndOp>", signed_xml)

    def test_dps_xml_falls_back_to_defaults_if_invoice_fields_empty(self):
        self.company.enable_cbs_ibs = True
        self.company.save()

        self.invoice.cst_ibs_cbs = ""
        self.invoice.c_class_trib_ibs_cbs = ""
        self.invoice.c_ind_op_ibs_cbs = ""
        self.invoice.save()

        provider = NacionalProvider()
        dps, signed_xml, _ = provider._build_and_sign_dps(
            self.invoice, self.company, 3, "4242"
        )
        self.assertIn("<IBSCBS>", signed_xml)
        self.assertIn("<CST>410</CST>", signed_xml)
        self.assertIn("<cClassTrib>410004</cClassTrib>", signed_xml)
        self.assertNotIn("<cIndOp>", signed_xml)

    def test_dps_xml_falls_back_to_defaults_if_invoice_fields_whitespace(self):
        self.company.enable_cbs_ibs = True
        self.company.save()

        self.invoice.cst_ibs_cbs = "   "
        self.invoice.c_class_trib_ibs_cbs = "   "
        self.invoice.c_ind_op_ibs_cbs = "   "
        self.invoice.save()

        provider = NacionalProvider()
        dps, signed_xml, _ = provider._build_and_sign_dps(
            self.invoice, self.company, 4, "4242"
        )
        self.assertIn("<IBSCBS>", signed_xml)
        self.assertIn("<CST>410</CST>", signed_xml)
        self.assertIn("<cClassTrib>410004</cClassTrib>", signed_xml)
        self.assertNotIn("<cIndOp>", signed_xml)
        self.assertNotIn("<CST></CST>", signed_xml)

    def test_dps_xml_validates_against_official_xsd_schema(self):
        self.company.enable_cbs_ibs = True
        self.company.save()

        provider = NacionalProvider()
        _, signed_xml, _ = provider._build_and_sign_dps(
            self.invoice, self.company, 1, "4242"
        )

        xsd_path = os.path.join(
            str(settings.BASE_DIR),
            "core",
            "nfse",
            "nacional",
            "xsd",
            "esquemas_prod_restrita_20261020",
            "DPS_v1.01.xsd",
        )
        self.assertTrue(os.path.exists(xsd_path), f"XSD schema file not found at {xsd_path}")

        xmlschema = etree.XMLSchema(etree.parse(xsd_path))
        doc = etree.fromstring(signed_xml.encode("utf-8"))

        is_valid = xmlschema.validate(doc)
        error_messages = [f"{err.message} (line {err.line})" for err in xmlschema.error_log]
        self.assertTrue(is_valid, f"XSD validation failed: {error_messages}")


class CbsIbsEmissionAndPersistenceTests(TestCase):
    def setUp(self):
        self.company = CompanySettings.objects.create(
            company_name="Synthetic IT Services Ltda",
            cnpj="12.345.678/0001-90",
            inscricao_municipal="123456",
            opening_date=date(2024, 1, 1),
            email="financeiro@synthetic.local",
            pfx_cert_pem="cert",
            pfx_key_pem="key",
            next_document_number=1,
            document_series="1",
            address_city_ibge="3550308",
            enable_cbs_ibs=True,
        )

        self.client_obj = Client.objects.create(
            name="Foreign Test Client LLC",
            email="client@example.com",
            address_country_code="US",
            address_city="New York",
            address_state_province="NY",
            address_postal_code="10001",
            address_line1="123 Broadway",
            address_number="100",
            address_neighborhood="Manhattan",
        )

        self.invoice = Invoice.objects.create(
            invoice_number="INV-EMIT-CBS-1",
            client=self.client_obj,
            issue_date=date.today(),
            currency="USD",
            exchange_rate_to_brl=Decimal("5.0000"),
            codigo_tributacao_nacional="010101",
            codigo_nbs="115029000",
            codigo_servico_municipio="001",
            cst_ibs_cbs="410",
            c_class_trib_ibs_cbs="410004",
            c_ind_op_ibs_cbs="100301",
            status="DRAFT",
        )
        InvoiceItem.objects.create(
            invoice=self.invoice,
            description="Consulting",
            quantity=1,
            unit_price_foreign=Decimal("500.00"),
        )
        self.invoice.status = "FINALIZED"
        self.invoice.save()

    @patch("core.services.nfse_services.fetch_and_save_nfse_pdf", return_value=b"%PDF-mock")
    @patch("core.nfse.nacional.provider.NacionalProvider.emitir_nfse")
    def test_emit_nfse_persists_cbs_ibs_on_nota_fiscal(self, mock_emit, mock_pdf):
        mock_emit.return_value = EmitResult(
            sucesso=True,
            numero_nf="888123",
            chave_acesso_nacional="35503082123456780001950000000000000000000001",
            codigo_verificacao="VERIF123",
            codigo_tributacao_nacional="010101",
            codigo_nbs="115029000",
            codigo_servico_municipio="001",
            cst_ibs_cbs="410",
            c_class_trib_ibs_cbs="410004",
            c_ind_op_ibs_cbs="100301",
            xml_retorno="<NFSe><numero>888123</numero></NFSe>",
        )

        success = enviar_nfe_para_prefeitura(self.invoice)
        self.assertTrue(success)
        self.invoice.refresh_from_db()
        nf = getattr(self.invoice, "nota_fiscal", None)
        self.assertIsNotNone(nf)
        self.assertEqual(nf.nf_number, "888123")
        self.assertEqual(nf.cst_ibs_cbs, "410")
        self.assertEqual(nf.c_class_trib_ibs_cbs, "410004")
        self.assertEqual(nf.c_ind_op_ibs_cbs, "100301")

    def test_parse_decompressed_nfse_xml_extracts_cbs_ibs(self):
        sample_xml = """<NFSe versao="1.01">
            <infNFSe>
                <nNFSe>999123</nNFSe>
                <dhProc>2026-10-19T12:00:00-03:00</dhProc>
                <cTribNac>010101</cTribNac>
                <cNBS>115029000</cNBS>
                <cTribMun>001</cTribMun>
                <IBSCBS>
                    <cIndOp>100301</cIndOp>
                    <valores>
                        <trib>
                            <gIBSCBS>
                                <CST>410</CST>
                                <cClassTrib>410004</cClassTrib>
                            </gIBSCBS>
                        </trib>
                    </valores>
                </IBSCBS>
            </infNFSe>
        </NFSe>"""
        parsed = _parse_decompressed_nfse_xml(sample_xml)
        self.assertEqual(parsed["numero_nf"], "999123")
        self.assertEqual(parsed["cst_ibs_cbs"], "410")
        self.assertEqual(parsed["c_class_trib_ibs_cbs"], "410004")
        self.assertEqual(parsed["c_ind_op_ibs_cbs"], "100301")

    @patch("core.services.nfse_services.fetch_and_save_nfse_pdf", return_value=b"%PDF-mock")
    @patch("core.nfse.nacional.provider.NacionalProvider.emitir_nfse")
    def test_emit_nfse_leaves_cbs_ibs_blank_when_toggle_is_disabled(self, mock_emit, mock_pdf):
        self.company.enable_cbs_ibs = False
        self.company.save()

        mock_emit.return_value = EmitResult(
            sucesso=True,
            numero_nf="888124",
            chave_acesso_nacional="35503082123456780001950000000000000000000002",
            codigo_verificacao="VERIF124",
            codigo_tributacao_nacional="010101",
            codigo_nbs="115029000",
            codigo_servico_municipio="001",
            cst_ibs_cbs="",
            c_class_trib_ibs_cbs="",
            c_ind_op_ibs_cbs="",
            xml_retorno="<NFSe><numero>888124</numero></NFSe>",
        )

        success = enviar_nfe_para_prefeitura(self.invoice)
        self.assertTrue(success)
        self.invoice.refresh_from_db()
        nf = getattr(self.invoice, "nota_fiscal", None)
        self.assertIsNotNone(nf)
        self.assertEqual(nf.nf_number, "888124")
        self.assertEqual(nf.cst_ibs_cbs, "")
        self.assertEqual(nf.c_class_trib_ibs_cbs, "")
        self.assertEqual(nf.c_ind_op_ibs_cbs, "")

    def test_parse_decompressed_nfse_xml_ignores_piscofins_cst_when_no_ibscbs(self):
        xml_without_ibscbs = """<NFSe versao="1.01">
            <infNFSe>
                <nNFSe>111222</nNFSe>
                <valores>
                    <trib>
                        <tribOutrosPisCofins>
                            <CST>08</CST>
                        </tribOutrosPisCofins>
                    </trib>
                </valores>
            </infNFSe>
        </NFSe>"""
        parsed = _parse_decompressed_nfse_xml(xml_without_ibscbs)
        self.assertEqual(parsed["cst_ibs_cbs"], "")
        self.assertEqual(parsed["c_class_trib_ibs_cbs"], "")
        self.assertEqual(parsed["c_ind_op_ibs_cbs"], "")

    def test_parse_decompressed_nfse_xml_extracts_correct_cst_when_both_piscofins_and_ibscbs_present(self):
        xml_with_both = """<NFSe versao="1.01">
            <infNFSe>
                <nNFSe>111333</nNFSe>
                <valores>
                    <trib>
                        <tribOutrosPisCofins>
                            <CST>08</CST>
                        </tribOutrosPisCofins>
                    </trib>
                </valores>
                <IBSCBS>
                    <cIndOp>100301</cIndOp>
                    <valores>
                        <trib>
                            <gIBSCBS>
                                <CST>410</CST>
                                <cClassTrib>410004</cClassTrib>
                            </gIBSCBS>
                        </trib>
                    </valores>
                </IBSCBS>
            </infNFSe>
        </NFSe>"""
        parsed = _parse_decompressed_nfse_xml(xml_with_both)
        self.assertEqual(parsed["cst_ibs_cbs"], "410")
        self.assertEqual(parsed["c_class_trib_ibs_cbs"], "410004")
        self.assertEqual(parsed["c_ind_op_ibs_cbs"], "100301")

    @patch("core.nfse.nacional.provider.NacionalProvider.consultar_eventos_nfse", return_value=[])
    @patch("core.services.nfse_services.fetch_and_save_nfse_pdf")
    @patch("core.nfse.nacional.provider.NacionalProvider.consultar_dfe_por_nsu")
    def test_import_nfses_populates_cbs_ibs_codes_from_nacional_nsu(self, mock_query, mock_pdf, mock_evs):
        xml_cbs = """<NFSe versao="1.01">
            <infNFSe>
                <nNFSe>555888</nNFSe>
                <dhProc>2026-10-19T10:00:00-03:00</dhProc>
                <cTribNac>010101</cTribNac>
                <cNBS>115029000</cNBS>
                <cTribMun>001</cTribMun>
                <valores>
                    <vLiq>5000.00</vLiq>
                    <trib>
                        <totTrib>
                            <vTotTrib>0.00</vTotTrib>
                        </totTrib>
                    </trib>
                </valores>
                <emit>
                    <CNPJ>12345678000190</CNPJ>
                </emit>
                <IBSCBS>
                    <cIndOp>100301</cIndOp>
                    <valores>
                        <trib>
                            <gIBSCBS>
                                <CST>410</CST>
                                <cClassTrib>410004</cClassTrib>
                            </gIBSCBS>
                        </trib>
                    </valores>
                </IBSCBS>
            </infNFSe>
        </NFSe>"""
        import gzip
        import base64
        b64_cbs = base64.b64encode(gzip.compress(xml_cbs.encode("utf-8"))).decode("utf-8")
        chave_50 = "35503082112345678000190" + "0" * 27

        mock_query.return_value = ([{
            "NSU": 99999,
            "TipoDocumento": "NFSE",
            "TipoEvento": None,
            "ChaveAcesso": chave_50,
            "ArquivoXml": b64_cbs,
        }], 99999)

        count, msg = import_nfses("NACIONAL")
        self.assertEqual(count, 1)

        nf = NotaFiscal.objects.filter(nf_number="555888").first()
        self.assertIsNotNone(nf)
        self.assertEqual(nf.cst_ibs_cbs, "410")
        self.assertEqual(nf.c_class_trib_ibs_cbs, "410004")
        self.assertEqual(nf.c_ind_op_ibs_cbs, "100301")


class CbsIbsFormsValidationTests(TestCase):
    def test_company_settings_form_includes_enable_cbs_ibs(self):
        form = CompanySettingsForm()
        self.assertIn("enable_cbs_ibs", form.fields)
        self.assertEqual(form.fields["enable_cbs_ibs"].label, "Ativar Grupo IBS/CBS na DPS Nacional")

    def test_invoice_form_includes_and_cleans_cbs_ibs(self):
        client = Client.objects.create(name="Form Client Test")
        form = InvoiceForm(
            data={
                "client": client.id,
                "invoice_number": "FORM-INV-001",
                "issue_date": "2026-10-19",
                "currency": "USD",
                "codigo_tributacao_nacional": "010101",
                "codigo_nbs": "115029000",
                "codigo_servico_municipio": "001",
                "cst_ibs_cbs": " 410 ",
                "c_class_trib_ibs_cbs": " 410004 ",
                "c_ind_op_ibs_cbs": " 100301 ",
                "nfse_description": "Valid service description",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["cst_ibs_cbs"], "410")
        self.assertEqual(form.cleaned_data["c_class_trib_ibs_cbs"], "410004")
        self.assertEqual(form.cleaned_data["c_ind_op_ibs_cbs"], "100301")

    def test_invoice_template_form_includes_and_cleans_cbs_ibs(self):
        form = InvoiceTemplateForm(
            data={
                "name": "Template Form Test",
                "currency": "CAD",
                "codigo_tributacao_nacional": "010101",
                "codigo_nbs": "115029000",
                "codigo_servico_municipio": "001",
                "cst_ibs_cbs": " 410 ",
                "c_class_trib_ibs_cbs": " 410004 ",
                "c_ind_op_ibs_cbs": " 100301 ",
                "nfse_description": "Valid template description",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["cst_ibs_cbs"], "410")
        self.assertEqual(form.cleaned_data["c_class_trib_ibs_cbs"], "410004")
        self.assertEqual(form.cleaned_data["c_ind_op_ibs_cbs"], "100301")
