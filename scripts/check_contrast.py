"""Check UI-UX section 2 using WCAG 2.x sRGB contrast, without dependencies."""

import argparse
import math
import re
import sys
import unittest
from pathlib import Path

RGB = tuple[float, float, float]
PAIR_PATTERN = re.compile(r"`(--[\w-]+)`\s+on\s+`(--[\w-]+)`")


def parse_rgb(value: str) -> RGB:
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise ValueError(f"Contract colors must be opaque six-digit sRGB hex: {value}")
    return (
        int(value[1:3], 16) / 255,
        int(value[3:5], 16) / 255,
        int(value[5:7], 16) / 255,
    )


def linearize(channel: float) -> float:
    if channel <= 0.04045:
        return channel / 12.92
    return math.pow((channel + 0.055) / 1.055, 2.4)


def luminance(color: RGB) -> float:
    red, green, blue = (linearize(channel) for channel in color)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast(foreground: RGB, background: RGB) -> float:
    lighter, darker = sorted(
        (luminance(foreground), luminance(background)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def parse_contract(
    document: str,
) -> tuple[dict[str, RGB], list[tuple[str, str, float]]]:
    section = re.search(r"^## 2\. [^\n]+\n(.*?)(?=^## |\Z)", document, re.M | re.S)
    if section is None:
        raise ValueError("Missing section 2")
    css = re.search(r"```css\s*\n(.*?)```", section[1], re.S)
    if css is None:
        raise ValueError("Missing section 2 CSS token block")
    values: dict[str, str] = {}
    for name, value in re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", css[1]):
        if name in values:
            raise ValueError(f"Duplicate token: {name}")
        values[name] = value.strip()
    contract = re.search(
        r"^Contrast contract[^\n]*\n(.*?)(?=\nThe values|\Z)", section[1], re.M | re.S
    )
    if contract is None:
        raise ValueError("Missing contrast contract")
    preamble = contract[0].splitlines()[0]
    threshold = re.search(r"All pairs below must be at least ([\d.]+):1", preamble)
    if threshold is None:
        raise ValueError("Missing default contrast threshold")
    default = float(threshold[1])
    pairs: list[tuple[str, str, float]] = []
    tokens: dict[str, RGB] = {}
    numbers: list[int] = []
    for line in contract[1].splitlines():
        if not line.strip():
            continue
        item = re.fullmatch(r"(\d+)\.\s+(.+)", line)
        if item is None:
            raise ValueError(f"Unrecognized contract line: {line}")
        numbers.append(int(item[1]))
        matches = list(PAIR_PATTERN.finditer(item[2]))
        if not matches:
            raise ValueError(f"No token pair in contract line: {line}")
        remainder = PAIR_PATTERN.sub("", item[2])
        annotation = re.search(r"\(non-text,\s*([\d.]+):1\)", remainder)
        minimum = float(annotation[1]) if annotation else default
        remainder = re.sub(r"\(non-text,\s*[\d.]+:1\)", "", remainder)
        if remainder.strip(" ,"):
            raise ValueError(f"Unrecognized contract syntax: {line}")
        if not math.isfinite(minimum) or not 1 <= minimum <= 21:
            raise ValueError("Contrast threshold must be between 1 and 21")
        for match in matches:
            foreground, background = match.groups()
            for name in (foreground, background):
                if name not in values:
                    raise ValueError(f"Undefined contract token: {name}")
                tokens[name] = parse_rgb(values[name])
            if any(pair[:2] == (foreground, background) for pair in pairs):
                raise ValueError(
                    f"Duplicate contract pair: {foreground} on {background}"
                )
            pairs.append((foreground, background, minimum))
    if not pairs or numbers != list(range(1, len(numbers) + 1)):
        raise ValueError("Contract must have consecutive numbered items starting at 1")
    return tokens, pairs


class ContrastChecks(unittest.TestCase):
    def test_UI_1_extreme_and_identical_colors(self) -> None:
        black, white = (0.0, 0.0, 0.0), (1.0, 1.0, 1.0)
        self.assertEqual(luminance(black), 0)
        self.assertEqual(luminance(white), 1)
        self.assertEqual(contrast(black, white), 21)
        self.assertEqual(contrast(white, white), 1)

    def test_UI_1_luminance_weights(self) -> None:
        self.assertAlmostEqual(luminance((1, 0, 0)), 0.2126)
        self.assertAlmostEqual(luminance((0, 1, 0)), 0.7152)
        self.assertAlmostEqual(luminance((0, 0, 1)), 0.0722)

    def test_UI_1_linearization_boundary(self) -> None:
        self.assertEqual(linearize(0.04045), 0.04045 / 12.92)
        self.assertAlmostEqual(linearize(0.5), 0.21404114048223255)

    def test_UI_1_unrounded_threshold_and_symmetry(self) -> None:
        white = (1.0, 1.0, 1.0)
        self.assertGreater(contrast(parse_rgb("#767676"), white), 4.5)
        self.assertLess(contrast(parse_rgb("#777777"), white), 4.5)
        self.assertEqual(
            contrast(parse_rgb("#767676"), white), contrast(white, parse_rgb("#767676"))
        )

    def test_UI_1_contract_parses_multiple_pairs_and_thresholds(self) -> None:
        tokens, pairs = parse_contract(self.example())
        self.assertEqual(len(tokens), 3)
        self.assertEqual(
            pairs, [("--a", "--b", 4.5), ("--a", "--c", 4.5), ("--c", "--b", 3.0)]
        )

    def test_UI_1_missing_and_unsupported_tokens_fail(self) -> None:
        for document in (
            self.example().replace("--a:", "--missing:"),
            self.example().replace("#000000", "rgba(0,0,0,0.5)"),
        ):
            with self.assertRaises(ValueError):
                parse_contract(document)

    def test_UI_1_malformed_contract_fails(self) -> None:
        for document in (
            "",
            self.example().replace("2. `", "3. `"),
            self.example().replace(" on ", " against "),
        ):
            with self.assertRaises(ValueError):
                parse_contract(document)

    @staticmethod
    def example() -> str:
        return """## 2. Design tokens
```css
:root { --a: #000000; --b: #FFFFFF; --c: #767676; }
```
Contrast contract. All pairs below must be at least 4.5:1:

1. `--a` on `--b`, `--a` on `--c`
2. `--c` on `--b` (non-text, 3:1)

The values are approved.
## 3. Typography
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "spec",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "docs/UI-UX.md",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run formula and parser checks without reading the spec",
    )
    args = parser.parse_args()
    if args.self_test:
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(ContrastChecks)
        )
        return 0 if result.wasSuccessful() else 1
    try:
        tokens, pairs = parse_contract(args.spec.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        print(f"Contrast input error: {error}", file=sys.stderr)
        return 2
    failures = 0
    print("| Pair | Ratio | Minimum | Result |")
    print("|---|---:|---:|---|")
    for foreground, background, minimum in pairs:
        ratio = contrast(tokens[foreground], tokens[background])
        passed = ratio >= minimum
        failures += not passed
        print(
            f"| `{foreground}` on `{background}` | {ratio:.4f}:1 | "
            f"{minimum:g}:1 | {'PASS' if passed else 'FAIL'} |"
        )
    print(f"\n{len(pairs) - failures}/{len(pairs)} pairs pass; {failures} fail.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
