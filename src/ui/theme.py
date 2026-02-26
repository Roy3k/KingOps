"""
KingOps Design Tokens — Pacific Northwest × Japanese Tea Garden

Design philosophy: cedar, moss, slate, leather, quiet fire.
Stewardship over decades, not trading terminals.
"""

from dataclasses import dataclass
from typing import NamedTuple


# -----------------------------------------------------------------------------
# Color Tokens (Section 3.1)
# -----------------------------------------------------------------------------

class ColorBase(NamedTuple):
    """Base / text colors."""
    forest_green: str = "#2F4A3E"      # Deep, desaturated
    slate_charcoal: str = "#2A2A2A"   # Primary text
    river_stone: str = "#7A858F"      # Muted gray-blue, secondary text


class ColorSurface(NamedTuple):
    """Background and card surfaces."""
    cream_linen: str = "#F3EFE6"     # Primary background
    soft_leather_tan: str = "#C8B89E" # Card background
    mist_gray: str = "#E8E4DC"        # Subtle gradient end


class ColorAccent(NamedTuple):
    """Accent and highlight colors."""
    moss_green: str = "#556B57"      # Muted accent
    driftwood_brown: str = "#6A5E4B" # Warm neutral
    ember_glow: str = "#B46A3C"      # Subtle highlight


class ColorAlert(NamedTuple):
    """Alert severity — subdued, never aggressive."""
    info: str = "#556B57"    # Subtle green border
    warning: str = "#8B7355" # Warm brown edge
    critical: str = "#B46A3C"  # Deeper ember tone


# -----------------------------------------------------------------------------
# Spacing Scale (Section 10.1)
# -----------------------------------------------------------------------------

class SpacingScale(NamedTuple):
    """Breathing room is a feature."""
    xs: str = "0.25rem"   # 4px
    sm: str = "0.5rem"    # 8px
    md: str = "1rem"      # 16px
    lg: str = "1.5rem"    # 24px
    xl: str = "2rem"      # 32px
    xxl: str = "3rem"     # 48px


# -----------------------------------------------------------------------------
# Radius & Shadow (Section 10.1)
# -----------------------------------------------------------------------------

class RadiusSoft(NamedTuple):
    """Rounded edges, no sharp corners."""
    sm: str = "6px"
    md: str = "10px"
    lg: str = "14px"


class ShadowSoft(NamedTuple):
    """Soft shadows, no harsh drop shadows."""
    card: str = "0 2px 8px rgba(42, 42, 42, 0.06)"
    hover: str = "0 4px 12px rgba(42, 42, 42, 0.08)"


# -----------------------------------------------------------------------------
# Typography (Section 3.2)
# -----------------------------------------------------------------------------

class FontPrimary(NamedTuple):
    """Humanist serif — warmth, understated confidence."""
    family: str = "Lora, Georgia, 'Times New Roman', serif"
    # Lora: humanist serif, Georgia-like warmth


class FontSecondary(NamedTuple):
    """Clean sans-serif for data tables."""
    family: str = "DM Sans, -apple-system, BlinkMacSystemFont, sans-serif"


class FontMono(NamedTuple):
    """Tabular figures for financial precision."""
    family: str = "'JetBrains Mono', 'SF Mono', Consolas, monospace"


# -----------------------------------------------------------------------------
# Motion (Section 6.1)
# -----------------------------------------------------------------------------

class Motion(NamedTuple):
    """Slow, easing-based. Sliding paper across a wooden desk."""
    duration: str = "200ms"
    easing: str = "ease-out"


# -----------------------------------------------------------------------------
# Aggregated Theme
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class Theme:
    """Complete design token set."""
    color_base: ColorBase = ColorBase()
    color_surface: ColorSurface = ColorSurface()
    color_accent: ColorAccent = ColorAccent()
    color_alert: ColorAlert = ColorAlert()
    spacing: SpacingScale = SpacingScale()
    radius: RadiusSoft = RadiusSoft()
    shadow: ShadowSoft = ShadowSoft()
    font_primary: FontPrimary = FontPrimary()
    font_secondary: FontSecondary = FontSecondary()
    font_mono: FontMono = FontMono()
    motion: Motion = Motion()


# Singleton for app-wide use
theme = Theme()


def generate_css_vars() -> str:
    """Generate CSS custom properties from design tokens."""
    t = theme
    return f"""
    :root {{
        /* color.base */
        --color-forest: {t.color_base.forest_green};
        --color-slate: {t.color_base.slate_charcoal};
        --color-river-stone: {t.color_base.river_stone};
        /* color.surface */
        --color-cream-linen: {t.color_surface.cream_linen};
        --color-soft-leather: {t.color_surface.soft_leather_tan};
        --color-mist: {t.color_surface.mist_gray};
        /* color.accent */
        --color-moss: {t.color_accent.moss_green};
        --color-driftwood: {t.color_accent.driftwood_brown};
        --color-ember: {t.color_accent.ember_glow};
        /* color.alert */
        --alert-info: {t.color_alert.info};
        --alert-warning: {t.color_alert.warning};
        --alert-critical: {t.color_alert.critical};
        /* spacing.scale */
        --space-xs: {t.spacing.xs};
        --space-sm: {t.spacing.sm};
        --space-md: {t.spacing.md};
        --space-lg: {t.spacing.lg};
        --space-xl: {t.spacing.xl};
        --space-xxl: {t.spacing.xxl};
        /* radius.soft */
        --radius-sm: {t.radius.sm};
        --radius-md: {t.radius.md};
        --radius-lg: {t.radius.lg};
        /* shadow.soft */
        --shadow-card: {t.shadow.card};
        --shadow-hover: {t.shadow.hover};
        /* font */
        --font-primary: {t.font_primary.family};
        --font-secondary: {t.font_secondary.family};
        --font-mono: {t.font_mono.family};
    }}
    """
