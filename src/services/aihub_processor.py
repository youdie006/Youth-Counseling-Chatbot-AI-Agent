# src/services/aihub_processor.py
from typing import Dict, List, Optional
from loguru import logger
from ..core.vector_store import get_vector_store

class TeenEmpathyDataProcessor:
    def __init__(self, vector_store):
        self.vector_store = vector_store
        logger.info("TeenEmpathyDataProcessor 초기화 완료. Vector Store가 주입되었습니다.")

    async def search_similar_contexts(self, query: str, emotion: Optional[str] = None,
                                      relationship: Optional[str] = None, top_k: int = 5) -> List[Dict]:
        try:
            conditions = []
            if emotion: conditions.append({"emotion": {"$eq": emotion}})
            if relationship: conditions.append({"relationship": {"$eq": relationship}})

            search_filter = None
            if len(conditions) > 1:
                search_filter = {"$and": conditions}
            elif len(conditions) == 1:
                search_filter = conditions[0]

            logger.info(f"🔍 벡터 검색 시작 - Query: '{query}', Filter: {search_filter}")
            results = await self.vector_store.search(
                query=query, top_k=top_k, filter_metadata=search_filter
            )
            formatted_results = [{
                "user_utterance": r.metadata.get("user_utterance", ""),
                "system_response": r.metadata.get("system_response", ""),
                "emotion": r.metadata.get("emotion", ""),
                "relationship": r.metadata.get("relationship", ""),
                "similarity_score": r.score
            } for r in results]
            logger.info(f"✅ 검색 완료: {len(formatted_results)}개 결과")
            return formatted_results
        except Exception as e:
            logger.error(f"❌ 유사 사례 검색 실패: {e}")
            return []

_processor_instance = None
async def get_teen_empathy_processor() -> TeenEmpathyDataProcessor:
    global _processor_instance
    if _processor_instance is None:
        vector_store = await get_vector_store()
        _processor_instance = TeenEmpathyDataProcessor(vector_store=vector_store)
    return _processor_instance