from sentence_transformers import SentenceTransformer

from config import MODEL_NAME

_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_for_indexing(text: str) -> list[float]:
    """색인용 임베딩 (passage: 프리픽스)"""
    model = get_model()
    vector = model.encode("passage: " + text)
    return vector.tolist()


def embed_for_query(text: str) -> list[float]:
    """검색용 임베딩 (query: 프리픽스)"""
    model = get_model()
    vector = model.encode("query: " + text)
    return vector.tolist()
