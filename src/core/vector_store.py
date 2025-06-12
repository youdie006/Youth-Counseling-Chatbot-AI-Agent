"""
ChromaDB 기반 Vector Store - 핵심 기능만
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

    async def initialize(self):
        """ChromaDB 및 임베딩 모델 초기화"""
        try:
            logger.info("ChromaDB Vector Store 초기화 시작...")

            # ChromaDB 클라이언트 생성
            db_path = os.getenv("CHROMADB_PATH", "./data/chromadb")
            os.makedirs(db_path, exist_ok=True)

            self.client = chromadb.PersistentClient(
                path=db_path,
                settings=Settings(allow_reset=True, anonymized_telemetry=False)
            )

            # 한국어 임베딩 모델 로드
            logger.info(f"한국어 임베딩 모델 로드 중: {self.model_name}")
            self.embedding_model = SentenceTransformer(self.model_name)
            logger.info(f"임베딩 모델 로드 완료 - 차원: {self.embedding_model.get_sentence_embedding_dimension()}")

            # 컬렉션 생성/연결
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(f"기존 컬렉션 연결: {self.collection_name}")
            except ValueError:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={
                        "description": "Teen empathy conversation embeddings",
                        "embedding_model": self.model_name,
                        "created_at": datetime.now().isoformat()
                    }
                )
                logger.info(f"새 컬렉션 생성: {self.collection_name}")

            logger.info("✅ ChromaDB Vector Store 초기화 완료")

        except Exception as e:
            logger.error(f"❌ ChromaDB 초기화 실패: {e}")
            raise

    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """한국어 임베딩 생성"""
        try:
            if not self.embedding_model:
                raise ValueError("임베딩 모델이 초기화되지 않았습니다")

            logger.info(f"임베딩 생성 중: {len(texts)}개 텍스트")
            embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
            embeddings_list = embeddings.tolist()
            logger.info(f"✅ 임베딩 생성 완료: {len(embeddings_list)}개")

            return embeddings_list

        except Exception as e:
            logger.error(f"❌ 임베딩 생성 실패: {e}")
            raise

    async def add_documents(self, documents: List[DocumentInput]) -> List[str]:
        """문서들을 Vector DB에 추가"""
        try:
            if not self.collection:
                raise ValueError("컬렉션이 초기화되지 않았습니다")

            logger.info(f"문서 추가 시작: {len(documents)}개")

            # 텍스트와 메타데이터 분리
            texts = [doc.content for doc in documents]
            metadatas = []
            document_ids = []

            for doc in documents:
                doc_id = doc.document_id or str(uuid.uuid4())
                document_ids.append(doc_id)

                metadata = doc.metadata.copy() if doc.metadata else {}
                metadata.update({
                    "timestamp": datetime.now().isoformat(),
                    "content_length": len(doc.content)
                })
                metadatas.append(metadata)

            # 임베딩 생성
            embeddings = self.create_embeddings(texts)

            # ChromaDB에 추가
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=document_ids
            )

            logger.info(f"✅ 문서 {len(documents)}개 추가 완료")
            return document_ids

        except Exception as e:
            logger.error(f"❌ 문서 추가 실패: {e}")
            raise

    async def search(self, query: str, top_k: int = 5,
                    filter_metadata: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """유사도 기반 문서 검색"""
        try:
            if not self.collection:
                raise ValueError("컬렉션이 초기화되지 않았습니다")

            start_time = time.time()
            logger.info(f"검색 시작 - 쿼리: '{query[:50]}...', top_k: {top_k}")

            # 쿼리 임베딩 생성
            query_embedding = self.create_embeddings([query])[0]

            # ChromaDB 검색
            search_kwargs = {
                "query_embeddings": [query_embedding],
                "n_results": top_k,
                "include": ["documents", "metadatas", "distances"]
            }

            if filter_metadata:
                search_kwargs["where"] = filter_metadata

            results = self.collection.query(**search_kwargs)

            # 결과 포맷팅
            search_results = []

            if results["documents"] and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    distance = results["distances"][0][i]

                    # 유클리드 거리를 유사도로 변환
                    if distance <= 200:
                        similarity_score = 0.8 - (distance / 200) * 0.3
                    elif distance <= 300:
                        similarity_score = 0.5 - ((distance - 200) / 100) * 0.3
                    else:
                        similarity_score = max(0.01, 1000 / (distance + 100))

                    similarity_score = max(0.0, min(1.0, similarity_score))

                    search_results.append(SearchResult(
                        content=results["documents"][0][i],
                        metadata=results["metadatas"][0][i] if results["metadatas"][0] else {},
                        score=similarity_score,
                        document_id=f"result_{i}"
                    ))

            search_time = (time.time() - start_time) * 1000
            logger.info(f"✅ 검색 완료: {len(search_results)}개 결과 ({search_time:.2f}ms)")
            return search_results

        except Exception as e:
            logger.error(f"❌ 검색 실패: {e}")
            raise

    async def get_collection_stats(self) -> VectorStoreStats:
        """컬렉션 통계 정보"""
        try:
            if not self.collection:
                raise ValueError("컬렉션이 초기화되지 않음")

            count = self.collection.count()

            return VectorStoreStats(
                collection_name=self.collection_name,
                total_documents=count,
                embedding_model=self.model_name,
                embedding_dimension=self.embedding_model.get_sentence_embedding_dimension() if self.embedding_model else None,
                database_path=os.getenv("CHROMADB_PATH", "./data/chromadb"),
                status="healthy" if count >= 0 else "error",
                last_updated=datetime.now().isoformat()
            )

        except Exception as e:
            logger.error(f"통계 조회 실패: {e}")
            raise


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