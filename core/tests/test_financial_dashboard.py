from datetime import date
from decimal import Decimal
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.test import Client as HttpClient, TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Client, CompanySettings, Invoice, MonthlyConsolidation, NotaFiscal
from core.services.tax_calculations import (
    attach_recommended_pl,
    get_unsynced_prior_months_for_ideal_pl,
    is_month_closed,
)
from core.services.consolidation import consolidate_month, reconsolidate_with_prior


class FinancialDashboardAndClosedMonthsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="secretpassword")
        self.client = HttpClient()
        self.client.login(username="testuser", password="secretpassword")

        self.company = CompanySettings.objects.create(
            company_name="Empresa Teste Dashboard",
            cnpj="12.345.678/0001-95",
            opening_date=date(2025, 1, 1),
            inscricao_municipal="987654",
            email="empresa@teste.com",
            debug_mode=True,
        )

    def test_is_month_closed_definition(self):
        # 1. Any month older than previous month is closed
        ref_today = date(2026, 10, 5)
        self.assertTrue(is_month_closed(date(2026, 8, 1), today=ref_today))
        self.assertTrue(is_month_closed(date(2025, 12, 1), today=ref_today))

        # 2. Previous month is OPEN if today <= 7
        self.assertFalse(is_month_closed(date(2026, 9, 1), today=date(2026, 10, 1)))
        self.assertFalse(is_month_closed(date(2026, 9, 1), today=date(2026, 10, 7)))

        # 3. Previous month is CLOSED if today > 7
        self.assertTrue(is_month_closed(date(2026, 9, 1), today=date(2026, 10, 8)))
        self.assertTrue(is_month_closed(date(2026, 9, 1), today=date(2026, 10, 20)))

        # 4. Current month is always OPEN
        self.assertFalse(is_month_closed(date(2026, 10, 1), today=date(2026, 10, 15)))
        self.assertFalse(is_month_closed(date(2026, 10, 1), today=date(2026, 10, 31)))

        # 5. Future months are OPEN
        self.assertFalse(is_month_closed(date(2026, 11, 1), today=date(2026, 10, 15)))

    def test_closed_month_pro_labore_rules(self):
        # Setup: today is Oct 18, 2026 -> Aug 2026 is closed, Sep 2026 is closed (today > 7), Oct 2026 is open
        today = date(2026, 10, 18)
        with patch("django.utils.timezone.localdate", return_value=today):
            # Create notes in August 2026 (closed)
            NotaFiscal.objects.create(
                issue_date=date(2026, 8, 15),
                amount_brl=Decimal("10000.00"),
                description="Test service",
                is_export=True,
            )

            # Consolidate August 2026: without eSocial, actual_pro_labore_paid MUST be 0.00
            cons_aug = consolidate_month(date(2026, 8, 1))
            self.assertEqual(cons_aug.actual_pro_labore_paid, Decimal("0.00"))

            # Now mark August 2026 as synced via eSocial with R$ 2.500,00
            cons_aug.esocial_synced = True
            cons_aug.actual_pro_labore_paid = Decimal("2500.00")
            cons_aug.save()

            # Reconsolidating August 2026 must preserve the eSocial value
            cons_aug_re = consolidate_month(date(2026, 8, 1))
            self.assertEqual(cons_aug_re.actual_pro_labore_paid, Decimal("2500.00"))

            # Create notes in October 2026 (open)
            NotaFiscal.objects.create(
                issue_date=date(2026, 10, 5),
                amount_brl=Decimal("12000.00"),
                description="Test current month service",
                is_export=True,
            )

            # Consolidate October 2026 (open): must auto-calculate ideal pró-labore
            cons_oct = consolidate_month(date(2026, 10, 1))
            self.assertGreater(cons_oct.actual_pro_labore_paid, Decimal("0.00"))

    def test_unsynced_prior_months_detection_and_warning(self):
        # Create consolidations for the last few months
        MonthlyConsolidation.objects.create(
            month_year=date(2026, 8, 1),
            esocial_synced=True,
            actual_pro_labore_paid=Decimal("2000.00"),
        )
        MonthlyConsolidation.objects.create(
            month_year=date(2026, 9, 1),
            esocial_synced=False,  # Unsynced!
            actual_pro_labore_paid=Decimal("0.00"),
        )

        unsynced = get_unsynced_prior_months_for_ideal_pl(date(2026, 10, 1))
        # September 2026 must be in unsynced list
        self.assertIn(date(2026, 9, 1), unsynced)

        cons_oct = MonthlyConsolidation.objects.create(month_year=date(2026, 10, 1))
        attach_recommended_pl(cons_oct)
        self.assertTrue(cons_oct.has_incomplete_esocial_window)
        self.assertIn(date(2026, 9, 1), cons_oct.unsynced_prior_months)

    def test_dashboard_view_renders_month_detail_and_blocks(self):
        today = date(2026, 10, 18)
        with patch("django.utils.timezone.localdate", return_value=today):
            # Create previous month consolidation (September 2026)
            cons_sep = MonthlyConsolidation.objects.create(
                month_year=date(2026, 9, 1),
                status="CONSOLIDATED",
                total_revenue_export=Decimal("15000.00"),
                total_revenue_internal=Decimal("0.00"),
                actual_pro_labore_paid=Decimal("3000.00"),
                das_tax=Decimal("450.00"),
                inss_tax=Decimal("330.00"),
                irrf_tax=Decimal("50.00"),
                esocial_synced=True,
            )

            # Create current month note and consolidation (October 2026)
            client_obj = Client.objects.create(name="Global Client Inc", address_neighborhood="Centro")
            inv = Invoice.objects.create(
                client=client_obj,
                invoice_number="INV-2026-001",
                currency="USD",
                exchange_rate_to_brl=Decimal("5.0000"),
                issue_date=date(2026, 10, 10),
            )
            NotaFiscal.objects.create(
                invoice=inv,
                nf_number="999",
                issue_date=date(2026, 10, 10),
                amount_brl=Decimal("10000.00"),
                description="Consulting Services",
                is_export=True,
            )

            response = self.client.get(reverse("dashboard"))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "core/mes_detail.html")

            # Check that financial blocks are rendered
            # Block 1: Faturamento
            self.assertContains(response, "Faturamento e Indicadores da Competência")
            self.assertContains(response, "10,000,00")

            # Block 2: A Pagar Neste Mês (from September 2026)
            self.assertContains(response, "A Pagar Neste Mês")
            self.assertContains(response, "450,00")  # DAS
            self.assertContains(response, "330,00")  # INSS
            self.assertContains(response, "50,00")   # IRRF

            # Block 3: Previsão para o Mês Seguinte
            self.assertContains(response, "Previsão para o Mês Seguinte")

            # Block 4: Notas Fiscais
            self.assertContains(response, "Notas Fiscais e Invoices Emitidas")
            self.assertContains(response, "INV-2026-001")
            self.assertContains(response, "Global Client Inc")

    def test_dashboard_view_month_parameter(self):
        # Access a specific month via query param
        response = self.client.get(reverse("dashboard") + "?month=2026-06")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["target_month"], date(2026, 6, 1))

    def test_consolidation_history_view(self):
        response = self.client.get(reverse("consolidation_history"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/dashboard.html")
        self.assertContains(response, "Histórico de Consolidação Mensal")
        self.assertContains(response, "Painel do Mês")

    def test_htmx_reconsolidate_month_redirects_when_next_param_present(self):
        c = MonthlyConsolidation.objects.create(
            month_year=date(2026, 10, 1),
            status="OUTDATED",
        )
        url = reverse("htmx_reconsolidate_month", kwargs={"pk": c.pk}) + "?next=" + reverse("dashboard")
        response = self.client.post(url)
        self.assertRedirects(response, reverse("dashboard"))

