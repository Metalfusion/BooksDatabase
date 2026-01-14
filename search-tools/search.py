#!/usr/bin/env python3
"""
Book Database Search CLI
Cross-platform command-line interface for searching the book database.
"""

import sys
from pathlib import Path

# Fix unicode output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import click
from colorama import init, Fore, Style
from tabulate import tabulate

from searcher import BookSearcher
from report_generator import ReportGenerator

# Initialize colorama for Windows color support
init(autoreset=True)


def print_success(msg):
    """Print success message in green."""
    click.echo(Fore.GREEN + msg + Style.RESET_ALL)


def print_error(msg):
    """Print error message in red."""
    click.echo(Fore.RED + msg + Style.RESET_ALL)


def print_info(msg):
    """Print info message in blue."""
    click.echo(Fore.BLUE + msg + Style.RESET_ALL)


def print_warning(msg):
    """Print warning message in yellow."""
    click.echo(Fore.YELLOW + msg + Style.RESET_ALL)


def format_book_table(books, limit=None):
    """Format books as a table for terminal output."""
    if limit and len(books) > limit:
        books = books[:limit]
    
    headers = ["Title", "ISBN", "Price", "Publisher", "Available"]
    rows = []
    
    for book in books:
        variants = book.get('variants', [])
        variant = variants[0] if variants else {}
        
        title = book.get('title', 'N/A')
        if len(title) > 40:
            title = title[:37] + '...'
        
        row = [
            title,
            variant.get('sku', 'N/A'),
            f"{variant.get('price', 'N/A')} EUR",
            book.get('vendor', 'N/A'),
            Fore.GREEN + '✓' + Style.RESET_ALL if variant.get('available', False) 
                else Fore.RED + '✗' + Style.RESET_ALL
        ]
        rows.append(row)
    
    return tabulate(rows, headers=headers, tablefmt='grid')


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """
    📚 Book Database Search Tool
    
    Advanced search and reporting for the kirja.fi book database.
    """
    pass


@cli.command()
@click.argument('query')
@click.option('--fields', '-f', multiple=True, help='Specific fields to search (advanced)')
@click.option('--output', '-o', type=click.Path(), help='Save results to markdown file')
@click.option('--limit', '-l', type=int, default=20, help='Limit number of results displayed')
@click.option('--simple', is_flag=True, help='Use simple search instead of smart ranking')
def search(query, fields, output, limit, simple):
    """
    Search for books by content (description, topics, title).
    
    Intelligently ranks results by relevance to find books you'll be interested in.
    
    Example: search "self-help mental health"
    """
    print_info(f"🔍 Searching for: '{query}'")
    
    searcher = BookSearcher()
    
    if simple or fields:
        # Use simple text search if requested or fields specified
        field_list = list(fields) if fields else None
        results = searcher.text_search(query, fields=field_list)
        results_display = [(book, None) for book in results]
    else:
        # Use smart search with ranking
        results_display = searcher.smart_search(query, limit=100)
    
    if not results_display:
        print_warning(f"No results found for '{query}'")
        return
    
    print_success(f"✓ Found {len(results_display)} books")
    print()
    
    # Display results with match reasons
    headers = ["Title", "Match Reason", "Price", "Type"]
    rows = []
    
    for book, reason in results_display[:limit]:
        variants = book.get('variants', [])
        variant = variants[0] if variants else {}
        
        title = book.get('title', 'N/A')
        if len(title) > 35:
            title = title[:32] + '...'
        
        match_info = reason if reason else "—"
        if len(match_info) > 40:
            match_info = match_info[:37] + '...'
        
        row = [
            title,
            Fore.CYAN + match_info + Style.RESET_ALL,
            f"{variant.get('price', 'N/A')} EUR",
            book.get('product_type', 'N/A')[:15]
        ]
        rows.append(row)
    
    print(tabulate(rows, headers=headers, tablefmt='grid'))
    
    if len(results_display) > limit:
        print_warning(f"\n⚠ Showing top {limit} of {len(results_display)} results")
        print_info(f"💡 Use --limit to show more or --output to save all results")
    
    if output:
        # Extract just books for report
        books = [book for book, _ in results_display]
        generator = ReportGenerator()
        report = generator.generate_search_report(books, query, search_type="smart content search")
        generator.save_report(report, output)


