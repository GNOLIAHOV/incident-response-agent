import os
import pickle
import sqlite3
from typing import Any, Sequence
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    ChannelVersions,
    Checkpoint,
    CheckpointMetadata,
)
from langgraph.checkpoint.memory import InMemorySaver


class PersistentSqliteSaver(InMemorySaver):
    """Checkpointer lưu trữ bền vững trạng thái LangGraph vào cơ sở dữ liệu SQLite cục bộ.

    Kế thừa InMemorySaver để giữ trọn vẹn thuật toán serialization/deserialization
    chuẩn của LangGraph, đồng thời đồng bộ hóa snapshot xuống file SQLite sau mỗi bước chạy.
    """

    def __init__(self, db_path: str = "data/incidents.db", **kwargs):
        super().__init__(**kwargs)
        self.db_path = db_path

        # Tạo thư mục chứa database nếu chưa tồn tại
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        self._init_db()
        self._load_all_from_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS thread_checkpoints (
                    thread_id TEXT PRIMARY KEY,
                    storage_blob BLOB,
                    writes_blob BLOB,
                    blobs_blob BLOB,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            conn.commit()

    def _load_all_from_db(self) -> None:
        """Tải toàn bộ snapshot đã lưu trong SQLite vào bộ nhớ khi khởi động."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT thread_id, storage_blob, writes_blob, blobs_blob FROM thread_checkpoints"
            )
            for row in cursor.fetchall():
                thread_id, storage_blob, writes_blob, blobs_blob = row
                try:
                    if storage_blob:
                        self.storage[thread_id] = pickle.loads(storage_blob)
                    if writes_blob:
                        thread_writes = pickle.loads(writes_blob)
                        self.writes.update(thread_writes)
                    if blobs_blob:
                        thread_blobs = pickle.loads(blobs_blob)
                        self.blobs.update(thread_blobs)
                except Exception:
                    continue

    def _sync_thread_to_db(self, thread_id: str) -> None:
        """Đồng bộ trạng thái của một thread xuống file SQLite."""
        thread_storage = self.storage.get(thread_id, {})
        # Lọc các write và blob liên quan đến thread_id này
        thread_writes = {k: v for k, v in self.writes.items() if k[0] == thread_id}
        thread_blobs = {k: v for k, v in self.blobs.items() if k[0] == thread_id}

        storage_blob = pickle.dumps(thread_storage)
        writes_blob = pickle.dumps(thread_writes)
        blobs_blob = pickle.dumps(thread_blobs)

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO thread_checkpoints (thread_id, storage_blob, writes_blob, blobs_blob, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(thread_id) DO UPDATE SET
                    storage_blob = excluded.storage_blob,
                    writes_blob = excluded.writes_blob,
                    blobs_blob = excluded.blobs_blob,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (thread_id, storage_blob, writes_blob, blobs_blob),
            )
            conn.commit()

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        res = super().put(config, checkpoint, metadata, new_versions)
        thread_id = config["configurable"]["thread_id"]
        self._sync_thread_to_db(thread_id)
        return res

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        super().put_writes(config, writes, task_id, task_path)
        thread_id = config["configurable"]["thread_id"]
        self._sync_thread_to_db(thread_id)

    def delete_thread(self, thread_id: str) -> None:
        super().delete_thread(thread_id)
        with self._get_connection() as conn:
            conn.execute("DELETE FROM thread_checkpoints WHERE thread_id = ?", (thread_id,))
            conn.commit()
