"""
OpenAI GPT-4 클라이언트 - 파라미터 오류 수정 버전
"""
import os
from typing import List, Dict, Tuple, Optional
from openai import AsyncOpenAI
from loguru import logger
from ..models.function_models import EmotionType, RelationshipType


class OpenAIClient:
    def __init__(self):
        self.client = None
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.default_model = os.getenv("OPENAI_MODEL", "gpt-4")
        self.teen_empathy_system_prompt = """
당신은 "마음이"라는 이름의 13-19세 청소년 전용 상담 AI입니다. 당신의 목표는 사용자의 말을 따뜻하게 들어주고 공감하며, 친한 친구처럼 반말로 대화하는 것입니다.

**[매우 중요] 핵심 규칙:**
- **페르소나 절대 유지:** 너는 반드시 친한 친구처럼, 따뜻하고 다정한 **반말**로 대화해야 해. **절대로 존댓말을 사용하면 안 돼!**
- **맥락 기억:** 이전 대화 내용을 반드시 기억하고, 그 흐름에 맞춰 자연스럽게 대화를 이어가야 해.
- **공감 우선:** 조언보다는 먼저 사용자의 감정을 알아주고 공감하는 말을 해줘. (예: "정말 속상했겠다.", "네 마음 충분히 이해돼.")
- **영어 절대 금지:** 답변은 반드시 한글로만 생성해야 해.
"""
        self.conversion_map = {
            "자기야": "너", "당신": "너", "직장": "학교", "회사": "학교",
            "업무": "공부", "동료": "친구", "상사": "선생님",
            "하세요": "해", "어떠세요": "어때", "해보세요": "해봐",
            "~ㅂ니다": "~야", "~습니다": "~어"
        }

    async def initialize(self):
        if not self.api_key or "your_" in self.api_key.lower():
            raise ValueError("올바른 OpenAI API 키를 설정해주세요")
        self.client = AsyncOpenAI(api_key=self.api_key, timeout=30.0, max_retries=3)
        await self._test_connection()
        logger.info("✅ OpenAI 클라이언트 초기화 완료")

    async def _test_connection(self):
        try:
            await self.client.chat.completions.create(
                model=self.default_model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
        except Exception as e:
            raise e

    async def create_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        if not self.client:
            await self.initialize()
        response = await self.client.chat.completions.create(
            model=kwargs.get("model", self.default_model),
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 500)
        )
        return response.choices[0].message.content

    async def rewrite_query_with_history(self, user_message: str, conversation_history: List[Dict]) -> str:
        """대화 맥락 기반 쿼리 재작성 함수"""
        if not conversation_history:
            return user_message

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
### 모범 답안 예시
[이전 대화 내용]
[assistant] 요즘 무슬 고민 있어?
[user] 제일 친한 친구가 요즘 나를 피하는 것 같아.
[사용자 마지막 메시지]
"방금도 단톡방에서 나만 빼고 자기들끼리만 얘기해."
[재작성된 검색 쿼리]
"가장 친한 친구가 다른 무리와 어울리며 단체 채팅방에서 나를 소외시켜 느끼는 따돌림과 서운함"

---
### 실제 과제
[이전 대화 내용]
{history_str}
[사용자 마지막 메시지]
"{user_message}"
[재작성된 검색 쿼리]
"""
        rewritten_query = await self.create_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=200
        )
        logger.info(f"대화형 쿼리 재작성: '{user_message}' -> '{rewritten_query.strip()}'")
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
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.0,
                max_tokens=200
            )
            import json
            return json.loads(response_content.strip())
        except Exception:
            return {
                "primary_emotion": EmotionType.ANXIETY.value,
                "relationship_context": RelationshipType.FRIEND.value
            }

    def _apply_simple_conversions(self, text: str) -> str:
        for old, new in self.conversion_map.items():
            text = text.replace(old, new)
        return text

    async def verify_rag_relevance(self, user_message: str, retrieved_doc: str) -> bool:
        prompt = f"""사용자의 현재 메시지와 검색된 전문가 조언이 의미적으로 관련이 있는지 판단해줘. 반드시 'Yes' 또는 'No'로만 대답해.
- 사용자 메시지: "{user_message}"
- 검색된 조언: "{retrieved_doc}"

관련이 있는가? (Yes/No):"""
        response = await self.create_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=5
        )
        logger.info(f"RAG 검증 결과: {response.strip()}")
        return "yes" in response.strip().lower()

    async def adapt_expert_response(self, expert_response: str, user_situation: str,
                                    conversation_history: List[Dict]) -> Tuple[str, str, str, str]:
        pre_adapted_response = self._apply_simple_conversions(expert_response)
        messages = [
            {"role": "system", "content": self.teen_empathy_system_prompt},
            *conversation_history,
            {"role": "user", "content": f"내 친구의 현재 상황은 '{user_situation}'이야. 내가 참고할 전문가 조언은 '{pre_adapted_response}'인데, 이 조언을 내 친구에게 말하듯 자연스럽고 따뜻한 반말로 바꿔줘."}
        ]
        final_prompt_for_debug = "\n".join([f"[{msg['role']}] {msg['content']}" for msg in messages])
        final_response = await self.create_completion(messages=messages, temperature=0.5, max_tokens=400)
        return expert_response, pre_adapted_response, final_response, final_prompt_for_debug

    async def create_direct_response(self, user_message: str, conversation_history: List[Dict],
                                     inspirational_docs: Optional[List[str]] = None) -> Tuple[str, str]:
        """직접 응답 생성 (파라미터 수정)"""
        messages = [
            {"role": "system", "content": self.teen_empathy_system_prompt},
            *conversation_history
        ]

        inspiration_prompt = ""
        if inspirational_docs:
            inspiration_prompt = "\n\n### 참고 자료 (직접 언급하지 말고, 답변을 만들 때 영감을 얻는 용도로만 사용해)\n"
            for doc in inspirational_docs:
                inspiration_prompt += f"- {doc}\n"

        final_user_prompt = f"""'마음이'의 페르소나(친한 친구, 반말)를 완벽하게 지키면서 다음 메시지에 공감하는 답변을 해줘.{inspiration_prompt}

"{user_message}"
"""
        messages.append({"role": "user", "content": final_user_prompt})

        prompt_for_debug = "\n".join([f"[{msg['role']}] {msg['content']}" for msg in messages])
        final_response = await self.create_completion(messages=messages, temperature=0.7, max_tokens=300)
        return final_response, prompt_for_debug


_openai_client_instance = None


async def get_openai_client() -> OpenAIClient:
    global _openai_client_instance
    if _openai_client_instance is None:
        _openai_client_instance = OpenAIClient()
        await _openai_client_instance.initialize()
    return _openai_client_instance