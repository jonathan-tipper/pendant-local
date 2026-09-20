# Using the workspace

## Library and imports

Import WAV, MP3, M4A, Ogg/Opus, FLAC, AAC or WebM, up to 250 MB per file.
Playback depends on your browser's codec support. A file accepted for import is
not guaranteed to be playable or decodable by every engine.

Select a recording to play it, change its title, add tags or notes, star it, or
archive it. Archive hides it from the active list and retains audio and transcript;
restore it from Archived. Archiving does not delete device pages or free disk
space. There is no automatic retention or permanent-delete workflow.

Search matches titles, notes, tags and transcript text. Transcript timestamps
seek the player to the corresponding segment. Export TXT, Markdown, SRT subtitles,
or JSON metadata and transcript. Exported files can contain personal information;
choose their destination accordingly.

## Transcription

Install the engines through bootstrap, then open **Settings** and explicitly
choose **Download model**. Downloads fetch public weights from Hugging Face and
do not upload recordings. Complete local files are required for inference.
No Ollama, LM Studio or GPU setup is required. Processing uses CPU `int8` through
faster-whisper.

| Models | Language | Approximate model download |
| --- | --- | --- |
| `tiny.en` | English | 80 MB |
| `base.en`, `base` | English / multilingual | 150 MB each |
| `small.en`, `small` | English / multilingual | 490 MB each |
| `medium.en`, `medium` | English / multilingual | 1.53 GB each |
| `large-v3-turbo` | Multilingual | 1.62 GB |
| `large-v3` | Multilingual | 3.10 GB |

Sizes are estimates, not RAM requirements. Begin with `base.en` for a smaller
English setup, or try `large-v3-turbo` if you can afford the download and memory.
Larger models require more resources; there is no universal speed or accuracy
promise. `.en` models require English. Multilingual models accept a language code
or automatic detection.

Once downloaded, use **Use as default** or select a model on an individual
recording. Choose the language and **Transcribe recording**. Review important
wording against playback. Transcription text editing and summaries are not
implemented. **Transcribe again** keeps the existing transcript until a replacement
succeeds. If sync extends an incomplete recording, its older transcript stays
available and is marked as needing an update.

## Workflow and automatic jobs

A persistent single-worker queue prevents competing inference jobs. Workflow
shows model loading, audio reading, transcription and saving stages, elapsed
time, and processed timestamps where available. Download status shows bytes on
disk, not an estimated percentage.

Automatic transcription is off by default. Enabling it queues newly imported or
decoded recordings with saved defaults. It does not record audio or schedule
Bluetooth sync. Batch queueing accepts up to 100 untranscribed recordings,
skipping archived, active or already transcribed entries. The dashboard considers
the first 500 entries for batching; search for older items and queue them individually.

Queued transcriptions resume after restart. Interrupted running jobs and model
downloads require explicit retry. Cancellation may wait for the current native
operation to return, and retry stays disabled until it stops. Avoid force-quitting
during capture or storage writes.

## Speaker labels

Install the optional `diarization` engine, explicitly download speaker models in
Settings and enable **Identify speakers** for transcription. Models are fetched
from the sherpa-onnx project, separately from Whisper. See the
[dependency and model notes](DIARIZATION_DEPENDENCIES.md).

Labels such as `speaker_1` distinguish voices within one recording. You can rename
these labels, and exports retain them. They do not recognise a person across
recordings or infer identity. Automatic speaker counts are estimates; provide a
known count when appropriate and listen to check boundaries and attribution.
Overlapping voices, short speech, noise and long meetings remain difficult.

Speaker analysis decodes the whole recording into memory. Long recordings may
need substantial RAM, and a native call cannot be interrupted immediately.
Disabling the feature retains existing transcripts and audio.
