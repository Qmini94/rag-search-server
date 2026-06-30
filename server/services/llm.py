from openai import OpenAI
from config import VLLM_BASE_URL, VLLM_MODEL

_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(base_url=VLLM_BASE_URL, api_key="not-needed")
    return _client


SYSTEM_PROMPT = """당신은 Q-CMS 솔루션 전문 도우미입니다.
아래 제공된 문서를 기반으로 Q-CMS 관련 질문에 답변하세요.

규칙:
- 제공된 문서에 있는 정보만 사용하세요.
- 문서에 없는 내용은 "해당 정보는 문서에서 찾을 수 없습니다"라고 답하세요.
- 코드 예시가 있으면 포함하세요.
- 한국어로 답변하세요."""


def ask_llm(question: str, context: str) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model=VLLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"## 참고 문서\n\n{context}\n\n## 질문\n\n{question}",
            },
        ],
        temperature=0.3,
        max_tokens=2048,
    )
    return response.choices[0].message.content
