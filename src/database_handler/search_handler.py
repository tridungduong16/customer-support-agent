import logging
from typing import Any, Dict, List

from flashrank import Ranker, RerankRequest

from .embedding_handler import EmbeddingHandler


class SearchHandler:
    def __init__(self, embedding_handler: EmbeddingHandler):
        """Initialize search handler with embedding handler and reranker.

        Args:
            embedding_handler (EmbeddingHandler): Handler for generating embeddings
        """
        self.embedding_handler = embedding_handler
        self.reranker = Ranker(model_name="rank-T5-flan", cache_dir="./models")

    def search_and_rerank(
        self, query: str, search_results: List[Dict[str, Any]], topk: int = 6
    ) -> List[Dict[str, Any]]:
        """Search and rerank results for a single query.

        Args:
            query (str): Search query
            search_results (List[Dict[str, Any]]): Initial search results
            topk (int): Number of top results to return

        Returns:
            List[Dict[str, Any]]: Reranked results
        """
        if not search_results:
            return []

        passages = [
            {
                "id": str(doc["id"]),
                "text": doc["payload"]["text"],
                "meta": {k: v for k, v in doc["payload"].items() if k != "text"},
            }
            for doc in search_results
        ]

        rerank_request = RerankRequest(query=query, passages=passages)
        reranked = self.reranker.rerank(rerank_request)
        reranked = reranked[:topk]

        return [
            {
                "score": item.get("score"),
                "id": item.get("id"),
                "text": item.get("text"),
                "payload": item.get("meta", {}),
            }
            for item in reranked
        ]

    def batch_search_and_rerank(
        self,
        query_list: List[str],
        batch_results: List[List[Dict[str, Any]]],
        topk: int = 3,
    ) -> List[List[Dict[str, Any]]]:
        """Batch search and rerank for multiple queries.

        Args:
            query_list (List[str]): List of search queries
            batch_results (List[List[Dict[str, Any]]]): Initial search results for each query
            topk (int): Number of top results to return per query

        Returns:
            List[List[Dict[str, Any]]]: Reranked results for each query
        """
        final_results = []

        for query, results in zip(query_list, batch_results):
            if not results:
                final_results.append([])
                continue

            # Filter invalid documents
            valid_docs = [
                doc
                for doc in results
                if doc.payload.get("description", "N/A") != "N/A"
                and "Fail to scrape description"
                not in doc.payload.get("description", "")
            ]

            if not valid_docs:
                final_results.append([])
                continue

            query_results = self.search_and_rerank(query, valid_docs, topk)
            final_results.append(query_results)

        return final_results
