"""
OpenAI 및 기타 기능 관련 데이터 모델들
GPT-4 API 호출, 채팅, 감정 분석 등의 모델들
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class ChatRole(str, Enum):
    """채팅 역할 열거형"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """채팅 메시지 모델"""
    role: ChatRole = Field(..., description="메시지 역할")
    content: str = Field(..., description="메시지 내용", min_length=1)
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat(), description="메시지 시간")


class OpenAICompletionRequest(BaseModel):
    """OpenAI 완성 요청 모델"""
    messages: List[ChatMessage] = Field(..., description="대화 메시지 목록")
    model: str = Field(default="gpt-4", description="사용할 모델")
    temperature: float = Field(default=0.7, description="응답 창의성", ge=0, le=2)
    max_tokens: int = Field(default=500, description="최대 토큰 수", ge=1, le=4000)
    top_p: float = Field(default=1.0, description="확률 임계값", ge=0, le=1)
    stream: bool = Field(default=False, description="스트리밍 여부")


class OpenAICompletionResponse(BaseModel):
    """OpenAI 완성 응답 모델"""
    content: str = Field(..., description="생성된 응답 내용")
    model: str = Field(..., description="사용된 모델")
    tokens_used: int = Field(..., description="사용된 토큰 수")
    processing_time_ms: float = Field(..., description="처리 시간 (밀리초)")
    finish_reason: str = Field(..., description="완료 이유")


class EmotionType(str, Enum):
    """감정 유형 열거형"""
    JOY = "기쁨"
    CONFUSION = "당황"
    ANGER = "분노"
    ANXIETY = "불안"
    HURT = "상처"
    SADNESS = "슬픔"


class RelationshipType(str, Enum):
    """관계 유형 열거형"""
    PARENT = "부모님"
    FRIEND = "친구"
    SIBLING = "형제자매"
    CRUSH = "좋아하는 사람"
    CLASSMATE = "동급생"
    FAMILY = "가족"


class EmpathyStrategy(str, Enum):
    """공감 전략 열거형"""
    ENCOURAGE = "격려"
    AGREE = "동조"
    COMFORT = "위로"
    ADVISE = "조언"


class EmotionAnalysisRequest(BaseModel):
    """감정 분석 요청 모델"""
    text: str = Field(..., description="분석할 텍스트", min_length=1, max_length=1000)
    context: Optional[str] = Field(default=None, description="추가 맥락 정보")


class EmotionAnalysisResponse(BaseModel):
    """감정 분석 응답 모델"""
    primary_emotion: EmotionType = Field(..., description="주요 감정")
    emotion_confidence: float = Field(..., description="감정 신뢰도", ge=0, le=1)
    relationship_context: Optional[RelationshipType] = Field(default=None, description="관계 맥락")
    recommended_strategies: List[EmpathyStrategy] = Field(..., description="추천 공감 전략")


class TeenChatRequest(BaseModel):
    """청소년 채팅 요청 모델"""
    message: str = Field(..., description="사용자 메시지", min_length=1, max_length=1000)


class ReActStep(BaseModel):
    """ReAct 추론 단계 모델"""
    step_type: Literal["thought", "action", "observation"] = Field(..., description="단계 유형")
    content: str = Field(..., description="단계 내용")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="단계 시간")


class TeenChatResponse(BaseModel):
    """청소년 채팅 응답 모델"""
    response: str = Field(..., description="공감형 응답")
    detected_emotion: EmotionType = Field(..., description="감지된 감정")
    empathy_strategy: List[EmpathyStrategy] = Field(..., description="적용된 공감 전략")
    similar_contexts: List[Dict[str, Any]] = Field(default=[], description="유사한 대화 맥락")
    react_steps: Optional[List[ReActStep]] = Field(default=None, description="ReAct 추론 과정")
    confidence_score: float = Field(..., description="응답 신뢰도", ge=0, le=1)
    response_metadata: Dict[str, Any] = Field(default={}, description="응답 메타데이터")


class SystemHealthCheck(BaseModel):
    """시스템 헬스 체크 모델"""
    status: Literal["healthy", "degraded", "unhealthy"] = Field(..., description="시스템 상태")
    services: Dict[str, bool] = Field(..., description="서비스별 상태")
    response_time_ms: float = Field(..., description="응답 시간 (밀리초)")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="체크 시간")
    version: str = Field(..., description="시스템 버전")