@cli.command()
@click.argument('isbn')
@click.option('--output', '-o', type=click.Path(), help='Save result to markdown file')
def isbn(isbn, output):
    """
    Search for a book by ISBN.
    
    Example: isbn 9789510405666
    """
    print_info(f"🔍 Searching for ISBN: {isbn}")
    
    searcher = BookSearcher()
    result = searcher.isbn_search(isbn)
    
    if not result:
        print_error(f"✗ No book found with ISBN: {isbn}")
        return
    
    print_success("✓ Book found!")
    print()
    
    details = searcher.get_book_details(result)
    
    # Print details
    print(Fore.CYAN + Style.BRIGHT + details['title'])
    print(Style.RESET_ALL)
    print(f"ISBN:      {details['isbn']}")
    print(f"Price:     {details['price']} EUR")
    print(f"Publisher: {details['publisher']}")
    print(f"Type:      {details['type']}")
    print(f"Available: {Fore.GREEN + '✓ Yes' if details['available'] else Fore.RED + '✗ No'}")
    print(f"URL:       {details['url']}")
    
    if output:
        generator = ReportGenerator()
        report = generator.generate_search_report([result], isbn, search_type="isbn")
        generator.save_report(report, output)


@cli.command()
@click.argument('query')
@click.option('--top-k', '-k', type=int, default=10, help='Number of results to return')
@click.option('--threshold', '-t', type=float, default=0.3, help='Minimum similarity threshold (0-1)')
@click.option('--output', '-o', type=click.Path(), help='Save results to markdown file')
def semantic(query, top_k, threshold, output):
    """
    Semantic search using AI embeddings (understands meaning).
    
    Example: semantic "books about Finnish history" --top-k 5
    """
    print_info(f"🧠 Semantic search for: '{query}'")
    print_info("This may take a moment on first run...")
    
    searcher = BookSearcher()
    
    try:
        results = searcher.semantic_search(query, top_k=top_k)
    except Exception as e:
        print_error(f"✗ Semantic search failed: {e}")
        return
    
    # Filter by threshold
    filtered_results = [(book, score) for book, score in results if score >= threshold]
    
    if not filtered_results:
        print_warning(f"No results above similarity threshold {threshold}")
        return
    
    print_success(f"✓ Found {len(filtered_results)} relevant books")
    print()
    
    # Display results with similarity scores
    headers = ["Similarity", "Title", "ISBN", "Publisher"]
    rows = []
    
    for book, score in filtered_results:
        variants = book.get('variants', [])
        variant = variants[0] if variants else {}
        
        title = book.get('title', 'N/A')
        if len(title) > 50:
            title = title[:47] + '...'
        
        # Color code by similarity
        similarity_str = f"{score*100:.1f}%"
        if score > 0.7:
            similarity_str = Fore.GREEN + similarity_str + Style.RESET_ALL
        elif score > 0.5:
            similarity_str = Fore.YELLOW + similarity_str + Style.RESET_ALL
        else:
            similarity_str = Fore.CYAN + similarity_str + Style.RESET_ALL
        
        row = [
            similarity_str,
            title,
            variant.get('sku', 'N/A'),
            book.get('vendor', 'N/A')
        ]
        rows.append(row)
    
    print(tabulate(rows, headers=headers, tablefmt='grid'))
    
    if output:
        books = [book for book, _ in filtered_results]
        scores = [score for _, score in filtered_results]
        generator = ReportGenerator()
        report = generator.generate_search_report(books, query, search_type="semantic", 
                                                 similarity_scores=scores)
        generator.save_report(report, output)


