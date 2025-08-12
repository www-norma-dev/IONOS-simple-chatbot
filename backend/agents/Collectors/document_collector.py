import os
import tempfile
import logging
from typing import Iterable, List, Optional

import requests
from fastapi import HTTPException

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    DirectoryLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter


logger = logging.getLogger("chatbot-server")


class DocumentCollector:
    """
    Collect text content from local files/directories and from direct file URLs.

    Supported extensions: .pdf, .docx, .txt
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}

    def __init__(self, chunk_size: int = 500, max_chunk_count: int = 256):
        self.chunk_size = chunk_size
        self.max_chunk_count = max_chunk_count

    async def collect_documents(self, sources: Iterable[str]) -> List[str]:
        """
        Collect and return text chunks from the given sources.

        A source can be a local file path, a directory path (will be scanned recursively),
        or a direct URL to a file (http/https).

        Args:
            sources: Iterable of paths or URLs

        Returns:
            List of text chunks

        Raises:
            HTTPException: If none of the sources can be processed
        """
        if not sources:
            return []

        aggregated_chunks: List[str] = []
        any_success = False

        for source in sources:
            source = source.strip()
            try:
                if self._is_url(source):
                    logger.info("Downloading document from URL: %s", source)
                    docs_texts = self._load_docs_from_url(source)
                else:
                    docs_texts = self._load_docs_from_path(source)

                if not docs_texts:
                    logger.warning("No text extracted from source: %s", source)
                    continue

                any_success = True
                aggregated_chunks.extend(self._split_and_chunk(docs_texts))

                if len(aggregated_chunks) >= self.max_chunk_count:
                    logger.info(
                        "Reached max chunk count (%d); truncating results",
                        self.max_chunk_count,
                    )
                    aggregated_chunks = aggregated_chunks[: self.max_chunk_count]
                    break
            except HTTPException:
                raise
            except Exception as exc:
                logger.error("Failed to process source %s: %s", source, exc)

        if not any_success and not aggregated_chunks:
            raise HTTPException(status_code=400, detail="No valid documents found in sources")

        logger.info("Collected %d chunks from %d source(s)", len(aggregated_chunks), len(list(sources)))
        return aggregated_chunks

    # -----------------------------
    # Helpers
    # -----------------------------
    @staticmethod
    def _is_url(value: str) -> bool:
        return value.lower().startswith(("http://", "https://"))

    def _extract_text_from_path(self, path: str) -> str:
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail=f"Path not found: {path}")

        if os.path.isdir(path):
            texts: List[str] = []
            for root, _dirs, files in os.walk(path):
                for filename in files:
                    if self._is_supported(filename):
                        file_path = os.path.join(root, filename)
                        file_text = self._extract_text_from_file(file_path)
                        if file_text:
                            texts.append(file_text)
            return "\n\n".join(texts)
        else:
            if not self._is_supported(path):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Unsupported file type for path: {path}. Supported: {sorted(self.SUPPORTED_EXTENSIONS)}"
                    ),
                )
            return self._extract_text_from_file(path)

    def _extract_text_from_url(self, url: str) -> str:
        # Stream download into a temporary file, then parse.
        response = requests.get(url, timeout=60)
        try:
            response.raise_for_status()
        except Exception as exc:  # requests.HTTPError
            raise HTTPException(status_code=500, detail=f"Failed to download {url}: {exc}")

        filename = self._infer_filename_from_url(url, response.headers.get("content-type"))
        if not self._is_supported(filename):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported file type from URL: {filename}. Supported: {sorted(self.SUPPORTED_EXTENSIONS)}"
                ),
            )

        suffix = os.path.splitext(filename)[1]
        with tempfile.NamedTemporaryFile(delete=True, suffix=suffix) as tmp:
            tmp.write(response.content)
            tmp.flush()
            return self._extract_text_from_file(tmp.name)

    def _extract_text_from_file(self, file_path: str) -> str:
        _, ext = os.path.splitext(file_path.lower())
        try:
            if ext == ".pdf":
                docs = PyPDFLoader(file_path).load()
            elif ext == ".docx":
                docs = Docx2txtLoader(file_path).load()
            elif ext == ".txt":
                docs = TextLoader(file_path, autodetect_encoding=True).load()
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to parse {file_path}: {exc}")

        return "\n".join([d.page_content for d in docs]).strip()

    # New: loader-based API returning list of raw texts before splitting
    def _load_docs_from_path(self, path: str) -> List[str]:
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail=f"Path not found: {path}")

        texts: List[str] = []
        if os.path.isdir(path):
            # Load supported files recursively
            for pattern in ("**/*.pdf", "**/*.docx", "**/*.txt"):
                try:
                    loader = DirectoryLoader(path, glob=pattern, show_progress=False)
                    docs = loader.load()
                    texts.extend([d.page_content for d in docs if d.page_content])
                except Exception as exc:
                    logger.warning("Directory loading failed for %s: %s", pattern, exc)
        else:
            texts.append(self._extract_text_from_file(path))
        return texts

    def _load_docs_from_url(self, url: str) -> List[str]:
        # Only handle direct file URLs for supported types
        lower = url.lower()
        if lower.endswith(".pdf") or lower.endswith(".docx") or lower.endswith(".txt"):
            content = self._extract_text_from_url(url)
            return [content] if content else []
        # Not a supported direct file URL
        return []

    def _split_and_chunk(self, raw_texts: List[str]) -> List[str]:
        # Combine texts into Documents, then split
        if not raw_texts:
            return []
        # Build pseudo documents for splitter
        # The text splitter operates on strings via create_documents
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=max(0, min(200, self.chunk_size // 10)),
        )
        documents = splitter.create_documents(raw_texts)
        # Now split again to ensure chunking constraints are respected per document
        split_docs = splitter.split_documents(documents)
        chunks = [d.page_content for d in split_docs if d.page_content and d.page_content.strip()]
        if len(chunks) > self.max_chunk_count:
            chunks = chunks[: self.max_chunk_count]
        return chunks

    def _chunk_text(self, text: str) -> List[str]:
        if not text:
            return []

        chunks: List[str] = []
        for i in range(0, len(text), self.chunk_size):
            chunk = text[i : i + self.chunk_size]
            if chunk.strip():
                chunks.append(chunk)
            if len(chunks) >= self.max_chunk_count:
                break
        return chunks

    def _is_supported(self, path_or_name: str) -> bool:
        _, ext = os.path.splitext(path_or_name.lower())
        return ext in self.SUPPORTED_EXTENSIONS

    @staticmethod
    def _infer_filename_from_url(url: str, content_type: Optional[str]) -> str:
        # Try to grab filename from URL path
        name = os.path.basename(url.split("?")[0].split("#")[0])
        if name and "." in name:
            return name
        # Fallback to content type
        if content_type:
            mapping = {
                "application/pdf": "download.pdf",
                "application/msword": "download.doc",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "download.docx",
                "text/plain": "download.txt",
            }
            return mapping.get(content_type.split(";")[0].strip(), "download.bin")
        return "download.bin"


