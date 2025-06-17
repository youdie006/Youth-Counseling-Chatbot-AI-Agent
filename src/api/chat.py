# src/api/chat.py

from fastapi import APIRouter, Header
import traceback
import asyncio
from loguru import logger
from ..services.openai_client import get_openai_client
from ..services.aihub_processor import get_teen_empathy_processor
from ..models.function_models import TeenChatRequest, ReActStep
from ..services.conversation_service import get_conversation_service

router = APIRouter()


async def run_pipeline(session_id: str, message: str) -> dict:
    """모든 처리 과정을 투명하게 추적하는 최종 파이프라인 (명시적 ReAct 적용)"""
    openai_client = await get_openai_client()
    conversation_service = await get_conversation_service()
    processor = await get_teen_empathy_processor()

    debug_info = {}
    react_steps = []

    # Step 1: Context Loading
    session_id = await conversation_service.get_or_create_session(session_id)
    conversation_history = await conversation_service.get_conversation_history(session_id)
    debug_info["step1_context_loading"] = {"session_id": session_id, "loaded_history": conversation_history}

    # Step 2: Input Analysis
    react_steps.append(ReActStep(step_type="thought", content="사용자의 입력 의도를 파악하기 위해 감정과 관계 맥락을 분석해야겠다."))
    analysis_result = await openai_client.analyze_emotion_and_context(message)
    emotion = analysis_result.get("primary_emotion", "불안")
    relationship = analysis_result.get("relationship_context", "동급생")
    react_steps.append(ReActStep(step_type="observation", content=f"분석 결과: 감정='{emotion}', 관계='{relationship}'"))
    debug_info["step2_input_analysis"] = {"input": message, "output": analysis_result}

    # Step 3: Conversational Query Rewriting
    react_steps.append(ReActStep(step_type="thought", content="RAG 검색 정확도를 높이기 위해, 이전 대화 내용까지 포함하여 검색어를 재작성해야겠다."))
    search_query = await openai_client.rewrite_query_with_history(message, conversation_history)
    react_steps.append(ReActStep(step_type="observation", content=f"재작성된 검색어: '{search_query}'"))
    debug_info["step3_query_rewriting"] = {"original_message": message, "rewritten_query": search_query}

    # Step 4: RAG Retrieval
    react_steps.append(ReActStep(step_type="thought", content="재작성된 검색어로 여러 개의 후보 문서를 찾아봐야겠다."))
    expert_responses = await processor.search_similar_contexts(query=search_query, emotion=emotion,
                                                               relationship=relationship, top_k=10)
    react_steps.append(ReActStep(step_type="observation", content=f"유사 사례 후보 {len(expert_responses)}건 발견."))
    debug_info["step4_rag_retrieval"] = {"retrieved_candidates": expert_responses}

    # Step 5: Sequential Relevance Check
    final_expert_advice = None
    verification_logs = []
    react_steps.append(ReActStep(step_type="thought", content="검색된 후보들이 현재 대화와 정말 관련이 있는지 하나씩 순서대로 검증해야겠다."))
    for i, doc in enumerate(expert_responses):
        original_doc_content = doc.get("system_response", "")
        converted_doc_content = openai_client._apply_simple_conversions(original_doc_content)
        is_relevant = await openai_client.verify_rag_relevance(message, converted_doc_content)
        verification_logs.append(
            {"candidate": i + 1, "is_relevant": is_relevant, "original_document": original_doc_content,
             "converted_document": converted_doc_content})
        if is_relevant:
            final_expert_advice = converted_doc_content
            react_steps.append(ReActStep(step_type="observation", content=f"후보 {i + 1}번이 관련 있음! RAG 전략을 사용하기로 결정했다."))
            break
    debug_info["step5_relevance_check"] = {"verification_logs": verification_logs}

    # Step 6: Generation (Explicit ReAct)
    final_response = ""
    if final_expert_advice:
        # Step 6-1: 핵심 전략 추출
        react_steps.append(ReActStep(step_type="thought", content="선택된 참고 자료에서 답변의 핵심 전략을 추출해야겠다."))
        core_strategy = await openai_client.extract_core_strategy(final_expert_advice)
        react_steps.append(ReActStep(step_type="observation", content=f"추출된 핵심 전략: '{core_strategy}'"))

        # Step 6-2: 최종 답변 생성
        react_steps.append(ReActStep(step_type="thought", content="추출된 전략을 바탕으로 최종 공감 답변을 생성해야겠다."))
        final_response, final_prompt = await openai_client.generate_response_from_strategy(
            core_strategy, message, conversation_history
        )
        debug_info["step6_generation"] = {
            "strategy": "RAG-Adaptation (Explicit ReAct)",
            "A_source_advice": final_expert_advice,
            "B_extracted_strategy": core_strategy,
            "C_final_gpt4_prompt": final_prompt,
            "D_final_response": final_response
        }
    else:
        # RAG 실패 시 직접 생성
        react_steps.append(ReActStep(step_type="thought", content="관련 있는 참고 자료가 없으므로, 대화 맥락에만 기반하여 직접 답변을 생성해야겠다."))
        final_response, final_prompt = await openai_client.create_direct_response(message, conversation_history)
        debug_info["step6_generation"] = {
            "strategy": "Direct-Generation",
            "A_final_gpt4_prompt": final_prompt,
            "B_final_response": final_response
        }

    react_steps.append(ReActStep(step_type="observation", content="최종 응답 생성을 완료했다."))

    # Step 7: Save Conversation
    await conversation_service.save_conversation_turn(session_id, message, final_response)
    debug_info["step7_save_conversation"] = {"user": message, "assistant": final_response}

    return {"response": final_response, "debug_info": debug_info, "react_steps": [r.dict() for r in react_steps]}


@router.post("/teen-chat-debug")
async def teen_chat_debug(request: TeenChatRequest, session_id: str = Header(None)):
    try:
        return await run_pipeline(session_id, request.message)
    except Exception as e:
        tb_str = traceback.format_exc()
        logger.error(f"디버깅 파이프라인 실패: {e}\n{tb_str}")
        return {"error": "Pipeline Error", "error_message": str(e), "debug_info": {"traceback": tb_str}}


@router.post("/teen-chat")
async def teen_chat(request: TeenChatRequest, session_id: str = Header(None)):
    result = await run_pipeline(session_id, request.message)
    return {"response": result["response"]}