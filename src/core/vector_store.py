# src/core/vector_store.py
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
from loguru import logger
import os
import uuid
from datetime import datetime
from ..models.vector_models import SearchResult, DocumentInput, VectorStoreStats

class ChromaVectorStore:
    def __init__(self, collection_name: str, metric: str = 'l2', device: str = 'cpu'):
        self.collection_name = collection_name
        self.metric = metric
        self.device = device
        self.client = None
        self.collection = None
        self.embedding_model = None
        self.model_name = os.getenv("EMBEDDING_MODEL", "jhgan/ko-sbert-multitask")
        self.cache_dir = os.getenv("HF_HOME", "/app/cache")
        self.db_path = os.getenv("CHROMADB_PATH", "/app/data/chromadb")

    async def initialize(self):
        try:
            logger.info(f"'{self.collection_name}' ({self.metric} 방식) Vector Store 초기화 시작...")
            os.makedirs(self.db_path, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.db_path)
            self.embedding_model = SentenceTransformer(
                self.model_name, cache_folder=self.cache_dir, device=self.device
            )
            logger.info(f"임베딩 모델 로드 완료. 사용 디바이스: {self.embedding_model.device}")
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": self.metric}
            )
            logger.info(f"✅ 컬렉션 연결/생성 완료: {self.collection_name} ({self.metric} 방식)")
        except Exception as e:
            if "mps" in str(e).lower() and "fallback" not in str(e).lower():
                logger.warning("⚠️ MPS 장치를 사용할 수 없어 CPU로 폴백합니다.")
                self.device = 'cpu'
                await self.initialize()
            else:
                logger.error(f"❌ '{self.collection_name}' 초기화 실패: {e}")
                raise

    def _calculate_similarity_from_distance(self, distance: float) -> float:
        return (1 - distance) if self.metric == 'cosine' else (1 / (1 + distance))

    async def search(self, query: str, top_k: int = 5, filter_metadata: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        if not self.collection: raise ValueError("컬렉션이 초기화되지 않았습니다")
        query_embedding = self.embedding_model.encode([query]).tolist()[0]
        results = self.collection.query(query_embeddings=[query_embedding], n_results=top_k, where=filter_metadata)
        
        search_results = []
        if results and results.get("ids", [[]])[0]:
            for i in range(len(results["ids"][0])):
                search_results.append(SearchResult(
                    content=results["documents"][0][i],
                    metadata=results["metadatas"][0][i],
                    score=self._calculate_similarity_from_distance(results["distances"][0][i]),
                    document_id=results["ids"][0][i]
                ))
        search_results.sort(key=lambda x: x.score, reverse=True)
        return search_results

    async def add_documents(self, documents: List[DocumentInput]) -> List[str]:
        if not self.collection: raise ValueError("컬렉션이 초기화되지 않았습니다")
        texts = [doc.content for doc in documents]
        metadatas = [doc.metadata or {} for doc in documents]
        document_ids = [doc.document_id or str(uuid.uuid4()) for doc in documents]
        embeddings = self.embedding_model.encode(texts).tolist()
        self.collection.add(embeddings=embeddings, documents=texts, metadatas=metadatas, ids=document_ids)
        return document_ids

_vector_store_instances = {}
async def get_vector_store() -> ChromaVectorStore:
    global _vector_store_instances
    metric = os.getenv("DB_METRIC", "cosine").lower()
    if metric not in _vector_store_instances:
        base_name = os.getenv("COLLECTION_NAME", "teen_empathy_chat")
        collection_name = f"{base_name}_{metric}"
        logger.info(f"환경변수 DB_METRIC='{metric}'에 따라 Vector Store 인스턴스를 생성합니다.")
        instance = ChromaVectorStore(collection_name=collection_name, metric=metric)
        await instance.initialize()
        _vector_store_instances[metric] = instance
    return _vector_store_instances[metric]