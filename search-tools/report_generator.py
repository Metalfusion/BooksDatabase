"""
Markdown Report Generator for Book Database
Creates formatted markdown reports with search results and statistics.
"""

import re
import sys
from typing import List, Dict, Optional
from datetime import datetime

# Fix unicode output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


class ReportGenerator:
    """Generate markdown reports from search results."""
    
    def __init__(self):
        """Initialize report generator."""
        self.report_lines = []
    
    def _clean_html(self, html: str) -> str:
        """Remove HTML tags from text."""
        clean = re.sub('<[^<]+?>', '', html)
        # Clean up multiple spaces and newlines
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean
    
    def add_header(self, title: str, level: int = 1):
        """Add a markdown header."""
        self.report_lines.append(f"{'#' * level} {title}\n")
    
    def add_text(self, text: str):
        """Add plain text."""
        self.report_lines.append(f"{text}\n")
    
    def add_horizontal_rule(self):
        """Add a horizontal rule."""
        self.report_lines.append("---\n")
    
    def generate_book_card(self, book: Dict, show_description: bool = True, 
                          similarity: Optional[float] = None) -> str:
        """
        Generate a markdown card for a single book with emphasis on content.
        
        Args:
            book: Book data dictionary
            show_description: Whether to include the description
            similarity: Optional similarity score for semantic search
        """
        variants = book.get('variants', [])
        variant = variants[0] if variants else {}
        
        title = book.get('title', 'Unknown Title')
        isbn = variant.get('sku', 'N/A')
        price = variant.get('price', 'N/A')
        publisher = book.get('vendor', 'Unknown')
        ptype = book.get('product_type', 'Unknown')
        available = variant.get('available', False)
        url = book.get('_metadata', {}).get('product_url', '#')
        
        card = []
        card.append(f"### {title}")
        
        if similarity is not None:
            card.append(f"**Relevance:** {similarity*100:.1f}%  ")
        
        # Tags first (what the book is about)
        tags = book.get('tags', [])
        if tags:
            # Filter out technical tags
            content_tags = [t for t in tags if not any(x in t.lower() for x in 
                          ['primary', 'new', 'final', '2024', '2025', '2026', 'ale', 'blackfriday'])]
            if content_tags:
                tag_str = ', '.join([f'`{tag}`' for tag in content_tags[:10]])
                if len(content_tags) > 10:
                    tag_str += f' (+{len(content_tags)-10} more)'
                card.append(f"**Topics:** {tag_str}  ")
        
        # Description (what it's about)
        if show_description:
            desc = book.get('body_html', '')
            if desc:
                desc_clean = self._clean_html(desc)
                # Show more of description (primary content)
                if len(desc_clean) > 500:
                    desc_clean = desc_clean[:500] + '...'
                card.append(f"\n{desc_clean}\n")
        
        # Technical details at bottom
        card.append(f"**Price:** {price} EUR | **Publisher:** {publisher} | **Type:** {ptype}  ")
        card.append(f"**ISBN:** {isbn} | **Available:** {'✓ Yes' if available else '✗ No'}  ")
        
        # Link
        card.append(f"\n[View on kirja.fi]({url})\n")
        
        return '\n'.join(card)
    
    def generate_search_report(
        self,
        results: List[Dict],
        query: str,
        search_type: str = "text",
        similarity_scores: Optional[List[float]] = None
    ) -> str:
        """
        Generate a complete search results report.
        
        Args:
            results: List of book dictionaries
            query: The search query
            search_type: Type of search performed
            similarity_scores: Optional similarity scores for semantic search
        """
        self.report_lines = []
        
        # Header
        self.add_header(f"Book Search Results: '{query}'")
        self.add_text(f"**Search Type:** {search_type.title()}")
        self.add_text(f"**Results:** {len(results)} books found")
        self.add_text(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.add_horizontal_rule()
        
        if not results:
            self.add_text("*No books found matching your query.*")
            return '\n'.join(self.report_lines)
        
        # Results
        for i, book in enumerate(results, 1):
            similarity = similarity_scores[i-1] if similarity_scores else None
            card = self.generate_book_card(book, show_description=True, similarity=similarity)
            self.add_text(card)
            if i < len(results):
                self.add_horizontal_rule()
        
        return '\n'.join(self.report_lines)
    
    def generate_statistics_report(self, stats: Dict) -> str:
        """Generate a statistics report."""
        self.report_lines = []
        
        self.add_header("Book Database Statistics")
        self.add_text(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.add_horizontal_rule()
        
        # Overview
        self.add_header("Overview", 2)
        self.add_text(f"- **Total Books:** {stats['total_books']}")
        self.add_text(f"- **Available Books:** {stats['available_books']}")
        self.add_text("")
        
        # Price statistics
        self.add_header("Price Statistics", 2)
        price_stats = stats['price_stats']
        self.add_text(f"- **Minimum Price:** {price_stats['min']:.2f} EUR")
        self.add_text(f"- **Maximum Price:** {price_stats['max']:.2f} EUR")
        self.add_text(f"- **Average Price:** {price_stats['avg']:.2f} EUR")
        self.add_text(f"- **Median Price:** {price_stats['median']:.2f} EUR")
        self.add_text("")
        
        # Publishers
        self.add_header("Top Publishers", 2)
        publishers = list(stats['publishers'].items())[:10]
        for publisher, count in publishers:
            self.add_text(f"- **{publisher}:** {count} books")
        self.add_text("")
        
        # Product types
        self.add_header("Product Types", 2)
        for ptype, count in stats['product_types'].items():
            self.add_text(f"- **{ptype}:** {count} books")
        self.add_text("")
        
        return '\n'.join(self.report_lines)
    
    def generate_comparison_report(self, books: List[Dict]) -> str:
        """Generate a comparison report for multiple books."""
        self.report_lines = []
        
        self.add_header("Book Comparison")
        self.add_text(f"**Books Compared:** {len(books)}")
        self.add_text(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.add_horizontal_rule()
        
        # Create comparison table
        headers = ["Title", "ISBN", "Price (EUR)", "Publisher", "Type", "Available"]
        rows = []
        
        for book in books:
            variants = book.get('variants', [])
            variant = variants[0] if variants else {}
            
            row = [
                book.get('title', 'N/A')[:40],
                variant.get('sku', 'N/A'),
                variant.get('price', 'N/A'),
                book.get('vendor', 'N/A'),
                book.get('product_type', 'N/A'),
                '✓' if variant.get('available', False) else '✗'
            ]
            rows.append(row)
        
        # Manual table formatting (simple markdown)
        self.add_text("| " + " | ".join(headers) + " |")
        self.add_text("|" + "|".join(["---" for _ in headers]) + "|")
        
        for row in rows:
            self.add_text("| " + " | ".join(str(cell) for cell in row) + " |")
        
        self.add_text("")
        
        # Detailed cards
        self.add_header("Detailed Information", 2)
        for i, book in enumerate(books, 1):
            card = self.generate_book_card(book, show_description=True)
            self.add_text(card)
            if i < len(books):
                self.add_horizontal_rule()
        
        return '\n'.join(self.report_lines)
    
    def save_report(self, content: str, filename: str):
        """Save report to a markdown file."""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Report saved to: {filename}")
