# Windows Trust Checklist

## Official References

- Microsoft SmartScreen reputation for Windows app developers: `https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation`
- Microsoft code signing options for Windows app developers: `https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options`
- Microsoft SignTool reference: `https://learn.microsoft.com/en-us/windows/win32/seccrypto/signtool`
- Microsoft Trusted Root Program requirements: `https://learn.microsoft.com/en-us/security/trusted-root/program-requirements`

## Key Points For This Project

- Unsigned PyInstaller `.exe` files are high-risk for SmartScreen and antivirus warnings.
- Self-signed certificates are only useful for internal testing when the target machine trusts the root. They do not solve public distribution trust.
- Public distribution needs a trusted code-signing path:
  - Microsoft Store/MSIX signing when distributing through Store.
  - Microsoft Trusted Signing / Azure Artifact Signing where available.
  - A publicly trusted code-signing certificate from a CA trusted by Windows.
- Sign the final executable after PyInstaller creates it. If an installer is later added, sign both the installer and embedded executables when applicable.
- Always timestamp Authenticode signatures.
- Keep secrets outside the repository and CI logs: PFX files, passwords, hardware-token secrets, Azure tenant/subscription identifiers when sensitive, and service-principal secrets.

## Manual Validation Steps

1. Build Windows artifact:
   - `python tools/build_release.py --platform windows`
2. Confirm the expected executable exists:
   - `dist/pinyin_tones_release/windows/pinyin_tones.exe`
3. Check signature status:
   - `signtool verify /pa /v path\to\pinyin_tones.exe`
4. Check timestamp status:
   - `signtool verify /pa /tw /v path\to\pinyin_tones.exe`
5. Inspect signer:
   - Confirm publisher name is the expected legal publisher identity.
   - Confirm certificate chain terminates in a Windows-trusted root.
6. Scan locally:
   - Run Microsoft Defender scan on the built release directory.
   - If available, test on a clean Windows VM after downloading the zip through the intended distribution path.
7. If SmartScreen or Defender warns:
   - Verify the signature first.
   - Record exact warning text and file hash.
   - Submit false positives through Microsoft Security Intelligence if Defender flags malware.
   - Treat SmartScreen reputation as separate from signature validity.

## Review Checklist For Code Changes

- Build script still produces `pinyin_tones.exe`.
- Release zip names remain stable unless explicitly changed:
  - `pinyin-tones-windows.zip`
  - `pinyin-tones-macos.zip`
  - `pinyin-tones-linux.zip`
- Docs do not imply "no warnings guaranteed."
- CI or release instructions never print or commit signing secrets.
- Tests cover any changed artifact names, release paths, or signing command assembly.
