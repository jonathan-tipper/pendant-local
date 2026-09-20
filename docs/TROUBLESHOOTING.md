# Troubleshooting

Start with the command below, using the same data directory as the server:

```bash
.venv/bin/pendant-local doctor
```

Windows: `.venv\Scripts\pendant-local.exe doctor`. It checks configuration and
local prerequisites without connecting to a device. Review its output before
sharing: paths and addresses may identify your computer or device.

| Symptom | What to check |
| --- | --- |
| Python or venv missing | Install Python 3.11+; on Linux install your distribution's venv support. Run bootstrap from the repository folder. |
| Optional engine installation fails | Use `bootstrap.py --without-transcription`, keep the error, and check whether the engine has a wheel for your OS, CPU and Python version. |
| Dashboard will not open | Leave `serve` running and open its printed localhost URL on the same computer. Python defaults to 8765; the Mac app uses 8766. |
| Port already in use | Open the existing service or choose another port with a separate development workspace. Do not kill an unidentified listener. |
| Another service owns the data directory | Finish current work and stop that service. A different port does not allow 2 services to use one workspace. |
| Sign-in rejected | Get the token from the same data directory and environment as the service. A `PENDANT_API_TOKEN` override takes precedence. Never paste it into a URL or issue. |
| Scan finds nothing | Charge the Pendant, bring it near the host, enable Bluetooth and allow OS permissions. On Linux check BlueZ and system D-Bus access. |
| Scan succeeds but connection fails | Disconnect other apps/hosts. Use the exact address from this OS's scan. A previous bond can block access. Do not factory-reset valuable recordings. |
| CLI scan/info fails while UI works | Stop the service before using CLI Bluetooth commands, or use the dashboard/API instead. |
| Start fails on clock acknowledgement | Verify connection and computer time; choose Set clock and retry only after acknowledgement. Do not assume recording began. |
| Zero new audio after sync | Check whether pages contained no audio, recordings were already saved, the transfer was partial, or decoding produced warnings. These are different results. |
| Newer recordings never appear | Short syncs can repeatedly retrieve early pages. Try a longer non-deleting transfer, up to 1 hour. The protocol has no resume offset and completeness is not guaranteed. |
| Missing-key / encrypted-packet warnings | Preserve raw captures and original keys. A new local key cannot decrypt vendor-encrypted audio. Unsupported encrypted layouts need further hardware work. |
| Audio imported but will not play | Try a browser supporting that codec, or inspect a private copy locally. Keep the original. Import acceptance does not guarantee valid audio. |
| Model unavailable | Explicitly download it in Settings. Dependency installation alone does not prepare weights. Check disk space and failed jobs in Workflow. |
| Cancel remains “stopping” | Wait for the current native inference operation. Do not repeatedly retry while it still runs. |
| Repeated or incorrect words / speaker labels | Listen to the audio, set the correct language, try another prepared model or known speaker count. Silence and overlapping speech can produce errors. |
| Mac app cannot use Bluetooth | Check OS permission. This packaged path remains unverified; try the Python service after quitting the app. |

## Before reporting a bug

Include application version, OS, CPU architecture, Python version, launch method,
firmware if known, exact steps, expected outcome and the redacted error. State
whether it concerns real hardware, imported audio or a synthetic test. Hardware
reports should include whether Start/Stop were confirmed and whether you listened
to the resulting audio.

Do not attach a workspace, database, raw capture, private key, token, full log or
personal transcript. Prefer a minimal synthetic example. Redact Bluetooth
addresses, serial numbers, account names and private filesystem paths. Sensitive
vulnerabilities belong in the private route described in [SECURITY.md](../SECURITY.md).
