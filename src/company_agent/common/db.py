from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg.rows import dict_row


@contextmanager
def connect(database_url: str) -> Iterator[psycopg.Connection]:
    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        yield connection


def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"

