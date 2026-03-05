"""
Knowledge Base Tool - Search FAQ and policies

Uses simple keyword search (in production, use RAG from Project 1!)
"""

from typing import List, Dict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class KnowledgeBaseTool:
    """Search knowledge base for answers"""

    def __init__(self, kb_path: str = 'data/knowledge_base'):
        """Load knowledge base"""
        self.kb_path = Path(kb_path)
        self.documents = self._load_documents()
        logger.info(f"Loaded {len(self.documents)} knowledge base documents")

    def _load_documents(self) -> List[Dict]:
        """Load all .txt files from knowledge base"""
        documents = []

        if not self.kb_path.exists():
            logger.warning(f"Knowledge base path not found: {self.kb_path}")
            return documents

        for file_path in self.kb_path.glob('*.txt'):
            with open(file_path, 'r') as f:
                content = f.read()

            # Split into Q&A pairs
            sections = content.split('\n\n')
            for section in sections:
                if section.strip():
                    documents.append({
                        'content': section,
                        'source': file_path.name
                    })

        return documents

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Search knowledge base

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of matching documents
        """
        logger.info(f"Searching knowledge base for: {query}")

        # Simple keyword matching (in production, use embeddings!)
        query_lower = query.lower()
        query_words = set(query_lower.split())

        # Score each document
        scored_docs = []
        for doc in self.documents:
            content_lower = doc['content'].lower()
            content_words = set(content_lower.split())

            # Count matching words
            matches = len(query_words & content_words)

            if matches > 0:
                scored_docs.append({
                    'score': matches,
                    'content': doc['content'],
                    'source': doc['source']
                })

        # Sort by score
        scored_docs.sort(key=lambda x: x['score'], reverse=True)

        results = scored_docs[:top_k]
        logger.info(f"Found {len(results)} matches")

        return results

    def format_results(self, results: List[Dict]) -> str:
        """Format search results for agent"""
        if not results:
            return "No relevant information found in knowledge base."

        formatted = ["## Knowledge Base Results\n"]

        for i, result in enumerate(results, 1):
            formatted.append(f"### Result {i} (Score: {result['score']})")
            formatted.append(result['content'])
            formatted.append(f"*Source: {result['source']}*\n")

        return "\n".join(formatted)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    kb = KnowledgeBaseTool()

    # Test searches
    queries = [
        "return policy",
        "how long shipping",
        "payment methods",
    ]

    for query in queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        results = kb.search(query)
        print(kb.format_results(results))
