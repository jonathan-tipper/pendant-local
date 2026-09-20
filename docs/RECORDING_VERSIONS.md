# Partial recording versions

The library distinguishes one device recording from the files recovered by
different syncs. A timed-out sync can end partway through a recording; a later
sync can recover a longer prefix. Duration and generated title are not identity.

## Evidence and matching

- `decode_capture(..., fingerprints_only=True)` reads journal-verified raw bytes
  without rewriting audio or manifests. Existing file names, packet counts,
  durations and full fingerprints must agree with the stored decode report.
- The first-packet fingerprint includes device scope, run, page, device timing
  and audio. Both copies must have an explicit recording start. Matching first
  packets alone is insufficient.
- The cumulative fingerprint at the shorter copy's packet count must equal its
  entire fingerprint. Every overlapping packet and its provenance therefore
  agree. The shorter copy must have no recording stop marker to permit extension.
- Prefix checks use only requested packet counts during replay, avoiding an
  on-disk hash for every packet. Proofs are checked against the family's current
  longest audio, not an obsolete shorter member. Conflicting longer versions
  sharing a short prefix remain separate.
- Missing raw data, changed decoding boundaries or any decode warnings leave
  uncertain copies separate. The implementation does not join arbitrary overlaps
  or infer identity from similar speech or silence.

## Storage and migration

`pendant_recording_versions` has one row per capture source key, storing bounded
identity and boundary metadata. Its start-fingerprint index narrows candidates.
The existing source-alias and fingerprint tables point future syncs to the main
recording ID. Recorded facts avoid repeated legacy replay on each startup.

The main recording points to the longest verified existing audio file. Shorter
retries cannot reduce its duration. No audio is concatenated, overwritten or
deleted. A later stop marker with identical audio can update its boundary status.

Existing duplicate rows move to Archived. `recording_version_merges` keeps both
rows' pre-merge metadata and the main ID. A custom title replaces a generated
title; conflicting custom titles remain available on the archived row. Distinct
notes are retained together, tags are combined and stars are preserved. Existing
transcripts are retained; a duplicate transcript fills an empty main transcript
but never overwrites an existing one. Archived copies retain their own metadata.

Alias changes, row updates, version facts and merge history share one SQLite
transaction. A failed write rolls back the merge. Schema creation and indexing
are repeatable. Previous alias mappings are respected, including a duplicate
the user deliberately restored before upgrading. A pending transcription on
an existing duplicate defers its merge until that capture is indexed again.

## Transcripts and API

The recording response adds `audio_incomplete`, `audio_version_count`,
`merged_into` and `transcript_needs_update`. Unknown boundary evidence yields
`audio_incomplete: null`. Absence of a stop marker is shown as a partial download;
the presence of a marker does not prove the entire device was drained.

`library_summary.extended` counts existing entries that gained audio. Those IDs
are not newly added and are not automatically queued again. Users explicitly
choose Transcribe again to cover additional audio. Existing transcripts and
speaker names remain available until a replacement finishes. Transcription
duration cannot shrink a known Pendant audio duration, including when a job
finishes on an older audio file after a sync has extended the entry.

## Verification and recovery

Tests use isolated data and exercise both arrival orders, unchanged retries,
different device events, conflicting audio, completed shorter recordings,
missing/corrupt evidence, write rollback, annotations, restores and pending jobs.
[VALIDATION.md](VALIDATION.md) separates software checks from hardware evidence.

Back up the idle workspace and rehearse the migration on a restored copy before
deployment. Preserve raw captures, keys, audio and the database together. To undo
a migration, use the matching source with a separately restored pre-migration
workspace; retain the current workspace so later recordings are not lost. The
in-app archive also provides reversible access to the original shorter rows.
