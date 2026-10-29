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


SAMPLE_NACIONAL_NFSE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<NFSe xmlns="http://www.sped.fazenda.gov.br/nfse" versao="1.00">
  <infNFSe Id="NFS35503082000000000001910000100000000000999991234567">
    <xLocEmi>São Paulo</xLocEmi>
    <xLocPrestacao>São Paulo</xLocPrestacao>
    <nNFSe>99999</nNFSe>
    <cVerif>ABCDEF123456</cVerif>
    <dhProc>2026-10-16T12:00:00-03:00</dhProc>
    <DPS xmlns="http://www.sped.fazenda.gov.br/nfse" versao="1.00">
      <infDPS Id="DPS3550308212345678000190000010000000000099999">
        <tpAmb>2</tpAmb>
        <dhEmi>2026-10-16T12:00:00-03:00</dhEmi>
        <verProc>1.0</verProc>
        <dCompet>2026-10-16</dCompet>
        <prest>
          <CNPJ>12345678000190</CNPJ>
          <xNome>EMPRESA TESTE LTDA</xNome>
          <end>
            <xLgr>RUA TESTE</xLgr>
            <nro>100</nro>
            <xBairro>CENTRO</xBairro>
            <cMun>3550308</cMun>
            <xMun>SAO PAULO</xMun>
            <UF>SP</UF>
            <CEP>01001000</CEP>
          </end>
          <regTrib>
            <opSimpNac>1</opSimpNac>
            <regEspTrib>0</regEspTrib>
          </regTrib>
        </prest>
        <toma>
          <xNome>CLIENT TEST FOREIGN INC</xNome>
          <end>
            <endExt>
              <cPais>CAN</cPais>
              <cEndPost>H2X 1Y4</cEndPost>
              <xCidade>Montreal</xCidade>
              <xEstProvReg>Quebec</xEstProvReg>
            </endExt>
            <xLgr>Rue Sainte-Catherine</xLgr>
            <nro>123</nro>
            <xBairro>Centre-Ville</xBairro>
          </end>
        </toma>
        <serv>
          <locPrest>
            <cLocPrestacao>3550308</cLocPrestacao>
          </locPrest>
          <cServ>
            <cTribNac>010101</cTribNac>
            <xDescServ>Servicos de desenvolvimento de software e consultoria em TI.</xDescServ>
          </cServ>
        </serv>
        <valores>
          <vServPrest>
            <vServ>1000.00</vServ>
          </vServPrest>
          <trib>
            <tribMun>
              <tribISSQN>3</tribISSQN>
              <tpRetISSQN>1</tpRetISSQN>
            </tribMun>
            <totTrib>
              <pTotTribSN>2.01</pTotTribSN>
            </totTrib>
          </trib>
        </valores>
      </infDPS>
    </DPS>
    <valores>
      <vServPrest>
        <vServ>1000.00</vServ>
      </vServPrest>
      <vLiq>1000.00</vLiq>
    </valores>
  </infNFSe>
</NFSe>"""


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
        from unittest.mock import patch
        _blocked_patcher = patch("core.models.paulistana_emission_blocked", return_value=False)
        _blocked_patcher.start()
        self.addCleanup(_blocked_patcher.stop)

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
            codigo_tributacao_nacional="010101",
            codigo_servico_municipio="",
            codigo_nbs="115029000",
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

    def test_client_nif_clean_and_whitespace_stripping(self):
        client = Client(
            name="NIF Test Client",
            address_neighborhood="Downtown",
            nif="  US123456789  ",
        )
        client.clean()
        self.assertEqual(client.nif, "US123456789")

    def test_client_form_nif(self):
        from core.forms import ClientForm

        form = ClientForm(
            data={
                "name": "Form Client",
                "nif": "  TAX-998877  ",
                "address_neighborhood": "Central",
                "address_country_code": "ca",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["nif"], "TAX-998877")
        self.assertEqual(form.cleaned_data["address_country_code"], "CA")

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
        # Verify prestador xNome is omitted when tpEmit=1 to prevent E0121
        self.assertNotIn(f"<xNome>{self.company.company_name}</xNome>", signed_xml)
        # Verify locPrest uses cLocPrestacao in Brazil and cPaisResult for export Scenario 2 (prevents E0591)
        self.assertIn(f"<cLocPrestacao>{self.company.address_city_ibge}</cLocPrestacao>", signed_xml)
        self.assertNotIn("<cPaisPrestacao>", signed_xml)
        self.assertIn("<cPaisResult>CA</cPaisResult>", signed_xml)
        # Verify pTotTribSN or indTotTrib
        self.assertTrue(
            "<pTotTribSN>" in signed_xml or "<indTotTrib>0</indTotTrib>" in signed_xml
        )
        # Verify tomador email and prestador email are included
        self.assertIn(f"<email>{self.client_obj.email}</email>", signed_xml)
        self.assertIn(f"<email>{self.company.email}</email>", signed_xml)

    def test_nacional_dps_with_client_nif(self):
        from core.nfse.nacional.provider import NacionalProvider

        self.client_obj.nif = "US987654321"
        self.client_obj.save()

        nacional_provider = NacionalProvider()
        dps, signed_xml, id_dps = nacional_provider._build_and_sign_dps(
            self.invoice, self.company, 1, "1"
        )
        self.assertIn("<NIF>US987654321</NIF>", signed_xml)
        self.assertNotIn("<cNaoNIF>", signed_xml)

    def test_nacional_dps_with_blank_or_whitespace_nif(self):
        from core.nfse.nacional.provider import NacionalProvider

        for empty_val in ["", "   "]:
            self.client_obj.nif = empty_val
            self.client_obj.save()

            nacional_provider = NacionalProvider()
            dps, signed_xml, id_dps = nacional_provider._build_and_sign_dps(
                self.invoice, self.company, 1, "1"
            )
            self.assertIn("<cNaoNIF>2</cNaoNIF>", signed_xml)
            self.assertNotIn("<NIF>", signed_xml)

    def test_nacional_dps_phone_sanitization(self):
        from core.nfse.nacional.provider import NacionalProvider

        self.company.phone_number = "+55 (11) 98765-4321"
        self.company.save()

        nacional_provider = NacionalProvider()
        dps, signed_xml, id_dps = nacional_provider._build_and_sign_dps(
            self.invoice, self.company, 2, "1"
        )
        self.assertIn("<fone>11987654321</fone>", signed_xml)

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

        fake_nfse_xml = SAMPLE_NACIONAL_NFSE_XML
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

    @patch("core.utils.http.requests.post")
    @patch("core.utils.http.requests.get")
    def test_nacional_emitir_cnc_habilitado_includes_im(self, mock_get, mock_post):
        import gzip
        import base64
        from core.nfse.nacional.provider import NacionalProvider

        fake_nfse_xml = "<xml><nNFSe>99991</nNFSe></xml>"
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

            if "/cnc/consulta/cad" in url:
                return MockResp(
                    200,
                    {
                        "ListaCadastroMunicipal": [
                            {
                                "CodigoMunicipio": int(self.company.address_city_ibge),
                                "InfCad": {
                                    "Inscricao": self.company.cnpj_clean,
                                    "InscricaoMunicipal": "000000072611693",
                                    "SituacaoEmissaoNFSe": "HABILITADO",
                                },
                            }
                        ],
                        "StatusProcessamento": "DOCUMENTOS_LOCALIZADOS",
                    },
                )
            elif "/dps/" in url:
                return MockResp(404, {})
            return MockResp(404, {})

        mock_get.side_effect = side_effect_get

        class MockPostResp:
            status_code = 201

            def json(self):
                return {
                    "tipoAmbiente": 2,
                    "chaveAcesso": "35503082000000000001910000100000000000999911234567",
                    "nfseXmlGZipB64": fake_b64,
                }

            @property
            def text(self):
                return "OK"

        mock_post.return_value = MockPostResp()

        provider = NacionalProvider()
        result = provider.emitir_nfse(self.invoice)
        self.assertTrue(result.sucesso)
        self.assertEqual(result.numero_nf, "99991")

        # Verify that mock_post received DPS XML containing <IM>000000072611693</IM>
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs.get("json") or {}
        compressed = base64.b64decode(payload["dpsXmlGZipB64"])
        decompressed_xml = gzip.decompress(compressed).decode("utf-8")
        self.assertIn("<IM>000000072611693</IM>", decompressed_xml)

    @patch("core.utils.http.requests.post")
    @patch("core.utils.http.requests.get")
    def test_nacional_emitir_cnc_desabilitado_aborts_emission(self, mock_get, mock_post):
        from core.nfse.nacional.provider import NacionalProvider

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

            if "/cnc/consulta/cad" in url:
                return MockResp(
                    200,
                    {
                        "ListaCadastroMunicipal": [
                            {
                                "CodigoMunicipio": int(self.company.address_city_ibge),
                                "InfCad": {
                                    "Inscricao": self.company.cnpj_clean,
                                    "InscricaoMunicipal": "000000072611693",
                                    "SituacaoEmissaoNFSe": "DESABILITADO",
                                },
                            }
                        ],
                        "StatusProcessamento": "DOCUMENTOS_LOCALIZADOS",
                    },
                )
            return MockResp(404, {})

        mock_get.side_effect = side_effect_get

        provider = NacionalProvider()
        result = provider.emitir_nfse(self.invoice)
        self.assertFalse(result.sucesso)
        self.assertTrue(any("não está habilitado para emissão" in err for err in result.erros))
        self.assertTrue(any("DESABILITADO" in err for err in result.erros))
        # Ensure Sefin Nacional was NEVER called
        mock_post.assert_not_called()

    @patch("core.utils.http.requests.post")
    @patch("core.utils.http.requests.get")
    def test_nacional_emitir_cnc_404_omits_im(self, mock_get, mock_post):
        import gzip
        import base64
        from core.nfse.nacional.provider import NacionalProvider

        fake_nfse_xml = "<xml><nNFSe>99992</nNFSe></xml>"
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

            if "/cnc/consulta/cad" in url:
                return MockResp(
                    404,
                    {"StatusProcessamento": "NENHUM_DOCUMENTO_LOCALIZADO"},
                )
            elif "/dps/" in url:
                return MockResp(404, {})
            return MockResp(404, {})

        mock_get.side_effect = side_effect_get

        class MockPostResp:
            status_code = 201

            def json(self):
                return {
                    "tipoAmbiente": 2,
                    "chaveAcesso": "35503082000000000001910000100000000000999921234567",
                    "nfseXmlGZipB64": fake_b64,
                }

            @property
            def text(self):
                return "OK"

        mock_post.return_value = MockPostResp()

        provider = NacionalProvider()
        result = provider.emitir_nfse(self.invoice)
        self.assertTrue(result.sucesso)

        # Verify that mock_post received DPS XML WITHOUT <IM>
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs.get("json") or {}
        compressed = base64.b64decode(payload["dpsXmlGZipB64"])
        decompressed_xml = gzip.decompress(compressed).decode("utf-8")
        self.assertNotIn("<IM>", decompressed_xml)

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

    def test_paulistana_provider_baixar_pdf_real_xml_in_debug_mode(self):
        from core.nfse.paulistana.provider import PaulistanaProvider
        from django.core.files.base import ContentFile
        from unittest.mock import patch

        self.company.debug_mode = True
        self.company.inscricao_municipal = "12345678"
        self.company.save()

        provider = PaulistanaProvider()

        real_xml = """<?xml version="1.0" encoding="utf-8"?>
