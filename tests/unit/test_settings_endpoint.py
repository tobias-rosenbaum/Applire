"""
Unit tests for GET/PATCH /api/settings.
Run: pytest tests/unit/test_settings_endpoint.py -v
"""
import sys
import uuid
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

_backend = Path(__file__).parent.parent.parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))


@pytest_asyncio.fixture
async def db():
    from applire.db.session import Base
    import applire.models.user
    import applire.models.job
    import applire.models.profile
    import applire.models.gap
    import applire.models.cv
    import applire.models.session
    import applire.models.application
    import applire.models.flow
    import applire.models.uploads
    import applire.models.color_profile
    import applire.models.company
    import applire.models.user_settings
    from applire.models.user import User
    from applire.services.color_detection import _CE_STUB_USER_ID

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        # Insert stub user (CE always has this user)
        user = User(id=_CE_STUB_USER_ID, email="local@applire.community")
        session.add(user)
        await session.commit()
        yield session
    await engine.dispose()


class TestSettingsEndpoint:
    @pytest.mark.asyncio
    async def test_get_settings_returns_null_defaults_when_no_row(self, db):
        from applire.routers.settings import get_settings
        result = await get_settings(db)
        assert result["default_accent_hex"] is None

    @pytest.mark.asyncio
    async def test_patch_settings_stores_default_color(self, db):
        from applire.routers.settings import update_settings, get_settings
        await update_settings("#334455", db)
        result = await get_settings(db)
        assert result["default_accent_hex"] == "#334455"

    @pytest.mark.asyncio
    async def test_patch_settings_raises_on_invalid_hex(self, db):
        from applire.routers.settings import update_settings
        with pytest.raises(ValueError):
            await update_settings("not-hex", db)

    @pytest.mark.asyncio
    async def test_patch_settings_updates_existing_row(self, db):
        from applire.routers.settings import update_settings, get_settings
        await update_settings("#aabbcc", db)
        await update_settings("#112233", db)
        result = await get_settings(db)
        assert result["default_accent_hex"] == "#112233"
