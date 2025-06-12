"""
간단한 대화 저장 시스템 - SQLite
"""
import sqlite3
import json
import uuid
import os
from datetime import datetime
from typing import List, Dict
from pathlib import Path
from contextlib import contextmanager
from loguru import logger

class ConversationService:
    def __init__(self):
        db_path = os.getenv("CONVERSATION_DB_PATH", "/app/data/conversations/conversations.db")
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_tables()
        logger.info(f"✅ 대화 DB 초기화: {self.db_path}")

    def _ensure_tables(self):
        try:
            with self._get_connection() as conn:
                conn.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);
                """)
        except Exception as e:
            logger.error(f"❌ DB 테이블 초기화 실패: {e}")
            raise

    @contextmanager
    def _get_connection(self):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=15.0)
            conn.row_factory = sqlite3.Row
            yield conn
        finally:
            if conn:
                conn.close()

    async def get_or_create_session(self, session_id: str = None) -> str:
        if session_id: return session_id
        return f"session_{uuid.uuid4().hex[:12]}"

    async def save_conversation_turn(self, session_id: str, user_message: str, assistant_response: str):
        now = datetime.now().isoformat()
        try:
            with self._get_connection() as conn:
                conn.execute("BEGIN")
                conn.execute(
                    "INSERT INTO conversations (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                    (session_id, 'user', user_message, now)
                )
                conn.execute(
                    "INSERT INTO conversations (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                    (session_id, 'assistant', assistant_response, now)
                )
                conn.commit()
            logger.info(f"💾 대화 턴 저장 완료: {session_id}")
        except Exception as e:
            logger.error(f"❌ 대화 턴 저장 실패: {e}")
            conn.rollback()

    async def get_conversation_history(self, session_id: str, limit: int = 6) -> List[Dict[str, str]]:
        """GPT 프롬프트에 사용하기 좋은 형태로 최근 대화 기록을 반환"""
        history = []
        try:
            with self._get_connection() as conn:
                rows = conn.execute("""
                    SELECT role, content FROM conversations
                    WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?
                """, (session_id, limit)).fetchall()

                # 시간 역순으로 가져왔으므로 뒤집어서 시간 순으로 정렬
                for row in reversed(rows):
                    history.append({"role": row['role'], "content": row['content']})
            logger.info(f"📚 대화 기록 조회 완료: {session_id}, {len(history)}개 메시지")
        except Exception as e:
            logger.warning(f"대화 기록 조회 실패: {e}")
        return history

_conversation_service_instance = None
async def get_conversation_service() -> ConversationService:
    global _conversation_service_instance
    if _conversation_service_instance is None:
        _conversation_service_instance = ConversationService()
    return _conversation_service_instance