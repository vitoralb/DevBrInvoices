# UI/UX & Frontend Architecture Guidelines — Notas Project

This document establishes the mandatory design system, theming rules, mobile responsiveness standards, interaction patterns, and redirection conventions for the `notas` project. All AI agents and developers must strictly follow these guidelines whenever creating or modifying templates, forms, views, or frontend scripts.

---

## 1. Visual Design System & Typography

The application follows a **Modern Fintech SaaS aesthetic** (inspired by Stripe and Linear): clean visual hierarchy, subtle borders, soft elevation, and high-legibility financial figures.

- **Typography**:
  - **Primary UI Font**: `Inter` (`400`, `500`, `600`, `700`) for all body text, headings, labels, and navigation.
  - **Monospace Font**: `JetBrains Mono` (or `.font-monospace`) for invoice numbers, NFS-e numbers, municipal verification codes, NSU badges, XML previews, and tabular currency figures (`font-variant-numeric: tabular-nums`).
- **Page & Container Hierarchy**:
  - `base.html` already wraps `{% block content %}` inside `<main class="container mb-5">`. **Never** add a redundant outer `<div class="container">` inside child templates.
  - Every child template **must** define `{% block title %}<Page Title> - {{ PROJECT_NAME }}{% endblock %}`.
  - Group related content and form sections inside `.card.shadow-sm` containers with `.card-header` and `.card-body` rather than placing raw form controls directly on the page background.
- **Iconography**:
  - **Strictly use Bootstrap Icons (`<i class="bi bi-*"></i>`)** for all buttons, navigation items, status indicators, and table actions.
  - **Never use Unicode emojis** (`📥`, `📦`, `🔄`, `👁️`, `📄`, `⚠️`, etc.) in UI controls, headers, or table actions, as they render inconsistently across operating systems and clash with dark/light theme styling.

---

## 2. Dark & Light Theme Compatibility (`data-bs-theme`)

The application supports **Light**, **Dark**, and **System (Auto)** modes via Bootstrap 5.3+ `data-bs-theme="light|dark"` on `<html>`, persisted in `localStorage`. Every view and component must look native and high-contrast in both themes.

### 2.1. Banned vs. Required Utility Classes
Hardcoded light-palette utility classes break Dark Mode by rendering bright white boxes or black-on-dark-gray text. Follow this strict mapping:

| Avoid (Breaks Dark Mode) | Use Instead (Theme-Adaptive) | Why |
| :--- | :--- | :--- |
| `.bg-light`, `.bg-white` | `.bg-body-tertiary` or `.bg-body-secondary` | Adapts seamlessly between soft slate/gray in Light Mode and elevated dark slate in Dark Mode. |
| `.text-dark` (on general surfaces) | `.text-body` or `.text-body-emphasis` | `.text-dark` forces `#212529` black text, which is invisible on dark cards/surfaces. (Only use `.text-dark` inside explicitly bright solid badges like `.badge.bg-warning.text-dark`). |
| `.text-dark` inside `.bg-*-subtle` | `.text-*-emphasis` (e.g., `.text-warning-emphasis`, `.text-info-emphasis`) | In Dark Mode, `.bg-warning-subtle` and `.bg-info-subtle` are dark-tinted backgrounds; `.text-*-emphasis` switches to a light tint automatically. |
| `.thead.table-light` | `.thead` with `.bg-body-tertiary` (or default `<thead>`) | `.table-light` forces a stark `#f8f9fa` header row inside dark tables. |
| `.btn-outline-dark` | `.btn-outline-secondary` | `.btn-outline-dark` has a `#212529` border and text that disappear completely in Dark Mode. |
| `.badge.bg-light.text-dark` | `.badge.bg-body-secondary.text-body.border` | Prevents jarring white pills in Dark Mode while keeping crisp borders in Light Mode. |
| Inline `background-color: #e9ecef` on readonly inputs | `.bg-body-secondary.text-body-secondary` | Hardcoded `#e9ecef` combined with Dark Mode's light text color (`#dee2e6`) makes readonly input values unreadable. |

### 2.2. Third-Party Widgets & Datepickers
- **Flatpickr**: Any `input[type="date"]` enhanced by Flatpickr must inherit theme-aware CSS variables (`--bs-body-bg`, `--bs-body-color`, `--bs-border-color`, `--bs-tertiary-bg`) so calendar popups, month headers, and day cells adapt dynamically when switching between Dark and Light modes.

### 2.3. Semantic Status Badges
Always use consistent semantic badge colors across all list and detail views:
- **Finalized / Authorized / Completed**: `badge bg-success-subtle text-success-emphasis border border-success-subtle` (or `badge bg-success`)
- **Processing / Pending**: `badge bg-warning-subtle text-warning-emphasis border border-warning-subtle` (or `badge bg-warning text-dark`)
- **Canceled / Error / Revoked**: `badge bg-danger-subtle text-danger-emphasis border border-danger-subtle` (or `badge bg-danger`)
- **Draft / Inactive**: `badge bg-secondary-subtle text-secondary-emphasis border border-secondary-subtle` (or `badge bg-secondary`)

