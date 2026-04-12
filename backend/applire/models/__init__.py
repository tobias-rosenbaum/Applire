# Import all models so SQLAlchemy can resolve FK string references (e.g. "companies.id")
# at mapper-configuration time, regardless of which service is imported first.
from applire.models import (  # noqa: F401
    application,
    color_profile,
    company,
    cv,
    flow,
    gap,
    job,
    profile,
    session,
    uploads,
    user,
    user_settings,
)
