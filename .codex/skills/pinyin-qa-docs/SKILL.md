---
name: pinyin-qa-docs
description: Review and maintain project-wide tests, documentation, contribution guidance, and consistency for Pinyin Tones. Use when adding or reorganizing tests, updating README/docs/user guidance, reviewing changes across multiple areas, or checking that behavior, documentation, and release expectations remain aligned.
---

# Pinyin QA Docs

## Workflow

1. Read `README.md`, `CONTRIBUTING.md`, and any docs related to the requested change.
2. Map behavior changes to focused tests under `tests/`; prefer `unittest` style already used by the repo.
3. Keep docs in sync with actual behavior, especially hotkeys, permissions, config fields, release assets, and troubleshooting.
4. Avoid broad rewrites of Spanish project docs unless the request is documentation-focused.
5. Run `python tools/run_tests.py` when possible. If only docs changed, explain why code tests were not necessary or still run a quick sanity check if available.

## Reference

Read `references/qa-docs-map.md` for the project documentation map, test ownership, and review checklist.