@cli.command()
@click.option('--min-price', type=float, help='Minimum price')
@click.option('--max-price', type=float, help='Maximum price')
@click.option('--publisher', '-p', help='Publisher name')
@click.option('--type', '-t', 'ptype', help='Product type (e.g., Kovakantinen)')
@click.option('--available', is_flag=True, help='Only show available books')
@click.option('--tag', multiple=True, help='Required tags')
@click.option('--output', '-o', type=click.Path(), help='Save results to markdown file')
@click.option('--limit', '-l', type=int, default=50, help='Limit number of results displayed')
def filter(min_price, max_price, publisher, ptype, available, tag, output, limit):
    """
    Filter books by various criteria.
    
    Example: filter --min-price 10 --max-price 30 --publisher WSOY --available
    """
    print_info("🔎 Filtering books...")
    
    searcher = BookSearcher()
    results = searcher.filter_books(
        min_price=min_price,
        max_price=max_price,
        publisher=publisher,
        product_type=ptype,
        available_only=available,
        tags=list(tag) if tag else None
    )
    
    if not results:
        print_warning("No books match the specified filters")
        return
    
    print_success(f"✓ Found {len(results)} books matching filters")
    
    # Show active filters
    filters = []
    if min_price:
        filters.append(f"min price: {min_price} EUR")
    if max_price:
        filters.append(f"max price: {max_price} EUR")
    if publisher:
        filters.append(f"publisher: {publisher}")
    if ptype:
        filters.append(f"type: {ptype}")
    if available:
        filters.append("available only")
    if tag:
        filters.append(f"tags: {', '.join(tag)}")
    
    if filters:
        print(Fore.CYAN + "Active filters: " + ", ".join(filters))
    
    print()
    print(format_book_table(results, limit=limit))
    
    if len(results) > limit:
        print_warning(f"\n⚠ Showing first {limit} of {len(results)} results")
    
    if output:
        generator = ReportGenerator()
        filter_desc = ", ".join(filters)
        report = generator.generate_search_report(results, filter_desc, search_type="filter")
        generator.save_report(report, output)


@cli.command()
@click.option('--output', '-o', type=click.Path(), help='Save statistics to markdown file')
def stats(output):
    """
    Show database statistics.
    
    Example: stats --output statistics.md
    """
    print_info("📊 Generating statistics...")
    
    searcher = BookSearcher()
    statistics = searcher.get_statistics()
    
    print_success(f"✓ Database Statistics\n")
    
    # Overview
    print(Fore.CYAN + Style.BRIGHT + "Overview:")
    print(Style.RESET_ALL + f"  Total books:     {statistics['total_books']}")
    print(f"  Available books: {statistics['available_books']}")
    print()
    
    # Price stats
    price_stats = statistics['price_stats']
    print(Fore.CYAN + Style.BRIGHT + "Price Statistics:")
    print(Style.RESET_ALL + f"  Minimum:  {price_stats['min']:.2f} EUR")
    print(f"  Maximum:  {price_stats['max']:.2f} EUR")
    print(f"  Average:  {price_stats['avg']:.2f} EUR")
    print(f"  Median:   {price_stats['median']:.2f} EUR")
    print()
    
    # Top publishers
    print(Fore.CYAN + Style.BRIGHT + "Top 10 Publishers:")
    publishers = list(statistics['publishers'].items())[:10]
    for publisher, count in publishers:
        print(Style.RESET_ALL + f"  {publisher:.<40} {count:>4} books")
    print()
    
    # Product types
    print(Fore.CYAN + Style.BRIGHT + "Product Types:")
    for ptype, count in statistics['product_types'].items():
        print(Style.RESET_ALL + f"  {ptype:.<40} {count:>4} books")
    
    if output:
        generator = ReportGenerator()
        report = generator.generate_statistics_report(statistics)
        generator.save_report(report, output)


@cli.command()
@click.argument('isbns', nargs=-1, required=True)
@click.option('--output', '-o', type=click.Path(), help='Save comparison to markdown file')
def compare(isbns, output):
    """
    Compare multiple books side by side.
    
    Example: compare 9789510405666 9789510527719 9789510508701
    """
    print_info(f"📊 Comparing {len(isbns)} books...")
    
    searcher = BookSearcher()
    books = []
    
    for isbn in isbns:
        book = searcher.isbn_search(isbn)
        if book:
            books.append(book)
        else:
            print_warning(f"⚠ ISBN not found: {isbn}")
    
    if not books:
        print_error("✗ No books found to compare")
        return
    
    if len(books) < len(isbns):
        print_warning(f"⚠ Only found {len(books)} of {len(isbns)} books")
    
    print()
    print(format_book_table(books))
    
    if output:
        generator = ReportGenerator()
        report = generator.generate_comparison_report(books)
        generator.save_report(report, output)


if __name__ == '__main__':
    cli()
