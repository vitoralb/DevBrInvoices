from core.models import CompanySettings
from django.conf import settings


def company_settings(request):
    try:
        company = CompanySettings.load()
        return {"company": company}
    except Exception:
        return {"company": None}


def project_settings(request):
    return {"PROJECT_NAME": getattr(settings, "PROJECT_NAME", "DevBrInvoices")}
