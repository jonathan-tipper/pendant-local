# Backup, restore and upgrades

Your Git checkout contains application source. Your recording workspace is
separate and contains private data. Back up the **whole workspace**, including
raw captures and keys, before upgrades or experiments with recording/storage.

## Find the workspace

Run `pendant-local doctor` through your virtual environment. Defaults are:

| OS | Default location |
| --- | --- |
| macOS | `~/Library/Application Support/pendant-local-api/` |
| Linux | `~/.local/share/pendant-local-api/`, subject to XDG settings |
| Windows | `%LOCALAPPDATA%\pendant-local-api\` |

`--data-dir` overrides `PENDANT_DATA_DIR`, which overrides the OS default.
`PENDANT_ADDRESS` and `PENDANT_API_TOKEN` override their saved settings. Put
`--data-dir` before the subcommand, and use the same directory for token, doctor,
configure and serve. The native Mac app uses its default workspace unless built
with an explicit development override.

| Path | Contents |
| --- | --- |
| `config.json` | Local API token and configured Bluetooth address |
| `keys/` | Private keys and associated device information |
| `captures/` | Raw bytes, integrity journals, capture metadata and decoded audio |
| `imports/` | Imported audio |
| `recordings.sqlite3` | Metadata, notes, transcripts and recording-version records |
| `jobs/` | Persistent job state |
| `models/` | Downloaded models and their notices |
| `workflow.json` | Model, language, automatic-job and speaker preferences |
| `service.lock` | Transient process lock, not recording content |

## Make a backup

1. Finish or cancel pending work. Quit the Mac app or stop the Python service.
   Do not copy a live SQLite database and assume the result is consistent.
2. Copy the complete directory to a new private, timestamped backup location.
   Retain permissions. Do not place it in the source repository or a shared folder.
3. Compare file counts and SHA-256 hashes between source and backup. Keep the
   manifest with the private backup, not in Git. Preserve model files too if
   you need an offline restore; otherwise they can be downloaded again.
4. Copy the backup to a **separate** restore directory, verify its hashes and run
   SQLite's `PRAGMA integrity_check` on that copy.
5. Start a service against the restored copy on an unused port. Sign in using
   its token, compare the expected library contents and play several recordings.
   Queued jobs may resume when you start the service, so establish the idle
   backup first. Do not start a Bluetooth sync during a restore check.

Example for a restored directory on macOS/Linux:

```bash
.venv/bin/pendant-local --data-dir /absolute/path/to/restored-workspace serve --port 8767
```

Get that copy's token in another terminal using the same option. Keep the
original, backup and checked copy until you are satisfied. A second copy on the
same disk protects against some mistakes, but not failure or loss of that disk.

## Upgrade or roll back

Stop the idle service, make and check a backup, then update the source checkout
or extract the new source release. Rerun bootstrap and start with the same data
directory. For the Mac app, rebuild and replace the idle app bundle; replacing
it does not replace the workspace.

A storage upgrade can change database records. A code rollback alone does not
undo a migration. Restore the matching pre-upgrade workspace into a separate
directory and use the matching source version. Do not overwrite the current
workspace or mix an older database with newer capture files.

Archive is reversible and retains files. There is no built-in automatic backup,
retention or permanent-deletion service. Removing the application or checkout
does not remove the recording workspace.
