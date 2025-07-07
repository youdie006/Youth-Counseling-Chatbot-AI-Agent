---
# 이 부분은 Hugging Face Space 설정에만 사용됩니다.
# GitHub에서는 이 부분이 회색 코드 블록처럼 보입니다.
title: 마음이 - 청소년 공감 AI 챗봇
emoji: 💙
colorFrom: purple
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# 🧠 Youth Counseling RAG Agent: Maeum-i

**Maeum-i** is an AI chatbot designed for youth counseling, powered by Retrieval-Augmented Generation (RAG).  
It utilizes GPT-4 Turbo and 200,000 real Korean counseling dialogues, combined with KoSBERT embeddings and ChromaDB vector search, to generate accurate and empathetic responses.

---

## ☁️ Deployment

- [Hugging Face Spaces (Chatbot Demo)](https://huggingface.co/spaces/youdie006/simsimi_ai_agent)

## 🧾 Dataset

- [Vectorized Dataset (processed from AI Hub Korean counseling data with KoSBERT embeddings)](https://huggingface.co/datasets/youdie006/simsimi-ai-agent-data)

## 📑 Project Materials

- [Project Presentation PDF](/report/Presentation.pdf)

---

## 🔍 Project Overview

- **Source Data:** AI Hub Korean Empathetic Dialogue Dataset (200,000 sentences)  
- **Core Techniques:** Retrieval-Augmented Generation (RAG), ReAct prompting  
- **Objective:** Build a trustworthy and empathetic dialogue agent beyond simple generative LLM responses

---

## 🚀 Key Features

- **RAG (Retrieval-Augmented Generation):** Prevents hallucination by grounding answers in retrieved counseling records based on vector similarity.
- **ReAct Prompting:** Enables logical reasoning through the structure of **"Thought → Action → Observation"**, ensuring interpretable and traceable responses.
- **Advanced Prompt Engineering:**
  - Contextual query rewriting
  - Decomposition and reconstruction of emotional responses (empathy, advice, encouragement)
  - **Chain-of-Thought (CoT)** reasoning for step-by-step cognitive flow
  - Secondary prompt verification to reduce uncertainty and ensure safety

---

## 🔧 Tech Stack

| Component         | Technology / Tool                                                   |
|-------------------|----------------------------------------------------------------------|
| LLM               | OpenAI GPT-4 Turbo                                                   |
| Embedding Model   | JHGAN/ko-sbert-multitask (KoSBERT)                                   |
| Vector Database   | ChromaDB (Cosine similarity search)                                  |
| Prompt Strategy   | ReAct pattern, advanced prompt engineering                           |
| Backend Server    | Python 3.10+, FastAPI, Docker                                        |
| Frontend          | HTML, CSS, JavaScript                                                |
| Deployment        | Hugging Face Spaces (demo), Localhost (development)                  |

---

## 🔗 How to Use

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/youth-rag-chatbot.git
   cd youth-rag-chatbot
2. Create a .env file and add your OpenAI API key:
   
4. Build and run the service with Docker:
  ```bash
   docker build -t youth-rag-agent.
   docker run -d -p 7860:7860 --env-file .env youth-rag-agent
```
## 🙋 Contact

**Byungseung Kong**  
Korea University, Dept. of Big Data Convergence  
Email: xncb135@korea.ac.kr

