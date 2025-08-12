import os
from itertools import chain
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
        srcs = list(map(str.strip, sources or []))
        missing = next(iter(filter(lambda s: not os.path.exists(s), srcs)), None)
        (missing is None) or (_ for _ in ()).throw(HTTPException(status_code=404, detail=f"Path not found: {missing}"))

        patterns = ("**/*.pdf", "**/*.docx", "**/*.txt")
        dir_docs = lambda s: chain.from_iterable(map(lambda p: DirectoryLoader(s, glob=p, show_progress=False).load(), patterns))
        file_docs = lambda s: {
            ".pdf": PyPDFLoader,
            ".docx": Docx2txtLoader,
            ".txt": lambda p: TextLoader(p, autodetect_encoding=True),
        }.get(
            os.path.splitext(s.lower())[1],
            lambda _p: (_ for _ in ()).throw(HTTPException(status_code=400, detail=f"Unsupported file type: {os.path.splitext(s.lower())[1]}")),
        )(s).load()

        all_docs = chain.from_iterable(map(lambda s: {True: dir_docs, False: file_docs}[os.path.isdir(s)](s), srcs))
        docs = list(filter(lambda d: getattr(d, "page_content", None) and d.page_content.strip(), all_docs))

        splitter = RecursiveCharacterTextSplitter(chunk_size=self.chunk_size, chunk_overlap=max(0, min(200, self.chunk_size // 10)))
        chunks = splitter.split_documents(docs)
        return [d.page_content for d in chunks][: self.max_chunk_count]


