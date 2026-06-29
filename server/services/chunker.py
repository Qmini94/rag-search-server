import re
from pathlib import Path

CHUNK_LINES = 80
OVERLAP_LINES = 20

EXTENSION_LANGUAGE = {
    ".java": "java",
    ".vue": "vue",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".md": "markdown",
    ".py": "python",
    ".go": "go",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".json": "json",
    ".xml": "xml",
}


def detect_language(file_path: str) -> str | None:
    ext = Path(file_path).suffix.lower()
    return EXTENSION_LANGUAGE.get(ext)


def chunk_file(file_path: str) -> list[dict]:
    """파일을 청크로 분할. 반환: [{"content": str, "chunk_index": int}]"""
    path = Path(file_path)
    if not path.exists():
        return []

    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError):
        return []

    if not text.strip():
        return []

    language = detect_language(file_path)

    if language == "markdown":
        return _chunk_markdown(text)
    else:
        return _chunk_by_lines(text)


def _chunk_markdown(text: str) -> list[dict]:
    """Markdown: ## 헤딩 단위로 분할"""
    sections = re.split(r"(?=^## )", text, flags=re.MULTILINE)
    chunks = []

    for section in sections:
        section = section.strip()
        if not section:
            continue

        if len(section) > 2000:
            lines = section.split("\n")
            sub_chunks = _split_lines(lines)
            for sc in sub_chunks:
                chunks.append({"content": sc, "chunk_index": len(chunks)})
        else:
            chunks.append({"content": section, "chunk_index": len(chunks)})

    return chunks


def _chunk_by_lines(text: str) -> list[dict]:
    """고정 라인 기반: 80줄 청크, 20줄 오버랩"""
    lines = text.split("\n")
    return [
        {"content": chunk, "chunk_index": i}
        for i, chunk in enumerate(_split_lines(lines))
    ]


def _split_lines(lines: list[str]) -> list[str]:
    """라인 리스트를 CHUNK_LINES/OVERLAP_LINES 기반으로 분할"""
    if len(lines) <= CHUNK_LINES:
        return ["\n".join(lines)]

    chunks = []
    start = 0
    while start < len(lines):
        end = start + CHUNK_LINES
        chunk = "\n".join(lines[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start = end - OVERLAP_LINES

    return chunks