---

## 3. Mobile Responsiveness & Viewport Ergonomics

All pages must function cleanly down to a **`320px–375px` mobile viewport** without horizontal page scrolling or clipped controls.

- **Tables**:
  - Every `<table class="table">` **must** be wrapped in `<div class="table-responsive">`.
  - Action columns in tables should keep buttons compact (`btn-sm`) and use `text-nowrap` so action buttons do not stack awkwardly inside narrow cells.
- **Flex Headers & Toolbars**:
  - Page headers and `.card-header` bars that combine titles and action buttons **must** include `flex-wrap gap-2` (e.g., `d-flex flex-wrap justify-content-between align-items-center gap-2`).
  - Never place 3+ buttons inside a narrow column header (`col-md-4`) without `flex-wrap gap-1`.
  - Long identifiers (UUIDs, Celery task IDs, access keys, XML strings) **must** use `.text-break` or `.text-truncate` so they do not push sibling buttons off-screen on mobile.
- **Responsive Grid Breakpoints**:
  - Always include row gutters (`row g-3`) when stacking cards or form columns so stacked items on mobile (`< 768px`) maintain vertical separation.
  - Use `h-100` on KPI summary cards inside a `.row.g-3` so cards in the same row match heights even when labels wrap.
  - Avoid narrow `col-md-1` columns for text inputs (like `UF` or `Quantidade`), which shrink to `< 60px` on tablets (`768px`) and clip input text; use `col-4 col-md-2` or `col-6 col-md-2` instead.
  - On inline multi-column forms (such as "Add Item"), ensure submit buttons in `col-12 col-sm-*` columns use `w-100` so they span cleanly on mobile.
- **No Hardcoded Pixel Widths**:
  - Avoid inline `style="width: 200px;"` or large `min-width` values inside flex containers or `.btn-group` elements that can exceed mobile viewport widths.

---

## 4. Redirection Flows & Navigation Context Preservation

Users must never lose their active page, selected month, or list filter context after executing an action.

### 4.1. Context-Preserving Redirects (`?next=`)
- **Rule**: Any POST action that can be triggered from multiple pages or from a filtered view (e.g., `sync_esocial`, `import_esocial_backup`, `export_esocial_backup`, `run_audit`, `invoice_delete`, `force_process_daily_invoices`, `htmx_reconsolidate_month`) **must**:
  1. Include `<input type="hidden" name="next" value="{{ request.get_full_path }}">` in the triggering `<form>`.
  2. Validate `next_url = request.POST.get("next") or request.GET.get("next")` in the view using `url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()})` and redirect to `next_url` before falling back to a default route.
- **Query String Encoding**:
  - Never concatenate unencoded `?` parameters into a form's `action="..."` attribute (e.g., `action="/path/?next=/?month=2026-03"`). Always pass `next` via `<input type="hidden" name="next" value="{{ request.get_full_path }}">`.

### 4.2. Breadcrumbs, Back-Links & Cancel Buttons
- Every detail view (`invoice_detail.html`, `nfse_detail.html`) must provide a clear back-navigation link at the top left (`← Voltar para Invoices`, `← Voltar para NFS-es`).
- Every create/edit form (`invoice_form.html`, `client_form.html`, `invoice_template_form.html`, `email_template_form.html`) must provide a `Cancelar` button next to the primary submit button that returns the user to the appropriate list or detail page.

### 4.3. Cascading Data & HTMX Refresh Integrity
- When an HTMX action mutates data that affects summary KPI cards or adjacent rows on the same page (such as recalculating a monthly consolidation on `/historico/`, which cascades RBT12 and Fator R projections and changes top-level totals), **do not** swap only a single `<tr>` in isolation. Either refresh the full content container (KPI cards + table) or trigger `HX-Refresh: true` so the UI never displays stale financial figures.

---

## 5. Interaction UX: Confirmations, Spinners, Alerts & Validation

### 5.1. Contextual Bootstrap Modals Over Native `confirm()` / `alert()`
- **Never use native browser `confirm(...)` or `alert(...)`**. Native dialogs block the browser thread, ignore Dark/Light themes, and lack domain context.
- Use the global reusable Bootstrap confirmation modal (`#globalConfirmModal` in `base.html`) via declarative `data-confirm-*` attributes (`data-confirm-title`, `data-confirm-message`, `data-confirm-variant="danger|warning|primary"`, `data-confirm-button-text`) or dedicated contextual modals.
- For fiscal or external actions (e.g., finalizing an invoice that dispatches emails to a client, or canceling an NFS-e on Sefin/Prefeitura), clearly state the consequence in the modal body.

### 5.2. Loading States & Async Polling
- **Synchronous Network / Compute Actions**: Every form submission or HTMX trigger that performs external API calls, XML/ZIP processing, or PDF generation must automatically disable the submit button and display an inline `<span class="spinner-border spinner-border-sm"></span>` while in flight.
- **Asynchronous Celery Tasks**: Whenever a view dispatches a background Celery task and redirects back to a detail page (such as `finalize_invoice`, `cancel_invoice`, or `nfse_cancel`), the detail page **must** display a live processing banner with HTMX polling (`hx-trigger="every 3s"`) and disable conflicting action buttons until the background task finishes.

