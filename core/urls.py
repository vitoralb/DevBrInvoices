from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path("", views.dashboard_view, name="dashboard"),
    path(
        "htmx/consolidate/<int:pk>/",
        views.htmx_reconsolidate_month,
        name="htmx_reconsolidate_month",
    ),
    path("audit/", views.run_audit, name="run_audit"),
    path("tasks/", views.tasks_view, name="tasks_view"),
    # Invoices
    path("invoices/", views.invoice_list, name="invoice_list"),
    path("invoices/new/", views.invoice_create, name="invoice_create"),
    path("invoices/<uuid:pk>/", views.invoice_detail, name="invoice_detail"),
    path("invoices/<uuid:pk>/delete/", views.invoice_delete, name="invoice_delete"),
    path(
        "invoices/<uuid:pk>/revert/",
        views.revert_invoice_to_draft,
        name="revert_invoice_to_draft",
    ),
    path("invoices/<uuid:pk>/cancel/", views.cancel_invoice, name="cancel_invoice"),
    path(
        "invoices/<uuid:pk>/add-item/",
        views.htmx_add_invoice_item,
        name="htmx_add_invoice_item",
    ),
    path(
        "invoices/<uuid:pk>/update-number/",
        views.htmx_update_invoice_number,
        name="htmx_update_invoice_number",
    ),
    path(
        "invoices/item/<uuid:item_pk>/delete/",
        views.htmx_delete_invoice_item,
        name="htmx_delete_invoice_item",
    ),
    path("invoices/<uuid:pk>/convert-nf/", views.issue_nfse, name="issue_nfse"),
    path(
        "invoices/<uuid:pk>/pdf/",
        views.generate_invoice_pdf,
        name="generate_invoice_pdf",
    ),
    path(
        "invoices/<uuid:pk>/nfse-pdf/",
        views.download_nfse_pdf,
        name="download_nfse_pdf",
    ),
    path("invoices/<uuid:pk>/clone/", views.clone_invoice, name="clone_invoice"),
    path(
        "invoices/<uuid:pk>/finalize/", views.finalize_invoice, name="finalize_invoice"
    ),
    path("invoices/<uuid:pk>/email/", views.email_invoice, name="email_invoice"),
    path(
        "invoices/force-daily/",
        views.force_process_daily_invoices,
        name="force_process_daily_invoices",
    ),
    # NFS-es
    path("nfse/", views.nfse_list, name="nfse_list"),
    path("nfse/import/", views.nfse_import, name="nfse_import"),
    path(
        "nfse/import/status/<str:task_id>/",
        views.htmx_import_status,
        name="htmx_import_status",
    ),
    path("nfse/<uuid:pk>/", views.nfse_detail, name="nfse_detail"),
    path("nfse/<uuid:pk>/pdf/", views.nfse_download_pdf, name="nfse_download_pdf"),
    path(
        "nfse/<uuid:pk>/link-invoice/",
        views.nfse_link_invoice,
        name="nfse_link_invoice",
    ),
    path("nfse/<uuid:pk>/cancel/", views.nfse_cancel, name="nfse_cancel"),
    path(
        "htmx/fetch-exchange-rate/",
        views.htmx_fetch_exchange_rate,
        name="htmx_fetch_exchange_rate",
    ),
    # Templates
    path("templates/emails/", views.email_template_list, name="email_template_list"),
    path(
        "templates/invoices/", views.invoice_template_list, name="invoice_template_list"
    ),
    path(
        "templates/email/<uuid:pk>/edit/",
        views.email_template_update,
        name="email_template_update",
    ),
    path(
        "templates/invoice/new/",
        views.invoice_template_create,
        name="invoice_template_create",
    ),
    path(
        "templates/invoice/<uuid:pk>/edit/",
        views.invoice_template_update,
        name="invoice_template_update",
    ),
    path(
        "templates/invoice/<uuid:pk>/delete/",
        views.invoice_template_delete,
        name="invoice_template_delete",
    ),
    path(
        "htmx/template-details/<uuid:pk>/",
        views.htmx_get_invoice_template,
        name="htmx_get_invoice_template",
    ),
    path("settings/company/", views.company_settings_view, name="company_settings"),
    path(
        "settings/company/remove-cert/",
        views.remove_certificate_view,
        name="remove_certificate",
    ),
    path("api/cep/<str:cep>/", views.api_cep_view, name="api_cep"),
    path("api/cnpj/<str:cnpj>/", views.api_cnpj_view, name="api_cnpj"),
    path(
        "api/taxes/",
        __import__("utils.taxes.api", fromlist=["api_tax_tables"]).api_tax_tables,
        name="api_taxes",
    ),
]