<NFe xmlns="http://www.prefeitura.sp.gov.br/nfe/tipos">
    <ChaveNFe>
        <InscricaoPrestador>12345678</InscricaoPrestador>
        <NumeroNFe>12345</NumeroNFe>
        <CodigoVerificacao>ABC12345</CodigoVerificacao>
    </ChaveNFe>
</NFe>"""

        nf = NotaFiscal.objects.create(
            invoice=self.invoice,
            nf_number="12345",
            issue_date=self.invoice.issue_date,
            amount_brl=Decimal("5000.00"),
            is_export=True,
            description="Service Real",
            verification_code="ABC12345",
        )
        nf.xml_autorizacao.save("NFS-e_12345.xml", ContentFile(real_xml.encode("utf-8")), save=True)

        with patch("core.nfse.paulistana.client.download_nfse_pdf", return_value=b"%PDF-1.4 Real Paulistana PDF") as mock_download:
            with patch("core.nfse.paulistana.mock.render_paulistana_debug_pdf") as mock_render_mock:
                pdf_bytes = provider.baixar_pdf(self.invoice)
                mock_download.assert_called_once_with("12345678", "12345", "ABC12345")
                mock_render_mock.assert_not_called()
                self.assertEqual(pdf_bytes, b"%PDF-1.4 Real Paulistana PDF")

    def test_is_paulistana_xml_mocked_helper(self):
        from core.nfse.paulistana.mock import is_paulistana_xml_mocked

        # Mocked verification codes
        self.assertTrue(is_paulistana_xml_mocked(None, "DEBUG-1"))
        self.assertTrue(is_paulistana_xml_mocked("<xml/>", "DEBUG-FAKE-CODE"))
        self.assertTrue(is_paulistana_xml_mocked("<NFe/>", "DBG0001X"))
        self.assertTrue(is_paulistana_xml_mocked("<NFe/>", ""))
        self.assertTrue(is_paulistana_xml_mocked(None, "ABC12345"))

        # Mocked XML contents
        mock_xml = "<NFe><CodigoVerificacao>DBG0001X</CodigoVerificacao></NFe>"
        self.assertTrue(is_paulistana_xml_mocked(mock_xml, "ABC12345"))

        invalid_xml = "not xml at all"
        self.assertTrue(is_paulistana_xml_mocked(invalid_xml, "ABC12345"))

        # Real valid XML and verification code
        valid_xml = '<NFe xmlns="http://www.prefeitura.sp.gov.br/nfe/tipos"><ChaveNFe><NumeroNFe>10</NumeroNFe><CodigoVerificacao>ABC12345</CodigoVerificacao></ChaveNFe></NFe>'
        self.assertFalse(is_paulistana_xml_mocked(valid_xml, "ABC12345"))

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

    @override_settings(FORCE_DEBUG_MODE=False)
    @patch("core.nfse.paulistana.provider.PaulistanaProvider.consultar_nfse", return_value=None)
    @patch("core.nfse.paulistana.client.NFeClient.consultar_lote", side_effect=Exception("mocked"))
    @patch("core.nfse.paulistana.client.NFeClient.enviar_lote_rps")
    def test_paulistana_emitir_nfse_extracts_list_and_national_key(
        self, mock_enviar, mock_lote, mock_consultar
    ):
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
        self.invoice.codigo_servico_municipio = "02668"
        self.invoice.save()

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
        self.invoice.codigo_servico_municipio = "02668"
        self.invoice.save()

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
        self.invoice.codigo_servico_municipio = "02668"
        self.invoice.save()

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

    def test_nacional_baixar_pdf_generates_pdf_via_brazilfiscalreport(self):
        from core.nfse.nacional.provider import NacionalProvider
        from django.core.files.base import ContentFile

        self.company.nfse_provider = "NACIONAL"
        self.company.save()

        nf = NotaFiscal.objects.create(
            invoice=self.invoice,
            nf_number="99999",
            issue_date=self.invoice.issue_date,
            amount_brl=Decimal("1000.00"),
            is_export=True,
            description="Software Development Services",
            chave_acesso_nacional="35503082000000000001910000100000000000999991234567",
        )
        nf.xml_autorizacao.save(
            "NFS-e_99999.xml", ContentFile(SAMPLE_NACIONAL_NFSE_XML.encode("utf-8"))
        )

        provider = NacionalProvider()
        pdf_bytes = provider.baixar_pdf(self.invoice)
        self.assertIsNotNone(pdf_bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertGreater(len(pdf_bytes), 10000)

    def test_nacional_baixar_pdf_with_cancelled_watermark(self):
        from core.nfse.nacional.provider import NacionalProvider
        from django.core.files.base import ContentFile
        from django.utils import timezone as dj_timezone

        self.company.nfse_provider = "NACIONAL"
        self.company.save()

        nf = NotaFiscal.objects.create(
            invoice=self.invoice,
            nf_number="99999",
            issue_date=self.invoice.issue_date,
            amount_brl=Decimal("1000.00"),
            is_export=True,
            is_canceled=True,
            cancelation_date=dj_timezone.now(),
            description="Software Development Services",
            chave_acesso_nacional="35503082000000000001910000100000000000999991234567",
        )
        nf.xml_autorizacao.save(
            "NFS-e_99999.xml", ContentFile(SAMPLE_NACIONAL_NFSE_XML.encode("utf-8"))
        )

        provider = NacionalProvider()
        pdf_bytes = provider.baixar_pdf(self.invoice)
        self.assertIsNotNone(pdf_bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertGreater(len(pdf_bytes), 10000)

    def test_nacional_baixar_pdf_recovers_xml_from_api_if_missing(self):
        from core.nfse.nacional.provider import NacionalProvider

        self.company.nfse_provider = "NACIONAL"
        self.company.save()

        nf = NotaFiscal.objects.create(
            invoice=self.invoice,
            nf_number="99999",
            issue_date=self.invoice.issue_date,
            amount_brl=Decimal("1000.00"),
            is_export=True,
            description="Software Development Services",
            chave_acesso_nacional="35503082000000000001910000100000000000999991234567",
        )

        provider = NacionalProvider()
        with patch.object(
            provider,
            "buscar_nfse_por_chave",
            return_value={"raw_xml": SAMPLE_NACIONAL_NFSE_XML},
        ):
            pdf_bytes = provider.baixar_pdf(self.invoice)

        self.assertIsNotNone(pdf_bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        nf.refresh_from_db()
        self.assertTrue(bool(nf.xml_autorizacao))

    @patch("core.nfse.paulistana.client.NFeClient.testar_envio_lote_rps")
    def test_paulistana_debug_emission_generates_authentic_xml_and_pdf(
        self, mock_testar_lote
    ):
        from core.services import enviar_nfe_para_prefeitura
        from core.nfse.paulistana.schemas_v1.retorno_envio_lote_rps_v01 import (
            RetornoEnvioLoteRps as RetornoEnvioLoteRpsV1,
        )

        self.company.nfse_provider = "PAULISTANA"
        self.company.debug_mode = True
        self.company.save()

        self.invoice.document_number = 101
        self.invoice.codigo_servico_municipio = "02668"
        self.invoice.save()

        mock_testar_lote.return_value = (
            RetornoEnvioLoteRpsV1(
                cabecalho=RetornoEnvioLoteRpsV1.Cabecalho(sucesso=True)
            ),
            "<signedXml/>",
            "<retornoXml/>",
        )

        success = enviar_nfe_para_prefeitura(self.invoice)
        self.assertTrue(success)

        nf = NotaFiscal.objects.get(invoice=self.invoice)
        self.assertEqual(nf.nf_number, "DEBUG-101")
        self.assertTrue(bool(nf.xml_autorizacao))

        # Verify XML contains tpNFe and authentic metadata
        with nf.xml_autorizacao.open("r") as f:
            xml_text = f.read()
        self.assertIn("tpNFe", xml_text)
        self.assertIn("Test Company", xml_text)
        self.assertIn("Canadian Tech Inc", xml_text)
        self.assertIn("<TributacaoNFe>P</TributacaoNFe>", xml_text)
        self.assertIn("<AliquotaServicos>0.0000</AliquotaServicos>", xml_text)
        self.assertIn("<ValorISS>0.00</ValorISS>", xml_text)
        self.assertEqual(nf.aliquota_iss, Decimal("0.00"))
        self.assertEqual(nf.valor_iss, Decimal("0.00"))

        # Verify PDF was generated
        self.assertTrue(bool(nf.danfse_pdf))
        with nf.danfse_pdf.open("rb") as f:
            pdf_data = f.read()
        self.assertTrue(pdf_data.startswith(b"%PDF"))

    @patch("core.nfse.paulistana.client.NFeClient.testar_envio_lote_rps")
    def test_paulistana_debug_cancellation_marks_xml_and_pdf_as_cancelled(
        self, mock_testar_lote
    ):
        from core.services import (
            enviar_nfe_para_prefeitura,
            cancel_nota_fiscal,
            fetch_and_save_nfse_pdf,
        )
        from core.nfse.paulistana.provider import PaulistanaProvider
        from core.nfse.paulistana.schemas_v1.retorno_envio_lote_rps_v01 import (
            RetornoEnvioLoteRps as RetornoEnvioLoteRpsV1,
        )

        self.company.nfse_provider = "PAULISTANA"
        self.company.debug_mode = True
        self.company.save()

        self.invoice.document_number = 102
        self.invoice.codigo_servico_municipio = "02668"
        self.invoice.save()

        mock_testar_lote.return_value = (
            RetornoEnvioLoteRpsV1(
                cabecalho=RetornoEnvioLoteRpsV1.Cabecalho(sucesso=True)
            ),
            "<signedXml/>",
            "<retornoXml/>",
        )

        success = enviar_nfe_para_prefeitura(self.invoice)
        self.assertTrue(success)

        # Cancel the emitted Nota Fiscal
        result = cancel_nota_fiscal(self.invoice)
        self.assertTrue(result.sucesso)

        nf = NotaFiscal.objects.get(invoice=self.invoice)
        self.assertTrue(nf.is_canceled)
        self.assertIsNotNone(nf.cancelation_date)

        # Verify updated XML has StatusNFe = C and DataCancelamento
        with nf.xml_autorizacao.open("r") as f:
            canceled_xml = f.read()
        self.assertIn("<StatusNFe>C</StatusNFe>", canceled_xml)
        self.assertIn("<DataCancelamento>", canceled_xml)

        # Verify re-generated PDF
        provider = PaulistanaProvider()
        pdf_bytes = fetch_and_save_nfse_pdf(self.invoice, provider, force=True)
        self.assertIsNotNone(pdf_bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))


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


class InvoiceNfseDescriptionTests(TestCase):
    def setUp(self):
        from django.core.cache import cache

        cache.clear()
        self.user = User.objects.create_superuser("testadmin", "admin@test.com", "pass")
        self.client_http = HttpClient()
        self.client_http.force_login(self.user)
        self.company = CompanySettings.objects.create(
            company_name="Acme Corp Test",
            cnpj="12.345.678/0001-90",
            inscricao_municipal="12345678",
            opening_date=date(2024, 1, 1),
            email="test@test.com",
            next_document_number=1,
            document_series="1",
            nfse_provider="PAULISTANA",
            address_city_ibge="3550308",
            debug_mode=True,
        )
        self.foreign_client = Client.objects.create(
            name="Foreign Test Client LLC",
            address_country_code="US",
            country="United States",
            address_postal_code="10001",
            address_city="New York",
            address_neighborhood="Downtown",
            address_line1="123 Fifth Ave",
            email="client@example.com",
        )

    def test_default_nfse_description_on_invoice_and_template(self):
        inv = Invoice(client=self.foreign_client, invoice_number="INV-TEST-001", issue_date=date(2026, 8, 1))
        self.assertEqual(inv.nfse_description, "Descrição dos Serviços")

        tpl = InvoiceTemplate(name="Test Template", currency="USD")
        self.assertEqual(tpl.nfse_description, "Descrição dos Serviços")

    def test_invoice_template_nfse_description_and_htmx_endpoint(self):
        custom_text = "Serviços de consultoria para {{ client_name }}. Câmbio: {{ exchange_rate }}."
        template = InvoiceTemplate.objects.create(
            name="Global Client Template",
            currency="USD",
            bank_details="Routing: 12345",
            nfse_description=custom_text,
        )
        InvoiceTemplateItem.objects.create(
            template=template,
            description="Consulting",
            quantity=Decimal("1.00"),
            unit_price_foreign=Decimal("1000.00"),
        )
        response = self.client_http.get(f"/htmx/template-details/{template.id}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["nfse_description"], custom_text)

    def test_clone_invoice_preserves_nfse_description(self):
        original = Invoice.objects.create(
            client=self.foreign_client,
            invoice_number="INV-ORIG-NFSE",
            issue_date=date(2026, 9, 1),
            currency="USD",
            bank_details="Bank info",
            nfse_description="Custom NFSe description with {{ invoice_number }} and {{ exchange_rate }}",
        )
        InvoiceItem.objects.create(
            invoice=original,
            description="Service item",
            quantity=Decimal("1.00"),
            unit_price_foreign=Decimal("2000.00"),
        )
        response = self.client_http.post(f"/invoices/{original.id}/clone/")
        self.assertEqual(response.status_code, 302)

        cloned = (
            Invoice.objects.filter(client=self.foreign_client)
            .exclude(id=original.id)
            .first()
        )
        self.assertIsNotNone(cloned)
        self.assertEqual(cloned.nfse_description, original.nfse_description)

    def test_htmx_update_nfse_description_draft_success(self):
        invoice = Invoice.objects.create(
            client=self.foreign_client,
            invoice_number="INV-UPDATE-01",
            issue_date=date(2026, 9, 1),
            currency="USD",
            nfse_description="Old description",
            status="DRAFT",
        )
        new_desc = "Nova descrição com {{ currency }} {{ value_original }} e taxa {{ exchange_rate }}."
        response = self.client_http.post(
            f"/invoices/{invoice.id}/update-nfse-description/",
            {"nfse_description": new_desc},
        )
        self.assertEqual(response.status_code, 200)
        invoice.refresh_from_db()
        self.assertEqual(invoice.nfse_description, new_desc)
        self.assertIn(new_desc, response.content.decode())

    def test_htmx_update_nfse_description_validation_errors(self):
        invoice = Invoice.objects.create(
            client=self.foreign_client,
            invoice_number="INV-ERR-01",
            issue_date=date(2026, 9, 1),
            currency="USD",
            nfse_description="Initial valid description",
            status="DRAFT",
        )

        # Empty description fails
        resp_empty = self.client_http.post(
            f"/invoices/{invoice.id}/update-nfse-description/",
            {"nfse_description": "   "},
        )
        self.assertEqual(resp_empty.status_code, 400)
        self.assertIn("A descrição da NFS-e é obrigatória.", resp_empty.content.decode())
        invoice.refresh_from_db()
        self.assertEqual(invoice.nfse_description, "Initial valid description")

        # Invalid macro fails
        resp_macro = self.client_http.post(
            f"/invoices/{invoice.id}/update-nfse-description/",
            {"nfse_description": "Texto com macro errada {{ macro_que_nao_existe }}"},
        )
        self.assertEqual(resp_macro.status_code, 400)
        self.assertIn("Macro inválida: {{ macro_que_nao_existe }}", resp_macro.content.decode())
        invoice.refresh_from_db()
        self.assertEqual(invoice.nfse_description, "Initial valid description")

        # Non-draft invoice cannot be updated
        invoice.status = "FINALIZED"
        invoice.save()
        resp_finalized = self.client_http.post(
            f"/invoices/{invoice.id}/update-nfse-description/",
            {"nfse_description": "Tentativa em finalizada"},
        )
        self.assertEqual(resp_finalized.status_code, 400)

    def test_forms_validation_nfse_description(self):
        from core.forms import InvoiceForm, InvoiceTemplateForm

        # InvoiceForm validation
        form_empty = InvoiceForm(data={
            "client": str(self.foreign_client.id),
            "invoice_number": "INV-FORM-01",
            "issue_date": "2026-09-01",
            "currency": "USD",
            "bank_details": "",
            "nfse_description": "   ",
        })
        self.assertFalse(form_empty.is_valid())
        self.assertIn("nfse_description", form_empty.errors)

        form_invalid_macro = InvoiceForm(data={
            "client": str(self.foreign_client.id),
            "invoice_number": "INV-FORM-02",
            "issue_date": "2026-09-01",
            "currency": "USD",
            "bank_details": "",
            "nfse_description": "Serviço com {{ unknown_placeholder }}",
        })
        self.assertFalse(form_invalid_macro.is_valid())
        self.assertIn("nfse_description", form_invalid_macro.errors)

        form_valid = InvoiceForm(data={
            "client": str(self.foreign_client.id),
            "invoice_number": "INV-FORM-03",
            "issue_date": "2026-09-01",
            "currency": "USD",
            "bank_details": "",
            "nfse_description": "Serviço {{ invoice_number }} - taxa {{ exchange_rate }} - imposto {{ effective_tax_rate }}%",
            "codigo_tributacao_nacional": "010101",
            "codigo_servico_municipio": "001",
            "codigo_nbs": "115029000",
        })
        self.assertTrue(form_valid.is_valid(), form_valid.errors)

        # InvoiceTemplateForm validation
        tpl_form_empty = InvoiceTemplateForm(data={
            "name": "Template Empty",
            "currency": "USD",
            "bank_details": "",
            "nfse_description": "",
        })
        self.assertFalse(tpl_form_empty.is_valid())
        self.assertIn("nfse_description", tpl_form_empty.errors)

        tpl_form_invalid = InvoiceTemplateForm(data={
            "name": "Template Bad Macro",
            "currency": "USD",
            "bank_details": "",
            "nfse_description": "Serviço {{ bad_tag }}",
        })
        self.assertFalse(tpl_form_invalid.is_valid())
        self.assertIn("nfse_description", tpl_form_invalid.errors)

        tpl_form_valid = InvoiceTemplateForm(data={
            "name": "Template Good",
            "currency": "USD",
            "bank_details": "",
            "nfse_description": "Serviço válido {{ currency }} {{ exchange_rate }}",
            "codigo_tributacao_nacional": "010101",
            "codigo_servico_municipio": "001",
            "codigo_nbs": "115029000",
        })
        self.assertTrue(tpl_form_valid.is_valid(), tpl_form_valid.errors)

    def test_prepare_nf_data_with_templated_nfse_description(self):
        from core.services import _prepare_nf_data

        invoice = Invoice.objects.create(
            client=self.foreign_client,
            invoice_number="INV-PREPARE-01",
            issue_date=date(2026, 9, 15),
            currency="USD",
            exchange_rate_to_brl=Decimal("5.0000"),
            nfse_description=(
                "Prestação de serviços no exterior.\n"
                "Ref: {{ prev_month_start }} até {{ prev_month_end }}.\n"
                "Valor em moeda estrangeira: {{ currency }} {{ value_original }}.\n"
                "Câmbio: {{ exchange_rate }}.\n"
                "Valor em BRL: R$ {{ value_brl }}.\n"
                "Alíquota efetiva estimada: {{ effective_tax_rate }}%."
            ),
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            description="Software Engineering",
            quantity=Decimal("2.00"),
            unit_price_foreign=Decimal("1000.00"),
        )
        amount_brl, desc, eff_rate = _prepare_nf_data(invoice)
        self.assertEqual(amount_brl, Decimal("10000.00"))
        self.assertIn("Ref: 01/08/2026 até 31/08/2026.", desc)
        self.assertIn("Valor em moeda estrangeira: USD 2.000,00.", desc)
        self.assertIn("Câmbio: 5,0000.", desc)
        self.assertIn("Valor em BRL: R$ 10.000,00.", desc)
        self.assertIn(f"Alíquota efetiva estimada: {eff_rate:.2f}%".replace(".", ","), desc)

        # Ensure raw invoice.nfse_description is unmutated
        invoice.refresh_from_db()
        self.assertIn("{{ exchange_rate }}", invoice.nfse_description)

    def test_invoice_create_get_renders_template_with_and_without_templates(self):
        # Case 1: templates exist
        InvoiceTemplate.objects.create(name="Tpl 1", currency="USD")
        resp = self.client_http.get("/invoices/new/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn('<select id="template-selector"', resp.content.decode())
        self.assertIn("macroAccordion", resp.content.decode())

        # Case 2: no templates
        InvoiceTemplate.objects.all().delete()
        resp_no_tpl = self.client_http.get("/invoices/new/")
        self.assertEqual(resp_no_tpl.status_code, 200)
        self.assertNotIn('<select id="template-selector"', resp_no_tpl.content.decode())
        self.assertIn("macroAccordion", resp_no_tpl.content.decode())

    def test_invoice_template_create_get_renders_template(self):
        resp = self.client_http.get("/templates/invoice/new/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("macroAccordion", resp.content.decode())
        self.assertIn("nfse_description", resp.content.decode())


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

    @patch("core.nfse.nacional.provider.NacionalProvider.consultar_dfe_por_nsu")
    @patch("core.nfse.nacional.provider.NacionalProvider.baixar_pdf")
    def test_import_nfses_nacional(self, mock_pdf, mock_consultar):
        import gzip
        import base64
        from core.services.nfse_services import import_nfses
        from core.models import NotaFiscalEvent

        mock_pdf.return_value = b"%PDF mock"

        # CNPJ of self.company is "00.000.000/0001-00" -> cleaned is "00000000000100"
        # Chave de acesso length 50: cMun(7) + ambGer(1='2') + tpEmis(1='1') + CNPJ(14) + rest(27)
        chave_nfse = "35503082100000000000100000000000000000000000000001"
        xml_nfse = f"""<NFSe xmlns="http://www.sped.fazenda.gov.br/nfse" versao="1.00">
  <infNFSe Id="NFS{chave_nfse}">
    <ambGer>2</ambGer>
    <tpAmb>2</tpAmb>
    <nNFSe>123</nNFSe>
    <cVerif>ABCDEF12</cVerif>
    <dhProc>2026-10-17T10:00:00-03:00</dhProc>
    <DPS xmlns="http://www.sped.fazenda.gov.br/nfse">
      <infDPS Id="DPS000000000123456780001994242000000000000005">
        <nDPS>5</nDPS>
        <serie>4242</serie>
        <dCompet>2026-10-17</dCompet>
        <prest>
          <CNPJ>00000000000100</CNPJ>
        </prest>
        <valores>
          <vServPrest>
            <vServ>1000.00</vServ>
          </vServPrest>
        </valores>
      </infDPS>
    </DPS>
  </infNFSe>
