"""
ChromaDB 기반 Vector Store - 최종 완성 버전
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
from loguru import logger
import os
import uuid
import time
from datetime import datetime

from ..models.vector_models import SearchResult, DocumentInput, VectorStoreStats


class ChromaVectorStore:
    """ChromaDB 기반 Vector Store"""

    def __init__(self, collection_name: str = "teen_empathy_chat"):
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.embedding_model = None
        self.model_name = "jhgan/ko-sbert-multitask"
        # [추가] 권한 문제가 없는 캐시 폴더 경로 지정
        self.cache_dir = "/app/cache"

    async def initialize(self):
        """ChromaDB 및 임베딩 모델 초기화"""
        try:
            logger.info("ChromaDB Vector Store 초기화 시작...")

            db_path = os.getenv("CHROMADB_PATH", "/app/data/chromadb")
            os.makedirs(db_path, exist_ok=True)

            self.client = chromadb.PersistentClient(
                path=db_path,
                settings=Settings(allow_reset=True, anonymized_telemetry=False)
            )

            # [수정] 한국어 임베딩 모델 로드 시, 캐시 폴더를 명시적으로 지정합니다.
            logger.info(f"한국어 임베딩 모델 로드 중: {self.model_name}")
            self.embedding_model = SentenceTransformer(self.model_name, cache_folder=self.cache_dir)
            logger.info(f"임베딩 모델 로드 완료 - 차원: {self.embedding_model.get_sentence_embedding_dimension()}")

            # 컬렉션 생성/연결
            self.collection = self.client.get_or_create_collection(name=self.collection_name)
            logger.info(f"컬렉션 '{self.collection_name}' 준비 완료.")

            logger.info("✅ ChromaDB Vector Store 초기화 완료")

        except Exception as e:
            logger.error(f"❌ ChromaDB 초기화 실패: {e}")
            raise

    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """한국어 임베딩 생성"""
        if not self.embedding_model: raise ValueError("임베딩 모델이 초기화되지 않았습니다")
        return self.embedding_model.encode(texts).tolist()

    async def add_documents(self, documents: List[DocumentInput]) -> List[str]:
        # ... (이하 다른 함수들은 변경 필요 없음, 그대로 유지) ...
        if not self.collection: raise ValueError("컬렉션이 초기화되지 않았습니다")
        texts = [doc.content for doc in documents]
        metadatas = [doc.metadata or {} for doc in documents]
        document_ids = [doc.document_id or str(uuid.uuid4()) for doc in documents]
        embeddings = self.create_embeddings(texts)
        self.collection.add(embeddings=embeddings, documents=texts, metadatas=metadatas, ids=document_ids)
        return document_ids

    async def search(self, query: str, top_k: int = 5,
                    filter_metadata: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        if not self.collection: raise ValueError("컬렉션이 초기화되지 않았습니다")
        query_embedding = self.create_embeddings([query])[0]
        search_kwargs = {"query_embeddings": [query_embedding], "n_results": top_k, "include": ["documents", "metadatas", "distances"]}
        if filter_metadata: search_kwargs["where"] = filter_metadata
        results = self.collection.query(**search_kwargs)
        search_results = []
        if results["documents"] and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                distance = results["distances"][0][i]
                similarity_score = 1 - (distance / 2) # 코사인 거리는 보통 0~2 범위, 유사도로 변환
                search_results.append(SearchResult(
                    content=results["documents"][0][i],
                    metadata=results["metadatas"][0][i] or {},
                    score=max(0.0, min(1.0, similarity_score)),
                    document_id=results["ids"][0][i]
                ))
        return search_results

    async def get_collection_stats(self) -> VectorStoreStats:
        if not self.collection: raise ValueError("컬렉션이 초기화되지 않음")
        count = self.collection.count()
        return VectorStoreStats(
            collection_name=self.collection_name,
            total_documents=count,
            embedding_model=self.model_name,
            embedding_dimension=self.embedding_model.get_sentence_embedding_dimension() if self.embedding_model else None,
            database_path=os.getenv("CHROMADB_PATH", "/app/data/chromadb"),
            status="healthy" if count >= 0 else "error",
            last_updated=datetime.now().isoformat()
        )

# 전역 인스턴스
_vector_store_instance = None

async def get_vector_store() -> ChromaVectorStore:
    """Vector Store 싱글톤 인스턴스 반환"""
    global _vector_store_instance
    if _vector_store_instance is None:
        collection_name = os.getenv("COLLECTION_NAME", "teen_empathy_chat")
        _vector_store_instance = ChromaVectorStore(collection_name)
        await _vector_store_instance.initialize()
    return _vector_store_instance