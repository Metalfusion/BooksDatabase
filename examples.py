"""
Example usage of the scraper and utilities.
"""

import asyncio
import json
from pathlib import Path


def example_1_view_metadata():
    """Example 1: View scraping metadata."""
    print("\n" + "=" * 60)
    print("Example 1: View Scraping Metadata")
    print("=" * 60)
    
    from utils import load_metadata
    
    metadata = load_metadata()
    if metadata:
        print(f"Scraped at: {metadata.get('scraped_at')}")
        print(f"Total products: {metadata.get('total_products')}")
        
        stats = metadata.get('statistics', {})
        print(f"\nStatistics:")
        print(f"  Books fetched: {stats.get('books_fetched', 0)}")
        print(f"  Images downloaded: {stats.get('images_downloaded', 0)}")
        print(f"  Errors: {stats.get('errors', 0)}")
    else:
        print("No metadata found. Run scraper first.")


def example_2_load_book():
    """Example 2: Load and display a specific book."""
    print("\n" + "=" * 60)
    print("Example 2: Load Specific Book")
    print("=" * 60)
    
    from utils import load_book, print_book_info
    
    # Load the first book we scraped
    book = load_book("hyvat-tyypit-9789510405666")
    
    if book:
        print_book_info(book)
    else:
        print("Book not found.")


def example_3_search_books():
    """Example 3: Search for books."""
    print("\n" + "=" * 60)
    print("Example 3: Search Books")
    print("=" * 60)
    
    from utils import search_books
    
    # Search by title
    results = search_books("kirja", field='title')
    print(f"Found {len(results)} books with 'kirja' in title:")
    
    for book in results[:5]:
        print(f"  - {book.get('title')}")


def example_4_extract_isbns():
    """Example 4: Extract all ISBNs."""
    print("\n" + "=" * 60)
    print("Example 4: Extract All ISBNs")
    print("=" * 60)
    
    from utils import load_all_books
    
    books = load_all_books()
    isbns = []
    
    for book in books:
        variants = book.get('variants', [])
        if variants:
            isbn = variants[0].get('sku', '')
            if isbn:
                isbns.append(isbn)
    
    print(f"Found {len(isbns)} ISBNs:")
    for isbn in isbns[:10]:
        print(f"  - {isbn}")
    
    if len(isbns) > 10:
        print(f"  ... and {len(isbns) - 10} more")


def example_5_price_analysis():
    """Example 5: Analyze pricing."""
    print("\n" + "=" * 60)
    print("Example 5: Price Analysis")
    print("=" * 60)
    
    from utils import load_all_books
    
    books = load_all_books()
    prices = []
    discounted = 0
    
    for book in books:
        variants = book.get('variants', [])
        if variants:
            variant = variants[0]
            try:
                price = float(variant.get('price', 0))
                compare_price = variant.get('compare_at_price')
                
                prices.append(price)
                
                if compare_price:
                    compare_price = float(compare_price)
                    if compare_price > price:
                        discounted += 1
            except (ValueError, TypeError):
                pass
    
    if prices:
        avg_price = sum(prices) / len(prices)
        print(f"Total books analyzed: {len(prices)}")
        print(f"Average price: {avg_price:.2f} EUR")
        print(f"Min price: {min(prices):.2f} EUR")
        print(f"Max price: {max(prices):.2f} EUR")
        print(f"Books with discount: {discounted}")


async def example_6_scrape_specific_collection():
    """Example 6: Scrape a specific collection."""
    print("\n" + "=" * 60)
    print("Example 6: Scrape Specific Collection")
    print("=" * 60)
    
    from scraper import KirjaFiScraper
    import config
    
    print("This would scrape a specific collection like 'uutuuskirjat'")
    print("Modify scraper.py fetch_all_products() to use:")
    print("  url = f'{config.BASE_URL}/collections/uutuuskirjat/products.json'")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print(" " * 20 + "KIRJA.FI SCRAPER - USAGE EXAMPLES")
    print("=" * 80)
    
    # Run examples that don't require scraped data
    # (assuming test_scraper.py was run)
    
    try:
        example_1_view_metadata()
        example_2_load_book()
        example_3_search_books()
        example_4_extract_isbns()
        example_5_price_analysis()
        example_6_scrape_specific_collection()
        
        print("\n" + "=" * 80)
        print("Examples completed!")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        print("Make sure you've run test_scraper.py first to generate sample data.")


if __name__ == "__main__":
    main()
