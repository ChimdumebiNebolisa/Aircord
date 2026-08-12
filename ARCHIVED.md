# Aircord archive record

Teardown date: 2026-08-12

## Resources deleted

None confirmed by this teardown run.

## Resources requiring manual deletion

- AWS EventBridge rule `aircord-purpleair-ingest-15m`: not changed because the configured AWS session expired.
- AWS Lambda function `aircord-purpleair-ingest`: not deleted because the configured AWS session expired.
- S3 bucket `aircord-raw-snapshots-chimdumebi-2026`: not emptied or deleted because the configured AWS session expired.
- Vercel project `aircord-demo`: not deleted because the local CLI has no Vercel credentials and the connected Vercel app exposes no delete operation.
- CockroachDB Cloud cluster `aircord` (ID `2766ef53-ca8e-4e43-a5c2-5fbb4c49f979`): not deleted because the available tooling does not support safe cluster deletion.
- GitHub repository archive action: completed after the repository wipe was pushed.
- Aircord-specific `cockroachdb-cloud` MCP block in `C:\Users\Chimdumebi\.codex\config.toml`: removed during this teardown run.

## Ingestion status

No active cloud ingestion remains cannot be confirmed. The AWS schedule and Lambda were not reachable for deletion during this run.

## Scope

All Aircord source code, documentation, frontend, backend, specifications, scripts, generated files, and project configuration are removed from the repository. `README.md`, `ARCHIVED.md`, and the pre-existing `LICENSE` are retained. The repository wipe, archive commit, and GitHub repository archive are complete.
