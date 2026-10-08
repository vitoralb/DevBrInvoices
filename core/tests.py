import re
import uuid
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from dateutil.relativedelta import relativedelta
from django.conf import settings
from config.settings import get_csrf_trusted_origins
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.middleware.csrf import CsrfViewMiddleware
from django.test import Client as HttpClient, RequestFactory, TestCase, override_settings
from django.urls import reverse

from core.models import (
    Client,
    CompanySettings,
    Invoice,
    InvoiceItem,
    InvoiceTemplate,
    InvoiceTemplateItem,
    MonthlyConsolidation,
    NotaFiscal,
)
from core.services import (
    calculate_ideal_pro_labore,
    calculate_inss,
    calculate_irrf,
    calculate_rbt12_and_fator_r,
    fetch_exchange_rate,
    get_minimum_salary,
)


class TaxCalculationTests(TestCase):
    def setUp(self):
        self.company = CompanySettings.objects.create(
            company_name="Test Co",
            cnpj="00.000.000/0001-00",
            opening_date=date(2024, 1, 1),
            inscricao_municipal="123456",
            email="test@test.com",
            pfx_cert_pem="cert",
            pfx_key_pem="key",
        )

    def test_minimum_salary(self):
        min_salary = get_minimum_salary(date(2024, 6, 1))
        self.assertEqual(min_salary, Decimal("1412.00"))

    def test_calculate_inss_below_ceiling(self):
        inss = calculate_inss(Decimal("2000.00"), date(2024, 6, 1))
        # 11% of 2000 = 220.00
        self.assertEqual(inss, Decimal("220.00"))

    def test_calculate_inss_above_ceiling(self):
        # Max bracket ceiling is 7786.02
        inss = calculate_inss(Decimal("10000.00"), date(2024, 6, 1))
        # 11% of 7786.02 = 856.46
        self.assertEqual(inss, Decimal("856.46"))

    def test_calculate_irrf_returns_decimal_not_tuple(self):
        # Pro labore below exemption
        irrf = calculate_irrf(Decimal("1412.00"), date(2024, 6, 1))
        self.assertIsInstance(irrf, Decimal)
        self.assertEqual(irrf, Decimal("0.00"))

    def test_calculate_irrf_progressive_brackets(self):
        # 10000 pró-labore on 2024-06-01:
        # INSS: min(10000, 7786.02) * 11% = 856.46
        # Base: 10000 - 856.46 = 9143.54
        # Bracket 0 (up to 2259.20): 2259.20 * 0% = 0.00
        # Bracket 1 (2259.20 to 2826.65): 567.45 * 7.5% = 42.55875
        # Bracket 2 (2826.65 to 3751.05): 924.40 * 15% = 138.66
        # Bracket 3 (3751.05 to 4664.68): 913.63 * 22.5% = 205.56675
        # Bracket 4 (above 4664.68): (9143.54 - 4664.68) * 27.5% = 4478.86 * 27.5% = 1231.6865
        # Total: 0 + 42.55875 + 138.66 + 205.56675 + 1231.6865 = 1618.472 -> 1618.47
        irrf = calculate_irrf(Decimal("10000.00"), date(2024, 6, 1))
        self.assertEqual(irrf, Decimal("1618.47"))

    def test_calculate_irrf_second_bracket(self):
        # 3000 pró-labore on 2024-06-01:
        # INSS: 3000 * 11% = 330.00
        # Base: 3000 - 330 = 2670.00
        # Bracket 0: 2259.20 * 0% = 0.00
        # Bracket 1: (2670.00 - 2259.20) * 7.5% = 410.80 * 7.5% = 30.81
        irrf = calculate_irrf(Decimal("3000.00"), date(2024, 6, 1))
        self.assertEqual(irrf, Decimal("30.81"))

    def test_calculate_irrf_zero_or_negative(self):
        self.assertEqual(
            calculate_irrf(Decimal("0.00"), date(2024, 6, 1)), Decimal("0.00")
        )

    def test_calculate_ideal_pro_labore_zero_revenue(self):
        pl = calculate_ideal_pro_labore(
            date(2024, 6, 1), estimated_current_revenue=Decimal("0.00")
        )
        self.assertIsInstance(pl, Decimal)
        self.assertEqual(pl, Decimal("0.00"))


class SignalAndModelIntegrityTests(TestCase):
    def setUp(self):
        self.client_obj = Client.objects.create(name="Foreign Client Inc")
        self.company = CompanySettings.objects.create(
            company_name="My Dev Corp",
            cnpj="12.345.678/0001-90",
            opening_date=date(2024, 1, 1),
            inscricao_municipal="123456",
            email="test@test.com",
            pfx_cert_pem="cert",
            pfx_key_pem="key",
            next_document_number=1,
            document_series="1",
        )

    def test_invoice_protect_on_client_delete(self):
        invoice = Invoice.objects.create(
            client=self.client_obj,
            invoice_number="INV-001",
            issue_date=date(2026, 1, 15),
            currency="CAD",
        )
        from django.db.models import ProtectedError

        with self.assertRaises(ProtectedError):
            self.client_obj.delete()

    def test_signal_does_not_overwrite_consolidated_pro_labore(self):
        target_month = date(2026, 5, 1)
        cons = MonthlyConsolidation.objects.create(
            month_year=target_month,
            status="CONSOLIDATED",
            actual_pro_labore_paid=Decimal("5000.00"),
        )

        # Save a NotaFiscal in this month
        NotaFiscal.objects.create(
            nf_number="NF-001",
            issue_date=date(2026, 5, 10),
            amount_brl=Decimal("15000.00"),
            description="Software Services",
        )

        cons.refresh_from_db()
        # Per bug fix: actual_pro_labore_paid must NOT be overwritten when status was CONSOLIDATED
        self.assertEqual(cons.actual_pro_labore_paid, Decimal("5000.00"))
        # But status is marked OUTDATED so accountant knows it needs reconsolidation
        self.assertEqual(cons.status, "OUTDATED")


class AuthenticationEnforcementTests(TestCase):
    def setUp(self):
        self.client_obj = Client.objects.create(name="Auth Test Client")
        self.invoice = Invoice.objects.create(
            client=self.client_obj,
            invoice_number="INV-AUTH-1",
            issue_date=date(2026, 1, 1),
            currency="CAD",
        )
        self.http_client = HttpClient()

    def test_anonymous_redirected_to_login(self):
        urls_to_test = [
            reverse("dashboard"),
            reverse("invoice_list"),
            reverse("invoice_create"),
            reverse("invoice_detail", args=[self.invoice.id]),
            reverse("tasks_view"),
        ]
        for url in urls_to_test:
            response = self.http_client.get(url)
            self.assertEqual(
                response.status_code, 302, f"URL {url} allowed unauthenticated access!"
            )
            self.assertIn("/accounts/login/", response.url)

    def test_authenticated_user_access(self):
        user = User.objects.create_user(username="testuser", password="password123")
        self.http_client.login(username="testuser", password="password123")
        response = self.http_client.get(reverse("invoice_list"))
        self.assertEqual(response.status_code, 302)


class ServicesExchangeRateTests(TestCase):
    @patch("core.services.requests.get")
    def test_fetch_exchange_rate(self, mock_get):
        class MockResponse:
            def __init__(self, content):
                self.content = content

            def raise_for_status(self):
                pass

        mock_content = b"12032024;48;A;CAD;4.0123;4.0124;4.0125;4.0126\n"
        mock_get.return_value = MockResponse(mock_content)

        target_date = date(2024, 3, 13)
        rate = fetch_exchange_rate(target_date, "CAD")
        self.assertEqual(rate, Decimal("4.0123"))


