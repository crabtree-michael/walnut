#!/usr/bin/env python
from __future__ import annotations

import os
import time

import psycopg
from psycopg import OperationalError


def wait_for_db() -> None:
    timeout = int(os.getenv("DB_READY_TIMEOUT", "60"))
    delay = float(os.getenv("DB_READY_POLL_INTERVAL", "1"))

    dsn = {
        "dbname": os.getenv("POSTGRES_DB", "fjord"),
        "user": os.getenv("POSTGRES_USER", "fjord"),
        "password": os.getenv("POSTGRES_PASSWORD", ""),
        "host": os.getenv("POSTGRES_HOST", "db"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
    }

    deadline = time.monotonic() + timeout

    while True:
        try:
            with psycopg.connect(**dsn):
                return
        except OperationalError as exc:
            if time.monotonic() >= deadline:
                raise RuntimeError("Database did not become ready in time") from exc
            time.sleep(delay)


if __name__ == "__main__":
    wait_for_db()
