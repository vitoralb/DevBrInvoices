import logging
import ipaddress
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import Group

logger = logging.getLogger(__name__)


def parse_groups_header(raw_groups) -> list[str]:
    """Parse groups from a header string, JSON array, or list."""
    if not raw_groups:
        return []
    if isinstance(raw_groups, (list, tuple, set)):
        items = [str(g).strip() for g in raw_groups if str(g).strip()]
    else:
        raw = str(raw_groups).strip()
        if not raw:
            return []
        items = []
        if raw.startswith("[") and raw.endswith("]"):
            try:
                import json

                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    items = [str(g).strip() for g in parsed if str(g).strip()]
            except Exception:
                pass
        if not items:
            delimiter = "," if "," in raw else (";" if ";" in raw else ",")
            items = [g.strip() for g in raw.split(delimiter) if g.strip()]

    # Deduplicate while preserving order and constrain to max_length=150
    cleaned = []
    seen = set()
    for item in items:
        trimmed = item[:150]
        if trimmed and trimmed not in seen:
            seen.add(trimmed)
            cleaned.append(trimmed)
    return cleaned


def normalize_header_name(header_name: str) -> str:
    """Normalize HTTP header name for request.META lookup."""
    if not header_name:
        return ""
    name = header_name.upper().replace("-", "_")
    if not name.startswith("HTTP_") and name not in ("CONTENT_TYPE", "CONTENT_LENGTH"):
        name = f"HTTP_{name}"
    return name


def get_request_header(request, header_name: str) -> str | None:
    """Safely fetch header from HttpRequest via headers or META."""
    if not header_name:
        return None
    # Try Django's request.headers (case-insensitive, no HTTP_ prefix needed)
    clean_name = header_name.replace("HTTP_", "").replace("_", "-")
    val = request.headers.get(clean_name)
    if val is not None:
        return val
    # Fallback to request.META
    meta_name = normalize_header_name(header_name)
    return request.META.get(meta_name, request.META.get(header_name))


def is_trusted_proxy(client_ip: str, trusted_cidrs: list[str]) -> bool:
    """
    Check if a client IP address matches any of the trusted CIDR blocks.
    """
    if not client_ip or not trusted_cidrs:
        return False
    try:
        ip = ipaddress.ip_address(client_ip.strip())
    except ValueError:
        return False

    for network_str in trusted_cidrs:
        network_str = network_str.strip()
        if not network_str:
            continue
        try:
            net = ipaddress.ip_network(network_str, strict=False)
            if ip in net:
                return True
        except ValueError:
            logger.warning(
                "Invalid CIDR or IP in PROXY_AUTH_TRUSTED_PROXIES: '%s'", network_str
            )
            continue
    return False


class ProxyHeaderBackend(ModelBackend):
    """
    Authentication backend for reverse proxy authentication headers
    (e.g., OAuth2-Proxy / Kanidm forward-auth).
    """

    def authenticate(
        self,
        request,
        remote_user=None,
        email=None,
        groups=None,
        **kwargs,
    ):
        if not remote_user:
            return None

        username = self.clean_username(remote_user)
        if not username:
            return None

        UserModel = get_user_model()
        user = None
        created = False

        try:
            user = UserModel.objects.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            auto_create = getattr(settings, "PROXY_AUTH_AUTO_CREATE_USER", True)
            if not auto_create:
                logger.warning(
                    "Proxy auth: user '%s' does not exist and auto-create is disabled.",
                    username,
                )
                return None
            user = UserModel.objects.create_user(
                username=username,
                email=email or "",
            )
            created = True
            logger.info("Proxy auth: created new user '%s'.", username)

        # Update email if provided and different
        if email and user.email != email:
            user.email = email
            user.save(update_fields=["email"])

        # Sync groups if provided
        if groups is not None:
            self.sync_groups(user, groups)

        # Sync permissions (is_staff / is_superuser)
        self.sync_permissions(user, groups, created=created)

        if not self.user_can_authenticate(user):
            logger.warning(
                "Proxy auth: user '%s' cannot authenticate (inactive).", username
            )
            return None

        return user

    def clean_username(self, username: str) -> str:
        return str(username).strip()[:150]

    def sync_groups(self, user, groups: list[str]) -> None:
        group_objs = []
        for group_name in groups:
            group_name = group_name[:150]
            group_obj, _ = Group.objects.get_or_create(name=group_name)
            group_objs.append(group_obj)
        user.groups.set(group_objs)

    def sync_permissions(
        self, user, groups: list[str] | None, created: bool = False
    ) -> None:
        staff_groups = getattr(settings, "PROXY_AUTH_STAFF_GROUPS", [])
        superuser_groups = getattr(settings, "PROXY_AUTH_SUPERUSER_GROUPS", [])
        default_is_staff = getattr(settings, "PROXY_AUTH_DEFAULT_IS_STAFF", False)

        update_fields = []
        user_groups_set = set(groups or [])

        # Check superuser
        if superuser_groups and any(g in user_groups_set for g in superuser_groups):
            if not user.is_superuser:
                user.is_superuser = True
                update_fields.append("is_superuser")
            if not user.is_staff:
                user.is_staff = True
                update_fields.append("is_staff")

        # Check staff
        if staff_groups and any(g in user_groups_set for g in staff_groups):
            if not user.is_staff:
                user.is_staff = True
                update_fields.append("is_staff")

        # Default staff on creation if configured
        if created and default_is_staff and not user.is_staff:
            user.is_staff = True
            update_fields.append("is_staff")

        if update_fields:
            user.save(update_fields=list(set(update_fields)))
