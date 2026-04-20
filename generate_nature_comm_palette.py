from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Iterable


WHITE = (255, 255, 255)
SCIENTIFIC_INK = (33, 45, 58)
OUTPUT_BASENAME = "nature_comm_scientific_palette"
SECTION_ORDER = (
    "Blue / Navy",
    "Cyan / Teal",
    "Green",
    "Earth / Ochre / Sand",
    "Red / Rose / Plum",
    "Neutral",
)

BASE_FAMILIES = (
    ("Blue / Navy", "Slate Blue", "General line plots", "#5E7B98"),
    ("Blue / Navy", "Harbor Blue", "Primary quantitative series", "#4E7397"),
    ("Blue / Navy", "Ink Navy", "High-contrast figure backbone", "#314C6B"),
    ("Blue / Navy", "Steel Blue", "Secondary comparison series", "#68849C"),
    ("Cyan / Teal", "Deep Teal", "Method structure and flow", "#4F8E8D"),
    ("Cyan / Teal", "Sea Glass", "Soft secondary emphasis", "#6C9EA4"),
    ("Cyan / Teal", "Mineral Cyan", "Technical highlight", "#5C9FB1"),
    ("Cyan / Teal", "Aqua Teal", "Modular pathway emphasis", "#4FA39B"),
    ("Green", "Sage Green", "Stable or positive state", "#7F9B7A"),
    ("Green", "Moss Olive", "Material and biology cues", "#8D8D59"),
    ("Green", "Pine Green", "Biological mechanism highlight", "#567A64"),
    ("Green", "Fern Green", "Supportive branch or module", "#6F956A"),
    ("Earth / Ochre / Sand", "Amber Ochre", "Process highlight", "#B18A4E"),
    ("Earth / Ochre / Sand", "Terracotta", "Intervention and comparison", "#B2735A"),
    ("Earth / Ochre / Sand", "Sandstone", "Background segmentation", "#C1AF8D"),
    ("Earth / Ochre / Sand", "Clay Brown", "Structural material cue", "#8D6E58"),
    ("Red / Rose / Plum", "Dusty Rose", "Soft annotation layer", "#B27C88"),
    ("Red / Rose / Plum", "Mulberry Plum", "Alternative branch or uncertainty", "#7D678B"),
    ("Red / Rose / Plum", "Brick Red", "Strong intervention cue", "#A35D52"),
    ("Red / Rose / Plum", "Wine Red", "High-contrast negative state", "#7D4B59"),
    ("Neutral", "Cool Gray", "Neutral framework", "#7E8895"),
    ("Neutral", "Warm Gray", "Substrate and context", "#998E84"),
    ("Neutral", "Lavender Gray", "Uncertainty background neutral", "#918B9C"),
    ("Neutral", "Graphite Neutral", "High-contrast neutral anchor", "#5F6670"),
)

