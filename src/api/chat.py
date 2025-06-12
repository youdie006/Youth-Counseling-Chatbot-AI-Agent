from fastapi import APIRouter, Header
import traceback
from loguru import logger
from ..services.openai_client import get_openai_client
from ..services.aihub_processor import get_teen_empathy_processor
from ..models.function_models import TeenChatRequest, ReActStep, EmotionType, RelationshipType
from ..services.conversation_service import get_conversation_service

router = APIRouter()


async def run_pipeline(session_id: str, message: str) -> dict:
    """모든 처리 과정을 투명하게 추적하는 최종 파이프라인 (RAG-Fusion 적용)"""

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
    emotion = analysis_result.get("primary_emotion", EmotionType.ANGER.value)
    relationship = analysis_result.get("relationship_context", RelationshipType.FAMILY.value)
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
                                                               relationship=relationship, top_k=5)
    react_steps.append(ReActStep(step_type="observation", content=f"유사 사례 후보 {len(expert_responses)}건 발견."))
    debug_info["step4_rag_retrieval"] = {"retrieved_candidates": expert_responses}

    # Step 5: Sequential Relevance Check & Strategy Decision
    strategy = "Direct-Generation"
    final_expert_advice = None
    verification_logs = []

    react_steps.append(ReActStep(step_type="thought", content="검색된 후보들이 현재 대화와 정말 관련이 있는지 하나씩 순서대로 검증해야겠다."))
    for i, doc in enumerate(expert_responses):
        doc_content = doc.get("system_response", "")
        is_relevant = await openai_client.verify_rag_relevance(message, doc_content)
        verification_logs.append({"candidate": i + 1, "is_relevant": is_relevant, "document": doc})
        if is_relevant:
            strategy = "RAG-Adaptation"
            final_expert_advice = doc_content
            react_steps.append(ReActStep(step_type="observation", content=f"후보 {i + 1}번이 관련 있음! RAG 전략을 사용하기로 결정했다."))
            break

    if not final_expert_advice:
        react_steps.append(
            ReActStep(step_type="observation", content="관련 있는 문서를 찾지 못했으므로, 검색된 문서들을 '영감'으로 삼아 직접 생성 전략을 사용한다."))

    debug_info["step5_strategy_decision"] = {"chosen_strategy": strategy, "verification_logs": verification_logs}

    # Step 6: Final Response Generation
    react_steps.append(ReActStep(step_type="thought", content=f"'{strategy}' 전략을 사용해, 최종 답변을 생성한다."))
    final_response = ""
    if strategy == "RAG-Adaptation":
        raw_advice, pre_adapted, final_adapted, final_prompt = await openai_client.adapt_expert_response(
            final_expert_advice, message, conversation_history)
        final_response = final_adapted
        debug_info["step6_generation"] = {"strategy": strategy, "A_source_expert_advice": raw_advice,
                                          "B_rule_based_adaptation": pre_adapted, "C_final_gpt4_prompt": final_prompt,
                                          "D_final_response": final_response}
    else:
        # RAG-Fusion 적용: 실패한 RAG 결과를 '영감'으로 제공
        inspirational_docs = [doc.get("system_response", "") for doc in expert_responses]
        final_response, final_prompt = await openai_client.create_direct_response(
            user_message=message,
            conversation_history=conversation_history,
            inspirational_docs=inspirational_docs
        )
        debug_info["step6_generation"] = {"strategy": strategy, "A_final_gpt4_prompt": final_prompt,
                                          "B_final_response": final_response}

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
        tb_str = traceback.format_exc();
        logger.error(f"디버깅 파이프라인 실패: {e}\n{tb_str}")
        return {"error": "Pipeline Error", "error_message": str(e), "debug_info": {"traceback": tb_str}}


@router.post("/teen-chat")
async def teen_chat(request: TeenChatRequest, session_id: str = Header(None)):
    result = await run_pipeline(session_id, request.message)
    return {"response": result["response"]}