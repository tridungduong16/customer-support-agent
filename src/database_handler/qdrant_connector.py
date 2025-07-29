import hashlib
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import boto3
from qdrant_client import QdrantClient as QClient
from qdrant_client.http.models import Distance, PointIdsList, VectorParams

from src.app_config import app_config

from .chunk_document import (ChunkDocument,  # adjust import as needed
                             SemanticChunkingStrategy,
                             SentenceChunkingStrategy, SimpleChunkingStrategy)
from .document_parser import DocumentParser
from .embedding_handler import EmbeddingHandler
from .search_handler import SearchHandler


class QdrantDBClient:
    def __init__(self, collection_name: str):
        """Initialize Qdrant client with all necessary components.

        Args:
            collection_name (str): Name of the Qdrant collection to use
        """
        self.collection_name = collection_name
        self.vector_size = 768
        self.client = None
        self.embedding_handler = EmbeddingHandler()
        self.document_parser = DocumentParser()
        self.search_handler = SearchHandler(self.embedding_handler)
        semantic_strategy = SemanticChunkingStrategy(
            model_name="all-MiniLM-L6-v2", similarity_threshold=0.75
        )
        # sentence_strategy = SentenceChunkingStrategy()
        simple_strategy = SimpleChunkingStrategy()
        self.chunker = ChunkDocument(strategy=simple_strategy)

    def connect_to_database(self) -> bool:
        """Establish connection to Qdrant database.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.client = QClient(
                url=app_config.QDRANT_URL,
                api_key=app_config.QDRANT_API_KEY,
                prefer_grpc=False,
            )
            logging.info("✅ Qdrant connection established")
            return True
        except Exception as e:
            logging.error(f"❌ Qdrant connection error: {e}")
            self.client = None
            return False

    def create_collection(self, collection_name: Optional[str] = None) -> bool:
        """Create a new collection in Qdrant.

        Args:
            collection_name (Optional[str]): Name of collection to create

        Returns:
            bool: True if creation successful, False otherwise
        """
        if not self.client:
            logging.error("❌ No Qdrant connection")
            return False

        try:
            collection = collection_name or self.collection_name
            self.client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(
                    size=self.vector_size, distance=Distance.COSINE
                ),
            )
            logging.info(f"✅ Collection '{collection}' created successfully")
            return True
        except Exception as e:
            logging.error(f"❌ Error creating collection: {e}")
            return False

    def insert_vectors(
        self, points: List[Dict[str, Any]], collection_name: Optional[str] = None
    ) -> bool:
        """Insert vectors into Qdrant collection.

        Args:
            points (List[Dict[str, Any]]): Points to insert
            collection_name (Optional[str]): Target collection name

        Returns:
            bool: True if insertion successful, False otherwise
        """
        if not self.client:
            logging.error("❌ No Qdrant connection")
            return False

        try:
            collection = collection_name or self.collection_name
            self.client.upsert(collection_name=collection, points=points)
            logging.info(f"✅ Successfully inserted {len(points)} vectors")
            return True
        except Exception as e:
            logging.error(f"❌ Error inserting vectors: {e}")
            return False

    def search_vectors(
        self,
        query_vector: List[float],
        limit: int = 10,
        collection_name: Optional[str] = None,
        score_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors in collection.

        Args:
            query_vector (List[float]): Vector to search for
            limit (int): Maximum number of results
            collection_name (Optional[str]): Target collection name
            score_threshold (Optional[float]): Minimum similarity score

        Returns:
            List[Dict[str, Any]]: Search results
        """
        if not self.client:
            logging.error("❌ No Qdrant connection")
            return []

        try:
            collection = collection_name or self.collection_name
            search_params = {}
            if score_threshold is not None:
                search_params["score_threshold"] = score_threshold

            results = self.client.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=limit,
                **search_params,
            )

            return [
                {"id": result.id, "score": result.score, "payload": result.payload}
                for result in results
            ]

        except Exception as e:
            logging.error(f"❌ Error searching vectors: {e}")
            return []

    def delete_vectors(
        self, point_ids: List[int], collection_name: Optional[str] = None
    ) -> bool:
        """Delete vectors from collection.

        Args:
            point_ids (List[int]): IDs of points to delete
            collection_name (Optional[str]): Target collection name

        Returns:
            bool: True if deletion successful, False otherwise
        """
        if not self.client:
            logging.error("❌ No Qdrant connection")
            return False

        try:
            collection = collection_name or self.collection_name
            self.client.delete(
                collection_name=collection,
                points_selector=PointIdsList(points=point_ids),
            )
            logging.info(f"✅ Successfully deleted {len(point_ids)} vectors")
            return True
        except Exception as e:
            logging.error(f"❌ Error deleting vectors: {e}")
            return False

    def upload_pdf_file_to_s3(self, md_path: str) -> str:
        today = datetime.now().strftime("%Y/%m/%d")
        md_name = os.path.basename(md_path)
        pdf_name = md_name.replace(".md", ".pdf")
        pdf_path = os.path.join("./data/input_brochure", pdf_name)
        # import pdb; pdb.set_trace()
        object_key = f"uploads/{today}/{pdf_name}"
        s3 = boto3.client(
            "s3",
            aws_access_key_id=app_config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=app_config.AWS_SECRET_ACCESS_KEY,
            region_name=app_config.AWS_REGION,
        )
        s3.upload_file(
            pdf_path,
            app_config.AWS_BUCKET_NAME,
            object_key,
        )
        url = f"https://{app_config.AWS_BUCKET_NAME}.s3.{app_config.AWS_REGION}.amazonaws.com/{object_key}"
        return url

    def get_collection_info(
        self, collection_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get information about a collection.

        Args:
            collection_name (Optional[str]): Target collection name

        Returns:
            Dict[str, Any]: Collection information
        """
        if not self.client:
            logging.error("❌ No Qdrant connection")
            return {}

        try:
            collection = collection_name or self.collection_name
            info = self.client.get_collection(collection_name=collection)
            return {
                "name": info.name,
                "vector_size": info.vectors_config.size,
                "distance": info.vectors_config.distance,
                "points_count": info.points_count,
            }
        except Exception as e:
            logging.error(f"❌ Error getting collection info: {e}")
            return {}

    def save_text_to_qdrant(
        self,
        id: int,
        text: str,
        metadata: dict = {},
        collection_name: Optional[str] = None,
    ) -> bool:
        """Save text document to Qdrant.

        Args:
            id (int): Document ID
            text (str): Text content
            metadata (dict): Additional metadata
            collection_name (Optional[str]): Target collection name

        Returns:
            bool: True if save successful, False otherwise
        """
        vector = self.embedding_handler.get_embedding(text)
        return self.insert_vectors(
            [{"id": id, "vector": vector, "payload": {"text": text, **metadata}}],
            collection_name,
        )

    def search_similar_texts(self, query: str, limit: int = 7) -> List[Dict[str, Any]]:
        """Search for similar texts and rerank results.

        Args:
            query (str): Search query
            limit (int): Maximum number of results

        Returns:
            List[Dict[str, Any]]: Reranked search results
        """
        query_vector = self.embedding_handler.get_embedding(query)
        results = self.search_vectors(query_vector=query_vector, limit=limit)
        return self.search_handler.search_and_rerank(query, results)

    def batch_search_similar_texts(
        self, query_list: List[str], limit: int = 5, topk: int = 3
    ) -> List[List[Dict[str, Any]]]:
        """Batch search for similar texts and rerank results.

        Args:
            query_list (List[str]): List of search queries
            limit (int): Maximum number of results per query
            topk (int): Number of top results to keep after reranking

        Returns:
            List[List[Dict[str, Any]]]: Reranked search results for each query
        """
        query_vectors = self.embedding_handler.get_batch_embeddings(query_list)
        batch_results = []

        for query_vector in query_vectors:
            results = self.search_vectors(query_vector=query_vector, limit=limit)
            batch_results.append(results)

        return self.search_handler.batch_search_and_rerank(
            query_list, batch_results, topk
        )

    def close_connection(self):
        """Close the connection to Qdrant."""
        if self.client:
            self.client.close()
            self.client = None
            logging.info("🔒 Qdrant connection closed")
        else:
            logging.info("ℹ️ No active Qdrant connection to close")

    def __del__(self):
        """Destructor to ensure connection is closed."""
        self.close_connection()

    def read_markdown_file_in_a_directory_convert_to_point(
        self, directory_path: str, chunk_size: int = 5000, chunk_overlap: int = 200
    ) -> List[Dict]:
        """Read markdown files from a directory and convert to points with chunking.

        Args:
            directory_path (str): Path to directory containing markdown files
            chunk_size (int): Maximum size of each text chunk
            chunk_overlap (int): Overlap between consecutive chunks

        Returns:
            List[Dict]: List of points ready for vector database insertion
        """
        points = []
        for filename in os.listdir(directory_path):
            if not filename.endswith(".md"):
                print("Skipping file: ", filename)
                continue
            filename_url = self.upload_pdf_file_to_s3(filename)
            print("Embedding file: ", filename)
            print("File name url: ", filename_url)
            # import pdb; pdb.set_trace()
            if filename.endswith(".md"):
                file_path = os.path.join(directory_path, filename)
                content = self.document_parser.read_markdown_file(file_path)
                if not content:
                    continue
                chunks = self.chunker.chunk_text(
                    content, chunk_size=1024, chunk_overlap=100
                )
                for i, chunk in enumerate(chunks):
                    print(chunk)
                    print("--------------------------------")
                    chunk_id = self.generate_doc_id(f"{filename}_chunk_{i}")
                    points.append(
                        {
                            "id": chunk_id,
                            "vector": None,
                            "payload": {
                                "text": chunk,
                                "filename": filename,
                                "file_path": filename_url,
                                "source_type": "pdf",
                                "chunk_index": i,
                                "total_chunks": len(chunks),
                            },
                        }
                    )
            # import pdb; pdb.set_trace()
        return points

    def insert_markdown_directory(
        self, directory_path: str, collection_name: Optional[str] = None
    ) -> bool:
        try:
            points = self.read_markdown_file_in_a_directory_convert_to_point(
                directory_path
            )
            success = True
            for point in points:
                if not self.save_text_to_qdrant(
                    id=point["id"],
                    text=point["payload"]["text"],
                    metadata={
                        "filename": point["payload"]["filename"],
                        "file_path": point["payload"]["file_path"],
                        "source_type": "markdown",
                    },
                    collection_name=collection_name,
                ):
                    success = False
                else:
                    print(
                        f"Successfully inserted document: {point['payload']['filename']}"
                    )
            return success
        except Exception as e:
            logging.error(f"Error processing markdown directory: {e}")
            return False

    def generate_doc_id(self, filename: str, row_index: Optional[int] = None) -> int:
        """Generate a document ID from filename hash."""
        identifier = filename
        if row_index is not None:
            identifier += f"_row_{row_index}"
        hash_object = hashlib.md5(identifier.encode())
        return int(hash_object.hexdigest(), 16) % 1000000

    def delete_collection(self, collection_name: Optional[str] = None) -> bool:
        """Delete a collection from Qdrant."""
        if not self.client:
            logging.error("❌ No Qdrant connection")
            return False
        try:
            self.client.delete_collection(collection_name=collection_name)
            logging.info(f"✅ Collection '{collection_name}' deleted successfully")
            return True
        except Exception as e:
            logging.error(f"❌ Error deleting collection: {e}")
            return False