COMBINATION_SPECS = (
    (
        "Core Results",
        "Main multi-series result figure with one crisp comparator and a quiet neutral support.",
        (
            ("Primary", "Harbor Blue", 4),
            ("Secondary", "Steel Blue", 3),
            ("Accent", "Brick Red", 4),
            ("Neutral", "Cool Gray", 2),
        ),
    ),
    (
        "Method Flow",
        "Clean pipeline and module diagrams with cool structure, warm signal, and soft context.",
        (
            ("Primary", "Ink Navy", 4),
            ("Secondary", "Aqua Teal", 3),
            ("Accent", "Amber Ochre", 4),
            ("Neutral", "Warm Gray", 2),
        ),
    ),
    (
        "Biology States",
        "Good for state transitions, tissue regions, or biological mechanisms with one caution color.",
        (
            ("Primary", "Pine Green", 4),
            ("Secondary", "Sage Green", 3),
            ("Accent", "Wine Red", 4),
            ("Neutral", "Sandstone", 2),
        ),
    ),
    (
        "Engineering Contrast",
        "Sharper technical contrast for robotics, systems, and ablation diagrams.",
        (
            ("Primary", "Ink Navy", 5),
            ("Secondary", "Mineral Cyan", 3),
            ("Accent", "Terracotta", 4),
            ("Neutral", "Graphite Neutral", 2),
        ),
    ),
    (
        "Calm Supplement",
        "Soft supplementary figures or appendix visuals where lower visual pressure matters.",
        (
            ("Primary", "Sea Glass", 3),
            ("Secondary", "Lavender Gray", 3),
            ("Accent", "Dusty Rose", 3),
            ("Neutral", "Cool Gray", 1),
        ),
    ),
    (
        "Clinical Warm-Cool",
        "Balanced warm-cool composition for comparative figures with human-readable contrast.",
        (
            ("Primary", "Slate Blue", 4),
            ("Secondary", "Sandstone", 3),
            ("Accent", "Brick Red", 4),
            ("Neutral", "Warm Gray", 1),
        ),
    ),
    (
        "Mechanics Highlight",
        "Strong structure with a restrained green and amber cue for mechanics or apparatus illustrations.",
        (
            ("Primary", "Graphite Neutral", 4),
            ("Secondary", "Fern Green", 4),
            ("Accent", "Amber Ochre", 4),
            ("Neutral", "Cool Gray", 2),
        ),
    ),
    (
        "Uncertainty Narrative",
        "Useful when uncertainty, alternatives, and confidence bands need a more nuanced palette.",
        (
            ("Primary", "Mulberry Plum", 4),
            ("Secondary", "Harbor Blue", 3),
            ("Accent", "Dusty Rose", 4),
            ("Neutral", "Lavender Gray", 2),
        ),
    ),
)

LIGHT_BLEND_FACTORS = (0.84, 0.62)
DARK_BLEND_FACTORS = (0.14, 0.32)


@dataclass(frozen=True)
class PaletteShade:
    family: str
    section: str
    role: str
    level: int
    label: str
    rgb: tuple[int, int, int]
    hex_code: str
    ai_rgb: str


@dataclass(frozen=True)
class PaletteFamily:
    name: str
    section: str
    role: str
    shades: tuple[PaletteShade, ...]


@dataclass(frozen=True)
class RecommendedSwatch:
    role_name: str
    family: str
    level: int
    label: str
    rgb: tuple[int, int, int]
    hex_code: str


@dataclass(frozen=True)
class RecommendedCombo:
    name: str
    usage: str
    swatches: tuple[RecommendedSwatch, ...]


def hex_to_rgb(hex_code: str) -> tuple[int, int, int]:
    value = hex_code.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError(f"Expected 6-digit hex color, got {hex_code!r}")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def format_ai_rgb(rgb: tuple[int, int, int]) -> str:
    return "RGB({}, {}, {})".format(*rgb)


def blend_rgb(
    source: tuple[int, int, int],
    target: tuple[int, int, int],
    factor: float,
) -> tuple[int, int, int]:
    return tuple(
        max(0, min(255, round(channel * (1.0 - factor) + target_channel * factor)))
        for channel, target_channel in zip(source, target)
    )


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = [channel / 255.0 for channel in rgb]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def preferred_text_color(rgb: tuple[int, int, int]) -> str:
    return "#203040" if relative_luminance(rgb) > 0.70 else "#FFFFFF"


def build_family(section: str, name: str, role: str, base_hex: str) -> PaletteFamily:
    base_rgb = hex_to_rgb(base_hex)
    ordered_rgbs = (
        [blend_rgb(base_rgb, WHITE, factor) for factor in LIGHT_BLEND_FACTORS]
        + [base_rgb]
        + [blend_rgb(base_rgb, SCIENTIFIC_INK, factor) for factor in DARK_BLEND_FACTORS]
    )

    shades = tuple(
        PaletteShade(
            family=name,
            section=section,
            role=role,
            level=level,
            label=f"{name} {level}",
            rgb=rgb,
            hex_code=rgb_to_hex(rgb),
            ai_rgb=format_ai_rgb(rgb),
        )
        for level, rgb in enumerate(ordered_rgbs, start=1)
    )
    return PaletteFamily(name=name, section=section, role=role, shades=shades)


