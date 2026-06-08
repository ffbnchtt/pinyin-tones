# Conversion Map

## Owned Files

- `src/pinyin_tones/pinyin_converter.py`: pure Hanyu Pinyin conversion helpers.
- `tests/test_converter.py`: focused unit tests for token conversion and vowel detection.

## Current Contracts

- `convert_pinyin_token(token: str) -> str` returns converted text or the original token.
- `apply_tone(syllable: str, tone_number: int) -> str` returns an empty string for invalid tone numbers or missing valid vowels.
- `get_tone_target_index(syllable: str) -> Optional[int]` encodes tone placement priority.
- `has_vowel(s: str) -> bool` accepts ASCII vowels, `v/V`, and `ü/Ü`.

## Edge Cases To Test

- `a/o/e` priority: examples such as `hao3`, `hua2`.
- `iu` and `ui`: examples such as `liu3`, `hui4`.
- Umlaut handling: `lü4`, `Lü4`, and any new `v` behavior.
- Neutral tone: decide whether tone `5` should remain unchanged or drop the digit before changing tests.
- Non-matches: embedded digits, suffixes after the tone digit, missing vowels, and invalid tone numbers.

## Non-Goals

- Do not add runtime buffering, clipboard, or UI behavior here.
- Do not broaden matching to sentence-level parsing unless the live runtime and tests are updated deliberately.
