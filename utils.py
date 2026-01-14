"""
Utility functions for working with scraped data.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import logging

import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_metadata() -> Optional[Dict]:
    """Load metadata file."""
    metadata_path = Path(config.METADATA_FILE)
    
    if not metadata_path.exists():
        logger.warning(f"Metadata file not found: {metadata_path}")
        return None
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_book(handle: str) -> Optional[Dict]:
    """Load a single book by handle."""
    book_path = Path(config.BOOKS_DIR) / f"{handle}.json"
    
    if not book_path.exists():
        logger.warning(f"Book not found: {handle}")
        return None
    
    with open(book_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_all_books() -> List[Dict]:
    """Load all scraped books."""
    books_dir = Path(config.BOOKS_DIR)
    books = []
    
    for book_file in books_dir.glob('*.json'):
        try:
            with open(book_file, 'r', encoding='utf-8') as f:
                books.append(json.load(f))
        except Exception as e:
            logger.error(f"Error loading {book_file}: {e}")
    
    return books


def search_books(query: str, field: str = 'title') -> List[Dict]:
    """Search books by field."""
    books = load_all_books()
    query_lower = query.lower()
    
    results = [
        book for book in books
        if query_lower in str(book.get(field, '')).lower()
    ]
    
    return results


def get_statistics() -> Dict:
    """Get statistics about scraped data."""
    metadata = load_metadata()
    books_dir = Path(config.BOOKS_DIR)
    images_dir = Path(config.IMAGES_DIR)
    
    stats = {
        'total_books': len(list(books_dir.glob('*.json'))),
        'total_images': len(list(images_dir.glob('*'))),
        'data_directory': str(Path(config.DATA_DIR).absolute()),
    }
    
    if metadata:
        stats['scraping_stats'] = metadata.get('statistics', {})
        stats['scraped_at'] = metadata.get('scraped_at', 'Unknown')
    
    return stats


def print_book_info(book: Dict):
    """Print formatted book information."""
    print("\n" + "=" * 60)
    print(f"Title: {book.get('title')}")
    print(f"Publisher: {book.get('vendor')}")
    print(f"Format: {book.get('product_type')}")
    
    variants = book.get('variants', [])
    if variants:
        variant = variants[0]
        print(f"ISBN: {variant.get('sku')}")
        print(f"Price: {variant.get('price')} EUR")
        if variant.get('compare_at_price'):
            print(f"Original Price: {variant.get('compare_at_price')} EUR")
    
    tags = book.get('tags', [])
    if tags:
        print(f"Tags: {', '.join(tags[:5])}" + ("..." if len(tags) > 5 else ""))
    
    metadata = book.get('_metadata', {})
    print(f"URL: {metadata.get('product_url', 'N/A')}")
    print("=" * 60)


def main():
    """CLI for exploring scraped data."""
    import sys
    
    stats = get_statistics()
    print("\n" + "=" * 60)
    print("Kirja.fi Scraper - Data Explorer")
    print("=" * 60)
    print(f"Total Books: {stats['total_books']}")
    print(f"Total Images: {stats['total_images']}")
    print(f"Data Directory: {stats['data_directory']}")
    
    if 'scraped_at' in stats:
        print(f"Last Scraped: {stats['scraped_at']}")
    
    if len(sys.argv) > 1:
        # Search mode
        query = ' '.join(sys.argv[1:])
        print(f"\nSearching for: '{query}'")
        
        results = search_books(query)
        print(f"Found {len(results)} results:\n")
        
        for book in results[:10]:  # Show first 10
            print(f"- {book.get('title')} ({book.get('vendor')})")
            variants = book.get('variants', [])
            if variants:
                print(f"  ISBN: {variants[0].get('sku')}")
        
        if len(results) > 10:
            print(f"\n... and {len(results) - 10} more results")
    else:
        print("\nUsage: python utils.py [search query]")
        print("Example: python utils.py 'Harry Potter'")


if __name__ == "__main__":
    main()
