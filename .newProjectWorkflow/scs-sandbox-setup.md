# SCS Sandbox One-Time Host Setup

The Supply Chain Security (SCS) agent runs all dependency scanning inside a pair of Windows Sandbox instances (Hyper-V isolation). Each sandbox is destroyed when it closes; sandbox processes can only access explicitly mapped folders.

**This setup runs ONCE per machine, ever.** It is NOT per-project and NOT something the SCS agent or orchestrator should run during normal operation. After completing the steps below, the infrastructure persists indefinitely. The SCS agent is explicitly forbidden from running these setup commands.

If you are reading this because a sandbox launch failed and the SCS agent reported missing infrastructure, run the steps below. Otherwise, no action needed.

---

## Folder Structure

All under `PLACEHOLDER_PATH\.scs-sandbox\`:

```
.scs-sandbox\
├── download.wsb          ← sandbox config for Phase 2 (download, network ON)
├── scan.wsb              ← sandbox config for Phase 3 (scan, network OFF)
├── staging\              ← download sandbox writes here; scan sandbox reads here
├── results\              ← scan sandbox writes Defender results here
└── scripts\              ← PowerShell scripts (mapped read-only into both sandboxes)
    ├── download.ps1
    └── scan.ps1
```

The download sandbox writes artifacts to `staging\`. The scan sandbox reads from `staging\` (mapped read-only) and writes results to `results\` (read-write). This separation ensures the scan sandbox cannot modify the downloaded artifact.

**Hard limit:** Only one Windows Sandbox can run at a time, so Phase 2 (download) and Phase 3 (scan) are strictly sequential.

---

## Step 1 — Create Folders

Run once on the host via PowerShell:

```powershell
$base = "PLACEHOLDER_PATH\.scs-sandbox"
New-Item -ItemType Directory -Force -Path "$base\staging"
New-Item -ItemType Directory -Force -Path "$base\results"
New-Item -ItemType Directory -Force -Path "$base\scripts"
```

---

## Step 2 — Write WSB Configuration Files

Write these two files to `.scs-sandbox\` once. They do not change between scans. Both configs disable VGpu, AudioInput, VideoInput, ClipboardRedirection, and PrinterRedirection. Both map `.scs-sandbox\scripts` to `C:\scripts` (read-only). The `LogonCommand` runs the respective `.ps1` file with `-ExecutionPolicy Bypass`.

| Setting | `download.wsb` | `scan.wsb` |
|---------|----------------|------------|
| Networking | **Enable** | **Disable** |
| ProtectedClient | (omit) | **Enable** |
| MemoryInMB | (omit) | **4096** |
| staging mapped as | `C:\staging` (read-write) | `C:\input` (**read-only**) |
| results mapped | (none) | `C:\results` (read-write) |
| LogonCommand | `C:\scripts\download.ps1` | `C:\scripts\scan.ps1` |

**Important — `scan.wsb` mapping name:** `scan.wsb` maps staging to `C:\input` (not `C:\staging`) because the scan sandbox treats it as read-only input. The scan script (`scan.ps1`) references `C:\input\`, not `C:\staging\`.

**Important — XML escaping in WSB files:** WSB files are XML. The `&` character is reserved in XML (it starts entity references like `&amp;`). Any literal `&` in the `<Command>` element — including the PowerShell call operator `&` — must be written as `&amp;`. Failing to escape it causes an XML parse error and the sandbox refuses to open.

---

## Step 3 — Write PowerShell Scripts

**CRITICAL: ASCII-only in `.ps1` files.** Windows Sandbox runs PowerShell 5.1, which reads scripts as Windows-1252 (not UTF-8). Em dashes, curly quotes, and other non-ASCII characters cause silent parse failures. Use only straight quotes, ASCII hyphens, and plain ASCII text in all `.ps1` files, **including comments**.

Write these two files to `.scs-sandbox\scripts\` once. They are mapped read-only into both sandboxes during scans.

**`scripts\download.ps1`** — runs inside the download sandbox:

1. Read `C:\staging\download-config.json` (fields: `url`, `fileName`). If missing, write `C:\staging\DOWNLOAD_ERROR` sentinel and `Stop-Computer -Force`.
2. Download with `curl.exe -L --fail --output C:\staging\$fileName $url`. If download fails, write `DOWNLOAD_ERROR` sentinel and `Stop-Computer -Force`.
3. Compute SHA-256 hash via `Get-FileHash -Algorithm SHA256`. Write hash to `C:\staging\hash.txt`.
4. Write `C:\staging\DOWNLOAD_DONE` sentinel. `Stop-Computer -Force`.

**`scripts\scan.ps1`** — runs inside the scan sandbox (network OFF):

1. Read `C:\input\scan-config.json` (field: `fileName`). If missing, write `C:\results\SCAN_ERROR` sentinel and `Stop-Computer -Force`.
2. Verify artifact exists at `C:\input\$fileName`. If missing, write `SCAN_ERROR` sentinel and `Stop-Computer -Force`.
3. Run Windows Defender: `& "C:\Program Files\Windows Defender\MpCmdRun.exe" -Scan -ScanType 3 -File $target`. Capture `$LASTEXITCODE`.
4. Defender exit codes: **0** = CLEAN (no threats), **2** = THREAT DETECTED, **other** = ERROR.
5. Write results JSON (`exitCode`, `threatFound`, `status`, plus `threatName` and `threatDetails` when a threat is found) to `C:\results\defender-results.json`.
6. Write `C:\results\SCAN_DONE` sentinel. `Stop-Computer -Force`.

---

## Verification

After all three steps, confirm the layout exists:

```powershell
Get-ChildItem "PLACEHOLDER_PATH\.scs-sandbox" -Recurse -Depth 1
```

You should see `download.wsb`, `scan.wsb`, the `staging\`, `results\`, and `scripts\` subfolders, and `download.ps1` + `scan.ps1` inside `scripts\`. Once verified, the SCS agent can be invoked normally.
