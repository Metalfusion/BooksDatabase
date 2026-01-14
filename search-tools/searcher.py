"""
Book Database Search Engine
Provides various search capabilities including semantic search.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import re

# Fix unicode output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


class BookSearcher:
    """Advanced book search engine with multiple search strategies."""
    
    def __init__(self, data_dir: str = "../data"):
        """Initialize the searcher with the data directory."""
        self.data_dir = Path(data_dir)
        self.books_dir = self.data_dir / "books"
        self.books_cache = None
        self.embeddings = None
        self.embedding_model = None
        
    def load_books(self) -> List[Dict]:
        """Load all books from JSON files."""
        if self.books_cache is not None:
            return self.books_cache
            
        books = []
        for json_file in self.books_dir.glob("*.json"):
            try:
                with open(json_file, encoding='utf-8') as f:
                    book = json.load(f)
                    books.append(book)
            except Exception as e:
                print(f"Error loading {json_file.name}: {e}", file=sys.stderr)
        
        self.books_cache = books
        return books
    
    def text_search(self, query: str, fields: Optional[List[str]] = None) -> List[Dict]:
        """
        Content-focused search across book descriptions and topics.
        
        Args:
            query: Search query string
            fields: List of fields to search in (default: body_html, tags, title)
        """
        if fields is None:
            # Prioritize content: description first, then tags, then title
            fields = ['body_html', 'tags', 'title']
        
        books = self.load_books()
        query_lower = query.lower()
        results = []
        
        for book in books:
            for field in fields:
                value = book.get(field, '')
                
                # Handle different field types
                if isinstance(value, str):
                    if query_lower in value.lower():
                        results.append(book)
                        break
                elif isinstance(value, list):
                    if any(query_lower in str(item).lower() for item in value):
                        results.append(book)
                        break
        
        return results
    
    def smart_search(self, query: str, limit: int = 50) -> List[tuple[Dict, str]]:
        """
        Smart content search that ranks results by relevance.
        Returns books with reason why they matched.
        
        Args:
            query: Search query
            limit: Maximum results to return
        """
        books = self.load_books()
        query_lower = query.lower()
        query_words = query_lower.split()
        
        results_with_scores = []
        
        for book in books:
            score = 0
            match_reasons = []
            
            # Check description (highest weight)
            desc = book.get('body_html', '') or ''
            desc_lower = desc.lower()
            desc_matches = sum(1 for word in query_words if word in desc_lower)
            if desc_matches > 0:
                score += desc_matches * 10
                # Extract relevant snippet
                desc_clean = re.sub('<[^<]+?>', '', desc).strip()
                match_reasons.append('description')
            
            # Check tags (medium weight)
            tags = book.get('tags', [])
            tags_lower = [t.lower() for t in tags]
            tag_matches = sum(1 for word in query_words 
                            for tag in tags_lower if word in tag)
            if tag_matches > 0:
                score += tag_matches * 5
                matching_tags = [t for t in tags for word in query_words if word in t.lower()]
                match_reasons.append(f"tags: {', '.join(matching_tags[:3])}")
            
            # Check title (lower weight)
            title = book.get('title', '').lower()
            title_matches = sum(1 for word in query_words if word in title)
            if title_matches > 0:
                score += title_matches * 3
                match_reasons.append('title')
            
            if score > 0:
                reason = ' | '.join(match_reasons)
                results_with_scores.append((book, score, reason))
        
        # Sort by score descending
        results_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top results with reasons
        return [(book, reason) for book, score, reason in results_with_scores[:limit]]
    
    def isbn_search(self, isbn: str) -> Optional[Dict]:
        """Search for a book by ISBN."""
        isbn_clean = isbn.replace('-', '').replace(' ', '')
        books = self.load_books()
        
        for book in books:
            variants = book.get('variants', [])
            if variants:
                book_isbn = variants[0].get('sku', '')
                if book_isbn == isbn_clean:
                    return book
        
        return None
    
    def filter_books(
        self,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        publisher: Optional[str] = None,
        product_type: Optional[str] = None,
        available_only: bool = False,
        tags: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Filter books by various criteria.
        
        Args:
            min_price: Minimum price filter
            max_price: Maximum price filter
            publisher: Publisher name (vendor)
            product_type: Type of book (Kovakantinen, Pehmeäkantinen, etc.)
            available_only: Only show available books
            tags: List of tags that book must have
        """
        books = self.load_books()
        results = []
        
        for book in books:
            # Price filter
            if min_price or max_price:
                variants = book.get('variants', [])
                if not variants:
                    continue
                
                try:
                    price = float(variants[0].get('price', 0))
                    if min_price and price < min_price:
                        continue
                    if max_price and price > max_price:
                        continue
                except (ValueError, TypeError):
                    continue
            
            # Publisher filter
            if publisher:
                if publisher.lower() not in book.get('vendor', '').lower():
                    continue
            
            # Product type filter
            if product_type:
                if product_type.lower() not in book.get('product_type', '').lower():
                    continue
            
            # Availability filter
            if available_only:
                variants = book.get('variants', [])
                if not variants or not variants[0].get('available', False):
                    continue
            
            # Tags filter
            if tags:
                book_tags = [t.lower() for t in book.get('tags', [])]
                if not all(tag.lower() in book_tags for tag in tags):
                    continue
            
            results.append(book)
        
        return results
    
    def semantic_search(self, query: str, top_k: int = 10) -> List[Tuple[Dict, float]]:
        """
        Semantic search using sentence embeddings.
        
        Args:
            query: Natural language query
            top_k: Number of results to return
        
        Returns:
            List of (book, similarity_score) tuples
        """
        try:
            from sentence_transformers import SentenceTransformer
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
        except ImportError:
            print("Error: Semantic search requires sentence-transformers and scikit-learn")
            print("Install with: pip install -r requirements.txt")
            return []
        
        # Load or initialize model
        if self.embedding_model is None:
            print("Loading semantic search model (first time may take a moment)...")
            self.embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        books = self.load_books()
        
        # Create embeddings if not cached
        if self.embeddings is None:
            print("Creating embeddings for books...")
            book_texts = []
            for book in books:
                # Prioritize description and tags for content-based search
                title = book.get('title', '')
                desc = book.get('body_html', '')
                # Remove HTML tags
                desc_clean = re.sub('<[^<]+?>', '', desc)
                tags = book.get('tags', [])
                
                # Weight: description (most important), tags, then title
                # Include description twice for higher weight
                tag_text = ' '.join(tags)
                text = f"{desc_clean} {tag_text} {title}"
                book_texts.append(text)
            
            self.embeddings = self.embedding_model.encode(book_texts, show_progress_bar=True)
        
        # Encode query
        query_embedding = self.embedding_model.encode([query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Get top-k results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = [(books[i], float(similarities[i])) for i in top_indices]
        return results
    
    def get_statistics(self) -> Dict:
        """Get statistics about the book database."""
        books = self.load_books()
        
        prices = []
        publishers = {}
        types = {}
        available_count = 0
        
        for book in books:
            # Price stats
            variants = book.get('variants', [])
            if variants:
                try:
                    price = float(variants[0].get('price', 0))
                    if price > 0:
                        prices.append(price)
                except (ValueError, TypeError):
                    pass
                
                if variants[0].get('available', False):
                    available_count += 1
            
            # Publisher stats
            vendor = book.get('vendor', 'Unknown')
            publishers[vendor] = publishers.get(vendor, 0) + 1
            
            # Type stats
            ptype = book.get('product_type', 'Unknown')
            types[ptype] = types.get(ptype, 0) + 1
        
        stats = {
            'total_books': len(books),
            'available_books': available_count,
            'price_stats': {
                'min': min(prices) if prices else 0,
                'max': max(prices) if prices else 0,
                'avg': sum(prices) / len(prices) if prices else 0,
                'median': sorted(prices)[len(prices)//2] if prices else 0
            },
            'publishers': dict(sorted(publishers.items(), key=lambda x: x[1], reverse=True)),
            'product_types': dict(sorted(types.items(), key=lambda x: x[1], reverse=True))
        }
        
        return stats
    
    def get_book_details(self, book: Dict) -> Dict:
        """Extract key details from a book."""
        variants = book.get('variants', [])
        variant = variants[0] if variants else {}
        
        return {
            'title': book.get('title', 'N/A'),
            'isbn': variant.get('sku', 'N/A'),
            'price': variant.get('price', 'N/A'),
            'publisher': book.get('vendor', 'N/A'),
            'type': book.get('product_type', 'N/A'),
            'available': variant.get('available', False),
            'tags': book.get('tags', []),
            'description': book.get('body_html', ''),
            'url': book.get('_metadata', {}).get('product_url', 'N/A'),
            'images': book.get('images', [])
        }
