"""Document processing module for loading and chunking files (PDF, TXT, CSV)."""

import tempfile
from pathlib import Path
from typing import BinaryIO, ClassVar

from langchain_community.document_loaders import CSVLoader, PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentProcessor:
    """Handles loading documents from disk or upload and chunking them for vector storage."""

    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = {".pdf", ".txt", ".csv"}

    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None):
        """
        Initialize the processor and character text splitter.
        Uses values from config.py if not explicitly provided.
        """
        settings = get_settings()
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

        # Text splitter to break large documents into manageable overlapping pieces
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )
        logger.info(f"DocumentProcessor ready: chunk_size={self.chunk_size}, chunk_overlap={self.chunk_overlap}")

    def load_file(self, file_path: str | Path) -> list[Document]:
        """
        Load a file (PDF, TXT, or CSV) based on its file extension.
        """
        path = Path(file_path)
        ext = path.suffix.lower()

        logger.info(f"Loading document: {path.name}")

        if ext == ".pdf":
            loader = PyPDFLoader(str(path))
        elif ext == ".csv":
            loader = CSVLoader(str(path), encoding="utf-8")
        elif ext == ".txt":
            loader = TextLoader(str(path), encoding="utf-8")
        else:
            formats = ", ".join(self.SUPPORTED_EXTENSIONS)
            raise ValueError(f"Unsupported format '{ext}'. Supported formats: {formats}")

        documents = loader.load()
        logger.info(f"Successfully loaded {len(documents)} page(s)/record(s) from {path.name}")
        return documents

    def load_from_upload(self, file: BinaryIO, filename: str) -> list[Document]:
        """
        Save an uploaded in-memory file stream to a temporary file, load it,
        and attach the original filename to the document metadata.
        """
        ext = Path(filename).suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            formats = ", ".join(self.SUPPORTED_EXTENSIONS)
            raise ValueError(f"Unsupported format '{ext}'. Supported formats: {formats}")

        # Write uploaded bytes to a temporary file so LangChain loaders can read it
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(file.read())
            tmp_path = Path(tmp.name)

        try:
            documents = self.load_file(tmp_path)
            # Replace temporary path in metadata with the actual uploaded filename
            for doc in documents:
                doc.metadata["source"] = filename
            return documents
        finally:
            # Always clean up the temporary file
            tmp_path.unlink(missing_ok=True)

    def split_documents(self, documents: list[Document]) -> list[Document]:
        """
        Split a list of Document objects into smaller chunks.
        """
        logger.info(f"Splitting {len(documents)} document(s) into chunks...")
        chunks = self.text_splitter.split_documents(documents)
        logger.info(f"Generated {len(chunks)} chunk(s).")
        return chunks

    def process_file(self, file_path: str | Path) -> list[Document]:
        """Convenience method: Load and chunk a file from disk in one call."""
        return self.split_documents(self.load_file(file_path))

    def process_upload(self, file: BinaryIO, filename: str) -> list[Document]:
        """Convenience method: Load and chunk an uploaded file stream in one call."""
        return self.split_documents(self.load_from_upload(file, filename))
