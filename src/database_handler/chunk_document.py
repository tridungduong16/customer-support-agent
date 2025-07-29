import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Union

import numpy as np
from sentence_transformers import SentenceTransformer


class ChunkingStrategy(Protocol):
    """Protocol defining the interface for document chunking strategies."""

    def chunk_text(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """Chunk text according to the strategy.

        Args:
            text (str): The text to chunk
            chunk_size (int): Maximum size of each chunk
            chunk_overlap (int): Overlap between consecutive chunks

        Returns:
            List[str]: List of text chunks
        """
        ...


class SimpleChunkingStrategy:
    """Simple chunking strategy that splits text by character count."""

    def chunk_text(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """Chunk text by character count.

        Args:
            text (str): The text to chunk
            chunk_size (int): Maximum size of each chunk in characters
            chunk_overlap (int): Overlap between consecutive chunks in characters

        Returns:
            List[str]: List of text chunks
        """
        if not text:
            return []

        chunks = []
        text_length = len(text)
        start = 0

        while start < text_length:
            end = min(start + chunk_size, text_length)
            chunks.append(text[start:end])

            # Move start position considering overlap
            start = end - chunk_overlap if end < text_length else end

        return chunks


class ParagraphChunkingStrategy:
    """Chunking strategy that respects paragraph boundaries."""

    def chunk_text(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """Chunk text by paragraphs, trying to respect paragraph boundaries.

        Args:
            text (str): The text to chunk
            chunk_size (int): Target maximum size of each chunk
            chunk_overlap (int): Approximate overlap between chunks

        Returns:
            List[str]: List of text chunks
        """
        if not text:
            return []

        # Split text into paragraphs
        paragraphs = re.split(r"\n\s*\n", text)
        chunks = []
        current_chunk = ""

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # Check if adding this paragraph would exceed chunk size
            if current_chunk and len(current_chunk) + len(paragraph) + 2 > chunk_size:
                chunks.append(current_chunk.strip())

                # Create overlap by keeping the last paragraph
                current_chunk = paragraph
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n"
                current_chunk += paragraph

        # Add the last chunk if it has content
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks


class SentenceChunkingStrategy:
    """Chunking strategy that respects sentence boundaries."""

    def chunk_text(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """Chunk text by sentences, trying to respect sentence boundaries.

        Args:
            text (str): The text to chunk
            chunk_size (int): Target maximum size of each chunk
            chunk_overlap (int): Approximate overlap between chunks

        Returns:
            List[str]: List of text chunks
        """
        if not text:
            return []

        # Simple sentence splitting pattern
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            # Check if adding this sentence would exceed chunk size
            if current_chunk and len(current_chunk) + len(sentence) + 1 > chunk_size:
                chunks.append(current_chunk.strip())

                # Create overlap by including some words from the end
                words = current_chunk.split()
                overlap_word_count = min(len(words), max(1, chunk_overlap // 5))
                current_chunk = " ".join(words[-overlap_word_count:]) + " " + sentence
            else:
                # Add sentence to current chunk
                if current_chunk:
                    current_chunk += " "
                current_chunk += sentence

        # Add the last chunk if it has content
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks


class MarkdownChunkingStrategy:
    """Chunking strategy that respects Markdown structure."""

    def __init__(self):
        """Initialize with compiled regex patterns for better performance."""
        self.header_pattern = re.compile(r"(#{1,6}\s+.+?\n)")
        self.header_level_pattern = re.compile(r"(#+)")

    def chunk_text(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """Chunk Markdown text, trying to respect headers and sections.

        Args:
            text (str): The Markdown text to chunk
            chunk_size (int): Target maximum size of each chunk
            chunk_overlap (int): Approximate overlap between chunks

        Returns:
            List[str]: List of text chunks
        """
        if not text:
            return []

        # Split by headers
        sections = self.header_pattern.split(text)

        chunks = []
        current_chunk = ""
        current_headers = []

        for section in sections:
            if not section:
                continue

            # Check if this is a header
            if self.header_pattern.match(section):
                header_level = len(self.header_level_pattern.match(section).group(1))

                # Update current headers based on this header's level
                current_headers = [h for h in current_headers if h[0] < header_level]
                current_headers.append((header_level, section))

                # Check if adding this would exceed chunk size
                if current_chunk and len(current_chunk) + len(section) > chunk_size:
                    chunks.append(current_chunk.strip())
                    # Start new chunk with current headers for context
                    current_chunk = "".join(h[1] for h in current_headers)
                else:
                    current_chunk += section
            else:
                # This is content, not a header
                if current_chunk and len(current_chunk) + len(section) > chunk_size:
                    chunks.append(current_chunk.strip())
                    # Start new chunk with current headers for context
                    current_chunk = "".join(h[1] for h in current_headers) + section
                else:
                    current_chunk += section

        # Add the last chunk if it has content
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks


class SemanticChunkingStrategy:
    """Chunking strategy that uses sentence embeddings to create semantic chunks."""

    def __init__(
        self, model_name: str = "all-MiniLM-L6-v2", similarity_threshold: float = 0.75
    ):
        """
        Args:
            model_name (str): Name of the sentence transformer model.
            similarity_threshold (float): Min cosine similarity to continue chunking together.
        """
        self.model = SentenceTransformer(model_name)
        self.similarity_threshold = similarity_threshold

    def chunk_text(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        # Split text into sentences
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        if not sentences:
            return []

        # Compute embeddings
        embeddings = self.model.encode(sentences)

        chunks = []
        current_chunk = [sentences[0]]
        last_embedding = embeddings[0]

        for i in range(1, len(sentences)):
            sim = np.dot(last_embedding, embeddings[i]) / (
                np.linalg.norm(last_embedding) * np.linalg.norm(embeddings[i])
            )
            # If similarity is low, or chunk too long, start new chunk
            current_chunk_len = sum(len(s) for s in current_chunk)
            if (
                sim < self.similarity_threshold
                or current_chunk_len + len(sentences[i]) > chunk_size
            ):
                chunks.append(" ".join(current_chunk))
                # For overlap, keep the last sentence
                if chunk_overlap > 0 and current_chunk:
                    current_chunk = [current_chunk[-1], sentences[i]]
                else:
                    current_chunk = [sentences[i]]
            else:
                current_chunk.append(sentences[i])
            last_embedding = embeddings[i]

        if current_chunk:
            chunks.append(" ".join(current_chunk))
        return chunks


class ChunkDocument:
    """Class for chunking documents using different strategies."""

    def __init__(self, strategy: Optional[ChunkingStrategy] = None):
        """Initialize with a chunking strategy.

        Args:
            strategy (Optional[ChunkingStrategy]): The chunking strategy to use.
                Defaults to SimpleChunkingStrategy if None.
        """
        self.strategy = strategy or SimpleChunkingStrategy()

    def set_strategy(self, strategy: ChunkingStrategy) -> None:
        """Change the chunking strategy.

        Args:
            strategy (ChunkingStrategy): The new chunking strategy to use
        """
        self.strategy = strategy

    def chunk_text(
        self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> List[str]:
        """Chunk text using the current strategy.

        Args:
            text (str): The text to chunk
            chunk_size (int): Maximum size of each chunk
            chunk_overlap (int): Overlap between consecutive chunks

        Returns:
            List[str]: List of text chunks
        """
        if not text:
            logging.warning("Empty text provided for chunking")
            return []

        return self.strategy.chunk_text(text, chunk_size, chunk_overlap)

    def chunk_document(
        self,
        document: Dict[str, Any],
        text_key: str = "text",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> List[Dict[str, Any]]:
        """Chunk a document dictionary and preserve metadata.

        Args:
            document (Dict[str, Any]): Document with text and metadata
            text_key (str): Key in document that contains the text to chunk
            chunk_size (int): Maximum size of each chunk
            chunk_overlap (int): Overlap between consecutive chunks

        Returns:
            List[Dict[str, Any]]: List of document chunks with metadata
        """
        if text_key not in document:
            logging.error(f"Document does not contain key '{text_key}'")
            return []

        text = document[text_key]
        chunks = self.chunk_text(text, chunk_size, chunk_overlap)

        if not chunks:
            return []

        # Create document chunks with metadata
        total_chunks = len(chunks)
        document_chunks = []

        for i, chunk in enumerate(chunks):
            # Create a copy of the original document
            doc_chunk = document.copy()
            # Replace the text with the chunk
            doc_chunk[text_key] = chunk
            # Add chunking metadata
            doc_chunk["chunk_index"] = i
            doc_chunk["total_chunks"] = total_chunks

            document_chunks.append(doc_chunk)

        return document_chunks