class NFSeProviderAbstractionTests(TestCase):
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
            [x509.NameAttribute(NameOID.COMMON_NAME, "test.com")]
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
            company_name="Test Company",
            cnpj="12.345.678/0001-90",
            inscricao_municipal="12345678",
            opening_date=date(2024, 1, 1),
            email="test@test.com",
            pfx_cert_pem=self.test_cert_pem,
            pfx_key_pem=self.test_key_pem,
            next_document_number=1,
            document_series="1",
            nfse_provider="PAULISTANA",
            address_line1="Av Paulista",
            address_number="1000",
            debug_mode=True,
        )
        self.client_obj = Client.objects.create(
            name="Canadian Tech Inc",
            address_neighborhood="Centre-Ville",
            address_country_code="CA",
            address_city="Toronto",
            address_postal_code="M5H 2N2",
            address_state_province="ON",
            email="accounting@canadiantech.ca",
        )
        self.invoice = Invoice.objects.create(
            client=self.client_obj,
            invoice_number="INV-2026-001",
            issue_date=date(2026, 9, 1),
            currency="CAD",
            exchange_rate_to_brl=Decimal("4.20"),
            bank_details="Test Beneficiary\n12345\n001\n0001",
        )
        InvoiceItem.objects.create(
            invoice=self.invoice,
            description="Software Development",
            quantity=Decimal("1.00"),
            unit_price_foreign=Decimal("3000.00"),
        )

    def test_provider_factory_resolution(self):
        from core.nfse.provider_factory import get_provider
        from core.nfse.paulistana.provider import PaulistanaProvider
        from core.nfse.nacional.provider import NacionalProvider

        self.company.nfse_provider = "PAULISTANA"
        self.company.save()

        class DummyInvoice:
            pass

        dummy = DummyInvoice()

        provider = get_provider(dummy)
        self.assertIsInstance(provider, PaulistanaProvider)

        self.company.nfse_provider = "NACIONAL"
        self.company.save()
        provider = get_provider(dummy)
        self.assertIsInstance(provider, NacionalProvider)

    def test_document_series_numeric_validation(self):
        from django.core.exceptions import ValidationError

        self.company.document_series = "ABC1"
        with self.assertRaises(ValidationError):
            self.company.full_clean()

        self.company.document_series = "00001"
        self.company.full_clean()  # Should succeed without error

    def test_client_bairro_validation(self):
        from django.core.exceptions import ValidationError

        client = Client(name="No Bairro Client")
        with self.assertRaises(ValidationError):
            client.clean()

    def test_nacional_dps_generation_and_signing(self):
        from core.nfse.nacional.provider import NacionalProvider

        nacional_provider = NacionalProvider()
        dps, signed_xml, id_dps = nacional_provider._build_and_sign_dps(
            self.invoice, self.company, 1, "1"
        )

        self.assertTrue(id_dps.startswith("DPS355030821234567800019000001"))
        self.assertEqual(len(id_dps), 45)
        self.assertIn("DPS", signed_xml)
        self.assertIn("Signature", signed_xml)
        self.assertIn("Canadian Tech Inc", signed_xml)
        self.assertIn("12600.00", signed_xml)  # 3000 CAD * 4.20
        self.assertIn("Centre-Ville", signed_xml)
        # Verify XML declaration header and DPS root element
        self.assertTrue(signed_xml.startswith('<?xml version="1.0" encoding="UTF-8"?>'))
        # Verify Signature has default namespace without ds: prefix
        self.assertIn(
            '<Signature xmlns="http://www.w3.org/2000/09/xmldsig#">', signed_xml
        )
        self.assertNotIn("ds:", signed_xml)
        # Verify no tag has colon namespace prefix
        self.assertEqual(
            re.findall(r"<(/?[a-zA-Z0-9_-]+:[a-zA-Z0-9_-]+)", signed_xml), []
        )
        # Verify cNaoNIF = 2 and no NIF tag
        self.assertIn("<cNaoNIF>2</cNaoNIF>", signed_xml)
        self.assertNotIn("<NIF>", signed_xml)
        # Verify IM is omitted to prevent E0120
        self.assertNotIn("<IM>", signed_xml)
        # Verify pTotTribSN or indTotTrib
        self.assertTrue(
            "<pTotTribSN>" in signed_xml or "<indTotTrib>0</indTotTrib>" in signed_xml
        )

    @patch("core.utils.http.requests.get")
    @patch("core.utils.http.requests.post")
    def test_nacional_emission_success(self, mock_post, mock_get):
        import gzip
        import base64
        from core.services import enviar_nfe_para_prefeitura

        # GET /dps/{id} returns 404 (not yet issued)
        class MockGetResp:
            status_code = 404

        mock_get.return_value = MockGetResp()

        fake_nfse_xml = "<xml><nNFSe>99999</nNFSe></xml>"
        fake_b64 = base64.b64encode(
            gzip.compress(fake_nfse_xml.encode("utf-8"))
        ).decode("utf-8")

        class MockPostResp:
            status_code = 201

            def json(self):
                return {
                    "tipoAmbiente": 2,
                    "chaveAcesso": "35503082000000000001910000100000000000999991234567",
                    "nfseXmlGZipB64": fake_b64,
                }

            @property
            def text(self):
                return "OK"

        mock_post.return_value = MockPostResp()

        self.company.nfse_provider = "NACIONAL"
        self.company.save()

        success = enviar_nfe_para_prefeitura(self.invoice)
        self.assertTrue(success)

        nf = NotaFiscal.objects.get(invoice=self.invoice)
        self.assertEqual(nf.nf_number, "99999")
        self.assertEqual(
            nf.chave_acesso_nacional,
            "35503082000000000001910000100000000000999991234567",
        )

    @patch("core.utils.http.requests.post")
    @patch("core.utils.http.requests.get")
    def test_nacional_idempotency_precheck(self, mock_get, mock_post):
        import gzip
        import base64
        from core.nfse.nacional.provider import NacionalProvider

        fake_nfse_xml = "<xml><nNFSe>88888</nNFSe></xml>"
        fake_b64 = base64.b64encode(
            gzip.compress(fake_nfse_xml.encode("utf-8"))
        ).decode("utf-8")

        def side_effect_get(url, *args, **kwargs):
            class MockResp:
                def __init__(self, sc, j):
                    self.status_code = sc
                    self._j = j

                def json(self):
                    return self._j

                @property
                def text(self):
                    return "OK"

            if "/dps/" in url:
                return MockResp(
                    200,
                    {
                        "chaveAcesso": "35503082000000000001910000100000000000888881234567"
                    },
                )
            elif "/nfse/" in url:
                return MockResp(200, {"nfseXmlGZipB64": fake_b64})
            return MockResp(404, {})

        mock_get.side_effect = side_effect_get

        provider = NacionalProvider()
        result = provider.emitir_nfse(self.invoice)
        self.assertTrue(result.sucesso)
        self.assertEqual(result.numero_nf, "88888")
        mock_post.assert_not_called()

    def test_dual_error_structure_parsing(self):
        from core.nfse.nacional.provider import NacionalProvider

        provider = NacionalProvider()

        class MockRespList:
            status_code = 400

            def json(self):
                return {
                    "erros": [
                        {
                            "codigo": "E01",
                            "descricao": "Erro em lote",
                            "complemento": "detalhe",
                        }
                    ]
                }

            @property
            def text(self):
                return ""

        class MockRespSingle:
            status_code = 400

            def json(self):
                return {
                    "erro": {
                        "codigo": "E02",
                        "descricao": "Erro individual",
                        "complemento": "",
                    }
                }

            @property
            def text(self):
                return ""

        errs_list = provider._parse_error_response(MockRespList())
        self.assertIn("E01 - Erro em lote (detalhe)", errs_list)

        errs_single = provider._parse_error_response(MockRespSingle())
        self.assertIn("E02 - Erro individual", errs_single)

    @patch("core.nfse.paulistana.provider.PaulistanaProvider.baixar_pdf")
    def test_fetch_nfse_pdf_task(self, mock_baixar):
        from core.tasks import fetch_nfse_pdf_task

        mock_baixar.return_value = b"%PDF-1.4 Fake PDF Content"

        nf = NotaFiscal.objects.create(
            invoice=self.invoice,
            nf_number="12345",
            issue_date=self.invoice.issue_date,
            amount_brl=Decimal("1000.00"),
            is_export=True,
            description="Service",
            verification_code="TEST-CODE",
        )

        res = fetch_nfse_pdf_task(self.invoice.id)
        self.assertIn("PDF successfully downloaded", res)
        nf.refresh_from_db()
        self.assertTrue(bool(nf.danfse_pdf))

    def test_download_nfse_pdf_when_already_saved_locally(self):
        from django.core.files.base import ContentFile

        user = User.objects.create_user(
            username="test_pdf_user", password="password123"
        )
        self.client.login(username="test_pdf_user", password="password123")

        nf = NotaFiscal.objects.create(
            invoice=self.invoice,
            nf_number="99881",
            issue_date=self.invoice.issue_date,
            amount_brl=Decimal("12600.00"),
            is_export=True,
            description="Service",
            verification_code="LOCAL-CODE",
        )
        nf.danfse_pdf.save("NFSe_99881.pdf", ContentFile(b"%PDF-1.4 Local Content"))

        response = self.client.get(f"/invoices/{self.invoice.id}/nfse-pdf/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn(b"%PDF-1.4 Local Content", b"".join(response.streaming_content))

    @patch("core.nfse.paulistana.provider.PaulistanaProvider.baixar_pdf")
    def test_download_nfse_pdf_fetches_from_provider_if_missing(self, mock_baixar):
        user = User.objects.create_user(
            username="test_fetch_user", password="password123"
        )
        self.client.login(username="test_fetch_user", password="password123")
        mock_baixar.return_value = b"%PDF-1.4 Fetched From Provider"

        nf = NotaFiscal.objects.create(
            invoice=self.invoice,
            nf_number="99882",
            issue_date=self.invoice.issue_date,
            amount_brl=Decimal("12600.00"),
            is_export=True,
            description="Service",
            verification_code="FETCH-CODE",
        )

        response = self.client.get(f"/invoices/{self.invoice.id}/nfse-pdf/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn(
            b"%PDF-1.4 Fetched From Provider", b"".join(response.streaming_content)
        )

        nf.refresh_from_db()
        self.assertTrue(bool(nf.danfse_pdf))

    @patch("core.nfse.paulistana.provider.PaulistanaProvider.baixar_pdf")
    def test_download_nfse_pdf_unavailable_redirects(self, mock_baixar):
        user = User.objects.create_user(
            username="test_unavail_user", password="password123"
        )
        self.client.login(username="test_unavail_user", password="password123")
        mock_baixar.return_value = None

        NotaFiscal.objects.create(
            invoice=self.invoice,
            nf_number="99883",
            issue_date=self.invoice.issue_date,
            amount_brl=Decimal("12600.00"),
            is_export=True,
            description="Service",
            verification_code="NONE-CODE",
        )

        response = self.client.get(
            f"/invoices/{self.invoice.id}/nfse-pdf/", follow=True
        )
        self.assertRedirects(response, f"/invoices/{self.invoice.id}/")
        self.assertContains(response, "O PDF da NFS-e ainda n")

    def test_download_nfse_pdf_no_nota_fiscal_redirects(self):
        user = User.objects.create_user(
            username="test_no_nf_user", password="password123"
        )
        self.client.login(username="test_no_nf_user", password="password123")

        response = self.client.get(
            f"/invoices/{self.invoice.id}/nfse-pdf/", follow=True
        )
        self.assertRedirects(response, f"/invoices/{self.invoice.id}/")
        self.assertContains(response, "Nenhuma NFS-e associada a esta invoice.")

    def test_paulistana_provider_baixar_pdf_unmocked_debug_mode(self):
        from core.nfse.paulistana.provider import PaulistanaProvider

        provider = PaulistanaProvider()

        NotaFiscal.objects.create(
            invoice=self.invoice,
            nf_number="99889",
            issue_date=self.invoice.issue_date,
            amount_brl=Decimal("12600.00"),
            is_export=True,
            description="Service",
            verification_code="DEBUG-FAKE-CODE",
        )
        pdf_bytes = provider.baixar_pdf(self.invoice)
        self.assertIsNotNone(pdf_bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    @patch("core.nfse.provider_factory.get_provider")
    def test_consultar_nfe_na_prefeitura_via_provider(self, mock_get_provider):
        from unittest.mock import MagicMock
        from core.services import consultar_nfe_na_prefeitura
        from core.nfse.base import EmitResult

        mock_provider = MagicMock()
        mock_provider.consultar_nfse.return_value = EmitResult(
            sucesso=True,
            numero_nf="77777",
            codigo_verificacao="VERIF-777",
            chave_acesso_nacional="35503082000000000001910000100000000000777771234567",
            xml_retorno="<xml>retorno</xml>",
        )
        mock_provider.baixar_pdf.return_value = b"%PDF-1.4 Fake Consulted PDF"
        mock_get_provider.return_value = mock_provider

        self.invoice.document_number = 100
        self.invoice.save()

        found = consultar_nfe_na_prefeitura(self.invoice)
        self.assertTrue(found)

        self.invoice.refresh_from_db()
        self.assertIsNotNone(self.invoice.nota_fiscal)
        self.assertEqual(self.invoice.nota_fiscal.nf_number, "77777")
        self.assertEqual(
            self.invoice.nota_fiscal.chave_acesso_nacional,
            "35503082000000000001910000100000000000777771234567",
        )
        self.assertTrue(bool(self.invoice.nota_fiscal.danfse_pdf))

    def test_provider_factory_resolution_by_invoice_metadata(self):
        from core.nfse.provider_factory import get_provider
        from core.nfse.paulistana.provider import PaulistanaProvider
        from core.nfse.nacional.provider import NacionalProvider

        self.company.nfse_provider = "NACIONAL"
        self.company.save()

        # Invoice with verification_code (Paulistana) should resolve to PaulistanaProvider
        NotaFiscal.objects.create(
            invoice=self.invoice,
            nf_number="1111",
            issue_date=self.invoice.issue_date,
            amount_brl=Decimal("1000.00"),
            is_export=True,
            description="Paulistana Invoice",
            verification_code="ABC-123",
        )
        self.invoice.refresh_from_db()
        provider = get_provider(self.invoice)
        self.assertIsInstance(provider, PaulistanaProvider)

        # Invoice with chave_acesso_nacional should resolve to NacionalProvider
        self.company.nfse_provider = "PAULISTANA"
        self.company.save()

        inv2 = Invoice.objects.create(
            client=self.client_obj,
            invoice_number="INV-NACIONAL-TEST",
            issue_date=date(2026, 9, 2),
            currency="CAD",
        )
        NotaFiscal.objects.create(
            invoice=inv2,
            nf_number="2222",
            issue_date=inv2.issue_date,
            amount_brl=Decimal("2000.00"),
            is_export=True,
            description="Nacional Invoice",
            chave_acesso_nacional="35503082000000000001910000100000000000222221234567",
        )
        inv2.refresh_from_db()
        provider2 = get_provider(inv2)
        self.assertIsInstance(provider2, NacionalProvider)

    @patch("core.nfse.paulistana.provider.PaulistanaProvider.baixar_pdf")
    def test_download_nfse_pdf_old_paulistana_when_company_is_nacional(
        self, mock_paulistana_baixar
    ):
        # Company setting is NACIONAL, but invoice has old Paulistana NFS-e
        self.company.nfse_provider = "NACIONAL"
        self.company.save()

        user = User.objects.create_user(
            username="test_cross_user", password="password123"
        )
        self.client.login(username="test_cross_user", password="password123")
        mock_paulistana_baixar.return_value = b"%PDF-1.4 Old Paulistana PDF"

        NotaFiscal.objects.create(
            invoice=self.invoice,
            nf_number="88801",
            issue_date=self.invoice.issue_date,
            amount_brl=Decimal("12600.00"),
            is_export=True,
            description="Old Service",
            verification_code="PAULISTANA-CODE",
        )

        response = self.client.get(f"/invoices/{self.invoice.id}/nfse-pdf/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn(
            b"%PDF-1.4 Old Paulistana PDF", b"".join(response.streaming_content)
        )
        mock_paulistana_baixar.assert_called_once_with(self.invoice)

    def test_paulistana_parser_handles_chave_nota_nacional(self):
        from core.nfse.paulistana.client import NFeClient
        from core.nfse.paulistana.schemas_v1.retorno_envio_lote_rps_v01 import (
            RetornoEnvioLoteRps as RetornoEnvioLoteRpsV1,
        )

        sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
<RetornoEnvioLoteRPS xmlns="http://www.prefeitura.sp.gov.br/nfe">
    <Cabecalho Versao="1" xmlns="">
        <Sucesso>true</Sucesso>
        <InformacoesLote>
            <NumeroLote>1</NumeroLote>
            <InscricaoPrestador>00000000</InscricaoPrestador>
            <CPFCNPJRemetente><CNPJ>00000000000191</CNPJ></CPFCNPJRemetente>
            <DataEnvioLote>2026-09-05T10:04:20</DataEnvioLote>
            <QtdNotasProcessadas>1</QtdNotasProcessadas>
            <TempoProcessamento>0</TempoProcessamento>
            <ValorTotalServicos>100.00</ValorTotalServicos>
        </InformacoesLote>
    </Cabecalho>
    <ChaveNFeRPS xmlns="">
        <ChaveRPS>
            <InscricaoPrestador>00000000</InscricaoPrestador>
            <SerieRPS>12</SerieRPS>
            <NumeroRPS>1</NumeroRPS>
        </ChaveRPS>
        <ChaveNFe>
            <InscricaoPrestador>00000000</InscricaoPrestador>
            <NumeroNFe>54</NumeroNFe>
            <CodigoVerificacao>AAAAAAAA</CodigoVerificacao>
            <ChaveNotaNacional>35503081200000000000191000000000005426097092595485</ChaveNotaNacional>
            <SomeFutureUnknownElement>value</SomeFutureUnknownElement>
        </ChaveNFe>
    </ChaveNFeRPS>
</RetornoEnvioLoteRPS>"""

        with patch(
            "core.nfse.paulistana.client.carregar_certificado_pfx",
            return_value=(b"key", b"cert"),
        ):
            client = NFeClient(b"cert_pem", b"key_pem", "00000000000191", "00000000")
            retorno = client.parser.from_string(sample_xml, RetornoEnvioLoteRpsV1)
            self.assertTrue(retorno.cabecalho.sucesso)
            self.assertEqual(len(retorno.chave_nfe_rps), 1)
            chave = retorno.chave_nfe_rps[0]
            self.assertEqual(chave.chave_nfe.numero_nfe, "54")
            self.assertEqual(chave.chave_nfe.codigo_verificacao, "AAAAAAAA")
            self.assertEqual(
                chave.chave_nfe.chave_nota_nacional,
                "35503081200000000000191000000000005426097092595485",
            )

    @patch("core.nfse.paulistana.client.NFeClient.enviar_lote_rps")
    def test_paulistana_emitir_nfse_extracts_list_and_national_key(self, mock_enviar):
        from core.nfse.paulistana.provider import PaulistanaProvider
        from core.nfse.paulistana.schemas_v1.retorno_envio_lote_rps_v01 import (
            RetornoEnvioLoteRps as RetornoEnvioLoteRpsV1,
        )
        from core.nfse.paulistana.schemas_v1.tipos_nfe_v01 import (
            TpChaveNfeRps,
            TpChaveNfe,
            TpChaveRps,
        )

        self.company.nfse_provider = "PAULISTANA"
        self.company.debug_mode = False
        self.company.save()

        mock_retorno = RetornoEnvioLoteRpsV1(
            cabecalho=RetornoEnvioLoteRpsV1.Cabecalho(sucesso=True),
            chave_nfe_rps=[
                TpChaveNfeRps(
                    chave_rps=TpChaveRps(
                        inscricao_prestador="00000000", serie_rps="12", numero_rps="1"
                    ),
                    chave_nfe=TpChaveNfe(
                        inscricao_prestador="00000000",
                        numero_nfe="54",
                        codigo_verificacao="AAAAAAAA",
                        chave_nota_nacional="35503081200000000000191000000000005426097092595485",
                    ),
                )
            ],
        )
        mock_enviar.return_value = (mock_retorno, "<signed_xml/>", "<retorno_xml/>")

        self.invoice.document_number = 1
        self.invoice.document_series = "12"
        self.invoice.save()

        with patch(
            "core.nfse.paulistana.client.carregar_certificado_pfx",
            return_value=(b"key", b"cert"),
        ):
            with patch(
                "core.nfse.paulistana.provider.assinar_rps_v1", return_value="fake-sig"
            ):
                provider = PaulistanaProvider()
                result = provider.emitir_nfse(self.invoice)

                self.assertTrue(result.sucesso)
                self.assertEqual(result.numero_nf, "54")
                self.assertEqual(result.codigo_verificacao, "AAAAAAAA")
                self.assertEqual(
                    result.chave_acesso_nacional,
                    "35503081200000000000191000000000005426097092595485",
                )

    @patch("core.nfse.paulistana.client.NFeClient.consultar_nfe_emitidas")
    def test_paulistana_consultar_nfse_date_range(self, mock_consultar):
        from core.nfse.paulistana.provider import PaulistanaProvider
        from core.nfse.paulistana.schemas.retorno_consulta_v02 import RetornoConsulta
        from core.nfse.paulistana.schemas.tipos_nfe_v02 import (
            TpChaveNfeRps,
            TpChaveNfe,
            TpChaveRps,
        )
        from unittest.mock import MagicMock

        self.company.nfse_provider = "PAULISTANA"
        self.company.save()

        self.invoice.document_number = 1
        self.invoice.issue_date = date(2026, 9, 5)
        self.invoice.save()

        mock_nota = MagicMock()
        mock_nota.chave_rps.numero_rps = "1"
        mock_nota.chave_nfe.numero_nfe = "54"
        mock_nota.chave_nfe.codigo_verificacao = "AAAAAAAA"
        mock_nota.chave_nfe.chave_nota_nacional = (
            "35503081200000000000191000000000005426097092595485"
        )
        mock_consultar.return_value = [mock_nota]

        with patch(
            "core.nfse.paulistana.client.carregar_certificado_pfx",
            return_value=(b"key", b"cert"),
        ):
            with patch("core.nfse.paulistana.provider.to_xml", return_value="<xml/>"):
                provider = PaulistanaProvider()
                result = provider.consultar_nfse(self.invoice)

                self.assertIsNotNone(result)
                self.assertTrue(result.sucesso)
                self.assertEqual(result.numero_nf, "54")
                self.assertEqual(result.codigo_verificacao, "AAAAAAAA")
                self.assertEqual(
                    result.chave_acesso_nacional,
                    "35503081200000000000191000000000005426097092595485",
                )

                mock_consultar.assert_called_once()
                call_kwargs = mock_consultar.call_args[1]
                dt_inicio = call_kwargs["dt_inicio"]
                dt_fim = call_kwargs["dt_fim"]
                self.assertLessEqual((dt_fim - dt_inicio).days, 30)

    @patch("core.utils.http.requests.post")
    def test_paulistana_soap_fault_logged_properly(self, mock_post):
        from core.services import enviar_nfe_para_prefeitura
        from core.models import NfseLog

        soap_fault_xml = """<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <soap:Fault>
                    <faultcode>soap:Server</faultcode>
                    <faultstring>Assinatura digital inválida: CNPJ do certificado não confere com prestador</faultstring>
                </soap:Fault>
            </soap:Body>
        </soap:Envelope>"""

        class MockResp:
            status_code = 500
            content = soap_fault_xml.encode("utf-8")
            text = soap_fault_xml

        mock_post.return_value = MockResp()
        self.company.debug_mode = False
        self.company.nfse_provider = "PAULISTANA"
        self.company.save()

        with patch(
            "core.nfse.paulistana.client.carregar_certificado_pfx",
            return_value=(b"key", b"cert"),
        ):
            with patch(
                "core.nfse.paulistana.provider.assinar_rps_v1",
                return_value="FAKE_SIGNATURE",
            ):
                with patch(
                    "core.nfse.paulistana.client.assinar_xml",
                    side_effect=lambda root, *a, **kw: root,
                ):
                    success = enviar_nfe_para_prefeitura(self.invoice)
                    self.assertFalse(success)

        log = (
            NfseLog.objects.filter(invoice=self.invoice).order_by("-created_at").first()
        )
        self.assertIsNotNone(log)
        self.assertIsNotNone(log.payload_enviado)
        self.assertIn("Assinatura digital inválida", log.erro_mensagem)
        self.assertNotIn("500 Server Error", log.erro_mensagem)
        self.assertEqual(log.payload_retorno, soap_fault_xml)

    @patch("core.nfse.paulistana.client.NFeClient._enviar_soap")
    def test_paulistana_xml_without_xmlns_empty_parsed_properly(self, mock_soap):
        from core.services import enviar_nfe_para_prefeitura
        from core.models import NfseLog

        # XML with default xmlns on root and no xmlns="" on children (which caused TypeError previously)
        retorno_xml = """<?xml version="1.0" encoding="utf-8"?>
        <RetornoEnvioLoteRPS xmlns="http://www.prefeitura.sp.gov.br/nfe">
            <Cabecalho Versao="1">
                <Sucesso>false</Sucesso>
            </Cabecalho>
            <Erro>
                <Codigo>1205</Codigo>
                <Descricao>Tomador com documento inválido na prefeitura</Descricao>
            </Erro>
        </RetornoEnvioLoteRPS>"""

        mock_soap.return_value = retorno_xml
        self.company.debug_mode = False
        self.company.nfse_provider = "PAULISTANA"
        self.company.save()

        with patch(
            "core.nfse.paulistana.client.carregar_certificado_pfx",
            return_value=(b"key", b"cert"),
        ):
            with patch(
                "core.nfse.paulistana.provider.assinar_rps_v1",
                return_value="FAKE_SIGNATURE",
            ):
                with patch(
                    "core.nfse.paulistana.client.assinar_xml",
                    side_effect=lambda root, *a, **kw: root,
                ):
                    success = enviar_nfe_para_prefeitura(self.invoice)
                    self.assertFalse(success)

        log = (
            NfseLog.objects.filter(invoice=self.invoice).order_by("-created_at").first()
        )
        self.assertIsNotNone(log)
        self.assertIn(
            "1205 - Tomador com documento inválido na prefeitura", log.erro_mensagem
        )
        self.assertNotIn("TypeError", log.erro_mensagem)
        self.assertEqual(log.payload_retorno, retorno_xml)

    @patch("core.utils.http.requests.get")
    @patch("core.utils.http.requests.post")
    def test_nacional_aspnet_errors_dict_logged_properly(self, mock_post, mock_get):
        from core.services import enviar_nfe_para_prefeitura
        from core.models import NfseLog

        class MockGetResp:
            status_code = 404

        mock_get.return_value = MockGetResp()

        aspnet_error_json = {
            "title": "One or more validation errors occurred.",
            "status": 400,
            "errors": {"dpsXmlGZipB64": ["O campo DPS compactado é obrigatório."]},
        }

        class MockPostResp:
            status_code = 400

            def json(self):
                return aspnet_error_json

            @property
            def text(self):
                return str(aspnet_error_json)

        mock_post.return_value = MockPostResp()
        self.company.nfse_provider = "NACIONAL"
        self.company.save()

        success = enviar_nfe_para_prefeitura(self.invoice)
        self.assertFalse(success)

        log = (
            NfseLog.objects.filter(invoice=self.invoice).order_by("-created_at").first()
        )
        self.assertIsNotNone(log)
        self.assertIn(
            "dpsXmlGZipB64: O campo DPS compactado é obrigatório.", log.erro_mensagem
        )
        self.assertIn("One or more validation errors occurred.", log.erro_mensagem)
        self.assertEqual(log.payload_retorno, str(aspnet_error_json))

    def test_consultar_nfe_na_prefeitura_propagates_exception(self):
        from core.services import consultar_nfe_na_prefeitura

        self.invoice.document_number = 100
        self.invoice.save()

        with patch("core.nfse.provider_factory.get_provider") as mock_gp:
            mock_provider = MagicMock()
            mock_provider.consultar_nfse.side_effect = Exception(
                "Prefeitura SOAP timeout"
            )
            mock_gp.return_value = mock_provider

            with self.assertRaises(Exception) as ctx:
                consultar_nfe_na_prefeitura(self.invoice)
            self.assertIn("Prefeitura SOAP timeout", str(ctx.exception))

    def test_issue_nfse_task_aborts_on_consultation_failure(self):
        from core.tasks import issue_nfse_task
        from core.models import NfseLog

        with patch(
            "core.tasks.nfse_tasks.consultar_nfe_na_prefeitura",
            side_effect=Exception("Prefeitura fora do ar"),
        ):
            with self.assertRaises(Exception) as ctx:
                issue_nfse_task(self.invoice.id, "4.20")

            self.assertIn("Falha na consulta prévia da NFS-e", str(ctx.exception))
            self.assertIn(
                "Emissão abortada para evitar duplicidade", str(ctx.exception)
            )

        log = (
            NfseLog.objects.filter(invoice=self.invoice).order_by("-created_at").first()
        )
        self.assertIsNotNone(log)
        self.assertIn("Prefeitura fora do ar", log.erro_mensagem)

    def test_issue_nfse_task_raises_real_provider_error_on_emission_failure(self):
        from core.tasks import issue_nfse_task
        from core.models import NfseLog

        def fake_emission(inv):
            NfseLog.objects.create(
                invoice=inv,
                origem="System / Celery",
                erro_mensagem="1205 - Tomador com CNPJ inválido",
            )
            return False

        with patch(
            "core.tasks.nfse_tasks.consultar_nfe_na_prefeitura", return_value=False
        ):
            with patch(
                "core.tasks.nfse_tasks.enviar_nfe_para_prefeitura",
                side_effect=fake_emission,
            ):
                with self.assertRaises(Exception) as ctx:
                    issue_nfse_task(self.invoice.id, "4.20")

                self.assertIn(
                    "Falha na emissão da NFS-e: 1205 - Tomador com CNPJ inválido",
                    str(ctx.exception),
                )

    def test_prepare_nf_data_uses_export_rates_and_ideal_pro_labore(self):
        from core.services import _prepare_nf_data

        target_month = date(2025, 6, 1)

        # Fictional export client and invoice
        export_client = Client.objects.create(
            name="Foreign Test Client LLC",
            address_country_code="US",
            address_neighborhood="Downtown",
            address_city="New York",
        )
        invoice = Invoice.objects.create(
            client=export_client,
            invoice_number="INV-EXP-TEST-001",
            issue_date=target_month,
            exchange_rate_to_brl=Decimal("5.0000"),
            currency="USD",
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            description="Consulting services",
            quantity=Decimal("1.00"),
            unit_price_foreign=Decimal("2000.00"),
        )

        # Create past 12 months with synthetic RBT12 = R$ 120,000 (Annex III Bracket 1)
        # All months have 0 actual pro-labore paid, which tests that ideal pro-labore is used
        for i in range(1, 13):
            m = target_month - relativedelta(months=i)
            MonthlyConsolidation.objects.update_or_create(
                month_year=m,
                defaults={
                    "total_revenue_export": Decimal("10000.00"),
                    "total_revenue_internal": Decimal("0.00"),
                    "actual_pro_labore_paid": Decimal("0.00"),
                    "status": "CONSOLIDATED",
                },
            )

        amount_brl, desc, eff_rate = _prepare_nf_data(invoice)
        self.assertEqual(amount_brl, Decimal("10000.00"))
        # Bracket 1 Annex III export rate (3.05%) vs domestic rate (6.00%) or Annex V export (10.67%)
        self.assertEqual(eff_rate, Decimal("3.05"))
        self.assertIn("3,05%", desc)

    def test_prepare_nf_data_uses_internal_rates_for_domestic_client(self):
        from core.services import _prepare_nf_data

        target_month = date(2025, 6, 1)

        # Fictional domestic client and invoice
        domestic_client = Client.objects.create(
            name="Domestic Test Client Ltda",
            address_country_code="BR",
            address_neighborhood="Centro",
            address_city="São Paulo",
        )
        invoice = Invoice.objects.create(
            client=domestic_client,
            invoice_number="INV-DOM-TEST-001",
            issue_date=target_month,
            exchange_rate_to_brl=Decimal("1.0000"),
            currency="BRL",
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            description="Domestic consulting services",
            quantity=Decimal("1.00"),
            unit_price_foreign=Decimal("10000.00"),
        )

        for i in range(1, 13):
            m = target_month - relativedelta(months=i)
            MonthlyConsolidation.objects.update_or_create(
                month_year=m,
                defaults={
                    "total_revenue_export": Decimal("10000.00"),
                    "total_revenue_internal": Decimal("0.00"),
                    "actual_pro_labore_paid": Decimal("0.00"),
                    "status": "CONSOLIDATED",
                },
            )

        amount_brl, desc, eff_rate = _prepare_nf_data(invoice)
        self.assertEqual(amount_brl, Decimal("10000.00"))
        # Bracket 1 Annex III internal rate is 6.00%
        self.assertEqual(eff_rate, Decimal("6.00"))
        self.assertIn("6,00%", desc)

    def test_calculate_rbt12_and_fator_r_use_ideal_pro_labore_flag(self):
        target_month = date(2025, 6, 1)
        for i in range(1, 13):
            m = target_month - relativedelta(months=i)
            MonthlyConsolidation.objects.update_or_create(
                month_year=m,
                defaults={
                    "total_revenue_export": Decimal("10000.00"),
                    "total_revenue_internal": Decimal("0.00"),
                    "actual_pro_labore_paid": Decimal("0.00"),
                    "status": "CONSOLIDATED",
                },
            )

        # Without flag: payroll is 0, Fator R is 0%
        rbt12, fator_r_normal, pl_norm, _ = calculate_rbt12_and_fator_r(
            target_month, use_ideal_pro_labore=False
        )
        self.assertEqual(fator_r_normal, Decimal("0.00"))

        # With flag: Fator R is at least 28.00%
        rbt12, fator_r_ideal, pl_ideal, _ = calculate_rbt12_and_fator_r(
            target_month, use_ideal_pro_labore=True
        )
        self.assertGreaterEqual(fator_r_ideal, Decimal("28.00"))
        self.assertGreater(pl_ideal, Decimal("0.00"))


class InvoiceBankDetailsTests(TestCase):
    def setUp(self):
        from django.core.cache import cache

        cache.clear()
        self.company = CompanySettings.objects.create(
            company_name="Test Company",
            cnpj="12.345.678/0001-90",
            inscricao_municipal="12345678",
            opening_date=date(2024, 1, 1),
            email="test@test.com",
            next_document_number=1,
            document_series="1",
            nfse_provider="PAULISTANA",
            address_line1="Av Paulista",
            address_number="1000",
            debug_mode=True,
        )
        self.client_obj = Client.objects.create(
            name="Canadian Tech Inc",
            address_neighborhood="Centre-Ville",
            address_country_code="CA",
            address_city="Toronto",
            address_postal_code="M5H 2N2",
            address_state_province="ON",
            email="accounting@canadiantech.ca",
        )
        self.user = User.objects.create_user(
            username="bank_tester", password="password123"
        )
        self.client.login(username="bank_tester", password="password123")

    def test_invoice_bank_details_markdown_rendering(self):
        markdown_text = (
            "**Bank Name:** Royal Bank\n\n"
            "- **Account:** 123456\n"
            "- **Transit:** 001\n"
            "- **SWIFT:** ROYCCAT2"
        )
        invoice = Invoice.objects.create(
            client=self.client_obj,
            invoice_number="INV-2026-B1",
            issue_date=date(2026, 9, 1),
            currency="CAD",
            bank_details=markdown_text,
        )
        html = invoice.bank_details_html
        self.assertIn("<strong>Bank Name:</strong> Royal Bank", html)
        self.assertIn("<ul>", html)
        self.assertIn("<li><strong>Account:</strong> 123456</li>", html)
        self.assertIn("<li><strong>SWIFT:</strong> ROYCCAT2</li>", html)

    def test_invoice_bank_details_empty_linebreaks_preserved(self):
        markdown_text = "Line 1\n\n" "Line 2\n\n\n" "Line 3"
        invoice = Invoice.objects.create(
            client=self.client_obj,
            invoice_number="INV-2026-LINES",
            issue_date=date(2026, 9, 1),
            currency="CAD",
            bank_details=markdown_text,
        )
        html = invoice.bank_details_html
        self.assertIn("<p>Line 1</p>", html)
        self.assertIn("<p>Line 2</p>", html)
        self.assertIn("<p>&nbsp;</p>", html)
        self.assertIn("<p>Line 3</p>", html)

    def test_invoice_template_bank_details_and_htmx_endpoint(self):
        template = InvoiceTemplate.objects.create(
            name="Canadian Client Template",
            currency="CAD",
            bank_details="**Bank:** RBC\nTransit: 123",
        )
        InvoiceTemplateItem.objects.create(
            template=template,
            description="Consulting Service",
            quantity=Decimal("1.00"),
            unit_price_foreign=Decimal("1000.00"),
        )
        self.assertIn("<strong>Bank:</strong> RBC", template.bank_details_html)

        response = self.client.get(f"/htmx/template-details/{template.id}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["currency"], "CAD")
        self.assertEqual(data["bank_details"], "**Bank:** RBC\nTransit: 123")
        self.assertEqual(len(data["items"]), 1)

    def test_clone_invoice_preserves_bank_details(self):
        original = Invoice.objects.create(
            client=self.client_obj,
            invoice_number="INV-ORIG-01",
            issue_date=date(2026, 9, 1),
            currency="CAD",
            bank_details="**Beneficiary:** My Company Ltd\nAccount: 778899",
        )
        InvoiceItem.objects.create(
            invoice=original,
            description="Dev Service",
            quantity=Decimal("1.00"),
            unit_price_foreign=Decimal("500.00"),
        )
        response = self.client.post(f"/invoices/{original.id}/clone/")
        self.assertEqual(response.status_code, 302)

        cloned = (
            Invoice.objects.filter(client=self.client_obj)
            .exclude(id=original.id)
            .first()
        )
        self.assertIsNotNone(cloned)
        self.assertEqual(cloned.bank_details, original.bank_details)

    def test_htmx_update_bank_details_on_draft_and_finalized(self):
        invoice = Invoice.objects.create(
            client=self.client_obj,
            invoice_number="INV-DRAFT-01",
            issue_date=date(2026, 9, 1),
            currency="CAD",
            bank_details="Initial Details",
            status="DRAFT",
        )
        # Update draft
        response = self.client.post(
            f"/invoices/{invoice.id}/update-bank-details/",
            {"bank_details": "**Updated:** Bank Info"},
        )
        self.assertEqual(response.status_code, 200)
        invoice.refresh_from_db()
        self.assertEqual(invoice.bank_details, "**Updated:** Bank Info")
        self.assertIn("<strong>Updated:</strong> Bank Info", response.content.decode())

        # Finalized invoice cannot update bank details
        invoice.status = "FINALIZED"
        invoice.save()
        bad_response = self.client.post(
            f"/invoices/{invoice.id}/update-bank-details/",
            {"bank_details": "New Info Attempt"},
        )
        self.assertEqual(bad_response.status_code, 400)
        invoice.refresh_from_db()
        self.assertEqual(invoice.bank_details, "**Updated:** Bank Info")

    def test_generate_pdf_with_markdown_bank_details(self):
        from core.pdf_service import generate_pdf_bytes

        invoice = Invoice.objects.create(
            client=self.client_obj,
            invoice_number="INV-PDF-01",
            issue_date=date(2026, 9, 1),
            currency="USD",
            bank_details="**Bank of America**\n- Routing: 111000025\n- Account: 987654321",
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            description="Cloud Architecture Consulting",
            quantity=Decimal("10.00"),
            unit_price_foreign=Decimal("150.00"),
        )
        pdf_bytes = generate_pdf_bytes(invoice, self.company)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_generate_pdf_without_bank_details(self):
        from core.pdf_service import generate_pdf_bytes

        invoice = Invoice.objects.create(
            client=self.client_obj,
            invoice_number="INV-PDF-EMPTY",
            issue_date=date(2026, 9, 1),
            currency="USD",
            bank_details="",
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            description="Design",
            quantity=Decimal("1.00"),
            unit_price_foreign=Decimal("100.00"),
        )
        pdf_bytes = generate_pdf_bytes(invoice, self.company)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_company_settings_has_no_bank_details_raw(self):
        self.assertFalse(hasattr(self.company, "bank_details_raw"))


class NfseCancelRestrictionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("admin", "admin@test.com", "pass")
        self.client_http = HttpClient()
        self.client_http.force_login(self.user)
        self.company = CompanySettings.objects.create(
            company_name="Test Company",
            cnpj="00.000.000/0001-00",
            opening_date=date(2024, 1, 1),
            inscricao_municipal="123456",
            email="test@test.com",
        )
        self.client_obj = Client.objects.create(
            name="Client A",
            email="client@example.com",
        )

    def test_nfse_authorized_less_than_24h_can_be_canceled(self):
        from django.utils import timezone

        nf = NotaFiscal.objects.create(
            nf_number="1001",
            issue_date=timezone.now().date(),
            amount_brl=Decimal("500.00"),
            data_hora_autorizacao=timezone.now() - timedelta(hours=2),
        )
        self.assertTrue(nf.can_be_canceled)

        response = self.client_http.get(reverse("nfse_detail", kwargs={"pk": nf.id}))
        self.assertContains(response, "Cancelar NFS-e")

    def test_nfse_authorized_more_than_24h_cannot_be_canceled(self):
        from django.utils import timezone

        nf = NotaFiscal.objects.create(
            nf_number="1002",
            issue_date=timezone.now().date(),
            amount_brl=Decimal("500.00"),
            data_hora_autorizacao=timezone.now() - timedelta(hours=25),
        )
        self.assertFalse(nf.can_be_canceled)

        # UI must not display cancel button
        response = self.client_http.get(reverse("nfse_detail", kwargs={"pk": nf.id}))
        self.assertNotContains(response, "Cancelar NFS-e")

        # POST to cancel must be rejected
        post_response = self.client_http.post(
            reverse("nfse_cancel", kwargs={"pk": nf.id})
        )
        self.assertRedirects(
            post_response, reverse("nfse_detail", kwargs={"pk": nf.id})
        )
        nf.refresh_from_db()
        self.assertFalse(nf.is_canceled)

    def test_invoice_with_old_nfse_cannot_be_canceled(self):
        from django.utils import timezone

        invoice = Invoice.objects.create(
            client=self.client_obj,
            invoice_number="INV-24H",
            issue_date=timezone.now().date(),
            currency="USD",
            status="FINALIZED",
        )
        NotaFiscal.objects.create(
            invoice=invoice,
            nf_number="1003",
            issue_date=timezone.now().date(),
            amount_brl=Decimal("500.00"),
            data_hora_autorizacao=timezone.now() - timedelta(hours=26),
        )
        self.assertFalse(invoice.can_be_canceled)

        # UI must not display cancel button
        response = self.client_http.get(
            reverse("invoice_detail", kwargs={"pk": invoice.id})
        )
        self.assertNotContains(response, "Cancelar Invoice")

        # POST to cancel must be rejected
        post_response = self.client_http.post(
            reverse("cancel_invoice", kwargs={"pk": invoice.id})
        )
        self.assertRedirects(
            post_response, reverse("invoice_detail", kwargs={"pk": invoice.id})
        )
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "FINALIZED")

    @patch("core.nfse.paulistana.client.NFeClient._enviar_soap")
    @patch("core.nfse.paulistana.client.assinar_xml")
    def test_paulistana_client_consultar_nfe(self, mock_sign, mock_soap):
        from core.nfse.paulistana.client import NFeClient
        from unittest.mock import MagicMock

        mock_sign.side_effect = lambda root, k, c: root
        mock_soap.return_value = "<xml/>"

        client = NFeClient(b"cert", b"key", "12345678000199", "12345678")

        mock_retorno_sucesso = MagicMock()
        mock_retorno_sucesso.cabecalho.sucesso = True
        mock_nfe = MagicMock()
        mock_nfe.chave_nfe.numero_nfe = "10"
        mock_nfe.chave_nfe.codigo_verificacao = "ABCDEFGH"
        mock_retorno_sucesso.nfe = [mock_nfe]

        with patch.object(
            client.parser, "from_string", return_value=mock_retorno_sucesso
        ):
            notas, raw_xml = client.consultar_nfe(10)
            self.assertEqual(len(notas), 1)
            self.assertEqual(str(notas[0].chave_nfe.numero_nfe), "10")
            self.assertEqual(str(notas[0].chave_nfe.codigo_verificacao), "ABCDEFGH")

        # Teste quando nota não é encontrada (alerta 1106)
        mock_retorno_inexistente = MagicMock()
        mock_retorno_inexistente.cabecalho.sucesso = True
        mock_retorno_inexistente.nfe = []
        mock_retorno_inexistente.erro = []
        mock_alerta = MagicMock()
        mock_alerta.codigo = "1106"
        mock_alerta.descricao = "NFS-e não encontrada."
        mock_retorno_inexistente.alerta = [mock_alerta]

        with patch.object(
            client.parser, "from_string", return_value=mock_retorno_inexistente
        ):
            notas_vazias, raw_empty = client.consultar_nfe(11)
            self.assertEqual(len(notas_vazias), 0)

    def test_rate_limiter(self):
        from core.utils.rate_limiter import RateLimiter
        import time

        limiter = RateLimiter(max_per_second=10.0)  # 10 req/s => 0.1s intervalo
        t0 = time.monotonic()
        for _ in range(3):
            limiter.wait()
        duracao = time.monotonic() - t0
        self.assertGreaterEqual(duracao, 0.18)

    @patch("core.nfse.paulistana.client.NFeClient.consultar_nfe")
    def test_paulistana_provider_buscar_nfse_por_numero(self, mock_consultar):
        from core.nfse.paulistana.provider import PaulistanaProvider
        from unittest.mock import MagicMock

        mock_nfe = MagicMock()
        mock_nfe.chave_nfe.numero_nfe = "10"
        mock_nfe.chave_nfe.codigo_verificacao = "ABCDEFGH"
        mock_nfe.chave_nfe.chave_nota_nacional = "12345"
        mock_nfe.valor_servicos = "250.00"
        mock_nfe.discriminacao = "Serviços de TI"
        mock_nfe.data_emissao_nfe = date(2026, 9, 1)
        mock_nfe.status_nfe = "N"
        mock_nfe.data_cancelamento = None
        mock_nfe.codigo_servico = "2668"
        mock_nfe.aliquota_servicos = "2.00"
        mock_nfe.valor_iss = "5.00"

        mock_consultar.side_effect = lambda num: (
            ([mock_nfe], "<xml/>") if str(num) == "10" else ([], "<xml/>")
        )

        self.company.pfx_cert_pem = b"fake-cert"
        self.company.pfx_key_pem = b"fake-key"
        self.company.save()

        with patch("core.nfse.paulistana.provider.to_xml", return_value="<xml/>"):
            provider = PaulistanaProvider()
            res = provider.buscar_nfse_por_numero(10)
            self.assertIsNotNone(res)
            self.assertEqual(res["nf_number"], "10")
            self.assertEqual(res["verification_code"], "ABCDEFGH")
            self.assertEqual(res["amount_brl"], "250.00")
            self.assertFalse(res["is_canceled"])

            res_none = provider.buscar_nfse_por_numero(11)
            self.assertIsNone(res_none)

    def test_nacional_provider_buscar_nfse_por_numero_stub(self):
        from core.nfse.nacional.provider import NacionalProvider

        provider = NacionalProvider()
        self.assertIsNone(provider.buscar_nfse_por_numero(1))

    @patch("core.nfse.paulistana.provider.PaulistanaProvider.buscar_nfse_por_numero")
    def test_import_nfses_empty_db(self, mock_buscar):
        from core.services.nfse_services import import_nfses
        from core.models import NotaFiscal

        NotaFiscal.objects.all().delete()

        def fake_buscar(num):
            if num in (1, 2):
                return {
                    "nf_number": str(num),
                    "verification_code": f"COD{num}",
                    "chave_acesso_nacional": f"CHAVE{num}",
                    "amount_brl": "100.00",
                    "description": f"Nota {num}",
                    "issue_date": date(2026, 9, num),
                    "is_canceled": False,
                    "cancelation_date": None,
                    "raw_xml": "<xml/>",
                }
            return None

        mock_buscar.side_effect = fake_buscar

        count, msg = import_nfses("PAULISTANA")
        self.assertEqual(count, 2)
        self.assertTrue(NotaFiscal.objects.filter(nf_number="1").exists())
        self.assertTrue(NotaFiscal.objects.filter(nf_number="2").exists())
        self.assertFalse(NotaFiscal.objects.filter(nf_number="3").exists())

    @patch("core.nfse.paulistana.provider.PaulistanaProvider.buscar_nfse_por_numero")
    def test_import_nfses_with_holes_and_newer(self, mock_buscar):
        from core.services.nfse_services import import_nfses
        from core.models import NotaFiscal

        NotaFiscal.objects.all().delete()
        # Seed notas 2, 4 e 5 (buracos são 1 e 3)
        for num in (2, 4, 5):
            NotaFiscal.objects.create(
                nf_number=str(num),
                verification_code=f"COD{num}",
                amount_brl=Decimal("100.00"),
                description=f"Nota {num}",
                issue_date=date(2026, 9, 1),
            )

        def fake_buscar(num):
            # Buracos 1 e 3 existem na prefeitura; 6 existe; 7 retorna None (fim)
            if num in (1, 3, 6):
                return {
                    "nf_number": str(num),
                    "verification_code": f"COD{num}",
                    "chave_acesso_nacional": f"CHAVE{num}",
                    "amount_brl": "150.00",
                    "description": f"Nota {num}",
                    "issue_date": date(2026, 9, 2),
                    "is_canceled": False,
                    "cancelation_date": None,
                    "raw_xml": "<xml/>",
                }
            return None

        mock_buscar.side_effect = fake_buscar

        count, msg = import_nfses("PAULISTANA")
        # Deve ter importado 3 notas: 1 e 3 (buracos) + 6 (nova)
        self.assertEqual(count, 3)
        self.assertTrue(NotaFiscal.objects.filter(nf_number="1").exists())
        self.assertTrue(NotaFiscal.objects.filter(nf_number="3").exists())
        self.assertTrue(NotaFiscal.objects.filter(nf_number="6").exists())
        self.assertFalse(NotaFiscal.objects.filter(nf_number="7").exists())
        self.assertEqual(NotaFiscal.objects.count(), 6)

    def test_import_nfses_nacional_stub(self):
        from core.services.nfse_services import import_nfses

        count, msg = import_nfses("NACIONAL")
        self.assertEqual(count, 0)
        self.assertIn("não está disponível", msg)

    @patch("core.nfse.paulistana.provider.PaulistanaProvider.buscar_nfse_por_numero")
    def test_sync_nota_fiscal_externally_canceled(self, mock_buscar):
        from core.services.nfse_services import sync_nota_fiscal
        from django.utils import timezone

        invoice = Invoice.objects.create(
            client=self.client_obj,
            invoice_number="INV-SYNC-01",
            issue_date=date(2026, 9, 1),
            currency="USD",
            status="FINALIZED",
        )
        nf = NotaFiscal.objects.create(
            invoice=invoice,
            nf_number="88",
            verification_code="VERIF88",
            issue_date=date(2026, 9, 1),
            amount_brl=Decimal("500.00"),
            is_canceled=False,
        )

        now = timezone.now()
        mock_buscar.return_value = {
            "nf_number": "88",
            "verification_code": "VERIF88",
            "chave_acesso_nacional": "CHAVE88",
            "amount_brl": "500.00",
            "description": "Serviços",
            "issue_date": date(2026, 9, 1),
            "is_canceled": True,
            "cancelation_date": now,
            "raw_xml": "<xml_canceled/>",
        }

        with patch("core.services.nfse_services.fetch_and_save_nfse_pdf") as mock_fetch_pdf:
            success, msg = sync_nota_fiscal(nf)
            self.assertTrue(success)
            self.assertIn("identificada como CANCELADA", msg)

        nf.refresh_from_db()
        self.assertTrue(nf.is_canceled)
        self.assertIsNotNone(nf.cancelation_date)

        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "CANCELED")

    @patch("core.services.nfse_services.sync_nota_fiscal")
    def test_nfse_refresh_view(self, mock_sync):
        mock_sync.return_value = (True, "NFS-e sincronizada com sucesso com o provedor.")

        nf = NotaFiscal.objects.create(
            nf_number="99",
            verification_code="VERIF99",
            issue_date=date(2026, 9, 1),
            amount_brl=Decimal("300.00"),
        )

        response = self.client_http.post(reverse("nfse_refresh", kwargs={"pk": nf.id}))
        self.assertRedirects(response, reverse("nfse_detail", kwargs={"pk": nf.id}))
        mock_sync.assert_called_once_with(nf)

    @patch("core.nfse.paulistana.provider.PaulistanaProvider.buscar_nfse_por_numero")
    def test_sync_nota_fiscal_not_found(self, mock_buscar):
        from core.services.nfse_services import sync_nota_fiscal

        nf = NotaFiscal.objects.create(
            nf_number="100",
            verification_code="VERIF100",
            issue_date=date(2026, 9, 1),
            amount_brl=Decimal("100.00"),
        )
        mock_buscar.return_value = None

        success, msg = sync_nota_fiscal(nf)
        self.assertFalse(success)
        self.assertIn("não encontrada", msg)

    @patch("core.nfse.paulistana.provider.PaulistanaProvider.buscar_nfse_por_numero")
    def test_sync_nota_fiscal_no_changes_does_not_outdate_consolidation(self, mock_buscar):
        from core.services.nfse_services import sync_nota_fiscal
        from core.models import MonthlyConsolidation

        target_month = date(2026, 9, 1)
        cons = MonthlyConsolidation.objects.create(
            month_year=target_month,
            status="CONSOLIDATED",
            actual_pro_labore_paid=Decimal("5000.00"),
        )
        nf = NotaFiscal.objects.create(
            nf_number="101",
            verification_code="VERIF101",
            issue_date=target_month,
            amount_brl=Decimal("1000.00"),
            is_canceled=False,
        )
        # Reset consolidation status to CONSOLIDATED after creating NF
        cons.status = "CONSOLIDATED"
        cons.save()

        # Mock provider returning identical values
        mock_buscar.return_value = {
            "nf_number": "101",
            "verification_code": "VERIF101",
            "amount_brl": "1000.00",
            "description": "Serviços",
            "issue_date": target_month,
            "is_canceled": False,
            "raw_xml": "<xml_identical/>",
        }

        success, msg = sync_nota_fiscal(nf)
        self.assertTrue(success)

        cons.refresh_from_db()
        self.assertEqual(cons.status, "CONSOLIDATED")

    @patch("core.nfse.paulistana.provider.PaulistanaProvider.buscar_nfse_por_numero")
    def test_sync_nota_fiscal_value_change_outdates_consolidation(self, mock_buscar):
        from core.services.nfse_services import sync_nota_fiscal
        from core.models import MonthlyConsolidation

        target_month = date(2026, 9, 1)
        cons = MonthlyConsolidation.objects.create(
            month_year=target_month,
            status="CONSOLIDATED",
            actual_pro_labore_paid=Decimal("5000.00"),
        )
        nf = NotaFiscal.objects.create(
            nf_number="102",
            verification_code="VERIF102",
            issue_date=target_month,
            amount_brl=Decimal("1000.00"),
            is_canceled=False,
        )
        cons.status = "CONSOLIDATED"
        cons.save()

        # Mock provider returning altered amount
        mock_buscar.return_value = {
            "nf_number": "102",
            "verification_code": "VERIF102",
            "amount_brl": "1500.00",
            "description": "Serviços",
            "issue_date": target_month,
            "is_canceled": False,
            "raw_xml": "<xml_value_changed/>",
        }

        success, msg = sync_nota_fiscal(nf)
        self.assertTrue(success)

        cons.refresh_from_db()
        self.assertEqual(cons.status, "OUTDATED")

    @patch("core.nfse.provider_factory.get_provider")
    def test_download_pdf_does_not_outdate_consolidation(self, mock_get_provider):
        from core.models import MonthlyConsolidation
        from unittest.mock import MagicMock

        mock_provider = MagicMock()
        mock_provider.baixar_pdf.return_value = b"%PDF-1.4 test pdf content"
        mock_get_provider.return_value = mock_provider

        target_month = date(2026, 9, 1)
        cons = MonthlyConsolidation.objects.create(
            month_year=target_month,
            status="CONSOLIDATED",
            actual_pro_labore_paid=Decimal("5000.00"),
        )
        nf = NotaFiscal.objects.create(
            nf_number="103",
            verification_code="VERIF103",
            issue_date=target_month,
            amount_brl=Decimal("1000.00"),
            is_canceled=False,
        )
        cons.status = "CONSOLIDATED"
        cons.save()

        response = self.client_http.get(reverse("nfse_download_pdf", kwargs={"pk": nf.id}))
        self.assertEqual(response.status_code, 200)

        cons.refresh_from_db()
        self.assertEqual(cons.status, "CONSOLIDATED")


    @patch("core.nfse.paulistana.provider.PaulistanaProvider.buscar_nfse_por_numero")
    def test_download_xml_does_not_outdate_consolidation(self, mock_buscar):
        from core.models import MonthlyConsolidation

        mock_buscar.return_value = {
            "nf_number": "104",
            "verification_code": "VERIF104",
            "amount_brl": "1000.00",
            "description": "Serviços",
            "issue_date": date(2026, 9, 1),
            "is_canceled": False,
            "raw_xml": "<xml_content>hello</xml_content>",
        }

        target_month = date(2026, 9, 1)
        cons = MonthlyConsolidation.objects.create(
            month_year=target_month,
            status="CONSOLIDATED",
            actual_pro_labore_paid=Decimal("5000.00"),
        )
        nf = NotaFiscal.objects.create(
            nf_number="104",
            verification_code="VERIF104",
            issue_date=target_month,
            amount_brl=Decimal("1000.00"),
            is_canceled=False,
        )
        cons.status = "CONSOLIDATED"
        cons.save()

        response = self.client_http.get(reverse("nfse_download_xml", kwargs={"pk": nf.id}))
        self.assertEqual(response.status_code, 200)

        cons.refresh_from_db()
        self.assertEqual(cons.status, "CONSOLIDATED")


class ProcessDailyInvoicesTaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("admin", "admin@test.com", "pass")
        self.company = CompanySettings.objects.create(
            company_name="Acme Services Inc",
            cnpj="00.000.000/0001-00",
            opening_date=date(2024, 1, 1),
            email="accounting@acmetest.com",
            auto_finalize_invoices=True,
            auto_send_emails=False,
            auto_emit_nfse=False,
            auto_invoice_hour=9,
        )
        self.client_obj = Client.objects.create(
            name="Foreign Test Client LLC",
            email="client@foreigntest.com",
            address_country_code="US",
        )

    def test_auto_finalization_disabled(self):
        self.company.auto_finalize_invoices = False
        self.company.save()
        from core.tasks.invoices_tasks import process_daily_invoices_task

        result = process_daily_invoices_task(force=False)
        self.assertEqual(result, "Auto finalization disabled.")

    def test_not_configured_hour(self):
        from core.tasks.invoices_tasks import process_daily_invoices_task
        from django.utils import timezone

        current_hour = timezone.localtime(timezone.now()).hour
        self.company.auto_invoice_hour = (current_hour + 1) % 24
        self.company.save()

        result = process_daily_invoices_task(force=False)
        self.assertIn("Not the configured hour", result)

    @patch("core.tasks.invoices_tasks.finalize_invoice_task.si")
    @patch("core.tasks.invoices_tasks.fetch_exchange_rate")
    def test_processes_draft_with_date_today_auto_emit_nfse_false(
        self, mock_fetch_rate, mock_finalize_si
    ):
        from core.tasks.invoices_tasks import process_daily_invoices_task
        from django.utils import timezone

        today = timezone.localdate()
        mock_fetch_rate.return_value = Decimal("5.0000")

        inv_today = Invoice.objects.create(
            client=self.client_obj,
            invoice_number="INV-TEST-001",
            issue_date=today,
            currency="USD",
            status="DRAFT",
        )
        InvoiceItem.objects.create(
            invoice=inv_today,
            description="Service",
            quantity=Decimal("1.00"),
            unit_price_foreign=Decimal("1000.00"),
        )
        inv_yesterday = Invoice.objects.create(
            client=self.client_obj,
            invoice_number="INV-TEST-002",
            issue_date=today - timedelta(days=1),
            currency="USD",
            status="DRAFT",
        )

        mock_sig = MagicMock()
        mock_sig.delay.return_value.id = "mock-task-id-1"
        mock_finalize_si.return_value = mock_sig

        res = process_daily_invoices_task(force=True)
        self.assertEqual(res, "Processed 1 daily invoices.")

        inv_today.refresh_from_db()
        self.assertEqual(inv_today.status, "PROCESSING")
        mock_sig.delay.assert_called_once()

        inv_yesterday.refresh_from_db()
        self.assertEqual(inv_yesterday.status, "DRAFT")

    @patch("core.tasks.invoices_tasks.chain")
    @patch("core.tasks.nfse_tasks.issue_nfse_task.si")
    @patch("core.tasks.invoices_tasks.finalize_invoice_task.si")
    @patch("core.tasks.invoices_tasks.fetch_exchange_rate")
    def test_processes_draft_with_auto_emit_nfse_chains_tasks(
        self, mock_fetch_rate, mock_finalize_si, mock_issue_si, mock_chain
    ):
        self.company.auto_emit_nfse = True
        self.company.save()

        from core.tasks.invoices_tasks import process_daily_invoices_task
        from django.utils import timezone

        today = timezone.localdate()
        mock_fetch_rate.return_value = Decimal("5.0000")

        inv = Invoice.objects.create(
            client=self.client_obj,
            invoice_number="INV-TEST-003",
            issue_date=today,
            currency="USD",
            status="DRAFT",
        )
        InvoiceItem.objects.create(
            invoice=inv,
            description="Service",
            quantity=Decimal("1.00"),
            unit_price_foreign=Decimal("1000.00"),
        )

        mock_final_sig = MagicMock()
        mock_issue_sig = MagicMock()
        mock_finalize_si.return_value = mock_final_sig
        mock_issue_si.return_value = mock_issue_sig

        mock_chained = MagicMock()
        mock_chained.delay.return_value.id = "mock-task-id-2"
        mock_chain.return_value = mock_chained

        res = process_daily_invoices_task(force=True)
        self.assertEqual(res, "Processed 1 daily invoices.")

        mock_finalize_si.assert_called_once_with(
            inv.id,
            send_to_client=False,
            send_to_company=False,
        )
        mock_issue_si.assert_called_once_with(
            inv.id,
            "5.0000",
            send_to_company=False,
            send_to_client=False,
        )
        mock_chain.assert_called_once_with(mock_final_sig, mock_issue_sig)
        mock_chained.delay.assert_called_once()

    @patch("core.tasks.invoices_tasks.send_email_with_debug")
    @patch("core.tasks.invoices_tasks.finalize_invoice_task.si")
    @patch("core.tasks.invoices_tasks.fetch_exchange_rate")
    def test_failsafe_triggered_aborts_nfse_and_sends_email(
        self, mock_fetch_rate, mock_finalize_si, mock_send_email
    ):
        self.company.auto_emit_nfse = True
        self.company.save()

        from core.tasks.invoices_tasks import process_daily_invoices_task
        from django.utils import timezone

        today = timezone.localdate()
        mock_fetch_rate.return_value = Decimal("5.0000")

        inv = Invoice.objects.create(
            client=self.client_obj,
            invoice_number="INV-TEST-004",
            issue_date=today,
            currency="USD",
            status="DRAFT",
        )
        InvoiceItem.objects.create(
            invoice=inv,
            description="High value project",
            quantity=Decimal("1.00"),
            unit_price_foreign=Decimal("25000.00"),
        )

        mock_final_sig = MagicMock()
        mock_final_sig.delay.return_value.id = "mock-task-id-3"
        mock_finalize_si.return_value = mock_final_sig

        res = process_daily_invoices_task(force=True)
        self.assertEqual(res, "Processed 1 daily invoices.")

        mock_final_sig.delay.assert_called_once()
        mock_send_email.assert_called_once()

    def test_legacy_task_alias_calls_process_daily_invoices_task(self):
        from core.tasks.invoices_tasks import legacy_process_daily_invoices_task

        self.company.auto_finalize_invoices = False
        self.company.save()
        res = legacy_process_daily_invoices_task(force=False)
        self.assertEqual(res, "Auto finalization disabled.")


class CompanySettingsAutoEmitNfseTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("admin", "admin@test.com", "pass")
        self.client_http = HttpClient()
        self.client_http.force_login(self.user)
        self.company = CompanySettings.objects.create(
            company_name="Acme Services Inc",
            cnpj="12.345.678/0001-95",
            opening_date=date(2024, 1, 1),
            inscricao_municipal="123456",
            email="test@test.com",
            address_line1="Main St",
            address_city_ibge="3550308",
            nfse_provider="PAULISTANA",
            next_document_number=1,
            document_series="1",
            default_codigo_tributacao_nacional="010101",
            auto_finalize_invoices=False,
            auto_emit_nfse=False,
        )

    def test_company_settings_view_renders_auto_emit_nfse(self):
        response = self.client_http.get(reverse("company_settings"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="auto_emit_nfse"')
        self.assertContains(response, 'Emitir NFS-e Automaticamente')

    def test_company_settings_view_saves_auto_emit_nfse(self):
        data = {
            "company_name": self.company.company_name,
            "cnpj": self.company.cnpj,
            "opening_date": self.company.opening_date.strftime("%d/%m/%Y"),
            "inscricao_municipal": self.company.inscricao_municipal,
            "email": self.company.email,
            "address_line1": self.company.address_line1,
            "address_city_ibge": self.company.address_city_ibge,
            "nfse_provider": self.company.nfse_provider,
            "next_document_number": self.company.next_document_number,
            "document_series": self.company.document_series,
            "default_codigo_tributacao_nacional": self.company.default_codigo_tributacao_nacional,
            "auto_invoice_hour": 8,
            "auto_finalize_invoices": "on",
            "auto_send_emails": "on",
            "auto_emit_nfse": "on",
        }
        response = self.client_http.post(reverse("company_settings"), data=data)
        self.assertEqual(response.status_code, 302)

        self.company.refresh_from_db()
        self.assertTrue(self.company.auto_finalize_invoices)
        self.assertTrue(self.company.auto_send_emails)
        self.assertTrue(self.company.auto_emit_nfse)


class SecuritySettingsTests(TestCase):
    def test_csrf_trusted_origins_configured(self):
        self.assertTrue(len(settings.CSRF_TRUSTED_ORIGINS) > 0)
        for origin in settings.CSRF_TRUSTED_ORIGINS:
            self.assertTrue(
                origin.startswith("http://") or origin.startswith("https://"),
                f"Origin {origin} must have a scheme",
            )

    def test_get_csrf_trusted_origins_derivation(self):
        origins = get_csrf_trusted_origins(
            ["app.example.com", ".sub.example.com", "*.wildcard.example.com"]
        )
        self.assertIn("https://app.example.com", origins)
        self.assertIn("http://app.example.com", origins)
        self.assertIn("https://*.sub.example.com", origins)
        self.assertIn("https://sub.example.com", origins)
        self.assertIn("https://*.wildcard.example.com", origins)
        self.assertIn("https://wildcard.example.com", origins)

    def test_get_csrf_trusted_origins_wildcard_debug(self):
        origins = get_csrf_trusted_origins(["*"], debug=True)
        self.assertIn("http://localhost", origins)
        self.assertIn("http://localhost:8080", origins)

    def test_secure_proxy_ssl_header_configured(self):
        self.assertEqual(
            settings.SECURE_PROXY_SSL_HEADER, ("HTTP_X_FORWARDED_PROTO", "https")
        )
        self.assertTrue(settings.USE_X_FORWARDED_HOST)

        rf = RequestFactory()
        request = rf.get("/", HTTP_X_FORWARDED_PROTO="https")
        self.assertTrue(request.is_secure())

    def test_csrf_origin_verification_with_trusted_origin(self):
        rf = RequestFactory()
        with override_settings(CSRF_TRUSTED_ORIGINS=["https://app.example.com"]):
            mw = CsrfViewMiddleware(lambda req: None)
            request = rf.post("/accounts/login/", HTTP_ORIGIN="https://app.example.com")
            self.assertTrue(mw._origin_verified(request))

            untrusted_request = rf.post(
                "/accounts/login/", HTTP_ORIGIN="https://malicious.example.com"
            )
            self.assertFalse(mw._origin_verified(untrusted_request))
