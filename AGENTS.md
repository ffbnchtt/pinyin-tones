# AGENTS.md

## Scope

These instructions apply to the whole repository.

Act as a senior software development coding agent. Before editing, inspect the relevant files and follow the repository architecture, conventions, tooling, and style. Make minimal, focused, production-quality changes. Avoid unrelated refactors and unnecessary dependencies.

Prioritize correctness, maintainability, clear error handling, security, and testability. Preserve backward compatibility unless the user explicitly asks for a breaking change.

## Project Commands

- Run tests: `python tools/run_tests.py`
- Run from source: `python -m pinyin_tones`
- Build a package: `python tools/build_release.py --platform windows`

Do not claim tests passed unless they actually ran. If GUI, OS permission, keyboard listener, tray, clipboard, registry, launch-agent, or network behavior cannot be verified locally, state that clearly.

## Agent Routing

Use the smallest applicable agent/skill for the request.

### Pinyin Conversion Agent

- Skill: `.codex/skills/pinyin-conversion-rules`
- Owns: `src/pinyin_tones/pinyin_converter.py`, `tests/test_converter.py`
- Use for: token matching, tone placement, `v`/`ü`, case preservation, neutral tone behavior, and pure conversion tests.
- Keep this area pure. Do not add runtime, UI, clipboard, keyboard, config, or platform concerns here.

### Pinyin Live Runtime Agent

- Skill: `.codex/skills/pinyin-live-runtime`
- Owns: `src/pinyin_tones/pinyin_live.py`, `buffer.py`, `clipboard.py`, `keyboard_output.py`, `hotkeys.py`, `settings_ui.py`, `tray_ui.py`, `config_store.py`, `autostart.py`, and `tests/test_live_flow.py`
- Use for: global keyboard listeners, live replacement, buffer state, synthetic input suppression, clipboard restore, hotkey capture, tray/settings UI, config, and autostart.
- Prefer mocks and isolated global-state setup in tests.

### Pinyin Release Updates Agent

- Skill: `.codex/skills/pinyin-release-updates`
- Owns: `tools/build_release.py`, `tools/build_*.sh`, `tools/build_windows.bat`, `src/pinyin_tones/update_check.py`, `update_dialog.py`, `version.py`, `pyproject.toml`, `docs/BUILD.md`, `docs/DOWNLOAD.md`, `tests/test_build_release.py`, and `tests/test_update_check.py`
- Use for: package builds, PyInstaller flags, release asset names, version comparisons, GitHub release checks, downloads, and update dialogs.
- Keep release asset names stable unless the user explicitly changes the release contract.

### Pinyin Windows Trust Agent

- Skill: `.codex/skills/pinyin-windows-trust`
- Owns: Windows signing/trust validation guidance, Authenticode/SignTool checks, certificate and timestamp requirements, SmartScreen/Defender warning risk, and docs/tests for Windows release trust readiness.
- Use for: Windows code signing, certificate choices, signing command validation, SmartScreen reputation, antivirus false-positive mitigation, and release security warnings.
- Do not commit signing secrets, certificates, private keys, PFX files, or token credentials.

### Pinyin QA Docs Agent

- Skill: `.codex/skills/pinyin-qa-docs`
- Owns: repository-wide review, `README.md`, `docs/`, `CONTRIBUTING.md`, issue/PR templates, and test coverage alignment.
- Use for: documentation updates, review tasks, cross-cutting test coverage, and consistency checks across behavior, docs, and release expectations.

## Testing Expectations

- Conversion changes: update/run `tests/test_converter.py`.
- Runtime changes: update/run `tests/test_live_flow.py`.
- Update/release changes: update/run `tests/test_update_check.py` and/or `tests/test_build_release.py`.
- Cross-cutting changes: run `python tools/run_tests.py` when feasible.

## Final Response Checklist

After changes, summarize:

1. What changed
2. Files modified
3. Tests/checks run
4. Assumptions, risks, or follow-ups
