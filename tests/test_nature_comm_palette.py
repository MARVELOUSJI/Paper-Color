import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "generate_nature_comm_palette.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "generate_nature_comm_palette", MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        return module
    finally:
        sys.modules.pop(spec.name, None)


class NatureCommPaletteTests(unittest.TestCase):
    def test_palette_catalog_has_twenty_four_families_with_sections_and_five_shades(self):
        module = _load_module()

        families = module.build_palette_catalog()

        self.assertEqual(len(families), 24)
        self.assertEqual(
            {family.section for family in families},
            {
                "Blue / Navy",
                "Cyan / Teal",
                "Green",
                "Earth / Ochre / Sand",
                "Red / Rose / Plum",
                "Neutral",
            },
        )
        for family in families:
            self.assertEqual(len(family.shades), 5)
            luminances = [
                module.relative_luminance(shade.rgb) for shade in family.shades
            ]
            self.assertEqual(luminances, sorted(luminances, reverse=True))

    def test_color_code_formatters_match_expected_values(self):
        module = _load_module()

        self.assertEqual(module.rgb_to_hex((45, 118, 167)), "#2D76A7")
        self.assertEqual(
            module.format_ai_rgb((45, 118, 167)),
            "RGB(45, 118, 167)",
        )

    def test_recommended_combinations_have_eight_curated_sets(self):
        module = _load_module()

        combos = module.build_recommended_combinations(module.build_palette_catalog())

        self.assertEqual(len(combos), 8)
        self.assertEqual(len({combo.name for combo in combos}), 8)
        for combo in combos:
            self.assertTrue(combo.usage)
            self.assertEqual(len(combo.swatches), 4)
            self.assertEqual(
                [swatch.role_name for swatch in combo.swatches],
                ["Primary", "Secondary", "Accent", "Neutral"],
            )

    def test_write_palette_assets_creates_svg_csv_and_markdown(self):
        module = _load_module()

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            paths = module.write_palette_assets(output_dir)

            self.assertTrue(paths["svg"].exists())
            self.assertTrue(paths["csv"].exists())
            self.assertTrue(paths["markdown"].exists())

            svg_text = paths["svg"].read_text(encoding="utf-8")
            csv_text = paths["csv"].read_text(encoding="utf-8")
            markdown_text = paths["markdown"].read_text(encoding="utf-8")

            self.assertIn("Nature Communications-Inspired Scientific Palette", svg_text)
            self.assertIn("Recommended Scientific Pairings", svg_text)
            self.assertIn("24 families x 5 tones", svg_text)
            self.assertIn("Core Results", svg_text)
            self.assertIn(
                "family,section,role,level,label,rgb,hex,ai_rgb,recommended_combo",
                csv_text,
            )
            self.assertIn(
                "| Combination | Usage | Primary | Secondary | Accent | Neutral |",
                markdown_text,
            )
            self.assertIn(
                "| Family | Section | Role | Level | Label | RGB | HEX | AI RGB | Recommended Combo |",
                markdown_text,
            )


if __name__ == "__main__":
    unittest.main()
