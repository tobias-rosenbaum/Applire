from applire.config import settings
from applire.auth.base import AuthProvider


def get_auth_provider() -> AuthProvider:
    """Factory: instantiate the configured auth provider (ADR 008).

    Controlled by the AUTH_PROVIDER environment variable:
      none  — NoAuthProvider; fixed single-user stub, zero enforcement (default)

    Cloud Edition backends (zitadel, oidc, apikey) are not part of this
    distribution and must be registered here by the Cloud layer.
    """
    provider = settings.auth_provider.lower()

    if provider == "none":
        from applire.auth.no_auth import NoAuthProvider
        return NoAuthProvider()

    raise ValueError(
        f"Unknown AUTH_PROVIDER '{settings.auth_provider}'. "
        "Community Edition supports: none. "
        "Cloud Edition backends (zitadel, oidc, apikey) are not included."
    )
