from __future__ import annotations

from aircord.db.connection import get_database_url


def test_database_url_uses_system_trust_store_for_verify_full(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:password@example.com:26257/aircord?sslmode=verify-full",
    )

    url = get_database_url()

    assert "sslmode=verify-full" in url
    assert "sslrootcert=system" in url


def test_database_url_preserves_explicit_root_certificate(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:password@example.com:26257/aircord?sslmode=verify-full&sslrootcert=C%3A%2Fcerts%2Froot.crt",
    )

    url = get_database_url()

    assert "sslrootcert=C%3A%2Fcerts%2Froot.crt" in url


def test_database_ca_cert_overrides_url_root_certificate(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:password@example.com:26257/aircord?sslmode=verify-full",
    )
    monkeypatch.setenv("DATABASE_CA_CERT", "C:\\certs\\aircord-ca.crt")

    url = get_database_url()

    assert "sslrootcert=C%3A%5Ccerts%5Caircord-ca.crt" in url
