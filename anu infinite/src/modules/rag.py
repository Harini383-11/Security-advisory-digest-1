"""
Retrieval Augmented Generation (RAG) Module using ChromaDB.

Stores advisory embeddings and enables semantic search.
"""

import chromadb
from typing import List, Dict, Optional
from loguru import logger
import json

from config.settings import CHROMA_COLLECTION_NAME, VECTOR_DB_PATH


class RAGEngine:
    """ChromaDB-based RAG system for advisories."""

    def __init__(self, collection_name: str = CHROMA_COLLECTION_NAME):
        """Initialize RAG engine with ChromaDB client."""
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
        self.collection = None
        self._init_collection()

    def _init_collection(self) -> None:
        """Initialize or retrieve ChromaDB collection."""
        try:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Initialized ChromaDB collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB collection: {e}")
            raise

    def add_advisory(self, advisory_id: str, advisory_data: Dict) -> bool:
        """
        Add advisory to vector database.

        Args:
            advisory_id: Unique advisory ID
            advisory_data: Advisory information dictionary

        Returns:
            Success status
        """
        try:
            # Create document text from advisory data
            doc_text = f"""
            CVE: {advisory_data.get('cve_id', '')}
            Title: {advisory_data.get('title', '')}
            Description: {advisory_data.get('description', '')}
            Severity: {advisory_data.get('severity', '')}
            Vendor: {advisory_data.get('vendor', '')}
            Product: {advisory_data.get('product', '')}
            """

            self.collection.add(
                ids=[advisory_id],
                documents=[doc_text],
                metadatas=[{
                    "cve_id": advisory_data.get("cve_id", ""),
                    "severity": advisory_data.get("severity", ""),
                    "vendor": advisory_data.get("vendor", ""),
                    "product": advisory_data.get("product", ""),
                    "source": advisory_data.get("source_feed", "")
                }]
            )
            logger.debug(f"Added advisory {advisory_id} to vector DB")
            return True
        except Exception as e:
            logger.error(f"Error adding advisory to vector DB: {e}")
            return False

    def add_advisories_batch(self, advisories: List[Dict]) -> int:
        """
        Add multiple advisories to vector database.

        Args:
            advisories: List of advisory dictionaries

        Returns:
            Number of successfully added advisories
        """
        logger.info(f"Adding {len(advisories)} advisories to vector DB")

        added_count = 0
        ids = []
        documents = []
        metadatas = []

        for advisory in advisories:
            try:
                advisory_id = advisory.get("id") or advisory.get("advisory_id")
                if not advisory_id:
                    continue

                doc_text = f"""
                CVE: {advisory.get('cve_id', '')}
                Title: {advisory.get('title', '')}
                Description: {advisory.get('description', '')}
                Severity: {advisory.get('severity', '')}
                Vendor: {advisory.get('vendor', '')}
                Product: {advisory.get('product', '')}
                """

                ids.append(str(advisory_id))
                documents.append(doc_text)
                metadatas.append({
                    "cve_id": advisory.get("cve_id", ""),
                    "severity": advisory.get("severity", ""),
                    "vendor": advisory.get("vendor", ""),
                    "product": advisory.get("product", ""),
                    "source": advisory.get("source_feed", "")
                })
                added_count += 1

            except Exception as e:
                logger.error(f"Error processing advisory: {e}")

        if ids:
            try:
                self.collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
                logger.info(f"Batch added {added_count} advisories to vector DB")
            except Exception as e:
                logger.error(f"Error in batch add: {e}")

        return added_count

    def search_vectors(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search for relevant advisories using semantic similarity.

        Args:
            query: Search query text
            top_k: Number of results to return

        Returns:
            List of relevant advisories
        """
        try:
            logger.debug(f"Searching vectors for: {query}")

            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )

            if not results or not results["ids"] or not results["ids"][0]:
                logger.debug("No results found for query")
                return []

            # Format results
            formatted_results = []
            for i, doc_id in enumerate(results["ids"][0]):
                result = {
                    "id": doc_id,
                    "document": results["documents"][0][i] if results["documents"] else "",
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {}
                }
                formatted_results.append(result)

            logger.debug(f"Found {len(formatted_results)} relevant advisories")
            return formatted_results

        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            return []

    def search_by_metadata(self, metadata_filter: Dict, top_k: int = 5) -> List[Dict]:
        """
        Search advisories by metadata filters.

        Args:
            metadata_filter: Filter criteria (e.g., {"severity": "Critical"})
            top_k: Number of results

        Returns:
            List of matching advisories
        """
        try:
            logger.debug(f"Searching by metadata filter: {metadata_filter}")

            results = self.collection.get(
                where=metadata_filter,
                limit=top_k
            )

            formatted_results = []
            for i, doc_id in enumerate(results["ids"]):
                result = {
                    "id": doc_id,
                    "document": results["documents"][i] if results["documents"] else "",
                    "metadata": results["metadatas"][i] if results["metadatas"] else {}
                }
                formatted_results.append(result)

            logger.debug(f"Found {len(formatted_results)} advisories by metadata")
            return formatted_results

        except Exception as e:
            logger.error(f"Error searching by metadata: {e}")
            return []

    def search_product_advisories(self, product: str, top_k: int = 20) -> List[Dict]:
        """
        Search for advisories related to a product.

        Args:
            product: Product name
            top_k: Number of results

        Returns:
            List of relevant advisories
        """
        logger.info(f"Searching advisories for product: {product}")

        # Semantic search
        semantic_results = self.search_vectors(product, top_k=top_k)

        # Metadata search
        try:
            metadata_results = self.search_by_metadata(
                {"product": {"$contains": product}},
                top_k=top_k
            )
            results = semantic_results + metadata_results

            # Remove duplicates
            seen_ids = set()
            unique_results = []
            for result in results:
                if result["id"] not in seen_ids:
                    seen_ids.add(result["id"])
                    unique_results.append(result)

            return unique_results[:top_k]
        except:
            return semantic_results

    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection."""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "vector_db_path": VECTOR_DB_PATH
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}

    def clear_collection(self) -> bool:
        """Clear all documents from collection."""
        try:
            logger.warning("Clearing ChromaDB collection")
            self.client.delete_collection(name=self.collection_name)
            self._init_collection()
            return True
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            return False

    def delete_advisory(self, advisory_id: str) -> bool:
        """Delete specific advisory from vector DB."""
        try:
            self.collection.delete(ids=[advisory_id])
            logger.debug(f"Deleted advisory {advisory_id} from vector DB")
            return True
        except Exception as e:
            logger.error(f"Error deleting advisory: {e}")
            return False
