# Security and privacy

Pendant Local is a single-user application for a trusted computer. It has not
received an independent security audit. Do not expose it through a public port,
reverse proxy, tunnel or shared hosting account.

## Trust boundaries

```text
Pendant -- Bluetooth --> local Python service --> private workspace directory
Browser or Mac window -- loopback HTTP + bearer token --> local Python service
Local model files --> local CPU transcription and speaker analysis
Explicit model preparation --> Hugging Face / sherpa-onnx model downloads
```

The CLI binds the service to `127.0.0.1`. All `/v1` routes require the local bearer
token. Health, UI assets, API schema/documentation and the native service identity
challenge are public on loopback. The identity response is bound to a challenge
so the Mac launcher can check a listener before handing it credentials.

The browser keeps its token in session storage and sends it in the Authorization
header, including audio requests. Tokens are never required in URLs. User content
is rendered as text. UI and Swagger assets are bundled locally; the online Swagger
validator is disabled. There are no application analytics or cloud transcription
calls in the supported application path.

Installing packages and requesting model downloads contact external registries
or model hosts. Those services see ordinary connection metadata, such as your
IP address. No recordings are sent by the application's download adapters.
Inference uses complete local model paths. Optional native libraries remain part
of the dependency trust boundary; Python socket-blocking tests are not proof
that native code cannot access the network. A firewall can enforce offline use.

## Data protection

The workspace contains plaintext audio, transcripts, metadata, a bearer token
and possibly private encryption keys. The app does not encrypt this directory.
Use OS account controls and full-disk encryption appropriate to your computer.
Protect backup and export destinations too. POSIX workspace directories use
owner-only permissions; Windows protection relies on the user's directory ACLs.

The token is not a second user account or a defence against malware running as
you. Anyone with your OS account's file access can obtain it or read the library.
Lock workspace clears one UI session; it neither revokes the token nor stops the
service. Untrusted browser extensions are outside this application's protection.

To replace a compromised token, stop every service for that workspace, preserve
a private backup, remove only the `api_token` field from `config.json` with a
local editor, and restart. A new random token is generated. If using
`PENDANT_API_TOKEN`, replace that override instead. Reconnect trusted clients.
Do not delete the complete configuration or the `keys/` directory to rotate a
login token; device encryption keys are a separate mechanism.

## Device and file handling

Dashboard capture always sends `acknowledge: false`. Explicit API acknowledgement
can delete device pages only after raw bytes and integrity journal records have
been durably written in sequence. Disk persistence does not prove decryption,
intelligibility or a complete backup. Preserve original keys and raw captures.

A new key cannot recover old vendor-encrypted audio. No reset, firmware flashing
or automatic deletion endpoint is provided by the supported API. The vendored
upstream CLI has other behaviours; it is not installed as an application command
and is not the supported workflow. See [third-party notices](THIRD-PARTY-NOTICES.md).

Imports are bounded to 250 MB and supported filename extensions. Audio parsers
and native inference libraries still process untrusted bytes. Only import files
you trust. Speaker analysis can decode the whole file into memory; there is no
multi-user quota or isolation service. Local authentication does not make this
suitable for hostile shared workloads.

## Reporting a vulnerability

On the published repository, use **Security > Advisories > Report a vulnerability**
if private vulnerability reporting is enabled. Do not put exploit details,
credentials, raw recordings or personal transcripts in a public issue.

If the private reporting button is unavailable, open a minimal issue asking for
a private security contact, without disclosing the vulnerability or personal
data. Maintainers should enable private reporting before publishing; see the
[release guide](docs/RELEASING.md). There is no guaranteed response time.

Security fixes are maintained for the latest source release. Older versions may
not receive backports. Report the version and a synthetic reproduction where
possible. The automated tests exercise authentication, traversal protection,
safe rendering, capture persistence and error redaction; they are not a security
certification.