</NFSe>"""
        b64_nfse = base64.b64encode(gzip.compress(xml_nfse.encode("utf-8"))).decode("utf-8")

        xml_evento = f"""<evento xmlns="http://www.sped.fazenda.gov.br/nfse" versao="1.01">
  <infEvento Id="EVT{chave_nfse}1011011">
    <tpAmb>2</tpAmb>
    <dhEvento>2026-10-17T11:00:00-03:00</dhEvento>
    <tpEvento>101101</tpEvento>
    <nSeqEvento>1</nSeqEvento>
    <chNFSe>{chave_nfse}</chNFSe>
    <e101101>
      <xDesc>Cancelamento de NFS-e</xDesc>
      <cMotivo>1</cMotivo>
      <xMotivo>Erro na emissao</xMotivo>
    </e101101>
  </infEvento>
</evento>"""
        b64_evento = base64.b64encode(gzip.compress(xml_evento.encode("utf-8"))).decode("utf-8")

        # Third party tomador document that must NOT create a NotaFiscal
        chave_third_party = "35503089999999999999990000000000000000000000000002"

        mock_consultar.return_value = (
            [
                {
                    "NSU": 10,
                    "ChaveAcesso": chave_nfse,
                    "TipoDocumento": "NFSE",
                    "TipoEvento": None,
                    "ArquivoXml": b64_nfse,
                },
                {
                    "NSU": 11,
                    "ChaveAcesso": chave_nfse,
                    "TipoDocumento": "EVENTO",
                    "TipoEvento": "CANCELAMENTO",
                    "ArquivoXml": b64_evento,
                },
                {
                    "NSU": 12,
                    "ChaveAcesso": chave_third_party,
                    "TipoDocumento": "NFSE",
                    "TipoEvento": None,
                    "ArquivoXml": b64_nfse,
                },
            ],
            12,
        )

        self.company.document_series = "4242"
        self.company.next_document_number = 1
        self.company.last_adn_nsu = 0
        self.company.save()

        count, msg = import_nfses("NACIONAL")
        self.assertEqual(count, 2)  # 1 NF + 1 event
        self.assertIn("Importação concluída", msg)

        # Check NotaFiscal was created and marked canceled
        nf = NotaFiscal.objects.get(chave_acesso_nacional=chave_nfse)
        self.assertEqual(nf.nf_number, "123")
        self.assertTrue(nf.is_canceled)
        self.assertEqual(nf.amount_brl, Decimal("1000.00"))

        # Check event was created
        evt = NotaFiscalEvent.objects.get(nota_fiscal=nf)
        self.assertEqual(evt.codigo_evento, "101101")
        self.assertEqual(evt.nsu, 11)
        self.assertTrue(evt.is_cancellation)

        # Third party NF should NOT be created
        self.assertFalse(NotaFiscal.objects.filter(chave_acesso_nacional=chave_third_party).exists())

        # Check CompanySettings updated: next_document_number advanced to 6 (since DPS was 5), last_adn_nsu to 12
        self.company.refresh_from_db()
        self.assertEqual(self.company.last_adn_nsu, 12)
        self.assertEqual(self.company.next_document_number, 6)

    @patch("core.nfse.nacional.provider.NacionalProvider.buscar_nfse_por_chave")
    def test_sync_nota_fiscal_nacional_events(self, mock_buscar):
        from core.services.nfse_services import sync_nota_fiscal
        from core.models import NotaFiscalEvent
        from django.utils import timezone

        invoice = Invoice.objects.create(
            client=self.client_obj,
            invoice_number="INV-SYNC-NAC",
            issue_date=date(2026, 9, 1),
            currency="USD",
            status="FINALIZED",
        )
        nf = NotaFiscal.objects.create(
            invoice=invoice,
            nf_number="456",
            chave_acesso_nacional="35503080000000000001000000000000000000000000000045",
            issue_date=date(2026, 9, 1),
            amount_brl=Decimal("800.00"),
            is_canceled=False,
        )

        now = timezone.now()
        mock_buscar.return_value = {
            "nf_number": "456",
            "verification_code": "",
            "chave_acesso_nacional": nf.chave_acesso_nacional,
            "amount_brl": "800.00",
            "description": "Consultoria",
            "issue_date": date(2026, 9, 1),
            "is_canceled": True,
            "cancelation_date": now,
            "events": [
                {
                    "nsu": 99,
                    "id_evento": "EVT123",
                    "tipo_evento": "CANCELAMENTO",
                    "codigo_evento": "101101",
                    "n_seq_evento": 1,
                    "dh_evento": now,
                    "motivo": "Cancelado externamente",
                    "is_cancellation": True,
                    "raw_xml": "<evento/>",
                }
            ],
            "raw_xml": "<nfse/>",
        }

        with patch("core.services.nfse_services.fetch_and_save_nfse_pdf"):
            success, msg = sync_nota_fiscal(nf)
            self.assertTrue(success)
            self.assertIn("identificada como CANCELADA", msg)

        nf.refresh_from_db()
        self.assertTrue(nf.is_canceled)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "CANCELED")
        self.assertTrue(NotaFiscalEvent.objects.filter(nota_fiscal=nf, codigo_evento="101101").exists())

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


class CompanySettingsPhoneNumberTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("admin_phone", "admin_phone@test.com", "pass")
        self.client_http = HttpClient()
        self.client_http.force_login(self.user)
        self.company = CompanySettings.objects.create(
            company_name="Acme Tech Ltda",
            cnpj="12.345.678/0001-95",
            opening_date=date(2024, 1, 1),
            inscricao_municipal="123456",
            email="tech@example.com",
            phone_number="+55 11 98765-4321",
            address_line1="Main St",
            address_city_ibge="3550308",
            nfse_provider="PAULISTANA",
            next_document_number=1,
            document_series="1",
        )

    def test_phone_number_and_property_alias(self):
        self.assertEqual(self.company.phone_number, "+55 11 98765-4321")
        self.assertEqual(self.company.phoneNumber, "+55 11 98765-4321")

        # Test setter alias
        self.company.phoneNumber = "+55 11 91234-5678"
        self.company.save()
        self.company.refresh_from_db()
        self.assertEqual(self.company.phone_number, "+55 11 91234-5678")
        self.assertEqual(self.company.phoneNumber, "+55 11 91234-5678")

    def test_company_settings_form_renders_and_saves_phone_number(self):
        resp = self.client_http.get(reverse("company_settings"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'name="phone_number"')
        self.assertContains(resp, "Telefone")

        data = {
            "company_name": self.company.company_name,
            "cnpj": self.company.cnpj,
            "opening_date": self.company.opening_date.strftime("%d/%m/%Y"),
            "inscricao_municipal": self.company.inscricao_municipal,
            "email": self.company.email,
            "phone_number": "+55 11 99999-0000",
            "address_line1": self.company.address_line1,
            "address_city_ibge": self.company.address_city_ibge,
            "nfse_provider": self.company.nfse_provider,
            "next_document_number": self.company.next_document_number,
            "document_series": self.company.document_series,
            "auto_invoice_hour": 9,
        }
        post_resp = self.client_http.post(reverse("company_settings"), data=data)
        self.assertEqual(post_resp.status_code, 302)

        self.company.refresh_from_db()
        self.assertEqual(self.company.phone_number, "+55 11 99999-0000")
        self.assertEqual(self.company.phoneNumber, "+55 11 99999-0000")

    def test_invoice_pdf_includes_company_phone_number(self):
        from core.pdf_service import generate_pdf_bytes

        client = Client.objects.create(
            name="Foreign Client LLC",
            address_neighborhood="Downtown",
            address_city="New York",
            address_country_code="US",
        )
        invoice = Invoice.objects.create(
            client=client,
            invoice_number="INV-PHONE-001",
            issue_date=date.today(),
            currency="USD",
            status="DRAFT",
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            description="Consulting services",
            quantity=Decimal("1.00"),
            unit_price_foreign=Decimal("1000.00"),
        )
        invoice.status = "FINALIZED"
        invoice.save()
        pdf_bytes = generate_pdf_bytes(invoice, self.company)
        self.assertIsNotNone(pdf_bytes)
        self.assertTrue(len(pdf_bytes) > 0)


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


class ProxyHeaderAuthTests(TestCase):
    def setUp(self):
        # Ensure tests are not blocked by host environment's PROXY_AUTH_TRUSTED_PROXIES
        self._settings_ctx = override_settings(PROXY_AUTH_TRUSTED_PROXIES=[])
        self._settings_ctx.enable()
        self.addCleanup(self._settings_ctx.disable)

        self.user = User.objects.create_user(
            username="existing_testuser",
            email="existing@example.com",
            password="testpassword123",
        )
        CompanySettings.objects.create(
            company_name="Test Company Ltd",
            cnpj="00.000.000/0001-91",
            email="test@example.com",
            opening_date=date(2024, 1, 1),
        )

    def test_parse_groups_header_variations(self):
        from core.backends import parse_groups_header

        # Comma-separated
        self.assertEqual(
            parse_groups_header("group1, group2, group3"),
            ["group1", "group2", "group3"],
        )
        # Semicolon-separated
        self.assertEqual(
            parse_groups_header("group1; group2"),
            ["group1", "group2"],
        )
        # JSON array
        self.assertEqual(
            parse_groups_header('["group_a", "group_b"]'),
            ["group_a", "group_b"],
        )
        # Empty and None
        self.assertEqual(parse_groups_header(""), [])
        self.assertEqual(parse_groups_header(None), [])
        self.assertEqual(parse_groups_header("   "), [])
        # Deduplication and max length
        long_name = "x" * 200
        parsed = parse_groups_header(f"{long_name}, {long_name}")
        self.assertEqual(len(parsed), 1)
        self.assertEqual(len(parsed[0]), 150)

    def test_backend_authenticate_existing_user(self):
        from core.backends import ProxyHeaderBackend

        backend = ProxyHeaderBackend()
        rf = RequestFactory()
        request = rf.get("/")

        user = backend.authenticate(
            request,
            remote_user="existing_testuser",
            email="updated_email@example.com",
            groups=["test_group_alpha"],
        )
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "existing_testuser")
        self.assertEqual(user.email, "updated_email@example.com")
        self.assertTrue(user.groups.filter(name="test_group_alpha").exists())

    def test_backend_authenticate_creates_new_user(self):
        from core.backends import ProxyHeaderBackend

        backend = ProxyHeaderBackend()
        rf = RequestFactory()
        request = rf.get("/")

        user = backend.authenticate(
            request,
            remote_user="synthetic_new_user",
            email="synthetic_new@example.com",
            groups=["group1", "group2"],
        )
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "synthetic_new_user")
        self.assertEqual(user.email, "synthetic_new@example.com")
        self.assertEqual(user.groups.count(), 2)

    def test_backend_auto_create_disabled(self):
        from core.backends import ProxyHeaderBackend

        backend = ProxyHeaderBackend()
        rf = RequestFactory()
        request = rf.get("/")

        with override_settings(PROXY_AUTH_AUTO_CREATE_USER=False):
            user = backend.authenticate(
                request,
                remote_user="non_existent_user",
                email="none@example.com",
            )
            self.assertIsNone(user)

    def test_backend_staff_and_superuser_groups(self):
        from core.backends import ProxyHeaderBackend

        backend = ProxyHeaderBackend()
        rf = RequestFactory()
        request = rf.get("/")

        with override_settings(
            PROXY_AUTH_STAFF_GROUPS=["staff_role_group"],
            PROXY_AUTH_SUPERUSER_GROUPS=["admin_role_group"],
        ):
            # Staff group grants is_staff
            u1 = backend.authenticate(
                request,
                remote_user="staff_test_user",
                groups=["staff_role_group"],
            )
            self.assertTrue(u1.is_staff)
            self.assertFalse(u1.is_superuser)

            # Superuser group grants both is_staff and is_superuser
            u2 = backend.authenticate(
                request,
                remote_user="admin_test_user",
                groups=["admin_role_group"],
            )
            self.assertTrue(u2.is_staff)
            self.assertTrue(u2.is_superuser)

    def test_middleware_skips_login_screen_for_incoming_headers(self):
        # Requesting /accounts/login/ with proxy headers should redirect to /
        resp = self.client.get(
            "/accounts/login/",
            HTTP_X_AUTH_REQUEST_PREFERRED_USERNAME="existing_testuser",
            HTTP_X_AUTH_REQUEST_EMAIL="existing@example.com",
            HTTP_X_AUTH_REQUEST_GROUPS="test_group",
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, "/")

    def test_middleware_skips_login_screen_with_next_param(self):
        # Requesting /accounts/login/?next=/invoices/ should redirect to /invoices/
        resp = self.client.get(
            "/accounts/login/?next=/invoices/",
            HTTP_X_AUTH_REQUEST_PREFERRED_USERNAME="existing_testuser",
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, "/invoices/")

    def test_middleware_access_protected_view_directly(self):
        # Accessing dashboard directly with proxy headers should authenticate and succeed
        resp = self.client.get(
            "/",
            HTTP_X_AUTH_REQUEST_PREFERRED_USERNAME="existing_testuser",
        )
        self.assertEqual(resp.status_code, 200)

    def test_middleware_without_headers_shows_login_screen(self):
        # Accessing /accounts/login/ without proxy headers shows the standard login form
        resp = self.client.get("/accounts/login/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Acesso ao Sistema")

    def test_middleware_user_switch(self):
        # First request as user 1
        resp1 = self.client.get(
            "/",
            HTTP_X_AUTH_REQUEST_PREFERRED_USERNAME="existing_testuser",
        )
        self.assertEqual(resp1.status_code, 200)

        # Second request with a different user header switches the session
        User.objects.create_user(username="second_testuser")
        resp2 = self.client.get(
            "/",
            HTTP_X_AUTH_REQUEST_PREFERRED_USERNAME="second_testuser",
        )
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(
            self.client.session["_auth_user_id"],
            str(User.objects.get(username="second_testuser").pk),
        )

    def test_logout_redirects_to_configured_url(self):
        # Login first
        self.client.force_login(self.user)
        logout_target = "https://auth.example.com/oauth2/sign_out?rd=https://sso.example.com/ui/logout"
        with override_settings(LOGOUT_REDIRECT_URL=logout_target):
            resp = self.client.post("/accounts/logout/")
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.url, logout_target)

    def test_is_trusted_proxy_helper(self):
        from core.backends import is_trusted_proxy

        cidrs = ["127.0.0.1/32", "10.0.0.0/8", "172.16.0.0/12", "192.168.1.50"]
        self.assertTrue(is_trusted_proxy("127.0.0.1", cidrs))
        self.assertTrue(is_trusted_proxy("10.50.2.1", cidrs))
        self.assertTrue(is_trusted_proxy("172.19.0.1", cidrs))
        self.assertTrue(is_trusted_proxy("192.168.1.50", cidrs))
        self.assertFalse(is_trusted_proxy("192.168.1.51", cidrs))
        self.assertFalse(is_trusted_proxy("203.0.113.1", cidrs))
        self.assertFalse(is_trusted_proxy("", cidrs))
        self.assertFalse(is_trusted_proxy("invalid-ip", cidrs))
        self.assertFalse(is_trusted_proxy("10.0.0.1", []))

    def test_middleware_trusted_proxy_cidr_enforcement(self):
        with override_settings(PROXY_AUTH_TRUSTED_PROXIES=["10.0.0.0/8"]):
            # Allowed from trusted CIDR
            resp_trusted = self.client.get(
                "/",
                REMOTE_ADDR="10.2.3.4",
                HTTP_X_AUTH_REQUEST_PREFERRED_USERNAME="existing_testuser",
            )
            self.assertEqual(resp_trusted.status_code, 200)

            # Untrusted IP should have headers ignored and redirect to login
            self.client.logout()
            resp_untrusted = self.client.get(
                "/",
                REMOTE_ADDR="198.51.100.99",
                HTTP_X_AUTH_REQUEST_PREFERRED_USERNAME="existing_testuser",
            )
            self.assertEqual(resp_untrusted.status_code, 302)
            self.assertTrue(resp_untrusted.url.startswith("/accounts/login/"))


class NfseMultiProviderAndReliabilityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("admin_multi", "admin_multi@test.com", "pass")
        self.client.force_login(self.user)
        self.company = CompanySettings.objects.create(
            company_name="Acme Tech Ltda",
            cnpj="12.345.678/0001-95",
            opening_date=date(2024, 1, 1),
            inscricao_municipal="123456",
            email="tech@example.com",
            address_line1="Main St",
            address_neighborhood="Centro",
            address_city_ibge="3550308",
            nfse_provider="NACIONAL",
            next_document_number=1,
            document_series="1",
        )
        self.client_obj = Client.objects.create(
            name="Global Client Inc",
            address_line1="Market St",
            address_number="100",
            address_neighborhood="Downtown",
            address_city="San Francisco",
            address_state_province="CA",
            country="United States",
            address_country_code="US",
            email="accounting@globalclient.com",
        )

    def test_notafiscal_number_collision_coexistence(self):
        from django.db import IntegrityError, transaction

        # Create Paulistana NF #2
        nf_paulistana = NotaFiscal.objects.create(
            nf_number="2",
            issue_date=date(2026, 1, 15),
            amount_brl=Decimal("5000.00"),
            description="Paulistana service",
            verification_code="ABCDEF",
            chave_acesso_nacional="35503081123456780001950000000000000222061168275466",
        )
        self.assertEqual(nf_paulistana.provider_type, "PAULISTANA")

        # Create Nacional NF #2 with same number
        nf_nacional = NotaFiscal.objects.create(
            nf_number="2",
            issue_date=date(2026, 10, 16),
            amount_brl=Decimal("15000.00"),
            description="Nacional service",
            verification_code="",
            chave_acesso_nacional="35503082123456780001950000000000000226100822290116",
        )
        self.assertEqual(nf_nacional.provider_type, "NACIONAL")

        # Confirm both exist
        self.assertEqual(NotaFiscal.objects.filter(nf_number="2").count(), 2)

        # Confirm duplicate non-empty chave_acesso_nacional is blocked by constraint
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                NotaFiscal.objects.create(
                    nf_number="999",
                    issue_date=date(2026, 10, 16),
                    amount_brl=Decimal("1000.00"),
                    description="Duplicate chave",
                    chave_acesso_nacional="35503082123456780001950000000000000226100822290116",
                )

    def test_provider_type_resolution(self):
        # 8th character is ambGer: '2' = NACIONAL, '1' = PAULISTANA
        nf_nac = NotaFiscal(
            nf_number="10",
            issue_date=date.today(),
            amount_brl=Decimal("100.00"),
            chave_acesso_nacional="35503082000000000000000000000000000000000000000000",
        )
        self.assertEqual(nf_nac.provider_type, "NACIONAL")

        nf_paul = NotaFiscal(
            nf_number="11",
            issue_date=date.today(),
            amount_brl=Decimal("100.00"),
            chave_acesso_nacional="35503081000000000000000000000000000000000000000000",
        )
        self.assertEqual(nf_paul.provider_type, "PAULISTANA")

        nf_code_only = NotaFiscal(
            nf_number="12",
            issue_date=date.today(),
            amount_brl=Decimal("100.00"),
            verification_code="XYZ123",
        )
        self.assertEqual(nf_code_only.provider_type, "PAULISTANA")

    def test_transient_error_classification(self):
        import requests
        from core.tasks.nfse_tasks import _is_transient_error

        # Transient: connection error, timeout
        self.assertTrue(_is_transient_error(requests.ConnectionError("Network drop")))
        self.assertTrue(_is_transient_error(requests.Timeout("Timed out")))

        # Transient: HTTP 500, 502, 503, 504
        resp_503 = requests.Response()
        resp_503.status_code = 503
        err_503 = requests.HTTPError(response=resp_503)
        self.assertTrue(_is_transient_error(err_503))

        # Non-transient: HTTP 400, 422, 404
        resp_400 = requests.Response()
        resp_400.status_code = 400
        err_400 = requests.HTTPError(response=resp_400)
        self.assertFalse(_is_transient_error(err_400))

        resp_422 = requests.Response()
        resp_422.status_code = 422
        err_422 = requests.HTTPError(response=resp_422)
        self.assertFalse(_is_transient_error(err_422))

        # Non-transient: ValueError, local validation errors
        self.assertFalse(_is_transient_error(ValueError("Invalid CPF/CNPJ")))

        # Transient: prefeitura / Sefin temporary outages & async processing
        self.assertTrue(_is_transient_error(Exception("Prefeitura fora do ar")))
        self.assertTrue(_is_transient_error(Exception("Serviço temporariamente indisponível")))
        self.assertTrue(_is_transient_error(Exception("PDF not ready yet for NF 100")))
        self.assertTrue(_is_transient_error(Exception("NFS-e batch submitted but not processed yet. Waiting for prefeitura.")))
        self.assertTrue(_is_transient_error(Exception("Falha na comunicação com Sefin Nacional (HTTP 502)")))

        # Deterministic: fiscal code validation, timeout > 24h, certificate/signature
        self.assertFalse(_is_transient_error(Exception("Código de Serviço do Município ('02668') possui mais de 3 dígitos.")))
        self.assertFalse(_is_transient_error(Exception("NFS-e 5 foi autorizada há mais de 24 horas e não pode ser cancelada.")))
        self.assertFalse(_is_transient_error(Exception("Rejeição: Certificado Inválido.")))
        self.assertFalse(_is_transient_error(Exception("Assinatura digital inválida: CNPJ do certificado não confere com prestador.")))
        self.assertFalse(_is_transient_error(Exception("NFS-e já cancelada.")))
        self.assertFalse(_is_transient_error(Exception("CompanySettings not found.")))

    def test_cancel_invoice_task_deterministic_failure(self):
        from unittest.mock import patch
        from core.tasks.invoices_tasks import cancel_invoice_task
        from celery.exceptions import Retry

        client = Client.objects.create(name="Cancel Test Client", email="cancel@example.com")
        inv = Invoice.objects.create(
            client=client,
            currency="USD",
            issue_date=date.today(),
            document_number=888,
            status="PROCESSING",
        )
        nf = NotaFiscal.objects.create(
            invoice=inv,
            nf_number="888",
            issue_date=date.today(),
            amount_brl=Decimal("1000.00"),
            description="Test",
        )

        # Mock cancel_nota_fiscal to raise deterministic error
        with patch("core.services.nfse_services.cancel_nota_fiscal", side_effect=Exception("NFS-e 888 foi autorizada há mais de 24 horas e não pode ser cancelada.")):
            with self.assertRaises(Exception) as ctx:
                cancel_invoice_task.apply(args=[inv.id], throw=True)
            self.assertIn("há mais de 24 horas", str(ctx.exception))
            self.assertNotIsInstance(ctx.exception, Retry)

        inv.refresh_from_db()
        self.assertEqual(inv.status, "FINALIZED")
        self.assertEqual(inv.task_id, "")
        self.assertEqual(inv.task_retry_count, 0)

    def test_cancel_invoice_task_transient_retry(self):
        import requests
        from unittest.mock import patch
        from core.tasks.invoices_tasks import cancel_invoice_task
        from celery.exceptions import Retry

        client = Client.objects.create(name="Retry Test Client", email="retry@example.com")
        inv = Invoice.objects.create(
            client=client,
            currency="USD",
            issue_date=date.today(),
            document_number=889,
            status="PROCESSING",
        )
        nf = NotaFiscal.objects.create(
            invoice=inv,
            nf_number="889",
            issue_date=date.today(),
            amount_brl=Decimal("1000.00"),
            description="Test",
        )

        with patch("core.services.nfse_services.cancel_nota_fiscal", side_effect=requests.ConnectionError("Connection timed out")):
            with self.assertRaises(Retry):
                cancel_invoice_task.apply(args=[inv.id], throw=True)

        inv.refresh_from_db()
        self.assertEqual(inv.task_retry_count, 1)

    def test_cancel_nfse_standalone_deterministic_failure(self):
        from unittest.mock import patch
        from core.tasks.nfse_tasks import cancel_nfse_standalone_task
        from celery.exceptions import Retry

        nf = NotaFiscal.objects.create(
            nf_number="890",
            issue_date=date.today(),
            amount_brl=Decimal("1000.00"),
            description="Standalone Test",
        )

        with patch("core.services.nfse_services.cancel_nota_fiscal", side_effect=Exception("CompanySettings not found.")):
            with self.assertRaises(Exception) as ctx:
                cancel_nfse_standalone_task.apply(args=[nf.id], throw=True)
            self.assertIn("CompanySettings not found", str(ctx.exception))
            self.assertNotIsInstance(ctx.exception, Retry)

    def test_email_invoice_task_deterministic_failure(self):
        import smtplib
        from unittest.mock import patch
        from core.tasks.invoices_tasks import email_invoice_task
        from celery.exceptions import Retry

        client = Client.objects.create(name="Email Test Client", email="email@example.com")
        inv = Invoice.objects.create(
            client=client,
            currency="USD",
            issue_date=date.today(),
            document_number=891,
            status="PROCESSING",
        )

        with patch("core.tasks.invoices_tasks.send_email_with_debug", side_effect=smtplib.SMTPAuthenticationError(535, b"Authentication failed")):
            with self.assertRaises(smtplib.SMTPAuthenticationError):
                email_invoice_task.apply(args=[inv.id], kwargs={"send_to_client": True}, throw=True)

    def test_email_invoice_task_transient_retry(self):
        import smtplib
        from unittest.mock import patch
        from core.tasks.invoices_tasks import email_invoice_task
        from celery.exceptions import Retry

        client = Client.objects.create(name="Email Test Client", email="email@example.com")
        inv = Invoice.objects.create(
            client=client,
            currency="USD",
            issue_date=date.today(),
            document_number=892,
            status="PROCESSING",
        )

        with patch("core.tasks.invoices_tasks.send_email_with_debug", side_effect=smtplib.SMTPServerDisconnected("Connection unexpectedly closed")):
            with self.assertRaises(Retry):
                email_invoice_task.apply(args=[inv.id], kwargs={"send_to_client": True}, throw=True)

    def test_fetch_nfse_pdf_task_deterministic_failure(self):
        from unittest.mock import patch
        from core.tasks.nfse_tasks import fetch_nfse_pdf_task
        from celery.exceptions import Retry

        nf = NotaFiscal.objects.create(
            nf_number="893",
            issue_date=date.today(),
            amount_brl=Decimal("1000.00"),
            description="PDF Test",
        )

        with patch("core.services.nfse_services.fetch_and_save_nfse_pdf", side_effect=Exception("Rejeição: Certificado Inválido.")):
            with self.assertRaises(Exception) as ctx:
                fetch_nfse_pdf_task.apply(args=[None, nf.id], throw=True)
            self.assertIn("Certificado Inválido", str(ctx.exception))
            self.assertNotIsInstance(ctx.exception, Retry)

    def test_fetch_nfse_pdf_task_transient_retry(self):
        from unittest.mock import patch
        from core.tasks.nfse_tasks import fetch_nfse_pdf_task
        from celery.exceptions import Retry

        nf = NotaFiscal.objects.create(
            nf_number="894",
            issue_date=date.today(),
            amount_brl=Decimal("1000.00"),
            description="PDF Test",
        )

        with patch("core.services.nfse_services.fetch_and_save_nfse_pdf", return_value=None):
            with self.assertRaises(Retry):
                fetch_nfse_pdf_task.apply(args=[None, nf.id], throw=True)

    def test_nfse_list_and_detail_views(self):
        # Create Paulistana NF
        nf_p = NotaFiscal.objects.create(
            nf_number="50",
            issue_date=date(2026, 5, 1),
            amount_brl=Decimal("2000.00"),
            description="Service P",
            verification_code="VERIF1",
            chave_acesso_nacional="355030811234567800019500000000000000502061168275466",
            is_canceled=False,
        )

        # Create Nacional NF
        inv = Invoice.objects.create(
            client=self.client_obj,
            invoice_number="INV-VIEW-001",
            issue_date=date(2026, 10, 1),
            currency="USD",
            status="FINALIZED",
        )
        nf_n = NotaFiscal.objects.create(
            invoice=inv,
            nf_number="50",
            issue_date=date(2026, 10, 1),
            amount_brl=Decimal("8000.00"),
            description="Service N",
            chave_acesso_nacional="3550308212345678000195000000000000005026100822290116",
            is_canceled=True,
        )

        # Create NfseLog
        from core.models import NfseLog

        NfseLog.objects.create(
            invoice=inv,
            nota_fiscal=nf_n,
            payload_enviado="<DPS>sample</DPS>",
            payload_retorno="<NFSe>sample</NFSe>",
            origem="Test Runner",
        )

        # Test list view with provider filter
        resp_all = self.client.get(reverse("nfse_list"))
        self.assertEqual(resp_all.status_code, 200)
        self.assertContains(resp_all, "Sefin Nacional")
        self.assertContains(resp_all, "Paulistana")

        resp_nac = self.client.get(reverse("nfse_list") + "?provider=NACIONAL")
        self.assertEqual(resp_nac.status_code, 200)
        self.assertEqual(len(resp_nac.context["notas"]), 1)
        self.assertEqual(resp_nac.context["notas"][0].id, nf_n.id)

        resp_paul = self.client.get(reverse("nfse_list") + "?provider=PAULISTANA")
        self.assertEqual(resp_paul.status_code, 200)
        self.assertEqual(len(resp_paul.context["notas"]), 1)
        self.assertEqual(resp_paul.context["notas"][0].id, nf_p.id)

        # Test status filter
        resp_act = self.client.get(reverse("nfse_list") + "?status=ACTIVE")
        self.assertEqual(resp_act.status_code, 200)
        self.assertEqual(len(resp_act.context["notas"]), 1)
        self.assertEqual(resp_act.context["notas"][0].id, nf_p.id)

        resp_canc = self.client.get(reverse("nfse_list") + "?status=CANCELED")
        self.assertEqual(resp_canc.status_code, 200)
        self.assertEqual(len(resp_canc.context["notas"]), 1)
        self.assertEqual(resp_canc.context["notas"][0].id, nf_n.id)

        # Test detail view
        resp_detail = self.client.get(reverse("nfse_detail", args=[nf_n.id]))
        self.assertEqual(resp_detail.status_code, 200)
        self.assertContains(resp_detail, "Sefin Nacional")
        self.assertContains(resp_detail, "Cancelada")
        self.assertContains(resp_detail, "Histórico de Transmissão e Logs")
        self.assertContains(resp_detail, "&lt;DPS&gt;sample&lt;/DPS&gt;")

    def test_paulistana_cancel_idempotent_when_already_canceled_externally(self):
        from unittest.mock import MagicMock
        from core.nfse.paulistana.provider import PaulistanaProvider
        from core.services.nfse_services import cancel_nota_fiscal
        from django.utils import timezone

        nf = NotaFiscal.objects.create(
            nf_number="12345",
            issue_date=date.today(),
            amount_brl=Decimal("1500.00"),
            description="Paulistana already canceled externally",
            verification_code="VALID99",
            chave_acesso_nacional="3550308112345678000195000000000000123452061168275466",
            is_canceled=False,
        )

        provider = PaulistanaProvider()
        now = timezone.now()
        mock_client = MagicMock()
        mock_client.cancelar_nfe.return_value = (
            False,
            "",
            "<retorno/>",
            ["Erro: 1206 - Nota Fiscal já cancelada."],
        )

        with patch.object(provider, "_get_client", return_value=(mock_client, "123456")):
            with patch.object(
                provider,
                "buscar_nfse_por_numero",
                return_value={
                    "is_canceled": True,
                    "cancelation_date": now,
                    "raw_xml": "<NFe><StatusNFe>C</StatusNFe></NFe>",
                },
            ):
                with patch("core.services.nfse_services.fetch_and_save_nfse_pdf"):
                    with patch("core.nfse.provider_factory.get_provider", return_value=provider):
                        with patch.object(CompanySettings, "load") as mock_load:
                            comp = CompanySettings.objects.get(id=self.company.id)
                            comp.debug_mode = False
                            mock_load.return_value = comp
                            result = cancel_nota_fiscal(nf)

        self.assertTrue(result.sucesso)
        nf.refresh_from_db()
        self.assertTrue(nf.is_canceled)
        self.assertEqual(nf.cancelation_date, now)

    def test_nacional_cancel_idempotent_when_already_canceled_externally(self):
        from unittest.mock import MagicMock
        from contextlib import contextmanager
        from lxml import etree
        from core.nfse.nacional.provider import NacionalProvider
        from core.services.nfse_services import cancel_nota_fiscal
        from django.utils import timezone

        nf = NotaFiscal.objects.create(
            nf_number="54321",
            issue_date=date.today(),
            amount_brl=Decimal("2500.00"),
            description="Nacional already canceled externally",
            chave_acesso_nacional="35503082123456780001950000000000005432126100822290116",
            is_canceled=False,
        )

        provider = NacionalProvider()
        now = timezone.now()

        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = "Sefin HTTP 400: Pedido de cancelamento rejeitado"

        @contextmanager
        def mock_temp_cert(cert, key):
            yield "/tmp/fake.pem"

        dummy_elem = etree.Element("root")

        with patch.object(provider, "_get_cert_pems", return_value=("fake_key", "fake_cert")):
            with patch("core.nfse.nacional.provider.XMLSigner.sign", return_value=dummy_elem):
                with patch("core.nfse.nacional.provider._temp_cert_file", side_effect=mock_temp_cert):
                    with patch("core.nfse.nacional.provider._logged_post", return_value=mock_resp):
                        with patch.object(
                            provider,
                            "consultar_eventos_nfse",
                            return_value=[
                                {
                                    "tipo_evento": "101101",
                                    "desc_evento": "Cancelamento de NFS-e",
                                    "dh_evento": now,
                                    "is_cancellation": True,
                                    "raw_xml": "<eventoCancelamento/>",
                                }
                            ],
                        ):
                            with patch("core.services.nfse_services.fetch_and_save_nfse_pdf"):
                                with patch("core.nfse.provider_factory.get_provider", return_value=provider):
                                    result = cancel_nota_fiscal(nf)

        self.assertTrue(result.sucesso)
        nf.refresh_from_db()
        self.assertTrue(nf.is_canceled)
        self.assertEqual(nf.cancelation_date, now)


class InvoiceFiscalCodesTests(TestCase):
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
            [x509.NameAttribute(NameOID.COMMON_NAME, "fiscaltest.com")]
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
        self.user = User.objects.create_superuser("fiscal_admin", "admin@fiscal.test", "pass")
        self.client_http = HttpClient()
        self.client_http.force_login(self.user)
        self.company = CompanySettings.objects.create(
            company_name="Fiscal Test Ltda",
            cnpj="12.345.678/0001-95",
            opening_date=date(2024, 1, 1),
            inscricao_municipal="123456",
            email="fiscal@test.com",
            address_line1="Rua Teste",
            address_city_ibge="3550308",
            nfse_provider="NACIONAL",
            next_document_number=1,
            document_series="1",
            pfx_cert_pem=self.test_cert_pem,
            pfx_key_pem=self.test_key_pem,
            debug_mode=True,
        )
        self.client_obj = Client.objects.create(
            name="Global Client Inc",
            address_neighborhood="Downtown",
            address_country_code="CA",
            address_city="Montreal",
            address_postal_code="H2Y 1M6",
            address_state_province="QC",
            email="client@global.test",
        )
        self.invoice = Invoice.objects.create(
            client=self.client_obj,
            invoice_number="INV-FISC-01",
            issue_date=date(2026, 10, 1),
            currency="USD",
            exchange_rate_to_brl=Decimal("5.00"),
            codigo_tributacao_nacional="010101",
            codigo_servico_municipio="",
            codigo_nbs="115029000",
            status="DRAFT",
        )
        InvoiceItem.objects.create(
            invoice=self.invoice,
            description="Software Consulting",
            quantity=Decimal("1.00"),
            unit_price_foreign=Decimal("1000.00"),
        )

    def test_invoice_form_validation(self):
        from core.forms import InvoiceForm
        # Empty fiscal codes -> invalid
        form_empty = InvoiceForm(data={
            "client": str(self.client_obj.id),
            "invoice_number": "INV-NEW-01",
            "issue_date": "2026-10-01",
            "currency": "USD",
            "bank_details": "",
            "nfse_description": "Service description",
            "codigo_tributacao_nacional": "",
            "codigo_servico_municipio": "",
            "codigo_nbs": "",
        })
        self.assertFalse(form_empty.is_valid())
        self.assertIn("codigo_tributacao_nacional", form_empty.errors)
        self.assertIn("codigo_nbs", form_empty.errors)
        # codigo_servico_municipio is optional
        self.assertNotIn("codigo_servico_municipio", form_empty.errors)

        # Valid without codigo_servico_municipio
        form_valid = InvoiceForm(data={
            "client": str(self.client_obj.id),
            "invoice_number": "INV-NEW-02",
            "issue_date": "2026-10-01",
            "currency": "USD",
            "bank_details": "",
            "nfse_description": "Service description",
            "codigo_tributacao_nacional": "010101",
            "codigo_servico_municipio": "",
            "codigo_nbs": "115029000",
        })
        self.assertTrue(form_valid.is_valid(), form_valid.errors)

        # Fresh form has no pre-filled default for fiscal codes
        fresh_form = InvoiceForm()
        self.assertFalse(fresh_form.initial.get("codigo_tributacao_nacional"))
        self.assertFalse(fresh_form.initial.get("codigo_servico_municipio"))
        self.assertFalse(fresh_form.initial.get("codigo_nbs"))

    def test_invoice_template_form_validation(self):
        from core.forms import InvoiceTemplateForm
        form_empty = InvoiceTemplateForm(data={
            "name": "Template Fiscal Empty",
            "currency": "USD",
            "bank_details": "",
            "nfse_description": "Service description",
            "codigo_tributacao_nacional": "",
            "codigo_servico_municipio": "",
            "codigo_nbs": "",
        })
        self.assertFalse(form_empty.is_valid())
        self.assertIn("codigo_tributacao_nacional", form_empty.errors)
        self.assertIn("codigo_nbs", form_empty.errors)
        self.assertNotIn("codigo_servico_municipio", form_empty.errors)

        form_valid = InvoiceTemplateForm(data={
            "name": "Template Fiscal Valid",
            "currency": "USD",
            "bank_details": "",
            "nfse_description": "Service description",
            "codigo_tributacao_nacional": "010101",
            "codigo_servico_municipio": "001",
            "codigo_nbs": "115029000",
        })
        self.assertTrue(form_valid.is_valid(), form_valid.errors)

    def test_htmx_get_invoice_template_returns_fiscal_codes(self):
        tmpl = InvoiceTemplate.objects.create(
            name="Template Codes",
            currency="EUR",
            bank_details="Bank info",
            nfse_description="NFSe info",
            codigo_tributacao_nacional="010101",
            codigo_servico_municipio="001",
            codigo_nbs="115029000",
        )
        resp = self.client_http.get(reverse("htmx_get_invoice_template", args=[tmpl.id]))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["codigo_tributacao_nacional"], "010101")
        self.assertEqual(data["codigo_servico_municipio"], "001")
        self.assertEqual(data["codigo_nbs"], "115029000")

    def test_clone_invoice_copies_fiscal_codes(self):
        self.invoice.codigo_tributacao_nacional = "010203"
        self.invoice.codigo_servico_municipio = "001"
        self.invoice.codigo_nbs = "115022999"
        self.invoice.save()

        resp = self.client_http.post(reverse("clone_invoice", args=[self.invoice.id]))
        self.assertEqual(resp.status_code, 302)

        cloned = Invoice.objects.exclude(id=self.invoice.id).first()
        self.assertIsNotNone(cloned)
        self.assertEqual(cloned.codigo_tributacao_nacional, "010203")
        self.assertEqual(cloned.codigo_servico_municipio, "001")
        self.assertEqual(cloned.codigo_nbs, "115022999")

    def test_htmx_update_fiscal_codes_flow(self):
        url = reverse("htmx_update_fiscal_codes", args=[self.invoice.id])

        # Valid update
        resp = self.client_http.post(url, data={
            "codigo_tributacao_nacional": "010102",
            "codigo_servico_municipio": "001",
            "codigo_nbs": "115022001",
        })
        self.assertEqual(resp.status_code, 200)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.codigo_tributacao_nacional, "010102")
        self.assertEqual(self.invoice.codigo_servico_municipio, "001")
        self.assertEqual(self.invoice.codigo_nbs, "115022001")

        # Invalid update (missing required)
        resp_err = self.client_http.post(url, data={
            "codigo_tributacao_nacional": "",
            "codigo_servico_municipio": "",
            "codigo_nbs": "",
        })
        self.assertEqual(resp_err.status_code, 400)
        self.assertContains(resp_err, "O Código de Tributação Nacional é obrigatório.", status_code=400)

        # Cannot update finalized invoice
        self.invoice.status = "FINALIZED"
        self.invoice.save()
        resp_final = self.client_http.post(url, data={
            "codigo_tributacao_nacional": "010101",
            "codigo_nbs": "115029000",
        })
        self.assertEqual(resp_final.status_code, 400)

    def test_nacional_provider_fiscal_code_rules(self):
        from core.nfse.nacional.provider import NacionalProvider
        nacional_provider = NacionalProvider()

        # 1. When codigo_servico_municipio is empty -> <cTribMun> omitted
        self.invoice.codigo_tributacao_nacional = "010101"
        self.invoice.codigo_servico_municipio = ""
        self.invoice.codigo_nbs = "115029000"
        self.invoice.save()

        _, signed_xml, _ = nacional_provider._build_and_sign_dps(
            self.invoice, self.company, 1, "1"
        )
        self.assertIn("<cTribNac>010101</cTribNac>", signed_xml)
        self.assertIn("<cNBS>115029000</cNBS>", signed_xml)
        self.assertNotIn("<cTribMun>", signed_xml)

        # 2. When codigo_servico_municipio has <= 3 digits -> <cTribMun> sent
        self.invoice.codigo_servico_municipio = "001"
        self.invoice.save()
        _, signed_xml_mun, _ = nacional_provider._build_and_sign_dps(
            self.invoice, self.company, 2, "1"
        )
        self.assertIn("<cTribMun>001</cTribMun>", signed_xml_mun)

        # 3. When codigo_servico_municipio has > 3 digits -> emitir_nfse fails with clear error
        self.invoice.codigo_servico_municipio = "02668"
        self.invoice.save()
        emit_res = nacional_provider.emitir_nfse(self.invoice)
        self.assertFalse(emit_res.sucesso)
        self.assertTrue(any("possui mais de 3 dígitos" in err for err in emit_res.erros))

    @patch("core.models.paulistana_emission_blocked", return_value=False)
    def test_paulistana_provider_fiscal_code_rules(self, mock_blocked):
        from core.nfse.paulistana.provider import PaulistanaProvider
        paulistana_provider = PaulistanaProvider()

        # 1. When codigo_servico_municipio is empty -> rejected
        self.invoice.codigo_servico_municipio = ""
        self.invoice.save()
        res_empty = paulistana_provider.emitir_nfse(self.invoice)
        self.assertFalse(res_empty.sucesso)
        self.assertTrue(any("Código de Serviço do Município é obrigatório" in err for err in res_empty.erros))

        # 2. When codigo_servico_municipio is provided -> accepted and passed to RPS
        self.invoice.codigo_servico_municipio = "02668"
        self.invoice.save()
        with patch("core.nfse.paulistana.client.NFeClient.testar_envio_lote_rps") as mock_test:
            from core.nfse.paulistana.schemas_v1.retorno_envio_lote_rps_v01 import (
                RetornoEnvioLoteRps as RetornoEnvioLoteRpsV1,
            )
            mock_test.return_value = (
                RetornoEnvioLoteRpsV1(cabecalho=RetornoEnvioLoteRpsV1.Cabecalho(sucesso=True)),
                "<signed/>",
                "<retorno/>",
            )
            res_ok = paulistana_provider.emitir_nfse(self.invoice)
            self.assertTrue(res_ok.sucesso)
            call_args = mock_test.call_args[0][0]
            self.assertEqual(call_args[0].codigo_servico, "02668")

    def test_create_nf_preserves_invoice_fiscal_codes(self):
        from core.services.nfse_services import _create_nf_from_emit_result
        from core.nfse.base import EmitResult

        self.invoice.codigo_tributacao_nacional = "010101"
        self.invoice.codigo_servico_municipio = "001"
        self.invoice.codigo_nbs = "115029000"
        self.invoice.save()

        # Provider result missing fiscal codes
        result = EmitResult(
            sucesso=True,
            numero_nf="9999",
            codigo_verificacao="XYZ-123",
            codigo_tributacao_nacional="",
            codigo_servico_municipio="",
            codigo_nbs="",
        )
        from unittest.mock import MagicMock
        mock_provider = MagicMock()
        mock_provider.baixar_pdf.return_value = b"%PDF mock"
        nf = _create_nf_from_emit_result(self.invoice, result, mock_provider)
        self.assertEqual(nf.codigo_tributacao_nacional, "010101")
        self.assertEqual(nf.codigo_servico_municipio, "001")
        self.assertEqual(nf.codigo_nbs, "115029000")


class PastConsolidationsImportTests(TestCase):
    def setUp(self):
        self.company = CompanySettings.objects.create(
            company_name="Synthetic Test Services Ltda",
            cnpj="00.000.000/0001-99",
            inscricao_municipal="987654",
            opening_date=date(2024, 1, 1),
            email="finance@example.com",
            address_city_ibge="3550308",
            nfse_provider="NACIONAL",
        )

    def test_populate_past_consolidations_leaves_closed_months_zero_unless_synced(self):
        from core.services.consolidation import populate_consolidations_for_imported_notes
        from core.models import NotaFiscal, MonthlyConsolidation

        # Notes in past months
        NotaFiscal.objects.create(
            nf_number="101",
            issue_date=date(2024, 2, 10),
            amount_brl=Decimal("10000.00"),
            description="Software Services",
            is_export=True,
        )
        NotaFiscal.objects.create(
            nf_number="102",
            issue_date=date(2024, 3, 10),
            amount_brl=Decimal("10000.00"),
            description="Software Services",
            is_export=True,
        )

        populate_consolidations_for_imported_notes([date(2024, 2, 10), date(2024, 3, 10)])

        cons_feb = MonthlyConsolidation.objects.get(month_year=date(2024, 2, 1))
        cons_mar = MonthlyConsolidation.objects.get(month_year=date(2024, 3, 1))

        # Closed months without eSocial sync must remain at 0.00 and not assume ideal pró-labore
        self.assertEqual(cons_feb.actual_pro_labore_paid, Decimal("0.00"))
        self.assertEqual(cons_mar.actual_pro_labore_paid, Decimal("0.00"))

    def test_populate_past_consolidations_resets_unsynced_closed_month_pro_labore_to_zero(self):
        from core.services.consolidation import populate_consolidations_for_imported_notes
        from core.models import NotaFiscal, MonthlyConsolidation

        # Pre-existing consolidation with minimum salary on a closed month
        cons = MonthlyConsolidation.objects.create(
            month_year=date(2024, 2, 1),
            status="CONSOLIDATED",
            actual_pro_labore_paid=Decimal("1412.00"),
        )
        NotaFiscal.objects.create(
            nf_number="103",
            issue_date=date(2024, 2, 10),
            amount_brl=Decimal("20000.00"),
            description="Software Services",
            is_export=True,
        )

        populate_consolidations_for_imported_notes([date(2024, 2, 10)])

        cons.refresh_from_db()
        # Closed months without eSocial sync must reset to 0.00, not force ideal or minimum salary
        self.assertEqual(cons.actual_pro_labore_paid, Decimal("0.00"))

    def test_audit_consolidations_leaves_unsynced_closed_months_at_zero(self):
        from core.services.consolidation import audit_consolidations
        from core.models import NotaFiscal, MonthlyConsolidation

        NotaFiscal.objects.create(
            nf_number="104",
            issue_date=date(2024, 4, 10),
            amount_brl=Decimal("20000.00"),
            description="Software Services",
            is_export=True,
        )
        NotaFiscal.objects.create(
            nf_number="105",
            issue_date=date(2024, 5, 10),
            amount_brl=Decimal("20000.00"),
            description="Software Services",
            is_export=True,
        )

        # Note creation in April 2024 flagged months outdated with default 0.00 pro-labore
        cons_apr = MonthlyConsolidation.objects.get(month_year=date(2024, 4, 1))
        self.assertEqual(cons_apr.actual_pro_labore_paid, Decimal("0.00"))

        audit_consolidations()

        cons_apr = MonthlyConsolidation.objects.get(month_year=date(2024, 4, 1))
        cons_may = MonthlyConsolidation.objects.get(month_year=date(2024, 5, 1))

        # Closed months without eSocial sync remain at 0.00
        self.assertEqual(cons_apr.actual_pro_labore_paid, Decimal("0.00"))
        self.assertEqual(cons_may.actual_pro_labore_paid, Decimal("0.00"))


class NfseEmissionErrorHandlingTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.test_key_pem = key.private_bytes(
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
        cls.test_cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")

    def setUp(self):
        self.company = CompanySettings.objects.create(
            company_name="Test Company",
            cnpj="12.345.678/0001-90",
            inscricao_municipal="12345678",
            opening_date=date(2024, 1, 1),
            email="test@test.com",
            address_city_ibge="3550308",
            address_neighborhood="Centro",
            pfx_cert_pem=self.test_cert_pem,
            pfx_key_pem=self.test_key_pem,
        )

    def test_nacional_parse_error_response_pascal_case_keys(self):
        from unittest.mock import MagicMock
        from core.nfse.nacional.provider import NacionalProvider

        provider = NacionalProvider()
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.json.return_value = {
            "tipoAmbiente": 2,
            "idDPS": "DPS355030824579135100010404242000000000000001",
            "erros": [
                {
                    "Codigo": "E1235",
                    "Descricao": "Falha no esquema XML do DF-e.",
                    "Complemento": "The 'cEndPost' element is invalid.",
                }
            ],
        }

        errs = provider._parse_error_response(mock_resp)
        self.assertEqual(len(errs), 1)
        self.assertIn("E1235", errs[0])
        self.assertIn("Falha no esquema XML do DF-e.", errs[0])
        self.assertIn("The 'cEndPost' element is invalid.", errs[0])

    def test_nfse_log_properties(self):
        from core.models import NfseLog

        # Error in payload_retorno with empty erro_mensagem
        log_err = NfseLog(
            payload_retorno='{"erros":[{"Codigo":"E1235","Descricao":"Falha no esquema XML","Complemento":"detalhe"}]}',
            erro_mensagem="",
        )
        self.assertFalse(log_err.is_success)
        self.assertIn("E1235 - Falha no esquema XML (detalhe)", log_err.display_error)

        # Successful log
        log_ok = NfseLog(
            payload_retorno='{"chaveAcesso":"3550308...","numeroNFSe":"1"}',
            erro_mensagem="",
        )
        self.assertTrue(log_ok.is_success)
        self.assertEqual(log_ok.display_error, "")

    def test_nacional_build_dps_foreign_address_fallback(self):
        from core.models import Client, Invoice
        from core.nfse.nacional.provider import NacionalProvider
        from datetime import date
        from decimal import Decimal

        company = self.company

        client = Client.objects.create(
            name="Foreign Test Client LLC",
            email="client@example.com",
            address_country_code="US",
            address_city="San Francisco",
            address_state_province="",  # Empty
            address_postal_code="",     # Empty
        )

        from core.models import InvoiceItem

        inv = Invoice.objects.create(
            invoice_number="999",
            client=client,
            issue_date=date.today(),
            currency="USD",
            exchange_rate_to_brl=Decimal("5.0000"),
            codigo_tributacao_nacional="010101",
            codigo_nbs="115029000",
            codigo_servico_municipio="001",
            status="DRAFT",
        )
        InvoiceItem.objects.create(
            invoice=inv,
            description="Service item",
            quantity=1,
            unit_price_foreign=Decimal("100.00"),
        )
        inv.status = "FINALIZED"
        inv.save()

        provider = NacionalProvider()
        dps, signed_xml, id_dps = provider._build_and_sign_dps(inv, company, 999, "4242")
        self.assertNotIn("<cEndPost/>", signed_xml)
        self.assertNotIn("<xEstProvReg/>", signed_xml)
        self.assertIn("<cEndPost>N/A</cEndPost>", signed_xml)
        self.assertIn("<xEstProvReg>N/A</xEstProvReg>", signed_xml)

    def test_unmocked_external_network_call_is_blocked_by_test_runner(self):
        import requests
        from core.test_runner import BlockedNetworkCallError

        with self.assertRaises(BlockedNetworkCallError) as ctx:
            requests.get("https://sefin.nfse.gov.br/test")
        self.assertIn("External network call blocked during tests", str(ctx.exception))
        self.assertIn("https://sefin.nfse.gov.br/test", str(ctx.exception))

