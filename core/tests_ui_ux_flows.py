from datetime import date
from decimal import Decimal
from unittest.mock import patch
from urllib.parse import quote

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client as HttpClient, TestCase
from django.urls import reverse

from core.models import (
    Client,
    CompanySettings,
    EmailTemplate,
    Invoice,
    InvoiceItem,
    InvoiceTemplate,
    InvoiceTemplateItem,
    MonthlyConsolidation,
    NotaFiscal,
)


class UIUXFlowsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username="admin_test", email="admin@test.com", password="password123"
        )
        self.client_http = HttpClient()
        self.client_http.force_login(self.user)

        self.company = CompanySettings.objects.create(
            company_name="Synthetic Software Ltda",
            cnpj="11.222.333/0001-44",
            opening_date=date(2024, 1, 1),
            inscricao_municipal="123456",
            email="financeiro@synthetic.local",
            pfx_cert_pem="dummy_cert",
            pfx_key_pem="dummy_key",
        )

        self.client1 = Client.objects.create(
            name="Synthetic Client LLC",
            email="contact@syntheticclient.local",
            country="United States",
            address_city="New York",
            address_neighborhood="Downtown",
        )

    def test_redirect_with_next_helper_and_views(self):
        # 1. Invoice Delete with next
        draft_invoice = Invoice.objects.create(
            client=self.client1,
            invoice_number="INV-DEL-1",
            issue_date=date(2026, 10, 1),
            currency="USD",
            status=Invoice.Status.DRAFT,
        )
        target_next = "/invoices/?status=DRAFT&year=2026"
        res = self.client_http.post(
            reverse("invoice_delete", kwargs={"pk": draft_invoice.pk}),
            {"next": target_next},
        )
        self.assertRedirects(res, target_next)
        self.assertFalse(Invoice.objects.filter(pk=draft_invoice.pk).exists())

        # 2. Evil external redirect rejection
        draft_invoice2 = Invoice.objects.create(
            client=self.client1,
            invoice_number="INV-DEL-2",
            issue_date=date(2026, 10, 1),
            currency="USD",
            status=Invoice.Status.DRAFT,
        )
        res = self.client_http.post(
            reverse("invoice_delete", kwargs={"pk": draft_invoice2.pk}),
            {"next": "https://evil.com/phishing"},
        )
        self.assertRedirects(res, reverse("invoice_list"))

        # 3. Audit redirect with next
        with patch("core.views.audit_consolidations", return_value={"total_fixed": 0}):
            res = self.client_http.post(
                reverse("run_audit"),
                {"next": "/?month=2026-10"},
            )
            self.assertRedirects(res, "/?month=2026-10")

        # 4. Sync eSocial redirect with next
        with patch("core.services.esocial_services.sync_esocial_payroll", return_value=(0, "ok")):
            res = self.client_http.post(
                reverse("sync_esocial"),
                {"next": "/?month=2026-10"},
            )
            self.assertRedirects(res, "/?month=2026-10")

        # 5. Force daily invoices redirect with next
        with patch("core.tasks.process_daily_invoices_task.delay"):
            res = self.client_http.post(
                reverse("force_process_daily_invoices"),
                {"next": "/invoices/?status=FINALIZED"},
            )
            self.assertRedirects(res, "/invoices/?status=FINALIZED")

    def test_draft_invoice_metadata_update(self):
        draft_inv = Invoice.objects.create(
            client=self.client1,
            invoice_number="INV-META-1",
            issue_date=date(2026, 10, 1),
            currency="USD",
            status=Invoice.Status.DRAFT,
        )
        client2 = Client.objects.create(
            name="Synthetic Client 2",
            email="c2@synthetic.local",
            address_neighborhood="Centro",
        )

        # Update metadata in draft
        update_url = reverse("htmx_update_invoice_metadata", kwargs={"pk": draft_inv.pk})
        res = self.client_http.post(
            update_url,
            {
                "client": str(client2.pk),
                "issue_date": "2026-10-15",
                "currency": "CAD",
            },
        )
        self.assertEqual(res.status_code, 302)
        draft_inv.refresh_from_db()
        self.assertEqual(draft_inv.client, client2)
        self.assertEqual(draft_inv.issue_date, date(2026, 10, 15))
        self.assertEqual(draft_inv.currency, "CAD")

        # Update metadata via HTMX
        res_htmx = self.client_http.post(
            update_url,
            {
                "client": str(self.client1.pk),
                "issue_date": "2026-10-20",
                "currency": "EUR",
            },
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(res_htmx.status_code, 200)
        draft_inv.refresh_from_db()
        self.assertEqual(draft_inv.currency, "EUR")

        # Security check: Block metadata update when FINALIZED
        draft_inv.status = Invoice.Status.FINALIZED
        draft_inv.save()
        res_blocked = self.client_http.post(
            update_url,
            {
                "client": str(self.client1.pk),
                "issue_date": "2026-10-25",
                "currency": "USD",
            },
        )
        self.assertEqual(res_blocked.status_code, 403)

    def test_draft_invoice_item_inline_edit(self):
        draft_inv = Invoice.objects.create(
            client=self.client1,
            invoice_number="INV-ITEM-1",
            issue_date=date(2026, 10, 1),
            currency="USD",
            status=Invoice.Status.DRAFT,
        )
        item = InvoiceItem.objects.create(
            invoice=draft_inv,
            description="Initial Synthetic Service",
            quantity=Decimal("1.00"),
            unit_price_foreign=Decimal("1000.00"),
        )

        item_edit_url = reverse("htmx_edit_invoice_item", kwargs={"item_pk": item.pk})

        # GET returns edit partial row
        get_res = self.client_http.get(item_edit_url)
        self.assertEqual(get_res.status_code, 200)
        self.assertContains(get_res, "Initial Synthetic Service")
        self.assertContains(get_res, 'name="unit_price_foreign"')

        # POST updates item and returns invoice_item_list partial with updated total
        post_res = self.client_http.post(
            item_edit_url,
            {
                "description": "Updated Synthetic Consulting",
                "quantity": "2.00",
                "unit_price_foreign": "1500.00",
            },
        )
        self.assertEqual(post_res.status_code, 200)
        self.assertEqual(post_res.headers.get("HX-Trigger"), "itemUpdated")
        item.refresh_from_db()
        self.assertEqual(item.description, "Updated Synthetic Consulting")
        self.assertEqual(item.quantity, Decimal("2.00"))
        self.assertEqual(item.unit_price_foreign, Decimal("1500.00"))
        self.assertEqual(item.total_price_foreign, Decimal("3000.00"))

        # Security check: Block item edit when invoice is FINALIZED
        draft_inv.status = Invoice.Status.FINALIZED
        draft_inv.save()
        blocked_get = self.client_http.get(item_edit_url)
        self.assertEqual(blocked_get.status_code, 403)
        blocked_post = self.client_http.post(
            item_edit_url,
            {
                "description": "Should Fail",
                "quantity": "1.00",
                "unit_price_foreign": "100.00",
            },
        )
        self.assertEqual(blocked_post.status_code, 403)

    def test_client_crud_views(self):
        # 1. List clients
        res = self.client_http.get(reverse("client_list"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Synthetic Client LLC")

        # 2. Create client with next redirect
        create_res = self.client_http.post(
            reverse("client_create"),
            {
                "name": "New Canadian Client Inc",
                "email": "billing@canadianclient.local",
                "address_line1": "100 King St W",
                "address_number": "100",
                "address_neighborhood": "Financial District",
                "address_city": "Toronto",
                "address_state_province": "ON",
                "address_postal_code": "M5X 1A9",
                "address_country_code": "CA",
                "country": "Canada",
                "next": reverse("invoice_create"),
            },
        )
        created_client = Client.objects.get(name="New Canadian Client Inc")
        self.assertRedirects(create_res, f"{reverse('invoice_create')}?client_id={created_client.id}")
        self.assertEqual(created_client.address_country_code, "CA")

        # 3. Update client
        update_res = self.client_http.post(
            reverse("client_update", kwargs={"pk": created_client.pk}),
            {
                "name": "New Canadian Client Inc (Updated)",
                "email": "billing@canadianclient.local",
                "address_line1": "100 King St W",
                "address_number": "100",
                "address_neighborhood": "Financial District",
                "address_city": "Toronto",
                "address_state_province": "ON",
                "address_postal_code": "M5X 1A9",
                "address_country_code": "CA",
                "country": "Canada",
            },
        )
        self.assertRedirects(update_res, reverse("client_list"))
        created_client.refresh_from_db()
        self.assertEqual(created_client.name, "New Canadian Client Inc (Updated)")

        # 4. Delete client without invoices
        delete_res = self.client_http.post(
            reverse("client_delete", kwargs={"pk": created_client.pk})
        )
        self.assertRedirects(delete_res, reverse("client_list"))
        self.assertFalse(Client.objects.filter(pk=created_client.pk).exists())

        # 5. Delete client with invoices should be BLOCKED
        Invoice.objects.create(
            client=self.client1,
            invoice_number="INV-PROTECT-1",
            issue_date=date(2026, 10, 1),
            currency="USD",
        )
        blocked_delete = self.client_http.post(
            reverse("client_delete", kwargs={"pk": self.client1.pk})
        )
        self.assertRedirects(blocked_delete, reverse("client_list"))
        self.assertTrue(Client.objects.filter(pk=self.client1.pk).exists())

    def test_nfse_canceling_banner_and_button(self):
        nf = NotaFiscal.objects.create(
            nf_number="999901",
            issue_date=date(2026, 10, 1),
            amount_brl=Decimal("5000.00"),
            chave_acesso_nacional="35503082123456780001950000000000005432126100822290116",
            verification_code="TEST1234",
            is_canceled=False,
        )

        detail_url = reverse("nfse_detail", kwargs={"pk": nf.pk})

        # Initially not canceling
        res = self.client_http.get(detail_url)
        self.assertEqual(res.status_code, 200)
        self.assertNotContains(res, "Cancelamento em processamento...")

        # Set cache flag to simulate cancellation in progress
        cache.set(f"nfse_canceling_{nf.pk}", True, timeout=60)
        res_canceling = self.client_http.get(detail_url)
        self.assertEqual(res_canceling.status_code, 200)
        self.assertContains(res_canceling, "Cancelamento em processamento...")
        self.assertContains(res_canceling, "Cancelando...")

        # When cancelled, flag is cleared and banner disappears
        nf.is_canceled = True
        nf.save()
        res_after_cancel = self.client_http.get(detail_url)
        self.assertEqual(res_after_cancel.status_code, 200)
        self.assertNotContains(res_after_cancel, "Cancelamento em processamento...")
        self.assertContains(res_after_cancel, "Cancelada")

    def test_total_foreign_rendering_on_pages(self):
        inv = Invoice.objects.create(
            client=self.client1,
            invoice_number="INV-TOTAL-1",
            issue_date=date(2026, 10, 1),
            currency="USD",
            status=Invoice.Status.DRAFT,
        )
        InvoiceItem.objects.create(
            invoice=inv,
            description="Synthetic Monthly Retainer",
            quantity=Decimal("1.00"),
            unit_price_foreign=Decimal("2500.00"),
        )
        inv.status = Invoice.Status.FINALIZED
        inv.save()
        NotaFiscal.objects.create(
            invoice=inv,
            nf_number="999902",
            issue_date=date(2026, 10, 1),
            amount_brl=Decimal("12500.00"),
            verification_code="VF999",
            is_canceled=False,
        )

        # 1. Invoice List page displays total_foreign
        res_list = self.client_http.get(reverse("invoice_list"))
        self.assertEqual(res_list.status_code, 200)
        self.assertContains(res_list, "2,500,00")
        self.assertContains(res_list, "USD")

        # 2. Month detail dashboard renders total_foreign
        res_dash = self.client_http.get(reverse("dashboard") + "?month=2026-10")
        self.assertEqual(res_dash.status_code, 200)
        self.assertContains(res_dash, "USD 2,500,00")

    def test_client_form_validation(self):
        from core.forms import ClientForm

        # Required fields: name and address_neighborhood
        form_invalid = ClientForm(data={"name": "Client Without Neighborhood"})
        self.assertFalse(form_invalid.is_valid())
        self.assertIn("address_neighborhood", form_invalid.errors)

        form_valid = ClientForm(
            data={
                "name": "Complete Synthetic Client",
                "email": "test@synthetic.local",
                "address_neighborhood": "Downtown",
                "address_country_code": "ca",
            }
        )
        self.assertTrue(form_valid.is_valid())
        self.assertEqual(form_valid.cleaned_data["address_country_code"], "CA")

    def test_htmx_delete_invoice_item_and_oob_badge(self):
        draft_inv = Invoice.objects.create(
            client=self.client1,
            invoice_number="INV-DEL-ITEM-1",
            issue_date=date(2026, 10, 1),
            currency="USD",
            status=Invoice.Status.DRAFT,
        )
        item1 = InvoiceItem.objects.create(
            invoice=draft_inv,
            description="Item 1",
            quantity=Decimal("1.00"),
            unit_price_foreign=Decimal("1000.00"),
        )
        item2 = InvoiceItem.objects.create(
            invoice=draft_inv,
            description="Item 2",
            quantity=Decimal("2.00"),
            unit_price_foreign=Decimal("500.00"),
        )
        self.assertEqual(draft_inv.total_foreign, Decimal("2000.00"))

        del_url = reverse("htmx_delete_invoice_item", kwargs={"item_pk": item1.pk})
        res = self.client_http.post(del_url, HTTP_HX_REQUEST="true")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'id="invoice-total-badge"')
        self.assertContains(res, 'hx-swap-oob="true"')
        self.assertContains(res, "1,000,00")
        self.assertFalse(InvoiceItem.objects.filter(pk=item1.pk).exists())
        self.assertTrue(InvoiceItem.objects.filter(pk=item2.pk).exists())

    def test_htmx_reconsolidate_month_returns_hx_refresh_on_historico(self):
        consolidation = MonthlyConsolidation.objects.create(
            month_year=date(2026, 10, 1),
            status="OUTDATED",
            total_revenue_internal=Decimal("5000.00"),
            actual_pro_labore_paid=Decimal("1500.00"),
        )
        reconcile_url = reverse("htmx_reconsolidate_month", kwargs={"pk": consolidation.pk})
        res = self.client_http.post(reconcile_url, HTTP_HX_REQUEST="true")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("HX-Refresh"), "true")

    def test_template_views_render_successfully(self):
        res_inv_templates = self.client_http.get(reverse("invoice_template_list"))
        self.assertEqual(res_inv_templates.status_code, 200)
        self.assertContains(res_inv_templates, "Invoice Templates")

        res_email_templates = self.client_http.get(reverse("email_template_list"))
        self.assertEqual(res_email_templates.status_code, 200)
        self.assertContains(res_email_templates, "Email Templates")

    def test_htmx_edit_invoice_item_macro_expansion_and_formatting(self):
        draft_inv = Invoice.objects.create(
            client=self.client1,
            invoice_number="INV-EDIT-MACRO-1",
            issue_date=date(2026, 10, 1),
            currency="USD",
            status=Invoice.Status.DRAFT,
        )
        item = InvoiceItem.objects.create(
            invoice=draft_inv,
            description="Initial Description",
            quantity=Decimal("1.50"),
            unit_price_foreign=Decimal("250.75"),
        )

        # GET inline edit row - verify dot-formatted decimal outputs
        edit_url = reverse("htmx_edit_invoice_item", kwargs={"item_pk": item.pk})
        res_get = self.client_http.get(edit_url)
        self.assertEqual(res_get.status_code, 200)
        self.assertContains(res_get, 'value="1.50"')
        self.assertContains(res_get, 'value="250.75"')

        # POST inline edit with macros
        res_post = self.client_http.post(
            edit_url,
            {
                "description": "Consulting for {{ client_name }} in {{ currency }}",
                "quantity": "2.00",
                "unit_price_foreign": "300.00",
            },
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(res_post.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.quantity, Decimal("2.00"))
        self.assertEqual(item.unit_price_foreign, Decimal("300.00"))
        self.assertIn("Synthetic Client LLC", item.description)
        self.assertIn("USD", item.description)

    def test_client_create_redirects_with_client_id_and_prepopulates_invoice_create(self):
        # 1. Create client with ?next=/invoices/new/
        res = self.client_http.post(
            reverse("client_create") + "?next=/invoices/new/",
            {
                "name": "New Client From Wizard",
                "email": "wizard@client.local",
                "address_neighborhood": "Central",
                "address_city": "Toronto",
                "country": "Canada",
                "address_country_code": "CA",
            },
        )
        new_client = Client.objects.get(name="New Client From Wizard")
        expected_redirect = f"/invoices/new/?client_id={new_client.id}"
        self.assertRedirects(res, expected_redirect)

        # 2. GET invoice_create with client_id pre-populates the form
        res_inv = self.client_http.get(expected_redirect)
        self.assertEqual(res_inv.status_code, 200)
        self.assertEqual(str(res_inv.context["form"]["client"].value()), str(new_client.id))

        # 3. Create client with complex next containing existing query parameters and fragment
        res_complex = self.client_http.post(
            reverse("client_create") + "?next=" + quote("/invoices/new/?mode=advanced&template=1#items"),
            {
                "name": "Complex Next Client",
                "email": "complex@client.local",
                "address_neighborhood": "Central",
                "address_city": "Vancouver",
                "country": "Canada",
                "address_country_code": "CA",
            },
        )
        complex_client = Client.objects.get(name="Complex Next Client")
        self.assertEqual(res_complex.status_code, 302)
        location = res_complex.headers.get("Location")
        self.assertIn(f"client_id={complex_client.id}", location)
        self.assertIn("mode=advanced", location)
        self.assertIn("template=1", location)
        self.assertTrue(location.endswith("#items"))

    def test_require_company_settings_middleware_redirect_and_cache(self):
        from core.middleware import COMPANY_SETTINGS_CACHE_KEY

        # Temporarily delete company settings
        CompanySettings.objects.all().delete()
        cache.delete(COMPANY_SETTINGS_CACHE_KEY)

        # Request protected view -> redirected to company_settings with ?next=
        res = self.client_http.get("/invoices/?status=DRAFT")
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse("company_settings"), res.url)
        self.assertIn("next=", res.url)

        # POST to company_settings clears cache (test with follow=False to inspect cache before next request)
        cache.set(COMPANY_SETTINGS_CACHE_KEY, False)
        post_data = {
            "company_name": "Recreated Synthetic Ltda",
            "cnpj": "12.345.678/0001-95",
            "inscricao_municipal": "123456",
            "opening_date": "01/01/2024",
            "email": "recreated@synthetic.local",
            "address_line1": "Rua Teste",
            "address_city_ibge": "3550308",
            "nfse_provider": "NACIONAL",
            "next_document_number": 1,
            "document_series": "4242",
            "auto_invoice_hour": 9,
            "next": "/invoices/?status=DRAFT",
        }
        res_post = self.client_http.post(reverse("company_settings"), post_data, follow=False)
        self.assertEqual(res_post.status_code, 302)
        self.assertEqual(res_post.headers.get("Location"), "/invoices/?status=DRAFT")
        self.assertIsNone(cache.get(COMPANY_SETTINGS_CACHE_KEY))

        # Following the redirect repopulates the cache with True
        res_follow = self.client_http.get(res_post.headers.get("Location"))
        self.assertEqual(res_follow.status_code, 200)
        self.assertTrue(cache.get(COMPANY_SETTINGS_CACHE_KEY))

    def test_nfse_detail_client_address_city_no_leading_comma(self):
        invoice = Invoice.objects.create(
            client=self.client1,
            invoice_number="INV-NF-CITY-1",
            issue_date=date(2026, 10, 1),
            currency="USD",
            status=Invoice.Status.FINALIZED,
        )
        nf = NotaFiscal.objects.create(
            invoice=invoice,
            chave_acesso_nacional="35503082123456780001950000000000005432126100822290116",
            nf_number="9988",
            issue_date=date(2026, 10, 1),
            amount_brl=Decimal("1000.00"),
        )

        res = self.client_http.get(reverse("nfse_detail", kwargs={"pk": nf.pk}))
        self.assertEqual(res.status_code, 200)
        # Should render "New York, United States" and NOT "<small class="text-muted">, United States</small>"
        self.assertContains(res, "New York, United States")
        self.assertNotContains(res, '<small class="text-muted">, United States</small>')

        # Client with country only should render "United States" without leading comma
        client_no_city = Client.objects.create(
            name="Client Without City LLC",
            email="nocity@client.local",
            country="United States",
            address_city="",
            address_neighborhood="Uptown",
        )
        invoice2 = Invoice.objects.create(
            client=client_no_city,
            invoice_number="INV-NF-CITY-2",
            issue_date=date(2026, 10, 1),
            currency="USD",
            status=Invoice.Status.FINALIZED,
        )
        nf2 = NotaFiscal.objects.create(
            invoice=invoice2,
            chave_acesso_nacional="35503082123456780001950000000000005432126100822290117",
            nf_number="9989",
            issue_date=date(2026, 10, 1),
            amount_brl=Decimal("1000.00"),
        )
        res2 = self.client_http.get(reverse("nfse_detail", kwargs={"pk": nf2.pk}))
        self.assertEqual(res2.status_code, 200)
        self.assertContains(res2, '<small class="text-muted">United States</small>')
        self.assertNotContains(res2, ", United States")

    def test_cancel_tasks_clear_cache_on_failure(self):
        from core.tasks.nfse_tasks import cancel_nfse_standalone_task
        from core.tasks.invoices_tasks import cancel_invoice_task

        invoice = Invoice.objects.create(
            client=self.client1,
            invoice_number="INV-TASK-FAIL-1",
            issue_date=date(2026, 10, 1),
            currency="USD",
            status=Invoice.Status.FINALIZED,
        )
        nf = NotaFiscal.objects.create(
            invoice=invoice,
            chave_acesso_nacional="35503082123456780001950000000000005432126100822290116",
            nf_number="9989",
            issue_date=date(2026, 10, 1),
            amount_brl=Decimal("1000.00"),
        )

        # Set cache key
        cache_key = f"nfse_canceling_{nf.pk}"
        cache.set(cache_key, True, timeout=60)

        # Test cancel_invoice_task deterministic failure clears cache
        with patch("core.services.nfse_services.cancel_nota_fiscal") as mock_cancel:
            from core.nfse.base import CancelResult
            mock_cancel.return_value = CancelResult(sucesso=False, erros=["Test Deterministic Error"])
            with self.assertRaises(Exception):
                cancel_invoice_task.apply(args=[invoice.id], throw=True)
            self.assertIsNone(cache.get(cache_key))

        # Test cancel_nfse_standalone_task failure clears cache
        cache.set(cache_key, True, timeout=60)
        with patch("core.services.nfse_services.cancel_nota_fiscal") as mock_cancel:
            from core.nfse.base import CancelResult
            mock_cancel.return_value = CancelResult(sucesso=False, erros=["Test Standalone Error"])
            with self.assertRaises(Exception):
                cancel_nfse_standalone_task.apply(args=[nf.id], throw=True)
            self.assertIsNone(cache.get(cache_key))

    def test_detail_views_safe_back_url(self):
        invoice = Invoice.objects.create(
            client=self.client1,
            invoice_number="INV-BACK-1",
            issue_date=date(2026, 10, 1),
            currency="USD",
            status=Invoice.Status.DRAFT,
        )
        nf = NotaFiscal.objects.create(
            invoice=invoice,
            chave_acesso_nacional="35503082123456780001950000000000005432126100822290116",
            nf_number="9990",
            issue_date=date(2026, 10, 1),
            amount_brl=Decimal("1000.00"),
        )

        # 1. Safe next URL on invoice_detail
        res = self.client_http.get(
            reverse("invoice_detail", kwargs={"pk": invoice.pk}) + "?next=/?month=2026-10"
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["back_url"], "/?month=2026-10")

        # 2. Malicious next URL rejected on invoice_detail
        res_evil = self.client_http.get(
            reverse("invoice_detail", kwargs={"pk": invoice.pk}) + "?next=https://evil.com"
        )
        self.assertEqual(res_evil.status_code, 200)
        self.assertEqual(res_evil.context["back_url"], reverse("invoice_list"))

        # 3. Safe next URL on nfse_detail
        res_nf = self.client_http.get(
            reverse("nfse_detail", kwargs={"pk": nf.pk}) + "?next=/nfse/?provider=NACIONAL"
        )
        self.assertEqual(res_nf.status_code, 200)
        self.assertEqual(res_nf.context["back_url"], "/nfse/?provider=NACIONAL")

        # 4. Malicious next URL rejected on nfse_detail
        res_nf_evil = self.client_http.get(
            reverse("nfse_detail", kwargs={"pk": nf.pk}) + "?next=https://evil.com"
        )
        self.assertEqual(res_nf_evil.status_code, 200)
        self.assertEqual(res_nf_evil.context["back_url"], reverse("nfse_list"))

    def test_htmx_update_invoice_metadata_invalid_state(self):
        draft_inv = Invoice.objects.create(
            client=self.client1,
            invoice_number="INV-META-INV-1",
            issue_date=date(2026, 10, 1),
            currency="USD",
            status=Invoice.Status.DRAFT,
        )
        url = reverse("htmx_update_invoice_metadata", kwargs={"pk": draft_inv.pk})
        res = self.client_http.post(
            url,
            {
                "client": "00000000-0000-0000-0000-000000000000",  # non-existent client UUID
                "issue_date": "invalid-date",
                "currency": "",
            },
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.context["metadata_form_invalid"])
        self.assertIsNotNone(res.context["metadata_errors"])
        self.assertContains(res, 'id="invoice-metadata-edit"')
        self.assertContains(res, 'alert alert-danger')

    def test_unified_template_list_views_and_delete_redirect(self):
        inv_tmpl = InvoiceTemplate.objects.create(name="Synthetic Template A", currency="USD")
        email_tmpl = EmailTemplate.objects.create(name="Synthetic Email Template A", subject="Invoice {{ invoice_number }}", body="Hello")

        # 1. Access invoice templates list default
        res = self.client_http.get(reverse("invoice_template_list"))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["active_tab"], "invoices")
        self.assertIn(inv_tmpl, res.context["invoice_templates"])
        self.assertIn(email_tmpl, res.context["email_templates"])
        self.assertContains(res, "Synthetic Template A")
        self.assertContains(res, "Synthetic Email Template A")

        # 2. Access with tab=emails
        res_emails = self.client_http.get(reverse("invoice_template_list") + "?tab=emails")
        self.assertEqual(res_emails.status_code, 200)
        self.assertEqual(res_emails.context["active_tab"], "emails")

        # 3. Access email templates list url
        res_email_view = self.client_http.get(reverse("email_template_list"))
        self.assertEqual(res_email_view.status_code, 200)
        self.assertEqual(res_email_view.context["active_tab"], "emails")

        # 4. GET to invoice_template_delete safely redirects
        del_get_res = self.client_http.get(reverse("invoice_template_delete", kwargs={"pk": inv_tmpl.pk}))
        self.assertRedirects(del_get_res, reverse("invoice_template_list"))
        self.assertTrue(InvoiceTemplate.objects.filter(pk=inv_tmpl.pk).exists())

    def test_dashboard_view_pending_invoices_and_closed_month(self):
        from dateutil.relativedelta import relativedelta
        from django.utils import timezone

        today = timezone.localdate()
        current_m = today.replace(day=1)
        closed_m = current_m - relativedelta(months=2)

        inv = Invoice.objects.create(
            client=self.client1,
            invoice_number="INV-DASH-1",
            issue_date=current_m,
            currency="USD",
            status=Invoice.Status.DRAFT,
        )

        # Open month dashboard (current month)
        res = self.client_http.get(reverse("dashboard") + f"?month={current_m.strftime('%Y-%m')}")
        self.assertEqual(res.status_code, 200)
        self.assertIn(inv, res.context["pending_invoices"])
        self.assertFalse(res.context["consolidation"].is_closed)
        self.assertContains(res, "INV-DASH-1")

        # Closed month dashboard (2 months ago)
        res_closed = self.client_http.get(reverse("dashboard") + f"?month={closed_m.strftime('%Y-%m')}")
        self.assertEqual(res_closed.status_code, 200)
        self.assertTrue(res_closed.context["consolidation"].is_closed)

    def test_htmx_update_invoice_metadata_invoice_number(self):
        inv = Invoice.objects.create(
            client=self.client1,
            invoice_number="INV-NUM-OLD",
            issue_date=date(2026, 10, 1),
            currency="USD",
            status=Invoice.Status.DRAFT,
        )
        Invoice.objects.create(
            client=self.client1,
            invoice_number="INV-NUM-OTHER",
            issue_date=date(2026, 10, 1),
            currency="USD",
            status=Invoice.Status.DRAFT,
        )
        url = reverse("htmx_update_invoice_metadata", kwargs={"pk": inv.pk})

        # Valid invoice number change with next URL preservation
        res = self.client_http.post(
            url,
            {
                "client": str(self.client1.pk),
                "invoice_number": "INV-NUM-NEW",
                "issue_date": "2026-10-02",
                "currency": "USD",
                "next": "/invoices/?status=DRAFT",
            },
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.context["metadata_saved"])
        self.assertEqual(res.context["back_url"], "/invoices/?status=DRAFT")
        inv.refresh_from_db()
        self.assertEqual(inv.invoice_number, "INV-NUM-NEW")

        # Non-HTMX post preserves next URL
        res_non_htmx = self.client_http.post(
            url,
            {
                "client": str(self.client1.pk),
                "invoice_number": "INV-NUM-NONHTMX",
                "issue_date": "2026-10-03",
                "currency": "EUR",
                "next": "/invoices/?status=DRAFT",
            },
        )
        self.assertRedirects(res_non_htmx, "/invoices/?status=DRAFT")
        inv.refresh_from_db()
        self.assertEqual(inv.invoice_number, "INV-NUM-NONHTMX")

        # Duplicate invoice number error
        res_dup = self.client_http.post(
            url,
            {
                "client": str(self.client1.pk),
                "invoice_number": "INV-NUM-OTHER",
                "issue_date": "2026-10-02",
                "currency": "USD",
            },
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(res_dup.status_code, 200)
        self.assertTrue(res_dup.context["metadata_form_invalid"])
        self.assertIn("invoice_number", res_dup.context["metadata_errors"])

    def test_lifecycle_actions_safe_redirects(self):
        # 1. Revert to draft with next
        inv = Invoice.objects.create(
            client=self.client1,
            invoice_number="INV-REV-1",
            issue_date=date(2026, 10, 1),
            currency="USD",
            status=Invoice.Status.FINALIZED,
        )
        res = self.client_http.post(
            reverse("revert_invoice_to_draft", kwargs={"pk": inv.pk}),
            {"next": "/?month=2026-10"},
        )
        self.assertRedirects(res, "/?month=2026-10")
        inv.refresh_from_db()
        self.assertEqual(inv.status, Invoice.Status.DRAFT)

        # 2. NFS-e link invoice with next
        nf = NotaFiscal.objects.create(
            chave_acesso_nacional="11112222333344445555666677778888999900001111222233",
            nf_number="8888",
            issue_date=date(2026, 10, 1),
            amount_brl=Decimal("500.00"),
        )
        inv2 = Invoice.objects.create(
            client=self.client1,
            invoice_number="INV-LINK-1",
            issue_date=date(2026, 10, 1),
            currency="USD",
            status=Invoice.Status.FINALIZED,
        )
        res_link = self.client_http.post(
            reverse("nfse_link_invoice", kwargs={"pk": nf.pk}),
            {"invoice_id": str(inv2.pk), "next": "/nfse/?provider=NACIONAL"},
        )
        self.assertRedirects(res_link, "/nfse/?provider=NACIONAL")
        nf.refresh_from_db()
        self.assertEqual(nf.invoice, inv2)

        # 3. NFS-e refresh with next
        with patch("core.services.nfse_services.sync_nota_fiscal", return_value=(True, "Synced")):
            res_ref = self.client_http.post(
                reverse("nfse_refresh", kwargs={"pk": nf.pk}),
                {"next": "/nfse/"},
            )
            self.assertRedirects(res_ref, "/nfse/")

    def test_nfse_import_renders_partial_template(self):
        with patch("core.tasks.import_nfses_task.delay") as mock_delay:
            mock_task = type("MockTask", (), {"id": "test-task-123"})()
            mock_delay.return_value = mock_task

            res = self.client_http.post(reverse("nfse_import"), {"provider": "NACIONAL"})
            self.assertEqual(res.status_code, 200)
            self.assertTemplateUsed(res, "core/partials/import_status.html")
            self.assertEqual(res.context["state"], "pending")
            self.assertEqual(res.context["task_id"], "test-task-123")
            self.assertContains(res, 'id="importModalContent"')
            self.assertContains(res, "btn-close")


