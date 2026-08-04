from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aircord.db.repositories import Repository  # noqa: E402
from aircord.reputation.vector import build_behavioral_fingerprint  # noqa: E402


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _demo_vector(vector: list[float], features: dict[str, float | str], delta: float, label: str):
    demo_vector = [max(0.0, min(1.0, value + delta)) for value in vector]
    demo_features = {
        key: value for key, value in features.items() if key != "source"
    }
    demo_features.update({"source": "demo_fixture", "label": label})
    return demo_vector, demo_features


def _seed_demo_fixtures(repository: Repository, vector, features) -> None:
    for sensor_id, delta, label in (
        ("demo-fixture-similar", 0.01, "similar behavioral fixture"),
        ("demo-fixture-different", 0.45, "different behavioral fixture"),
    ):
        demo_vector, demo_features = _demo_vector(vector, features, delta, label)
        repository.upsert_sensor_embedding(sensor_id, demo_vector, demo_features, _now())


def main() -> None:
    parser = argparse.ArgumentParser(description="Query CockroachDB sensor behavioral similarity")
    parser.add_argument("--sensor-id", required=True)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument(
        "--seed-demo-fixtures",
        action="store_true",
        help="Add clearly labeled demo-only vectors when the live set is small",
    )
    args = parser.parse_args()

    repository = Repository(backend="cockroach")
    sensor = repository.read_sensor(args.sensor_id)
    if not sensor:
        raise SystemExit(f"Sensor is not present in CockroachDB: {args.sensor_id}")
    reading = repository.one(
        "SELECT * FROM sensor_readings WHERE sensor_id = ? ORDER BY observed_at DESC LIMIT 1",
        (args.sensor_id,),
    )
    monitor = repository.one(
        "SELECT * FROM monitors ORDER BY observed_at DESC NULLS LAST, updated_at DESC LIMIT 1"
    )
    estimate = repository.latest_estimate(f"greater-la-sensor-{args.sensor_id}")
    vector, features = build_behavioral_fingerprint(
        sensor,
        reading,
        monitor,
        confidence=estimate.get("confidence") if estimate else None,
    )
    features["source"] = "live_similarity"
    repository.upsert_sensor_embedding(args.sensor_id, vector, features, _now())
    if args.seed_demo_fixtures:
        _seed_demo_fixtures(repository, vector, features)
    nearest = repository.similar_sensor_embeddings(
        vector,
        exclude_sensor_id=args.sensor_id,
        limit=args.limit,
    )

    print("Aircord sensor similarity")
    print(f"selected sensor: {args.sensor_id} ({sensor.get('name') or 'unnamed'})")
    print("fingerprint dimensions: 8 (handcrafted; not a trained embedding)")
    print("fingerprint values:")
    for name, value in features.items():
        print(f"- {name}={value}")
    print("nearest similar sensors:")
    if not nearest:
        print("- none (no other fingerprints available; use --seed-demo-fixtures for a demo)")
    else:
        for row in nearest:
            metadata = row.get("feature_json") or {}
            print(
                f"- {row['sensor_id']}: cosine_distance={float(row['cosine_distance']):.6f} "
                f"source={metadata.get('source', 'unknown')} label={metadata.get('label', '')}"
            )
    print(
        "drift/similarity explanation: the vector compares reputation, channel divergence, "
        "recent PM2.5, missingness, freshness, monitor disagreement, drift, and confidence. "
        "A lower cosine distance means the handcrafted feature directions are more similar; "
        "it is not an accuracy score."
    )


if __name__ == "__main__":
    main()
