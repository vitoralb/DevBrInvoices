import logging
from django.conf import settings
from django.contrib import auth
from django.shortcuts import redirect
from django.urls import reverse
from django.core.cache import cache
from django.utils.http import url_has_allowed_host_and_scheme
from .models import CompanySettings
from .backends import (
    get_request_header,
    parse_groups_header,
    is_trusted_proxy,
)

logger = logging.getLogger(__name__)

COMPANY_SETTINGS_CACHE_KEY = "company_settings_exists"
COMPANY_SETTINGS_CACHE_TIMEOUT = 60  # seconds


class ProxyHeaderAuthenticationMiddleware:
    """
    Middleware that reads reverse proxy authentication headers
    (e.g., X-Auth-Request-Preferred-Username, X-Auth-Request-Email, X-Auth-Request-Groups)
    and authenticates the user, skipping the login screen when headers are available.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(settings, "PROXY_AUTH_ENABLED", True):
            return self.get_response(request)

        # Do not authenticate or intercept logout requests
        if self._is_logout_path(request):
            return self.get_response(request)

        username_hdr = getattr(
            settings, "PROXY_AUTH_USERNAME_HEADER", "X-Auth-Request-Preferred-Username"
        )
        email_hdr = getattr(
            settings, "PROXY_AUTH_EMAIL_HEADER", "X-Auth-Request-Email"
        )
        groups_hdr = getattr(
            settings, "PROXY_AUTH_GROUPS_HEADER", "X-Auth-Request-Groups"
        )

        raw_username = get_request_header(request, username_hdr)
        username = raw_username.strip() if raw_username else ""

        if username:
            # Enforce trusted proxy CIDR check if configured
            trusted_proxies = getattr(settings, "PROXY_AUTH_TRUSTED_PROXIES", [])
            if trusted_proxies:
                client_ip = request.META.get("REMOTE_ADDR", "").strip()
                if not is_trusted_proxy(client_ip, trusted_proxies):
                    logger.warning(
                        "Proxy auth headers ignored: client IP '%s' is not in PROXY_AUTH_TRUSTED_PROXIES.",
                        client_ip,
                    )
                    return self.get_response(request)

            raw_email = get_request_header(request, email_hdr)
            email = raw_email.strip() if raw_email else ""

            raw_groups = get_request_header(request, groups_hdr)
            parsed_groups = (
                parse_groups_header(raw_groups) if raw_groups is not None else None
            )

            # Check existing authentication state
            if request.user.is_authenticated:
                if request.user.get_username() != username:
                    # Header user changed; switch session
                    auth.logout(request)
                    self._login_user(request, username, email, parsed_groups)
                else:
                    # Same user; sync metadata if headers changed
                    self._sync_metadata_if_changed(request, email, parsed_groups)
            else:
                self._login_user(request, username, email, parsed_groups)

            # If authenticated and navigating to login page, redirect to skip login screen
            if request.user.is_authenticated and self._is_login_path(request):
                return self._redirect_to_next_or_default(request)

        return self.get_response(request)

    def _login_user(self, request, username, email, groups):
        user = auth.authenticate(
            request,
            remote_user=username,
            email=email,
            groups=groups,
        )
        if user:
            auth.login(request, user)
            request.session["_proxy_auth_email"] = email
            request.session["_proxy_auth_groups"] = groups

    def _sync_metadata_if_changed(self, request, email, groups):
        session_email = request.session.get("_proxy_auth_email")
        session_groups = request.session.get("_proxy_auth_groups")

        email_changed = email and (session_email != email)
        groups_changed = (groups is not None) and (session_groups != groups)

        if email_changed or groups_changed:
            user = auth.authenticate(
                request,
                remote_user=request.user.get_username(),
                email=email if email_changed else None,
                groups=groups if groups_changed else None,
            )
            if user:
                request.user = user
                request.session["_proxy_auth_email"] = email
                if groups is not None:
                    request.session["_proxy_auth_groups"] = groups

    def _is_login_path(self, request):
        try:
            return request.path == reverse("login")
        except Exception:
            return request.path in ("/accounts/login/", "/login/")

    def _is_logout_path(self, request):
        try:
            return request.path == reverse("logout")
        except Exception:
            return request.path in ("/accounts/logout/", "/logout/")

    def _redirect_to_next_or_default(self, request):
        next_url = request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)
        return redirect(getattr(settings, "LOGIN_REDIRECT_URL", "/"))


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