def build_palette_catalog() -> list[PaletteFamily]:
    return [
        build_family(section, name, role, base_hex)
        for section, name, role, base_hex in BASE_FAMILIES
    ]


def iter_shades(families: Iterable[PaletteFamily]) -> Iterable[PaletteShade]:
    for family in families:
        yield from family.shades


def build_family_lookup(families: Iterable[PaletteFamily]) -> dict[str, PaletteFamily]:
    return {family.name: family for family in families}


def build_recommended_combinations(
    families: list[PaletteFamily],
) -> list[RecommendedCombo]:
    family_lookup = build_family_lookup(families)
    combos: list[RecommendedCombo] = []
    for name, usage, swatch_specs in COMBINATION_SPECS:
        swatches = []
        for role_name, family_name, level in swatch_specs:
            family = family_lookup[family_name]
            shade = family.shades[level - 1]
            swatches.append(
                RecommendedSwatch(
                    role_name=role_name,
                    family=family_name,
                    level=level,
                    label=shade.label,
                    rgb=shade.rgb,
                    hex_code=shade.hex_code,
                )
            )
        combos.append(
            RecommendedCombo(name=name, usage=usage, swatches=tuple(swatches))
        )
    return combos


def build_recommended_lookup(
    combos: Iterable[RecommendedCombo],
) -> dict[tuple[str, int], list[str]]:
    combo_lookup: dict[tuple[str, int], list[str]] = defaultdict(list)
    for combo in combos:
        for swatch in combo.swatches:
            combo_lookup[(swatch.family, swatch.level)].append(combo.name)
    return combo_lookup


