import os
from typing import Iterable, List

from fastapi import HTTPException
from langchain_community.document_loaders import DirectoryLoader, Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentCollector:
    """Minimal local-only document collector for .pdf, .docx, .txt."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}

    def __init__(self, chunk_size: int = 500, max_chunk_count: int = 256):
        self.chunk_size = chunk_size
        self.max_chunk_count = max_chunk_count

    async def collect_documents(self, sources: Iterable[str]) -> List[str]:
        if not sources:
            return []

        texts: List[str] = []
        for src in map(str.strip, sources):
            if not os.path.exists(src):
                raise HTTPException(status_code=404, detail=f"Path not found: {src}")
            if os.path.isdir(src):
                for pattern in ("**/*.pdf", "**/*.docx", "**/*.txt"):
                    for d in DirectoryLoader(src, glob=pattern, show_progress=False).load():
                        if d.page_content:
                            texts.append(d.page_content)
            else:
                ext = os.path.splitext(src.lower())[1]
                if ext not in self.SUPPORTED_EXTENSIONS:
                    raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
                loader = PyPDFLoader(src) if ext == ".pdf" else Docx2txtLoader(src) if ext == ".docx" else TextLoader(src, autodetect_encoding=True)
                docs = loader.load()
                texts.extend(d.page_content for d in docs if d.page_content)

        if not texts:
            raise HTTPException(status_code=400, detail="No valid documents found in sources")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=max(0, min(200, self.chunk_size // 10)),
        )
        split_docs = splitter.split_documents(splitter.create_documents(texts))
        chunks = [d.page_content for d in split_docs if d.page_content and d.page_content.strip()]
        return chunks[: self.max_chunk_count] if len(chunks) > self.max_chunk_count else chunks


