from django.shortcuts import redirect
from django.urls import reverse
from django.core.cache import cache
from .models import CompanySettings

COMPANY_SETTINGS_CACHE_KEY = "company_settings_exists"
COMPANY_SETTINGS_CACHE_TIMEOUT = 60  # seconds


class RequireCompanySettingsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin/"):
            return self.get_response(request)

        if (
            request.path.startswith("/static/")
            or request.path.startswith("/media/")
            or request.path.startswith("/api/")
        ):
            return self.get_response(request)

        if request.path == reverse("login") or request.path == reverse("logout"):
            return self.get_response(request)

        if request.user.is_authenticated:
            if request.path != reverse("company_settings"):
                exists = cache.get(COMPANY_SETTINGS_CACHE_KEY)
                if exists is None:
                    exists = CompanySettings.objects.exists()
                    cache.set(
                        COMPANY_SETTINGS_CACHE_KEY,
                        exists,
                        COMPANY_SETTINGS_CACHE_TIMEOUT,
                    )
                if not exists:
                    from django.contrib import messages

                    messages.warning(
                        request,
                        "Por favor, configure os dados da sua empresa antes de continuar.",
                    )
                    return redirect("company_settings")

        return self.get_response(request)
