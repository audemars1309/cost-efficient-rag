# Nimbus Cloud Storage — Troubleshooting

## Sync stuck at "Preparing to sync"

This usually means the local Nimbus client cache is corrupted. Quit the desktop app fully, delete the local `.nimbus-cache` folder in your home directory, and relaunch the app. This forces a fresh index build and does not delete any files from Nimbus servers.

## "Storage quota exceeded" on Business plan

Since Business plans are unlimited, this error almost always means a per-folder sharing limit was hit rather than a true storage cap — Business folders shared externally are capped at 50,000 files per folder. Split the folder or remove old shared links to resolve it.

## Two-factor codes not accepted

TOTP codes are time-based and require the device clock to be accurate within 30 seconds. If codes are consistently rejected, check that automatic time sync is enabled on the authenticator device before contacting support.

## Slow uploads on large files

Uploads over 1 GB use resumable chunked transfer automatically. If a large upload appears slow, it is more often a network issue than a Nimbus issue — the desktop app throttles chunk size based on measured upload bandwidth rather than a fixed limit for files under the API's 5 GB single-request threshold.