def render_palette_svg(
    families: list[PaletteFamily],
    combos: list[RecommendedCombo],
    output_path: Path,
) -> None:
    margin_x = 56
    margin_y = 48
    width = 1296
    combo_gap_x = 16
    combo_gap_y = 18
    combo_card_w = (width - margin_x * 2 - combo_gap_x * 3) // 4
    combo_card_h = 132
    combo_rows = (len(combos) + 3) // 4
    combo_header_h = 56
    combo_section_h = (
        combo_header_h + combo_rows * combo_card_h + (combo_rows - 1) * combo_gap_y + 20
    )

    label_w = 220
    cell_w = 180
    cell_gap = 16
    swatch_h = 56
    text_h = 58
    row_gap = 20
    row_h = swatch_h + text_h
    section_header_h = 32
    section_gap = 18
    palette_header_h = 42

    grouped: dict[str, list[PaletteFamily]] = {section: [] for section in SECTION_ORDER}
    for family in families:
        grouped[family.section].append(family)

    height = (
        margin_y * 2
        + 86
        + combo_section_h
        + palette_header_h
        + len(families) * row_h
        + (len(families) - 1) * row_gap
        + len(SECTION_ORDER) * section_header_h
        + (len(SECTION_ORDER) - 1) * section_gap
        + 56
    )

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}">'
        ),
        '<rect width="100%" height="100%" fill="#FAFBFC"/>',
        (
            '<text x="{x}" y="{y}" font-family="Georgia, Times New Roman, serif" '
            'font-size="28" fill="#1F2D3A">Nature Communications-Inspired Scientific Palette</text>'
        ).format(x=margin_x, y=margin_y),
        (
            '<text x="{x}" y="{y}" font-family="Helvetica, Arial, sans-serif" '
            'font-size="14" fill="#516070">'
            '{count} families x 5 tones. Left to right: light to dark. Tuned for white-background research figures and method diagrams.'
            '</text>'
        ).format(x=margin_x, y=margin_y + 28, count=len(families)),
        (
            '<text x="{x}" y="{y}" font-family="Helvetica, Arial, sans-serif" '
            'font-size="13" fill="#6D7A86">'
            'The top summary gives curated color combinations. The full catalog below keeps the selection broad without turning into visual noise.'
            '</text>'
        ).format(x=margin_x, y=margin_y + 49),
    ]

    combo_section_y = margin_y + 86
    parts.append(
        (
            '<text x="{x}" y="{y}" font-family="Helvetica, Arial, sans-serif" '
            'font-size="20" font-weight="700" fill="#243240">Recommended Scientific Pairings</text>'
        ).format(x=margin_x, y=combo_section_y)
    )
    parts.append(
        (
            '<text x="{x}" y="{y}" font-family="Helvetica, Arial, sans-serif" '
            'font-size="13" fill="#667382">'
            'Start here when you want fast, balanced figure styling. Each set includes a primary, secondary, accent, and neutral anchor.'
            '</text>'
        ).format(x=margin_x, y=combo_section_y + 22)
    )

    combo_card_y0 = combo_section_y + combo_header_h
    for combo_index, combo in enumerate(combos):
        row_index = combo_index // 4
        col_index = combo_index % 4
        card_x = margin_x + col_index * (combo_card_w + combo_gap_x)
        card_y = combo_card_y0 + row_index * (combo_card_h + combo_gap_y)
        swatch_gap = 8
        swatch_w = (combo_card_w - 24 - swatch_gap * 3) // 4
        swatch_y = card_y + 56

        parts.append(
            (
                '<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" ry="14" '
                'fill="#FFFFFF" stroke="#D7DEE7" stroke-width="1.2"/>'
            ).format(x=card_x, y=card_y, w=combo_card_w, h=combo_card_h)
        )
        parts.append(
            (
                '<text x="{x}" y="{y}" font-family="Helvetica, Arial, sans-serif" '
                'font-size="16" font-weight="700" fill="#243240">{name}</text>'
            ).format(x=card_x + 14, y=card_y + 22, name=escape(combo.name))
        )
        parts.append(
            (
                '<text x="{x}" y="{y}" font-family="Helvetica, Arial, sans-serif" '
                'font-size="11" fill="#667382">{usage}</text>'
            ).format(x=card_x + 14, y=card_y + 39, usage=escape(combo.usage))
        )

        for swatch_index, swatch in enumerate(combo.swatches):
            swatch_x = card_x + 12 + swatch_index * (swatch_w + swatch_gap)
            parts.append(
                (
                    '<text x="{x}" y="{y}" font-family="Helvetica, Arial, sans-serif" '
                    'font-size="10" fill="#5E6C78">{role_name}</text>'
                ).format(
                    x=swatch_x,
                    y=swatch_y - 6,
                    role_name=escape(swatch.role_name),
                )
            )
            parts.append(
                (
                    '<rect x="{x}" y="{y}" width="{w}" height="26" rx="8" ry="8" '
                    'fill="{fill}" stroke="#D1D9E0" stroke-width="0.6"/>'
                ).format(
                    x=swatch_x,
                    y=swatch_y,
                    w=swatch_w,
                    fill=swatch.hex_code,
                )
            )
            parts.append(
                (
                    '<text x="{x}" y="{y}" font-family="Helvetica, Arial, sans-serif" '
                    'font-size="9" fill="#2B3947">{label}</text>'
                ).format(
                    x=swatch_x,
                    y=swatch_y + 40,
                    label=escape(swatch.label),
                )
            )
            parts.append(
                (
                    '<text x="{x}" y="{y}" font-family="Menlo, Consolas, monospace" '
                    'font-size="8.5" fill="#6A7885">{hex_code}</text>'
                ).format(
                    x=swatch_x,
                    y=swatch_y + 53,
                    hex_code=swatch.hex_code,
                )
            )

    palette_title_y = combo_card_y0 + combo_rows * combo_card_h + (combo_rows - 1) * combo_gap_y + 36
    parts.append(
        (
            '<text x="{x}" y="{y}" font-family="Helvetica, Arial, sans-serif" '
            'font-size="20" font-weight="700" fill="#243240">Full Palette Catalog</text>'
        ).format(x=margin_x, y=palette_title_y)
    )
    parts.append(
        (
            '<text x="{x}" y="{y}" font-family="Helvetica, Arial, sans-serif" '
            'font-size="13" fill="#667382">'
            'Families are grouped by color section so the broader selection remains scannable.'
            '</text>'
        ).format(x=margin_x, y=palette_title_y + 22)
    )

    current_y = palette_title_y + palette_header_h
    for section_index, section in enumerate(SECTION_ORDER):
        parts.append(
            (
                '<text x="{x}" y="{y}" font-family="Helvetica, Arial, sans-serif" '
                'font-size="18" font-weight="700" fill="#314252">{section}</text>'
            ).format(x=margin_x, y=current_y, section=escape(section))
        )
        parts.append(
            (
                '<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="#D6DDE5" stroke-width="1"/>'
            ).format(x1=margin_x, x2=width - margin_x, y=current_y + 10)
        )
        current_y += section_header_h

        for family in grouped[section]:
            row_y = current_y
            parts.append(
                (
                    '<text x="{x}" y="{y}" font-family="Helvetica, Arial, sans-serif" '
                    'font-size="18" font-weight="700" fill="#243240">{name}</text>'
                ).format(x=margin_x, y=row_y + 24, name=escape(family.name))
            )
            parts.append(
                (
                    '<text x="{x}" y="{y}" font-family="Helvetica, Arial, sans-serif" '
                    'font-size="12" fill="#667382">{role}</text>'
                ).format(x=margin_x, y=row_y + 46, role=escape(family.role))
            )

            swatch_x = margin_x + label_w
            for shade_index, shade in enumerate(family.shades):
                cell_x = swatch_x + shade_index * (cell_w + cell_gap)
                parts.append(
                    (
                        '<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" ry="12" '
                        'fill="#FFFFFF" stroke="#D5DDE5" stroke-width="1"/>'
                    ).format(x=cell_x, y=row_y, w=cell_w, h=row_h)
                )
                parts.append(
                    (
                        '<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" ry="12" '
                        'fill="{fill}"/>'
                    ).format(
                        x=cell_x,
                        y=row_y,
                        w=cell_w,
                        h=swatch_h,
                        fill=shade.hex_code,
                    )
                )
                parts.append(
                    (
                        '<text x="{x}" y="{y}" font-family="Helvetica, Arial, sans-serif" '
                        'font-size="13" font-weight="700" fill="{fill}">{label}</text>'
                    ).format(
                        x=cell_x + 12,
                        y=row_y + 22,
                        fill=preferred_text_color(shade.rgb),
                        label=escape(shade.label),
                    )
                )
                parts.append(
                    (
                        '<text x="{x}" y="{y}" font-family="Menlo, Consolas, monospace" '
                        'font-size="12" fill="#25303A">RGB {rgb}</text>'
                    ).format(
                        x=cell_x + 12,
                        y=row_y + swatch_h + 18,
                        rgb=", ".join(str(channel) for channel in shade.rgb),
                    )
                )
                parts.append(
                    (
                        '<text x="{x}" y="{y}" font-family="Menlo, Consolas, monospace" '
                        'font-size="12" fill="#25303A">HEX {hex_code}</text>'
                    ).format(
                        x=cell_x + 12,
                        y=row_y + swatch_h + 35,
                        hex_code=shade.hex_code,
                    )
                )
                parts.append(
                    (
                        '<text x="{x}" y="{y}" font-family="Menlo, Consolas, monospace" '
                        'font-size="11" fill="#52606D">{ai_rgb}</text>'
                    ).format(
                        x=cell_x + 12,
                        y=row_y + swatch_h + 51,
                        ai_rgb=shade.ai_rgb,
                    )
                )
            current_y += row_h + row_gap

        current_y -= row_gap
        if section_index < len(SECTION_ORDER) - 1:
            current_y += section_gap

    parts.append("</svg>")
    output_path.write_text("\n".join(parts), encoding="utf-8")


