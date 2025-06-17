# scripts/copy_l2_to_cosine.py

import asyncio
import os
import sys
from loguru import logger
import chromadb
from sentence_transformers import SentenceTransformer

# 스크립트가 src 폴더를 찾을 수 있도록 경로를 추가
sys.path.append(os.getcwd())
from src.models.vector_models import DocumentInput

# --- 설정 ---
# 원본이 될 기존 컬렉션 이름 (아마도 기본 이름)
SOURCE_COLLECTION_NAME = "teen_empathy_chat"
# 새로 만들 코사인 컬렉션 이름
TARGET_COLLECTION_NAME = "teen_empathy_chat_cosine"

DB_PATH = "./data/chromadb"
BATCH_SIZE = 100
EMBEDDING_MODEL = "jhgan/ko-sbert-multitask"
CACHE_DIR = "./cache"
# macOS의 GPU(MPS)를 사용하도록 설정. 실패 시 CPU로 자동 전환됨.
DEVICE = 'mps'


# -----------------

async def copy_data():
    """
    기존 L2 컬렉션에서 모든 데이터를 읽어,
    새로운 코사인 컬렉션으로 복사(재입력)합니다. (Chroma 0.4.x 호환)
    """
    logger.info(f"데이터 복사를 시작합니다: '{SOURCE_COLLECTION_NAME}' (L2) -> '{TARGET_COLLECTION_NAME}' (Cosine)")

    # 1. 최신 버전 클라이언트 생성
    os.makedirs(DB_PATH, exist_ok=True)
    client = chromadb.PersistentClient(path=DB_PATH)

    # 2. 원본(L2) 컬렉션 객체 가져오기
    try:
        source_collection = client.get_collection(name=SOURCE_COLLECTION_NAME)
        logger.info(f"✅ 원본 컬렉션 '{SOURCE_COLLECTION_NAME}'에 성공적으로 연결했습니다.")
    except ValueError:
        logger.error(f"❌ 오류: 원본 컬렉션('{SOURCE_COLLECTION_NAME}')을 찾을 수 없습니다.")
        logger.error("먼저 .env 파일에서 DB_METRIC=l2 로 설정하고 앱을 한번 실행하여, 기본 L2 컬렉션이 존재하는지 확인하세요.")
        return

    # 3. 대상(코사인) 컬렉션 생성/연결
    logger.info(f"대상 (Cosine) 컬렉션 '{TARGET_COLLECTION_NAME}'을 생성/연결합니다.")
    target_collection = client.get_or_create_collection(name=TARGET_COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

    # 4. 원본 컬렉션에서 모든 데이터 읽어오기
    total_docs_count = source_collection.count()
    if total_docs_count == 0:
        logger.warning("원본 컬렉션에 문서가 없습니다. 복사를 중단합니다.")
        return

    logger.info(f"총 {total_docs_count}개의 문서를 원본 컬렉션에서 읽어옵니다...")
    all_data = source_collection.get(include=["metadatas", "documents"])

    # 5. 임베딩 모델 로드
    try:
        embedding_model = SentenceTransformer(EMBEDDING_MODEL, cache_folder=CACHE_DIR, device=DEVICE)
        logger.info(f"✅ 임베딩 모델 '{EMBEDDING_MODEL}'을 로드했습니다. (Device: {embedding_model.device})")
    except Exception as e:
        logger.warning(f"⚠️ MPS 장치 사용 불가. CPU로 전환합니다. 에러: {e}")
        embedding_model = SentenceTransformer(EMBEDDING_MODEL, cache_folder=CACHE_DIR, device='cpu')
        logger.info(f"✅ 임베딩 모델 '{EMBEDDING_MODEL}'을 로드했습니다. (Device: {embedding_model.device})")

    # 6. 데이터를 배치 단위로 '새로 임베딩'하여 코사인 컬렉션에 추가
    ids_list = all_data['ids']
    documents_list = all_data['documents']
    metadatas_list = all_data['metadatas']

    logger.info(f"데이터 복사를 시작합니다. 배치 크기: {BATCH_SIZE}")
    added_count = 0
    for i in range(0, len(ids_list), BATCH_SIZE):
        batch_ids = ids_list[i:i + BATCH_SIZE]
        batch_docs = documents_list[i:i + BATCH_SIZE]
        batch_metadatas = metadatas_list[i:i + BATCH_SIZE]

        try:
            logger.info(f"배치 {i // BATCH_SIZE + 1}: {len(batch_docs)}개 문서 임베딩 중...")
            batch_embeddings = embedding_model.encode(batch_docs).tolist()

            target_collection.add(
                ids=batch_ids,
                documents=batch_docs,
                embeddings=batch_embeddings,
                metadatas=batch_metadatas
            )
            added_count += len(batch_ids)
            logger.info(f"진행 상황: {added_count} / {total_docs_count} 문서 처리 완료...")
        except Exception as e:
            logger.error(f"배치 {i // BATCH_SIZE + 1} 처리 중 오류 발생: {e}")
            logger.error("복사를 중단합니다.")
            return

    # 7. 최종 결과 확인
    final_count = target_collection.count()
    if final_count >= total_docs_count:
        logger.success("🎉 데이터 복사가 성공적으로 완료되었습니다!")
        logger.success(f"총 {final_count}개의 문서가 '{TARGET_COLLECTION_NAME}' 컬렉션으로 복사되었습니다.")
    else:
        logger.error("❌ 데이터 복사 실패. 원본과 대상의 문서 수가 일치하지 않습니다.")
        logger.error(f"원본: {total_docs_count}개, 대상: {final_count}개")


if __name__ == "__main__":
    # 이 스크립트는 프로젝트 루트 디렉토리에서 모듈로 실행하는 것이 가장 안전합니다.
    # 예: python3 -m scripts.copy_l2_to_cosine
    asyncio.run(copy_data())