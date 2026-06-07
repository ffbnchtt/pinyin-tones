---
name: pinyin-windows-trust
description: Validate Windows release trust readiness for Pinyin Tones. Use when changing Windows packaging, signing, certificates, PyInstaller release artifacts, SmartScreen/Defender false-positive risk, Authenticode signatures, timestamping, publisher identity, installer/executable trust, or documentation about Windows security warnings.
---

# Pinyin Windows Trust

## Workflow

1. Read `references/windows-trust-checklist.md`, then inspect the Windows build path:
   - `tools/build_release.py`
   - `tools/build_windows.bat`
   - `docs/BUILD.md`
   - `docs/DOWNLOAD.md`
   - release payload tests under `tests/`
2. Treat signing/trust as release validation, not normal unit-test behavior.
3. Prefer official Microsoft documentation for current SmartScreen, Trusted Signing, SignTool, and certificate behavior. Browser-check Microsoft docs if the task asks for current recommendations.
4. Keep internal Python package names separate from signed artifact names. The user-facing Windows artifact is `pinyin_tones.exe` inside a stable release zip such as `pinyin-tones-windows.zip`.
5. Do not promise that signing fully prevents antivirus or SmartScreen warnings. State residual reputation risk clearly.
6. Do not add private keys, certificate files, PFX passwords, tenant IDs, or signing secrets to the repo.

## Validation Targets

- Artifact identity: final Windows executable is named consistently and has stable product/publisher metadata where supported.
- Signature: executable and any installer/zip-contained executable are Authenticode-signed by a trusted code-signing certificate or Microsoft Trusted Signing/Azure Artifact Signing.
- Timestamp: signature includes a trusted timestamp so it remains valid after certificate expiration.
- Verification: `signtool verify` succeeds on a clean Windows machine with normal root trust.
- Reputation: SmartScreen risk is assessed separately from signature validity; new binaries may still need reputation or Store/Microsoft signing path.
- Security scanning: Windows Defender scan is clean, and false-positive handling is documented.

## Expected Output

When validating or implementing Windows trust work, report:

- Current signing status: unsigned, self-signed, OV/EV CA-signed, Trusted Signing/Azure Artifact Signing, or Store-signed.
- Commands used to sign and verify, redacting secrets.
- Whether timestamping is present.
- Whether the release artifact name and docs match `Pinyin Tones` / `pinyin_tones`.
- Remaining risks and manual checks that cannot be verified locally.

