# src/services/openai_client.py

"""
OpenAI GPT-4 클라이언트 - 최종 버전 (구조적 분석 및 재조립 프롬프트)
"""
import os
from typing import List, Dict, Tuple, Optional
from openai import AsyncOpenAI
from loguru import logger
import json
from ..models.function_models import EmotionType, RelationshipType


class OpenAIClient:
    def __init__(self):
        self.client = None
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.default_model = os.getenv("OPENAI_MODEL", "gpt-4-turbo")
        self.teen_empathy_system_prompt = """
당신은 "마음이"라는 이름의 13-19세 청소년 전용 상담 AI입니다. 당신의 목표는 사용자의 말을 따뜻하게 들어주고 공감하며, 친한 친구처럼 반말로 대화하는 것입니다.

**[매우 중요] 핵심 규칙:**
- **페르소나 절대 유지:** 너는 반드시 친한 친구처럼, 따뜻하고 다정한 **반말**로 대화해야 해. **절대로 존댓말을 사용하면 안 돼!**
- **맥락 기억:** 이전 대화 내용을 반드시 기억하고, 그 흐름에 맞춰 자연스럽게 대화를 이어가야 해.
- **공감 우선:** 조언보다는 먼저 사용자의 감정을 알아주고 공감하는 말을 해줘. (예: "정말 속상했겠다.", "네 마음 충분히 이해돼.")
- **대화 유도:** 답변의 마지막에는 항상 사용자가 다음 말을 이어가기 쉽도록 **개방형 질문(Open-ended question)을 포함**해야 해. (예: "그때 기분이 어땠어?", "좀 더 자세히 얘기해 줄 수 있어?")
- **영어 절대 금지:** 답변은 반드시 한글로만 생성해야 해.
"""
        self.word_conversion_map = {
            "자기야": "너", "당신": "너", "직장": "학교", "회사": "학교",
            "업무": "공부", "동료": "친구", "상사": "선생님", "아드님도": "너도"
        }
        self.ending_conversion_map = {
            "합니다": "해", "하세요": "해", "어떠세요": "어때", "해보세요": "해봐",
            "습니다": "어", "ㅂ니다": "야", "시겠어요": "겠어", "인데요": "인데", "이죠": "이지"
        }

    async def initialize(self):
        if not self.api_key or "sk-proj-" not in self.api_key:
            raise ValueError("올바른 OpenAI API 키를 설정해주세요 (`sk-proj-` 형태)")
        self.client = AsyncOpenAI(api_key=self.api_key, timeout=30.0, max_retries=3)
        await self._test_connection()
        logger.info("✅ OpenAI 클라이언트 초기화 완료")

    async def _test_connection(self):
        try:
            await self.client.chat.completions.create(
                model=self.default_model, messages=[{"role": "user", "content": "Hello"}], max_tokens=5
            )
        except Exception as e:
            logger.error(f"OpenAI API 연결 테스트 실패: {e}")
            raise e

    async def create_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        if not self.client: await self.initialize()
        is_json_mode = kwargs.get("json_mode", False)
        response_format = {"type": "json_object"} if is_json_mode else None

        response = await self.client.chat.completions.create(
            model=kwargs.get("model", self.default_model),
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 400),
            response_format=response_format
        )
        return response.choices[0].message.content

    async def rewrite_query_with_history(self, user_message: str, conversation_history: List[Dict]) -> str:
        if not conversation_history: return user_message
        history_str = "\n".join([f"[{msg['role']}] {msg['content']}" for msg in conversation_history])
        prompt = f"""당신은 사용자의 대화 전체를 깊이 이해하여, 벡터 검색에 가장 적합한 검색 문장을 생성하는 '쿼리 재작성 전문가'입니다.
### 임무
주어진 '이전 대화 내용'과 '사용자의 마지막 메시지'를 종합하여, 사용자가 겪고 있는 문제의 핵심 상황과 감정이 모두 담긴, 단 하나의 완벽한 문장으로 재작성해야 합니다.
### 규칙
1. 반드시 사용자의 입장에서, 사용자가 겪는 문제 상황을 중심으로 서술해야 합니다.
2. 단순 키워드 나열은 절대 금지됩니다.
3. 재작성된 문장은 그 자체로 완전한 의미를 가져야 합니다.
4. 오직 '재작성된 검색 쿼리:' 부분의 내용만 결과로 출력해야 합니다.
---
### 실제 과제
[이전 대화 내용]
{history_str}
[사용자 마지막 메시지]
"{user_message}"
[재작성된 검색 쿼리]
"""
        rewritten_query = await self.create_completion(
            messages=[{"role": "user", "content": prompt}], temperature=0.0, max_tokens=200
        )
        return rewritten_query.strip()

    async def analyze_emotion_and_context(self, text: str) -> dict:
        emotion_list = [e.value for e in EmotionType]
        relationship_list = [r.value for r in RelationshipType]
        analysis_prompt = f"""다음 청소년의 메시지에서 primary_emotion과 relationship_context를 추출해줘. 반드시 아래 목록의 한글 단어 중에서만 선택해서 JSON으로 응답해야 해.
- primary_emotion: {emotion_list}
- relationship_context: {relationship_list}
메시지: "{text}"
"""
        try:
            response_content = await self.create_completion(
                messages=[{"role": "user", "content": analysis_prompt}], temperature=0.0, max_tokens=200, json_mode=True
            )
            return json.loads(response_content.strip())
        except Exception as e:
            logger.error(f"감정 분석 실패: {e}")
            return {"primary_emotion": "불안", "relationship_context": "친구"}

    def _apply_simple_conversions(self, text: str) -> str:
        for old, new in self.word_conversion_map.items():
            text = text.replace(old, new)
        words = text.split(' ')
        converted_words = []
        for word in words:
            for old_ending, new_ending in sorted(self.ending_conversion_map.items(), key=lambda item: len(item[0]),
                                                 reverse=True):
                if word.endswith(old_ending):
                    word = word[:-len(old_ending)] + new_ending
                    break
            converted_words.append(word)
        return ' '.join(converted_words)

    async def verify_rag_relevance(self, user_message: str, retrieved_doc: str) -> bool:
        prompt = f"""사용자의 현재 메시지와 검색된 조언이 의미적으로 관련이 있는지 판단해줘. 반드시 'Yes' 또는 'No'로만 대답해.
- 사용자 메시지: "{user_message}"
- 검색된 조언: "{retrieved_doc}"
관련이 있는가? (Yes/No):"""
        response = await self.create_completion(
            messages=[{"role": "user", "content": prompt}], temperature=0.0, max_tokens=5
        )
        return "yes" in response.strip().lower()

    #  [핵심 수정] 함수 1: 답변을 구조적으로 분석하여 핵심 요소들을 추출
    async def extract_core_strategy(self, expert_response: str) -> str:
        """주어진 모범 답안을 구조적으로 분석하여 핵심 요소들을 JSON으로 추출합니다."""
        prompt = f"""[너의 임무]
아래 '모범 답안'을 읽고, 아래 '추출 포맷'에 맞춰 핵심 요소들을 추출해줘. 반드시 JSON 형식으로만 응답해야 해.

[모범 답안]
"{expert_response}"

[추출 포맷]
{{
  "empathy_phrase": "<사용자의 감정에 직접 공감하는 핵심 문장>",
  "core_suggestion": "<답변에 담긴 구체적인 제안이나 조언>",
  "encouragement_phrase": "<마지막에 힘을 주는 격려의 메시지>"
}}
"""
        strategy_json = await self.create_completion(
            messages=[{"role": "system", "content": prompt}],
            temperature=0.0,
            max_tokens=500,
            json_mode=True
        )
        return strategy_json

    #  [핵심 수정] 함수 2: 추출된 구조화된 요소를 바탕으로 최종 답변 재조립
    async def generate_response_from_strategy(self, core_strategy_json: str, user_situation: str,
                                              conversation_history: List[Dict]) -> Tuple[str, str]:
        """추출된 핵심 요소들을 바탕으로 최종 답변을 생성합니다."""
        messages = [
            {"role": "system", "content": self.teen_empathy_system_prompt},
            *conversation_history,
            {"role": "user", "content": user_situation}
        ]

        final_prompt_instruction = f"""[너의 임무]
너는 상담가 '마음이'야. 아래 '핵심 요소'들을 자연스럽게 조합하여, 너의 페르소나에 맞는 가장 따뜻하고 진심 어린 최종 답변을 생성해줘.

[핵심 요소]
{core_strategy_json}
"""
        messages.append({"role": "system", "content": final_prompt_instruction})

        final_prompt_for_debug = "\n".join([f"[{msg['role']}] {msg['content']}" for msg in messages])
        final_response = await self.create_completion(messages=messages, temperature=0.7, max_tokens=800)

        return final_response, final_prompt_for_debug

    async def create_direct_response(self, user_message: str, conversation_history: List[Dict]) -> Tuple[str, str]:
        """RAG 실패 시 직접 생성"""
        messages = [
            {"role": "system", "content": self.teen_empathy_system_prompt},
            *conversation_history,
            {"role": "user", "content": user_message}
        ]
        prompt_for_debug = "\n".join([f"[{msg['role']}] {msg['content']}" for msg in messages])
        final_response = await self.create_completion(messages=messages, temperature=0.7, max_tokens=400)
        return final_response, prompt_for_debug


_openai_client_instance = None


async def get_openai_client() -> OpenAIClient:
    global _openai_client_instance
    if _openai_client_instance is None:
        _openai_client_instance = OpenAIClient()
        await _openai_client_instance.initialize()
    return _openai_client_instance