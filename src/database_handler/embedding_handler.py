import logging
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingHandler:
    def __init__(self, model_name: str = "nomic-ai/nomic-embed-text-v1.5"):
        """Initialize the embedding handler with a specific model.

        Args:
            model_name (str): Name of the sentence transformer model to use
        """
        self.model = SentenceTransformer(
            model_name, trust_remote_code=True, cache_folder="./models"
        )

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text.

        Args:
            text (str): Text to embed

        Returns:
            List[float]: Embedding vector
        """
        try:
            return self.model.encode(text).tolist()
        except Exception as e:
            logging.error(f"❌ Error generating embedding: {e}")
            raise

    def get_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts in batch.

        Args:
            texts (List[str]): List of texts to embed

        Returns:
            List[List[float]]: List of embedding vectors
        """
        try:
            embeddings = self.model.encode(texts)
            if isinstance(embeddings, np.ndarray):
                return embeddings.tolist()
            return embeddings
        except Exception as e:
            logging.error(f"❌ Batch embedding error: {e}")
            raise
