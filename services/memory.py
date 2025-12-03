# app/services/memory.py
"""
Async Memory service using SQLAlchemy + asyncpg.

Usage:
    from app.services.memory import MemoryService
    memory = MemoryService(os.getenv("DATABASE_URL"))
    await memory.init_db()
"""

import os
import json
from rapidfuzz import fuzz
from typing import Any, Dict, List, Optional
from datetime import datetime
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy import (
    Table, Column, MetaData, BigInteger, Text, JSON, DateTime, select, insert, update, delete, Integer
)
from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector


# DATABASE_URL_DEFAULT = "postgresql+asyncpg://postgres:password@localhost:5432/sales_agent"

metadata = MetaData()

memories_table = Table(
    "memories",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("user_id", Text, nullable=False),
    Column("key", Text, nullable=False),
    Column("value", JSON, nullable=False),
    Column("summary", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

document_chunks_table = Table(
    "document_chunks",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("business_id", Integer, nullable=False),
    Column("filename", Text, nullable=True),
    Column("chunk_index", Integer, nullable=True),
    Column("text", Text, nullable=True),
    Column("embedding", Vector(384), nullable=False),  # pgvector column
)


def clean_row(row: Row) -> Dict[str, Any]:
    return {
        "id": row.id,
        "user_id": row.user_id,
        "key": row.key,
        "value": row.value,
        "summary": row.summary,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


class MemoryService:
    def __init__(self, db_url: Optional[str] = None, echo: bool = False):
        self.db_url = db_url
        self.engine: AsyncEngine = create_async_engine(self.db_url, echo=echo, future=True)
        self.async_session = sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)

    async def init_db(self):
        async with self.engine.begin() as conn:
            # In production use migrations (alembic). This is convenient for dev.
            await conn.run_sync(metadata.create_all)

    async def init_vector_db(self):
        async with self.engine.begin() as conn:
            # Ensure pgvector extension exists

            await conn.run_sync(
                lambda sync_conn: sync_conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            )

            # In production use migrations (alembic). This is convenient for dev.
            await conn.run_sync(metadata.create_all)
            

    async def write(self, user_id: str, key: str, value: Dict[str, Any], summary: Optional[str] = None) -> Dict[str, Any]:
        """Create or update a memory item for a user and key (upsert-like behaviour)."""
        now = datetime.utcnow()
        async with self.async_session() as session:
            # check existing
            stmt = select(memories_table).where(memories_table.c.user_id == user_id, memories_table.c.key == key)
            res = await session.execute(stmt)
            row = res.first()

            if row is None:
                ins = insert(memories_table).values(
                    user_id=user_id,
                    key=key,
                    value=value,
                    summary=summary,
                    created_at=now,
                    updated_at=now
                ).returning(*memories_table.c)
                r = await session.execute(ins)
                await session.commit()
                returned = r.fetchone()
                return clean_row(returned)
            else:
                upd = update(memories_table).where(memories_table.c.id == row.id).values(
                    value=value,
                    summary=summary,
                    updated_at=now
                ).returning(*memories_table.c)
                r = await session.execute(upd)
                await session.commit()
                returned = r.fetchone()
                return clean_row(returned)

    async def read(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Return the most recent memory entries for a user."""
        async with self.async_session() as session:
            stmt = (
                select(memories_table)
                .where(memories_table.c.user_id == user_id)
                .order_by(memories_table.c.updated_at.desc().nullslast())
                .limit(limit)
            )
            res = await session.execute(stmt)
            rows = res.fetchall()
            return [
                {
                    "id": row.id,
                    "user_id": str(row.user_id),
                    "key": row.key,
                    "value": row.value,
                    "summary": row.summary,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                }
                for row in rows
            ]


    async def search(self, user_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Simple search: load recent memories and heuristically filter by presence of query in key/summary/value.
        Replace/upgrade this with pgvector + embeddings for semantic search in production.
        """
        async with self.async_session() as session:
            stmt = select(memories_table).where(memories_table.c.user_id == user_id).order_by(memories_table.c.updated_at.desc()).limit(50)
            res = await session.execute(stmt)
            rows = res.fetchall()
            q = query.lower()
            matched: List[Dict[str, Any]] = []
            for r in rows:
                print(f"Checking memory row: key={r.key}, summary={r.summary}")
                summary = (r.summary or "").lower()
                key = (r.key or "").lower()
                value_text = json.dumps(r.value or {}).lower()
                print("→", r.key)
                print("summary score:", fuzz.token_set_ratio(q, summary))
                print("key score:", fuzz.token_set_ratio(q, key))
                print("value score:", fuzz.token_set_ratio(q, value_text))

                # if q in summary or q in key or q in value_text:
                if (
                        fuzz.token_set_ratio(q, summary) > 70 or
                        fuzz.token_set_ratio(q, key) > 70 or
                        fuzz.token_set_ratio(q, value_text) > 70
                    ):
                    matched.append({
                        "id": r.id,
                        "user_id": str(r.user_id),
                        "key": r.key,
                        "value": r.value,
                        "summary": r.summary,
                        "created_at": r.created_at.isoformat() if r.created_at else None,
                        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                    })
                    if len(matched) >= limit:
                        break
            print(f"Matched searched memories: {len(matched)}")
            return matched

    async def delete(self, user_id: str, key: str) -> bool:
        async with self.async_session() as session:
            stmt = delete(memories_table).where(memories_table.c.user_id == user_id, memories_table.c.key == key)
            res = await session.execute(stmt)
            await session.commit()
            return res.rowcount > 0

    