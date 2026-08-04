from __future__ import annotations

import json

from aircord.ingestion.snapshots import S3SnapshotStore


class FakeS3Client:
    def __init__(self):
        self.arguments = None

    def put_object(self, **kwargs):
        self.arguments = kwargs


def test_s3_snapshot_store_uploads_json_with_content_type():
    client = FakeS3Client()
    store = S3SnapshotStore(bucket="aircord-test", region="us-east-1", client=client)

    reference = store.put_json("raw/purpleair/test.json", {"fields": ["sensor_index"], "data": [[123]]})

    assert reference.uri == "s3://aircord-test/raw/purpleair/test.json"
    assert client.arguments["Bucket"] == "aircord-test"
    assert client.arguments["Key"] == "raw/purpleair/test.json"
    assert client.arguments["ContentType"] == "application/json"
    assert json.loads(client.arguments["Body"]) == {"fields": ["sensor_index"], "data": [[123]]}
