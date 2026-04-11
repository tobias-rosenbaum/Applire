# backend/applire/services/color_schemes.py
"""Color scheme derivation and DB service functions."""
import colorsys
import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from applire.models.color_scheme import ColorScheme


# ---------------------------------------------------------------------------
# Color math helpers
# ---------------------------------------------------------------------------

def _hex_to_hsl(hex_color: str) -> tuple[float, float, float]:
    """Convert #rrggbb → (h, s, l) with all values in [0, 1]."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255
    # colorsys returns (h, l, s) — note the l/s swap
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h, s, l


def _hsl_to_hex(h: float, s: float, l: float) -> str:
    """Convert (h, s, l) with all values in [0, 1] → #rrggbb."""
    # colorsys expects (h, l, s)
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    r_i = max(0, min(255, round(r * 255)))
    g_i = max(0, min(255, round(g * 255)))
    b_i = max(0, min(255, round(b * 255)))
    return f"#{r_i:02x}{g_i:02x}{b_i:02x}"


def _derive_color(hex_color: str, lightness: float, saturation: float) -> str:
    """Keep hue from hex_color, override lightness and saturation."""
    h, _, _ = _hex_to_hsl(hex_color)
    return _hsl_to_hex(h, saturation, lightness)


# ---------------------------------------------------------------------------
# Public derivation function (used by router + tests)
# ---------------------------------------------------------------------------

def derive_scheme(
    seed_primary: str,
    seed_accent: str,
    seed_secondary: str,
    surface_lightness: float,
) -> dict[str, str]:
    """Derive all 15 CSS custom property values from 3 seeds + surface lightness."""
    L = surface_lightness
    return {
        "--color-primary": seed_primary.lower(),
        "--color-primary-container": _derive_color(seed_primary, 0.90, 0.30),
        "--color-teal": seed_accent.lower(),
        "--color-teal-dim": _derive_color(seed_accent, 0.12, 1.00),
        "--color-teal-container": _derive_color(seed_accent, 0.92, 0.40),
        "--color-teal-container-light": _derive_color(seed_accent, 0.97, 0.15),
        "--color-gold": seed_secondary.lower(),
        "--color-gold-dim": _derive_color(seed_secondary, 0.20, 1.00),
        "--color-gold-container": _derive_color(seed_secondary, 0.92, 0.60),
        "--color-surface-dim": _derive_color(seed_primary, L, 0.08),
        "--color-surface-bright": "#ffffff",
        "--color-surface-container": _derive_color(seed_primary, max(0.0, L - 0.02), 0.10),
        "--color-surface-container-high": _derive_color(seed_primary, max(0.0, L - 0.05), 0.12),
        "--color-surface-container-highest": _derive_color(seed_primary, max(0.0, L - 0.08), 0.14),
        "--color-neutral-light": _derive_color(seed_primary, L, 0.05),
    }


# ---------------------------------------------------------------------------
# DB service functions
# ---------------------------------------------------------------------------

async def get_active_scheme(db: AsyncSession) -> ColorScheme | None:
    result = await db.execute(
        select(ColorScheme).where(ColorScheme.is_active == True)  # noqa: E712
    )
    return result.scalar_one_or_none()


async def list_schemes(db: AsyncSession) -> list[ColorScheme]:
    result = await db.execute(
        select(ColorScheme).order_by(ColorScheme.created_at)
    )
    return list(result.scalars().all())


async def create_scheme(
    db: AsyncSession,
    name: str,
    seed_primary: str,
    seed_accent: str,
    seed_secondary: str,
    surface_lightness: float,
) -> ColorScheme:
    derived = derive_scheme(seed_primary, seed_accent, seed_secondary, surface_lightness)
    scheme = ColorScheme(
        id=uuid.uuid4(),
        name=name,
        is_active=False,
        is_builtin=False,
        seed_primary=seed_primary.lower(),
        seed_accent=seed_accent.lower(),
        seed_secondary=seed_secondary.lower(),
        surface_lightness=surface_lightness,
        derived=derived,
    )
    db.add(scheme)
    await db.commit()
    await db.refresh(scheme)
    return scheme


async def activate_scheme(db: AsyncSession, scheme_id: uuid.UUID) -> ColorScheme | None:
    scheme = await db.get(ColorScheme, scheme_id)
    if scheme is None:
        return None
    # Deactivate all, then activate the target — in one transaction
    await db.execute(
        update(ColorScheme).values(is_active=False)
    )
    scheme.is_active = True
    await db.commit()
    await db.refresh(scheme)
    return scheme


async def delete_scheme(db: AsyncSession, scheme_id: uuid.UUID) -> ColorScheme | None:
    scheme = await db.get(ColorScheme, scheme_id)
    if scheme is None:
        return None
    if scheme.is_builtin:
        raise ValueError(f"Cannot delete builtin scheme {scheme_id}")
    await db.delete(scheme)
    await db.commit()
    return scheme
