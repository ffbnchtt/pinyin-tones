---
name: pinyin-conversion-rules
description: Maintain the pure Hanyu Pinyin conversion logic for this project. Use when changing token parsing, tone placement rules, umlaut/v handling, case preservation, neutral tone behavior, or tests around src/pinyin_app/pinyin_converter.py and tests/test_converter.py.
---

# Pinyin Conversion Rules

## Workflow

1. Inspect `src/pinyin_app/pinyin_converter.py` and `tests/test_converter.py` before editing.
2. Keep conversion pure and deterministic: no clipboard, keyboard, UI, logging, config, or platform logic belongs in this area.
3. Preserve the existing public helpers unless the request explicitly allows a breaking change: `convert_pinyin_token`, `apply_tone`, `get_tone_target_index`, and `has_vowel`.
4. Add or update focused `unittest` cases for every behavior change.
5. Run at least `python tools/run_tests.py` when possible; for a narrow change, also mention that the relevant coverage is `tests/test_converter.py`.

## Rules To Preserve

- Only full tokens shaped like pinyin letters plus a trailing tone digit `1`-`5` are converted.
- Tone `5` is neutral and currently returns the original token because no diacritic is applied.
- Tone placement priority is `a`, then `o`, then `e`, then special `iu`/`ui`, then the last valid `i/u/v/ü` vowel.
- `v` and `ü` represent the umlaut vowel; uppercase input should preserve uppercase output where applicable.
- Non-matching or unconvertible input returns the original token.

## Reference

Read `references/conversion-map.md` when you need a compact map of owned files, tests, and common edge cases.
