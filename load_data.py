import json
import uuid
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions
import os

# --- 설정 ---
# 이 파일과 같은 위치에 AI Hub 원본 데이터 파일이 있다고 가정합니다.
SOURCE_DATA_FILE = 'AI_Hub_감성대화.json'
DB_PATH = "./data/chromadb"
COLLECTION_NAME = "teen_empathy_chat"
MODEL_NAME = 'jhgan/ko-sbert-multitask'


def setup_database():
    """VectorDB를 설정하고 데이터를 구축하는 메인 함수"""

    # 0. 필수 파일 확인
    if not os.path.exists(SOURCE_DATA_FILE):
        print(f"오류: 원본 데이터 파일 '{SOURCE_DATA_FILE}'을 찾을 수 없습니다.")
        print("AI Hub 데이터를 다운로드하여 이 스크립트와 같은 폴더에 저장해주세요.")
        return

    print("1. 데이터베이스 및 컬렉션 설정 시작...")
    client = chromadb.PersistentClient(path=DB_PATH)

    # HuggingFace 임베딩 함수 설정
    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODEL_NAME)

    # 컬렉션 생성 또는 가져오기
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_func,
        metadata={"hnsw:space": "cosine"}  # 유사도 측정 기준: 코사인 유사도
    )
    print(f"'{COLLECTION_NAME}' 컬렉션 준비 완료.")

    # 2. 원본 JSON 데이터 로드
    print(f"2. '{SOURCE_DATA_FILE}' 파일에서 데이터 로드 중...")
    with open(SOURCE_DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"총 {len(data)}개의 대화 데이터 로드 완료.")

    # 3. 데이터 배치 처리 및 VectorDB에 추가
    print("3. 데이터 임베딩 및 데이터베이스 저장 시작... (시간이 걸릴 수 있습니다)")
    batch_size = 100
    total_batches = (len(data) + batch_size - 1) // batch_size

    for i in range(0, len(data), batch_size):
        batch_data = data[i:i + batch_size]

        # 문서, 메타데이터, ID 리스트 생성
        documents = [item['user_utterance'] for item in batch_data]
        metadatas = [
            {
                "user_utterance": item['user_utterance'],
                "system_response": item['system_response'],
                "emotion": item['emotion'],
                "relationship": item.get('relationship', '기타')  # relationship 필드가 없을 경우 대비
            } for item in batch_data
        ]
        ids = [str(uuid.uuid4()) for _ in batch_data]

        # 컬렉션에 데이터 추가
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        print(f"  - 배치 {i // batch_size + 1}/{total_batches} 처리 완료...")

    print("🎉 데이터베이스 구축이 성공적으로 완료되었습니다!")
    print(f"총 {collection.count()}개의 문서가 '{COLLECTION_NAME}' 컬렉션에 저장되었습니다.")
    print(f"데이터베이스는 '{DB_PATH}' 경로에 저장되었습니다.")


if __name__ == "__main__":
    setup_database()