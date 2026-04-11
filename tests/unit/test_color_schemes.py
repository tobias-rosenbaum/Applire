# tests/unit/test_color_schemes.py
"""
Unit tests for the color scheme derivation service.
No Docker, no DB, no LLM.

Run:
    pytest tests/unit/test_color_schemes.py -v
"""
import pytest
from applire.services.color_schemes import derive_scheme, _hex_to_hsl, _hsl_to_hex


class TestHexHslConversion:
    def test_round_trip_primary_blue(self):
        h, s, l = _hex_to_hsl("#1b4f72")
        result = _hsl_to_hex(h, s, l)
        assert result == "#1b4f72"

    def test_round_trip_white(self):
        h, s, l = _hex_to_hsl("#ffffff")
        result = _hsl_to_hex(h, s, l)
        assert result == "#ffffff"

    def test_round_trip_black(self):
        h, s, l = _hex_to_hsl("#000000")
        result = _hsl_to_hex(h, s, l)
        assert result == "#000000"


class TestDeriveScheme:
    EU_BLUE = dict(
        seed_primary="#1b4f72",
        seed_accent="#2a8f9d",
        seed_secondary="#c9a84c",
        surface_lightness=0.97,
    )

    def test_returns_all_required_variables(self):
        derived = derive_scheme(**self.EU_BLUE)
        expected_keys = {
            "--color-primary", "--color-primary-container",
            "--color-teal", "--color-teal-dim", "--color-teal-container",
            "--color-teal-container-light",
            "--color-gold", "--color-gold-dim", "--color-gold-container",
            "--color-surface-dim", "--color-surface-bright",
            "--color-surface-container", "--color-surface-container-high",
            "--color-surface-container-highest",
            "--color-neutral-light",
        }
        assert set(derived.keys()) == expected_keys

    def test_seeds_pass_through(self):
        derived = derive_scheme(**self.EU_BLUE)
        assert derived["--color-primary"] == "#1b4f72"
        assert derived["--color-teal"] == "#2a8f9d"
        assert derived["--color-gold"] == "#c9a84c"

    def test_surface_bright_is_always_white(self):
        derived = derive_scheme(**self.EU_BLUE)
        assert derived["--color-surface-bright"] == "#ffffff"

    def test_all_values_are_valid_hex(self):
        import re
        hex_re = re.compile(r"^#[0-9a-f]{6}$")
        derived = derive_scheme(**self.EU_BLUE)
        for key, value in derived.items():
            assert hex_re.match(value), f"{key}: {value!r} is not a valid hex color"

    def test_container_is_lighter_than_seed(self):
        derived = derive_scheme(**self.EU_BLUE)
        _, _, l_seed = _hex_to_hsl(self.EU_BLUE["seed_primary"])
        _, _, l_container = _hex_to_hsl(derived["--color-primary-container"])
        assert l_container > l_seed

    def test_dim_is_darker_than_seed(self):
        derived = derive_scheme(**self.EU_BLUE)
        _, _, l_seed = _hex_to_hsl(self.EU_BLUE["seed_accent"])
        _, _, l_dim = _hex_to_hsl(derived["--color-teal-dim"])
        assert l_dim < l_seed

    def test_surface_container_high_is_darker_than_surface_dim(self):
        derived = derive_scheme(**self.EU_BLUE)
        _, _, l_dim = _hex_to_hsl(derived["--color-surface-dim"])
        _, _, l_high = _hex_to_hsl(derived["--color-surface-container-high"])
        assert l_high < l_dim

    def test_lower_surface_lightness_produces_darker_surfaces(self):
        light = derive_scheme(seed_primary="#1b4f72", seed_accent="#2a8f9d",
                              seed_secondary="#c9a84c", surface_lightness=0.97)
        dark = derive_scheme(seed_primary="#1b4f72", seed_accent="#2a8f9d",
                             seed_secondary="#c9a84c", surface_lightness=0.88)
        _, _, l_light = _hex_to_hsl(light["--color-surface-dim"])
        _, _, l_dark = _hex_to_hsl(dark["--color-surface-dim"])
        assert l_dark < l_light
