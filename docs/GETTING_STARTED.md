# Getting started

## Install and sign in

Follow the [README quick start](../README.md#quick-start). Use a terminal on the
computer with Bluetooth, not a cloud shell. The browser controls the local
service; it does not talk to Bluetooth directly. A phone browser cannot pair the
Pendant through this application.

Python 3.11+ is supported by the package. Python 3.13.2 on Apple Silicon macOS is
the current checked environment; a Python 3.12 Linux baseline also exists. Wheel
availability for optional engines may differ by OS and Python version.
On Debian/Ubuntu, a missing `venv` or `ensurepip` usually means the distribution's
`python3-venv` package is needed. Linux Bluetooth also requires BlueZ and access
to the system D-Bus service. Containers and virtual machines need explicit
adapter access; begin on the host OS.

Bootstrap creates `.venv`, updates pip to at least 26.2 and installs from this checkout. It needs access to the
Python package registry. It does not download Whisper or speaker model weights.
Use `--without-transcription` if optional engine installation fails. No Node.js,
frontend build, paid account or cloud API key is needed to run the dashboard.

Leave the `serve` terminal open. Ctrl+C stops the service. Retrieve the token
with the same `--data-dir` used by the server if you selected a custom directory.
The browser stores it in session storage. Avoid using an untrusted browser
profile or extensions with access to localhost pages.

## Connect the Pendant

Charge the Pendant and keep it near the computer. Close or disconnect the
vendor app and other Bluetooth clients. In **Device**, choose **Scan**, select
the returned device and choose **Check device**. On macOS the address is usually
a UUID, not a MAC address. Do not replace it with the address shown on another OS.

Allow Bluetooth access to the process your OS identifies. With Python on macOS
this may be your terminal application. Device information does not start a
recording or change encryption keys. It reports state at the time of the request,
not continuous live monitoring.

An existing bond to another host can prevent access. This application cannot
bypass a bond or recover a lost encryption key. Do not factory-reset a device
containing recordings you want to preserve. See [troubleshooting](TROUBLESHOOTING.md).

For CLI discovery, stop the service first:

```bash
.venv/bin/pendant-local scan
.venv/bin/pendant-local configure ADDRESS_FROM_SCAN
.venv/bin/pendant-local info
.venv/bin/pendant-local serve
```

Substitute the exact returned address. On Windows replace `.venv/bin/pendant-local`
with `.venv\Scripts\pendant-local.exe`. While the service is running, use the
UI or API; a process lock prevents a competing CLI scan or info request.

## Preserve existing audio first

Before recording or setting up a key, try **Sync from Pendant** with deletion
off. The dashboard downloads raw pages, saves an integrity journal, attempts
decoding and adds playable audio to the library. Downloading does not itself
start the microphone. Keep the computer awake and the page open.

The dashboard's default limit is 30 minutes, with choices up to 1 hour. This is
transfer time, not audio duration. The choice is remembered in each browser.
A short transfer can stop before reaching recent audio. The protocol used here
has no resume offset, so repeated syncs can begin with the same old pages.
Some device behaviour may require acknowledgements to advance. A timeout or
zero new recordings never proves that every recording was downloaded.

Repeated exact recordings reuse a library entry. A verified longer partial copy
can extend an entry while preserving its metadata and original files. Ambiguous
matches stay separate. These rules avoid duplicate entries, not repeat Bluetooth
traffic. Raw captures are retained even if decoding fails.

Listen to the recovered audio. Back up the [whole workspace](BACKUP_AND_RESTORE.md),
including `keys/` and raw `captures/`, before experimenting further. Do not enable
API acknowledgement merely to make a stalled sync progress: it deletes device
pages and durable raw bytes may still be undecodable.

## Make a short recording check

1. Press **Start** and wait for the clock acknowledgement and state readback.
   “Listening for speech” means armed; it is not evidence that speech was saved.
2. Say “Pendant test, beginning”, speak for 20 seconds, then say “end of test”.
3. Press **Stop** and check that stopped state is confirmed. If it is not,
   treat that as a failed control operation.
4. Sync with deletion off, find the spoken label and listen from start to end.
   Check both boundary phrases and intelligibility. One recording may become
   several library segments.
5. Rename the recording, refresh the page and replay it. Try transcription after
   an explicit model download.

After power loss, use **Set clock** before testing the physical record button.
Start in the dashboard sets the clock automatically. A failed clock acknowledgement
prevents Start from being sent. Successful mocked tests and non-silent decoded
bytes do not establish intelligible microphone audio; listening does.

## Encryption keys

Old vendor-encrypted recordings require the original private key. A newly
created key cannot decrypt them. Preserve raw captures even if they currently
produce only missing-key warnings.

**Set up local key** saves a private key locally before sending its public key
to the Pendant for future recordings. It requires explicit confirmation and
reuses the saved key on later requests. Back up `keys/` immediately afterwards.
A reboot may require the same key to be applied again. Actual encrypted-audio
recovery and firmware-specific encrypted packet layouts remain unverified.

The application exposes no reset or firmware-flashing endpoint. It does not
claim to recover every previously owned, reset or vendor-encrypted Pendant.
