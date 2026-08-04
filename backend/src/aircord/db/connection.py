from __future__ import annotations

import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import psycopg
from psycopg import Connection


def database_url_configured() -> bool:
    return bool(os.getenv("DATABASE_URL"))


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is required for CockroachDB connections")
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    ca_cert = os.getenv("DATABASE_CA_CERT")
    if ca_cert:
        query["sslrootcert"] = ca_cert
    elif query.get("sslmode") == "verify-full" and "sslrootcert" not in query:
        query["sslrootcert"] = "system"
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def connect_database() -> Connection:
    return psycopg.connect(get_database_url())