def write_palette_csv(
    families: list[PaletteFamily],
    combos: list[RecommendedCombo],
    output_path: Path,
) -> None:
    recommended_lookup = build_recommended_lookup(combos)
    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            [
                "family",
                "section",
                "role",
                "level",
                "label",
                "rgb",
                "hex",
                "ai_rgb",
                "recommended_combo",
            ]
        )
        for shade in iter_shades(families):
            writer.writerow(
                [
                    shade.family,
                    shade.section,
                    shade.role,
                    shade.level,
                    shade.label,
                    ", ".join(str(channel) for channel in shade.rgb),
                    shade.hex_code,
                    shade.ai_rgb,
                    "; ".join(recommended_lookup.get((shade.family, shade.level), [])),
                ]
            )


def write_palette_markdown(
    families: list[PaletteFamily],
    combos: list[RecommendedCombo],
    output_path: Path,
) -> None:
    recommended_lookup = build_recommended_lookup(combos)
    lines = [
        "# Nature Communications-Inspired Scientific Palette",
        "",
        "A research-oriented palette for white-background figures and method diagrams.",
        "",
        "## Recommended Scientific Pairings",
        "",
        "| Combination | Usage | Primary | Secondary | Accent | Neutral |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for combo in combos:
        lines.append(
            "| {name} | {usage} | {primary} | {secondary} | {accent} | {neutral} |".format(
                name=combo.name,
                usage=combo.usage,
                primary=f"{combo.swatches[0].label} ({combo.swatches[0].hex_code})",
                secondary=f"{combo.swatches[1].label} ({combo.swatches[1].hex_code})",
                accent=f"{combo.swatches[2].label} ({combo.swatches[2].hex_code})",
                neutral=f"{combo.swatches[3].label} ({combo.swatches[3].hex_code})",
            )
        )

    lines.extend(
        [
            "",
            "## Full Palette Catalog",
            "",
            "| Family | Section | Role | Level | Label | RGB | HEX | AI RGB | Recommended Combo |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for shade in iter_shades(families):
        lines.append(
            "| {family} | {section} | {role} | {level} | {label} | {rgb} | {hex_code} | {ai_rgb} | {recommended_combo} |".format(
                family=shade.family,
                section=shade.section,
                role=shade.role,
                level=shade.level,
                label=shade.label,
                rgb=", ".join(str(channel) for channel in shade.rgb),
                hex_code=shade.hex_code,
                ai_rgb=shade.ai_rgb,
                recommended_combo=", ".join(
                    recommended_lookup.get((shade.family, shade.level), [])
                ),
            )
        )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_palette_assets(output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    families = build_palette_catalog()
    combos = build_recommended_combinations(families)

    svg_path = output_dir / f"{OUTPUT_BASENAME}.svg"
    csv_path = output_dir / f"{OUTPUT_BASENAME}.csv"
    markdown_path = output_dir / f"{OUTPUT_BASENAME}.md"

    render_palette_svg(families, combos, svg_path)
    write_palette_csv(families, combos, csv_path)
    write_palette_markdown(families, combos, markdown_path)

    return {
        "svg": svg_path,
        "csv": csv_path,
        "markdown": markdown_path,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a research-friendly Nature Communications-inspired palette."
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory for generated palette assets. Defaults to the current directory.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    paths = write_palette_assets(Path(args.output_dir).expanduser())
    for label, path in paths.items():
        print(f"[palette] wrote {label}: {path}")


if __name__ == "__main__":
    main()