### 5.3. Django Messages & Form Validation Errors
- **Django `error` Tag Mapping**: Bootstrap 5 uses `.alert-danger`, whereas Django's default `messages.error()` tag is `error`. `base.html` (and/or `MESSAGE_TAGS` in `settings.py`) must map `error` -> `danger` so error banners are always visibly styled in red.
- **Form & Formset Errors**:
  - Never use unstyled `{{ form.as_p }}`. Render fields explicitly with `.form-label`, `.form-control` / `.form-select`, and `.mb-3` wrappers.
  - Always render `{{ form.non_field_errors }}`, field-level `{{ field.errors }}`, and—on pages with formsets (`invoice_form.html`, `invoice_template_form.html`)—`{{ formset.non_form_errors }}` and each item's `{{ item_form.<field>.errors }}`. Silent validation failures on POST are strictly forbidden.
  - Handle `htmx:responseError` (4xx/5xx responses) visibly so inline HTMX forms never fail silently.

---

## 6. Language & Domain Display Rules

- **Language Split**:
  - **All Web UI Templates, Labels, Messages, Modals, and Tooltips**: Strictly in **Portuguese - Brasil (`pt-BR`)**. Watch out for accidental English-Portuguese portmanteaus (e.g., use `"Faturamento"`, never `"Invoicemento"`).
  - **Invoice PDF Template (`invoice_pdf.html`)**: Strictly in **English**, as invoices are issued to foreign clients.
  - **Python Codebase (Models, Views, Services, Variables)**: Strictly in **English**.
- **Draft vs. Finalized Invoice Rules**:
  - While an Invoice is in `DRAFT` status, all metadata (`invoice_number`, `client`, `issue_date`, `currency`, `bank_details`, `nfse_description`, `fiscal_codes`) and items (add, edit, delete) must be editable in the UI.
  - Once an Invoice transitions to `FINALIZED` (or `PROCESSING` / `CANCELED`), item additions/edits/deletions and core metadata edits must be locked and hidden in the UI, enforcing fiscal integrity.
- **Monetary Totals**:
  - Always display the formatted foreign currency total (`{{ invoice.currency }} {{ invoice.total_foreign|floatformat:2|intcomma }}`) prominently on `invoice_list.html`, `invoice_detail.html` (both in the summary card and the items table footer), and `mes_detail.html`.

---

## 7. Button Hierarchy, Detail Headers, Tables & Form Standards

### 7.1. Button & Header Hierarchy
- **Single Primary CTA**: Each page or major section must have at most one primary CTA (`btn-primary fw-semibold`). Secondary actions must use `btn-outline-secondary` or `btn-outline-primary`. Destructive actions must use `btn-outline-danger` (or reside within an `Ações` dropdown).
- **Detail View Full-Width Header**:
  - Placed outside and above the multi-column content grid.
  - **Top-Left**: `← Voltar` link (`btn-outline-secondary btn-sm mb-2`) above `<h2 class="mb-0 fw-bold">` with semantic status badge.
  - **Top-Right**: Direct labeled buttons for primary document actions (`Baixar PDF`, `Enviar E-mail`) plus an **`Ações`** dropdown (`btn-outline-secondary dropdown-toggle` with `bi-three-dots`) grouping secondary and destructive actions (`Clonar`, `Reverter para Rascunho`, divider, `Excluir` / `Cancelar`).

### 7.2. Universal Table Row Action Standards
- **Column 1 Clickable Identifier**: The primary identifier column (`Invoice #`, `NFS-e #`, `Cliente`, `Mês/Ano`) **must** be a clickable `fw-bold text-decoration-none font-monospace` link directly opening the record.
- **No `.clickable-row` JavaScript**: Avoid whole-row click handlers that interfere with text selection and nested links.
- **Strict Left-to-Right Action Order**:
  Inside `<td class="text-end pe-3 py-3 text-nowrap"><div class="d-inline-flex align-items-center gap-1 text-nowrap">`:
  1. `Ver/Editar` (`bi-eye` / `bi-pencil`)
  2. `Downloads` (`bi-file-earmark-pdf` / `bi-filetype-xml`)
  3. `Destrutivo` (`bi-trash` with `#globalConfirmModal`)

### 7.3. Universal Form Header & Footer Standards
- **Form Header**:
  - **Top-Left (Outside Card)**: `← Voltar` (`btn-outline-secondary btn-sm mb-2`) above `<h2 class="mb-0 fw-bold">Title</h2>`.
  - **Top-Right (Outside Card)**: `Excluir` button (`btn-outline-danger btn-sm` with `#globalConfirmModal`) when editing an existing deletable record.
- **Form Footer**:
  - Compact right-aligned container: `<div class="d-flex justify-content-end gap-2 mt-4">`.
  - Left button: `[Cancelar]` (`btn-outline-secondary`).
  - Right button: `[Salvar ...]` (`btn-primary px-4 fw-semibold`).
  - **Never** use full-width or giant 50%/50% (`w-50`) buttons in form footers.


