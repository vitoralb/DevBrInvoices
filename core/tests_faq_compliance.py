import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from unittest.mock import patch, MagicMock

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from core.forms import CompanySettingsForm, VALID_INVOICE_MACROS, VALID_EMAIL_MACROS
from core.models import (
    CompanySettings,
    Client,
    Invoice,
    InvoiceItem,
    NotaFiscal,
    DEFAULT_NFSE_DESCRIPTION_TEMPLATE,
    PAULISTANA_EMISSION_END_DATE,
    paulistana_emission_blocked,
    series_range_validator,
)
from core.nfse.nacional.provider import NacionalProvider
from core.nfse.paulistana.provider import PaulistanaProvider
from core.services import (
    calculate_approx_tax_rate_pct,
    get_approx_tax_rate_pct,
    _prepare_nf_data,
    import_nfses,
)
from core.tasks.nfse_tasks import sync_adn_periodic_task, import_nfses_task
from core.utils.macros import apply_invoice_macros
from utils.taxes import get_applicable_bracket


class TaxCalculationsFaqComplianceTest(TestCase):
    def test_calculate_approx_tax_rate_export_vs_internal(self):
        reference_date = date(2026, 10, 1)
        rbt12 = Decimal("500000.00")
        annex_type = "ANNEX_III"

        bracket = get_applicable_bracket(annex_type, rbt12, reference_date)
        self.assertIsNotNone(bracket)

        # Internal: nominal rate of the bracket
        rate_internal = calculate_approx_tax_rate_pct(
            rbt12, annex_type, reference_date, is_export=False
        )
        expected_internal = bracket.nominal_rate.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        self.assertEqual(rate_internal, expected_internal)

        # Export: nominal rate minus PIS, COFINS, ISS exemptions
        rate_export = calculate_approx_tax_rate_pct(
            rbt12, annex_type, reference_date, is_export=True
        )
        exempt_frac = (
            bracket.pis_allocation + bracket.cofins_allocation + bracket.iss_allocation
        ) / Decimal("100")
        expected_export = (bracket.nominal_rate * (Decimal("1") - exempt_frac)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        self.assertEqual(rate_export, expected_export)
        self.assertLess(rate_export, rate_internal)

    def test_calculate_approx_tax_rate_zero_rbt12(self):
        reference_date = date(2026, 10, 1)
        rbt12 = Decimal("0.00")
        rate = calculate_approx_tax_rate_pct(
            rbt12, "ANNEX_III", reference_date, is_export=True
        )
        bracket = get_applicable_bracket("ANNEX_III", Decimal("0.00"), reference_date)
        exempt_frac = (
            bracket.pis_allocation + bracket.cofins_allocation + bracket.iss_allocation
        ) / Decimal("100")
        expected = (bracket.nominal_rate * (Decimal("1") - exempt_frac)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        self.assertEqual(rate, expected)

    def test_calculate_approx_tax_rate_invalid_annex(self):
        rate = calculate_approx_tax_rate_pct(
            Decimal("100000.00"), "INVALID_ANNEX", date(2026, 10, 1), is_export=True
        )
        self.assertEqual(rate, Decimal("0.00"))

    def test_calculate_approx_tax_rate_none_and_invalid_inputs(self):
        self.assertEqual(
            calculate_approx_tax_rate_pct(None, "ANNEX_III", date(2026, 10, 1), is_export=True),
            Decimal("0.00"),
        )
        self.assertEqual(
            calculate_approx_tax_rate_pct(Decimal("100000.00"), "ANNEX_III", None, is_export=True),
            Decimal("0.00"),
        )
        self.assertEqual(
            calculate_approx_tax_rate_pct(Decimal("100000.00"), None, date(2026, 10, 1), is_export=True),
            Decimal("0.00"),
        )


class MacrosFaqComplianceTest(TestCase):
    def setUp(self):
        cache.clear()
        self.company = CompanySettings.load()
        if not self.company:
            self.company = CompanySettings.objects.create(
                company_name="Test Company Ltda",
                cnpj="12.345.678/0001-95",
                inscricao_municipal="12345678",
                opening_date=date(2024, 1, 1),
                address_city_ibge="3550308",
                email="test@synthetic.local",
            )
        else:
            self.company.email = "test@synthetic.local"
            self.company.save()

        self.client = Client.objects.create(
            name="Synthetic Foreign Client LLC",
            address_country_code="US",
            email="client@synthetic.local",
        )
        self.invoice = Invoice.objects.create(
            invoice_number="INV-2026-901",
            client=self.client,
            issue_date=date(2026, 10, 15),
            exchange_rate_to_brl=Decimal("5.0000"),
            currency="USD",
        )

    def test_nominal_tax_rate_macro_default(self):
        text_pt = "Alíquota aproximada: {{ nominal_tax_rate }}%"
        rendered_pt = apply_invoice_macros(text_pt, self.invoice, language="pt-br")
        self.assertIn("Alíquota aproximada: 0,00%", rendered_pt)

        text_en = "Approximate tax rate: {{ nominal_tax_rate }}%"
        rendered_en = apply_invoice_macros(text_en, self.invoice, language="en")
        self.assertIn("Approximate tax rate: 0.00%", rendered_en)

    def test_nominal_tax_rate_macro_with_extra_context(self):
        text = "Alíquota aproximada: {{ nominal_tax_rate }}%"
        rendered = apply_invoice_macros(
            text,
            self.invoice,
            language="pt-br",
            extra_context={"{{ nominal_tax_rate }}": Decimal("6.87")},
        )
        self.assertEqual(rendered, "Alíquota aproximada: 6,87%")

    def test_valid_invoice_macros_contains_nominal_tax_rate(self):
        self.assertIn("{{ nominal_tax_rate }}", VALID_INVOICE_MACROS)
        self.assertIn("{{ nominal_tax_rate }}", VALID_EMAIL_MACROS)

    def test_default_nfse_description_template_uses_nominal_tax_rate(self):
        self.assertIn("{{ nominal_tax_rate }}", DEFAULT_NFSE_DESCRIPTION_TEMPLATE)
        self.assertNotIn("{{ effective_tax_rate }}", DEFAULT_NFSE_DESCRIPTION_TEMPLATE)

    def test_prepare_nf_data_injects_both_macros(self):
        InvoiceItem.objects.create(
            invoice=self.invoice,
            description="Software Services",
            quantity=1,
            unit_price_foreign=Decimal("1000.00"),
        )
        self.invoice.nfse_description = "Nominal: {{ nominal_tax_rate }}% | Efetiva: {{ effective_tax_rate }}%"
        self.invoice.save()

        amount_brl, desc, eff_rate = _prepare_nf_data(self.invoice)
        self.assertEqual(amount_brl, Decimal("5000.00"))
        self.assertIn("Nominal: ", desc)
        self.assertIn("Efetiva: ", desc)
        # Ensure neither placeholder remained unrendered
        self.assertNotIn("{{ nominal_tax_rate }}", desc)
        self.assertNotIn("{{ effective_tax_rate }}", desc)


class SeriesValidationTest(TestCase):
    def test_series_range_validator(self):
        # Valid series
        series_range_validator("1")
        series_range_validator("4242")
        series_range_validator("49999")
        series_range_validator("")
        series_range_validator(None)

        # Invalid series (out of range 1-49999)
        with self.assertRaises(ValidationError) as cm:
            series_range_validator("0")
        self.assertIn("entre 1 e 49999", str(cm.exception))

        with self.assertRaises(ValidationError) as cm:
            series_range_validator("50000")
        self.assertIn("entre 1 e 49999", str(cm.exception))

        with self.assertRaises(ValidationError) as cm:
            series_range_validator("70000")
        self.assertIn("entre 1 e 49999", str(cm.exception))

    def test_company_settings_series_validation(self):
        company = CompanySettings.load()
        if not company:
            company = CompanySettings.objects.create(
                company_name="Test Company Ltda",
                cnpj="12.345.678/0001-95",
                inscricao_municipal="12345678",
                opening_date=date(2024, 1, 1),
                address_city_ibge="3550308",
                email="test@synthetic.local",
            )
        else:
            company.email = "test@synthetic.local"
            company.save()

        # Valid series
        company.document_series = "4242"
        company.full_clean()

        # Series out of range
        company.document_series = "50000"
        with self.assertRaises(ValidationError):
            company.full_clean()

        company.document_series = "0"
        with self.assertRaises(ValidationError):
            company.full_clean()

        # Non-numeric
        company.document_series = "ABC"
        with self.assertRaises(ValidationError):
            company.full_clean()


class PaulistanaEmissionBlockedTest(TestCase):
    def setUp(self):
        cache.clear()
        self.company = CompanySettings.load()
        if not self.company:
            self.company = CompanySettings.objects.create(
                company_name="Test Company Ltda",
                cnpj="12.345.678/0001-95",
                inscricao_municipal="12345678",
                opening_date=date(2024, 1, 1),
                address_city_ibge="3550308",
                email="test@synthetic.local",
                pfx_cert_pem="dummy-cert",
                pfx_key_pem="dummy-key",
            )
        else:
            self.company.cnpj = "12.345.678/0001-95"
            self.company.email = "test@synthetic.local"
            self.company.pfx_cert_pem = "dummy-cert"
            self.company.pfx_key_pem = "dummy-key"
            self.company.save()

        self.client = Client.objects.create(
            name="Synthetic Foreign Client LLC",
            address_country_code="US",
            email="client@synthetic.local",
        )
        self.invoice = Invoice.objects.create(
            invoice_number="INV-2026-902",
            client=self.client,
            issue_date=date(2026, 10, 15),
            exchange_rate_to_brl=Decimal("5.0000"),
            currency="USD",
            codigo_servico_municipio="001",
        )
        InvoiceItem.objects.create(
            invoice=self.invoice,
            description="Service Item",
            quantity=1,
            unit_price_foreign=Decimal("1000.00"),
        )

    def test_paulistana_emission_blocked_dates(self):
        self.assertFalse(paulistana_emission_blocked(date(2026, 10, 31)))
        self.assertTrue(paulistana_emission_blocked(date(2026, 11, 1)))
        self.assertTrue(paulistana_emission_blocked(date(2026, 12, 1)))
        self.assertEqual(PAULISTANA_EMISSION_END_DATE, date(2026, 11, 1))

    def test_paulistana_emission_blocked_with_datetime(self):
        dt_before = datetime(2026, 10, 31, 23, 59, 59)
        dt_after = datetime(2026, 11, 1, 0, 0, 0)
        self.assertFalse(paulistana_emission_blocked(dt_before))
        self.assertTrue(paulistana_emission_blocked(dt_after))

    @patch("core.models.paulistana_emission_blocked")
    def test_company_settings_form_clean_nfse_provider(self, mock_blocked):
        form_data = {
            "company_name": self.company.company_name,
            "cnpj": "12.345.678/0001-95",
            "inscricao_municipal": self.company.inscricao_municipal,
            "opening_date": self.company.opening_date,
            "address_city_ibge": "3550308",
            "document_series": "1",
            "next_document_number": 1,
            "nfse_provider": "PAULISTANA",
            "email": "test@synthetic.local",
            "auto_invoice_hour": 9,
        }

        # Blocked: raises error
        mock_blocked.return_value = True
        form = CompanySettingsForm(data=form_data, instance=self.company)
        self.assertFalse(form.is_valid())
        self.assertIn("nfse_provider", form.errors)
        self.assertIn(
            "ME/EPP do Simples Nacional devem emitir pelo Emissor Nacional desde 01/11/2026.",
            form.errors["nfse_provider"][0],
        )

        # Not blocked: valid
        mock_blocked.return_value = False
        form = CompanySettingsForm(data=form_data, instance=self.company)
        self.assertTrue(form.is_valid(), form.errors)

    @patch("core.models.paulistana_emission_blocked")
    def test_paulistana_provider_emitir_nfse_blocked(self, mock_blocked):
        mock_blocked.return_value = True
        provider = PaulistanaProvider()
        result = provider.emitir_nfse(self.invoice)

        self.assertFalse(result.sucesso)
        self.assertTrue(any("encerrada desde 01/11/2026" in err for err in result.erros))


class NacionalProviderDpsTotTribTest(TestCase):
    def setUp(self):
        cache.clear()
        self.company = CompanySettings.load()
        if not self.company:
            self.company = CompanySettings.objects.create(
                company_name="Test Company Ltda",
                cnpj="12.345.678/0001-95",
                inscricao_municipal="12345678",
                opening_date=date(2024, 1, 1),
                address_city_ibge="3550308",
                pfx_cert_pem="dummy-cert",
                pfx_key_pem="dummy-key",
                email="test@synthetic.local",
            )
        else:
            self.company.pfx_cert_pem = "dummy-cert"
            self.company.pfx_key_pem = "dummy-key"
            self.company.save()

        self.client = Client.objects.create(
            name="Synthetic Foreign Client LLC",
            address_country_code="US",
            email="client@synthetic.local",
        )
        self.invoice = Invoice.objects.create(
            invoice_number="INV-2026-903",
            client=self.client,
            issue_date=date(2026, 10, 15),
            exchange_rate_to_brl=Decimal("5.0000"),
            currency="USD",
            codigo_servico_municipio="026",
            codigo_tributacao_nacional="010101",
            codigo_nbs="115029000",
        )
        InvoiceItem.objects.create(
            invoice=self.invoice,
            description="Service Item",
            quantity=1,
            unit_price_foreign=Decimal("1000.00"),
        )

    @patch("core.services.get_approx_tax_rate_pct")
    @patch("core.nfse.nacional.provider.XMLSigner")
    def test_dps_uses_approx_tax_rate_pct_in_tot_trib(self, mock_signer_cls, mock_approx):
        mock_approx.return_value = Decimal("6.87")
        mock_signer = MagicMock()
        mock_signer.sign.side_effect = lambda root, **kwargs: root
        mock_signer_cls.return_value = mock_signer

        provider = NacionalProvider()
        dps_obj, signed_xml, id_dps = provider._build_and_sign_dps(
            self.invoice, self.company, 1, "1"
        )

        self.assertIsNotNone(dps_obj.inf_dps.valores.trib.tot_trib)
        self.assertEqual(
            dps_obj.inf_dps.valores.trib.tot_trib.p_tot_trib_sn, "6.87"
        )

    def test_get_approx_tax_rate_pct_supports_nota_fiscal(self):
        nf = NotaFiscal.objects.create(
            nf_number="1001",
            issue_date=date(2026, 10, 15),
            amount_brl=Decimal("5000.00"),
            is_export=True,
            description="Test Service",
        )
        rate = get_approx_tax_rate_pct(nf)
        self.assertIsInstance(rate, Decimal)
        self.assertGreater(rate, Decimal("0.00"))

    def test_get_approx_tax_rate_pct_with_no_issue_date(self):
        self.invoice.issue_date = None
        rate = get_approx_tax_rate_pct(self.invoice)
        self.assertEqual(rate, Decimal("0.00"))


class AdnCooldownAndPeriodicSyncTest(TestCase):
    def setUp(self):
        cache.clear()
        self.company = CompanySettings.load()
        if not self.company:
            self.company = CompanySettings.objects.create(
                company_name="Test Company Ltda",
                cnpj="12.345.678/0001-95",
                inscricao_municipal="12345678",
                opening_date=date(2024, 1, 1),
                address_city_ibge="3550308",
                nfse_provider="NACIONAL",
                pfx_cert_pem="dummy-cert",
                pfx_key_pem="dummy-key",
                email="test@synthetic.local",
            )
        else:
            self.company.nfse_provider = "NACIONAL"
            self.company.pfx_cert_pem = "dummy-cert"
            self.company.pfx_key_pem = "dummy-key"
            self.company.save()

    @patch("core.nfse.nacional.provider._logged_get")
    def test_consultar_dfe_por_nsu_sets_cooldown_on_404(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        provider = NacionalProvider()
        items, max_nsu = provider.consultar_dfe_por_nsu(ultimo_nsu=10)
        self.assertEqual(items, [])
        self.assertEqual(max_nsu, 10)

        cooldown = cache.get("adn_dfe_cooldown_until")
        self.assertIsNotNone(cooldown)

    @patch("core.nfse.nacional.provider._logged_get")
    def test_consultar_dfe_por_nsu_sets_cooldown_on_empty_lote(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"LoteDFe": []}
        mock_get.return_value = mock_resp

        provider = NacionalProvider()
        items, max_nsu = provider.consultar_dfe_por_nsu(ultimo_nsu=5)
        self.assertEqual(items, [])
        self.assertEqual(max_nsu, 5)

        cooldown = cache.get("adn_dfe_cooldown_until")
        self.assertIsNotNone(cooldown)

    @patch("core.nfse.nacional.provider._logged_get")
    def test_consultar_dfe_por_nsu_skips_when_cooldown_active(self, mock_get):
        cache.set("adn_dfe_cooldown_until", timezone.now() + timedelta(minutes=45), timeout=3600)

        provider = NacionalProvider()
        items, max_nsu = provider.consultar_dfe_por_nsu(ultimo_nsu=10)
        self.assertEqual(items, [])
        self.assertEqual(max_nsu, 10)
        mock_get.assert_not_called()

    def test_import_nfses_returns_cooldown_message(self):
        cache.set("adn_dfe_cooldown_until", timezone.now() + timedelta(minutes=30), timeout=1800)

        count, msg = import_nfses("NACIONAL")
        self.assertEqual(count, 0)
        self.assertIn("Consulta ao ADN em espera obrigatória até", msg)

    @patch("core.services.import_nfses")
    def test_sync_adn_periodic_task_runs_when_configured(self, mock_import):
        mock_import.return_value = (2, "Importação concluída: 2 nova(s) NFS-e(s)")

        res = sync_adn_periodic_task()
        self.assertEqual(res, {"count": 2, "message": "Importação concluída: 2 nova(s) NFS-e(s)"})
        mock_import.assert_called_once_with("NACIONAL")

    @patch("core.services.import_nfses")
    def test_sync_adn_periodic_task_skipped_if_not_nacional(self, mock_import):
        self.company.nfse_provider = "PAULISTANA"
        self.company.save()

        res = sync_adn_periodic_task()
        self.assertIn("Skipped", str(res))
        mock_import.assert_not_called()

    @patch("core.services.import_nfses")
    def test_sync_adn_periodic_task_skipped_if_no_cert(self, mock_import):
        self.company.pfx_cert_pem = ""
        self.company.save()

        res = sync_adn_periodic_task()
        self.assertIn("Skipped", str(res))
        mock_import.assert_not_called()

    @patch("core.services.import_nfses")
    def test_sync_adn_periodic_task_skips_if_lock_held(self, mock_import):
        cache.set("adn_sync_lock", "true", timeout=600)

        res = sync_adn_periodic_task()
        self.assertIn("Skipped", str(res))
        mock_import.assert_not_called()

    def test_import_nfses_task_skips_if_lock_held(self):
        cache.set("adn_sync_lock", "true", timeout=600)

        res = import_nfses_task("NACIONAL")
        self.assertEqual(res["count"], 0)
        self.assertIn("já em andamento", res["message"])

    @patch("core.nfse.nacional.provider._logged_get")
    def test_consultar_dfe_por_nsu_cleans_up_expired_cooldown(self, mock_get):
        past_time = timezone.now() - timedelta(minutes=5)
        cache.set("adn_dfe_cooldown_until", past_time, timeout=3600)

        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        provider = NacionalProvider()
        items, max_nsu = provider.consultar_dfe_por_nsu(ultimo_nsu=10)
        # Should have called the API because the past cooldown was deleted
        mock_get.assert_called_once()

    def test_import_nfses_cleans_up_expired_cooldown(self):
        past_time = timezone.now() - timedelta(minutes=5)
        cache.set("adn_dfe_cooldown_until", past_time, timeout=3600)

        with patch("core.nfse.nacional.provider.NacionalProvider.consultar_dfe_por_nsu", return_value=([], 0)):
            count, msg = import_nfses("NACIONAL")
            self.assertNotIn("espera obrigatória", msg)
            self.assertIsNone(cache.get("adn_dfe_cooldown_until"))

    def test_import_nfses_defaults_to_company_provider(self):
        self.company.nfse_provider = "NACIONAL"
        self.company.save()

        with patch("core.nfse.nacional.provider.NacionalProvider.consultar_dfe_por_nsu", return_value=([], 0)) as mock_nac:
            count, msg = import_nfses()
            mock_nac.assert_called_once()
