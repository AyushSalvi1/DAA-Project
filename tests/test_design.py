"""Design-system tests.

The stylesheet is the product's user interface, so it gets the same
treatment as the algorithms: the fonts must actually load, every colour
token must be defined in *both* themes, and every text/background pair
must clear WCAG AA. A theme tweak that silently drops a token or drops
contrast to 3:1 fails here instead of on the page.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

STATIC = Path(__file__).resolve().parents[1] / "static"
CSS = (STATIC / "css" / "style.css").read_text(encoding="utf-8")
FONTS = STATIC / "fonts"

ROOT_BLOCK = re.search(r":root\s*\{(.*?)\n\}", CSS, re.S).group(1)
LIGHT_BLOCK = re.search(r'\[data-theme="light"\]\s*\{(.*?)\n\}', CSS, re.S).group(1)

FONT_FILES = [
    "inter-var-latin.woff2",
    "space-grotesk-var-latin.woff2",
    "jetbrains-mono-var-latin.woff2",
]


def token(block: str, name: str) -> str | None:
    match = re.search(rf"{re.escape(name)}\s*:\s*([^;]+);", block)
    return match.group(1).strip() if match else None


def parse_hex(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def parse_rgba(value: str) -> tuple[float, float, float, float]:
    inner = value[value.index("(") + 1:value.rindex(")")]
    parts = [p.strip() for p in inner.replace(",", " ").replace("/", " ").split()]
    red, green, blue = (float(p) for p in parts[:3])
    return (red, green, blue, float(parts[3]) if len(parts) > 3 else 1.0)


def composite(foreground, background):
    """Flatten an rgba foreground onto an opaque background."""
    if len(foreground) == 3:
        return foreground
    red, green, blue, alpha = foreground
    return tuple(round(f * alpha + b * (1 - alpha))
                 for f, b in zip((red, green, blue), background))


def luminance(rgb) -> float:
    channels = []
    for raw in rgb:
        value = raw / 255
        channels.append(value / 12.92 if value <= 0.03928
                        else ((value + 0.055) / 1.055) ** 2.4)
    red, green, blue = channels
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast(foreground, background) -> float:
    first = luminance(composite(foreground, background))
    second = luminance(background)
    lighter, darker = max(first, second), min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


# ---------------------------------------------------------------- fonts
class TestFonts:
    @pytest.mark.parametrize("name", FONT_FILES)
    def test_font_file_is_a_real_woff2(self, name):
        data = (FONTS / name).read_bytes()
        assert data[:4] == b"wOF2"
        assert 5_000 < len(data) < 200_000

    @pytest.mark.parametrize("name", FONT_FILES)
    def test_font_is_declared_with_a_variable_range(self, name):
        face = re.search(
            r"@font-face\s*\{(?=[^}]*url\(\"\.\./fonts/" + re.escape(name) + r"\"\))[^}]*\}",
            CSS, re.S).group(0)
        assert 'format("woff2")' in face
        assert "font-display: swap" in face
        assert "font-style: normal" in face
        weight = re.search(r"font-weight:\s*(\d{3})\s+(\d{3})", face).groups()
        assert 100 <= int(weight[0]) < int(weight[1]) <= 900

    def test_fonts_are_self_hosted_not_fetched_from_a_cdn(self, client):
        """The project must run offline, so no stylesheet or template may
        reach out to a font CDN."""
        assert not re.search(r"fonts\.(googleapis|gstatic)\.com", CSS)
        for url in ("/", "/search", "/algorithms/", "/graph"):
            body = client.get(url).get_data(as_text=True)
            assert "fonts.googleapis.com" not in body
            assert "fonts.gstatic.com" not in body

    def test_font_url_in_the_stylesheet_resolves(self, client):
        """The path inside url() must match what the app actually serves."""
        served = {
            f"/static/fonts/{name}" for name in FONT_FILES
        }
        referenced = set(re.findall(r'url\("\.\./fonts/([^"]+)"\)', CSS))
        assert referenced == {name for name in FONT_FILES}
        for path in served:
            assert client.get(path).headers["Content-Type"] == "font/woff2"

    def test_three_distinct_type_faces_are_in_use(self, client):
        body = client.get("/").get_data(as_text=True)
        assert 'href="/static/fonts/inter-var-latin.woff2"' in body
        assert 'href="/static/fonts/space-grotesk-var-latin.woff2"' in body
        css_font = token(ROOT_BLOCK, "--font")
        css_display = token(ROOT_BLOCK, "--font-display")
        css_mono = token(ROOT_BLOCK, "--mono")
        assert len({css_font, css_display, css_mono}) == 3
        assert "Inter var" in css_font
        assert "Space Grotesk" in css_display
        assert "JetBrains Mono" in css_mono


# ---------------------------------------------------------------- tokens
class TestTokens:
    def test_no_undefined_custom_properties_are_used(self):
        """Every var(--x) must be defined in :root, otherwise the property
        silently falls back to nothing and the component loses its colour."""
        defined = set(re.findall(r"(--[a-z0-9-]+)\s*:", ROOT_BLOCK))
        used = set(re.findall(r"var\((--[a-z0-9-]+)", CSS))
        assert used <= defined, f"undefined tokens: {sorted(used - defined)}"

    def test_every_root_token_also_exists_in_the_light_theme_when_tinted(self):
        """Semantic text tones must be re-declared for the light theme; the
        dark neon values are unreadable on white."""
        themed = ["--brand", "--brand-2-text", "--ok-text", "--warn-text",
                  "--err-text", "--tint-text", "--tint-warn-text", "--tint-brand-text"]
        for name in themed:
            assert token(ROOT_BLOCK, name), f"{name} missing from :root"
            assert token(LIGHT_BLOCK, name), f"{name} missing from the light theme"
            assert token(ROOT_BLOCK, name) != token(LIGHT_BLOCK, name)

    def test_stylesheet_braces_are_balanced(self):
        assert CSS.count("{") == CSS.count("}")
        assert not re.search(r"\{\s*\}", CSS)


# -------------------------------------------------------------- contrast
# (label, token, "page" | "panel")
CONTRAST_CHECKS = [
    ("body text", "--text", "panel"),
    ("secondary text", "--text-2", "page"),
    ("muted text", "--text-3", "panel"),
    ("success / result url", "--ok-text", "page"),
    ("warning", "--warn-text", "page"),
    ("danger", "--err-text", "page"),
    ("brand", "--brand", "page"),
    ("cyan accent", "--brand-2-text", "panel"),
    ("tint blue text", "--tint-brand-text", "panel"),
    ("tint green text", "--tint-text", "panel"),
    ("tint amber text", "--tint-warn-text", "panel"),
]


class TestContrast:
    @pytest.mark.parametrize("theme,block", [("dark", ROOT_BLOCK), ("light", LIGHT_BLOCK)])
    @pytest.mark.parametrize("label,name,where", CONTRAST_CHECKS,
                             ids=[c[0] for c in CONTRAST_CHECKS])
    def test_text_clears_wcag_aa(self, theme, block, label, name, where):
        page = parse_hex(token(block, "--bg"))
        surface = composite(parse_rgba(token(block, "--surface-2")), page) \
            if where == "panel" else page
        ratio = contrast(parse_hex(token(block, name)), surface)
        assert ratio >= 4.5, f"{theme}: {label} is {ratio:.2f}:1"

    def test_primary_button_text_sits_on_the_accent_gradient(self):
        """The primary button is #061022 on the brand gradient - check the
        darkest end of that gradient."""
        brand = parse_hex(token(ROOT_BLOCK, "--brand"))
        darkest = tuple(min(brand[i], parse_hex(token(ROOT_BLOCK, "--brand-2"))[i])
                        for i in range(3))
        assert contrast(parse_hex("#061022"), darkest) >= 4.5


# ------------------------------------------------------------ behaviour
class TestMotionAndAccessibility:
    def test_reduced_motion_is_respected(self):
        assert "prefers-reduced-motion: reduce" in CSS

    def test_focus_is_always_visible(self):
        assert ":focus-visible" in CSS
        assert "outline: none" not in CSS or ":focus-visible" in CSS

    def test_body_text_meets_a_readable_line_height_and_measure(self):
        body = re.search(r"body\s*\{(.*?)\n\}", CSS, re.S).group(1)
        assert "line-height: 1.6" in body or "line-height: 1.65" in body
        assert ".prose { color: var(--text-2); max-width: 74ch; }" in CSS

    def test_numerical_ui_uses_tabular_figures(self):
        assert "font-variant-numeric: tabular-nums" in CSS

    def test_stylesheet_size_stays_reasonable(self):
        assert len(CSS.encode("utf-8")) < 60_000

    def test_stylesheet_parses_without_errors(self):
        """tinycss2 is a dev-only helper; skip when it is not installed."""
        tinycss2 = pytest.importorskip("tinycss2")

        errors = []
        rules = 0
        declarations = 0
        for node in tinycss2.parse_stylesheet(CSS, skip_comments=True, skip_whitespace=True):
            if node.type == "error":
                errors.append(f"line {node.source_line}: {node.message}")
                continue
            if node.type == "qualified-rule":
                rules += 1
                for decl in tinycss2.parse_blocks_contents(node.content, skip_comments=True,
                                                           skip_whitespace=True):
                    if decl.type == "error":
                        selector = tinycss2.serialize(node.prelude).strip()[:60]
                        errors.append(f"line {decl.source_line} in {selector}: {decl.message}")
                    elif decl.type == "declaration":
                        declarations += 1
        assert not errors, errors[:10]
        assert rules > 200, f"only {rules} rules parsed - the file looks truncated"
        assert declarations > 800, f"only {declarations} declarations parsed"