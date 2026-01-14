# Kirja.fi Books Database Scraper

A robust async Python scraper for collecting book data from kirja.fi, with advanced search tools.

## Features

### Scraper
- ✅ **Async I/O** for fast parallel downloads
- ✅ **Automatic retry logic** with exponential backoff
- ✅ **Parallelism control** to respect server limits
- ✅ **Downloads book cover images** automatically
- ✅ **Organized JSON storage** with ISBNs and metadata
- ✅ **Progress tracking** with batch updates every 10 products
- ✅ **Comprehensive error handling** and logging
- ✅ **Unicode support** for Finnish characters

### Search Tools
- 🔍 **Text Search** - Fast keyword search
- 🧠 **Semantic Search** - AI-powered search that understands meaning
- 🎯 **Advanced Filtering** - Filter by price, publisher, type, availability
- 📊 **Statistics** - Database analytics and insights
- 📝 **Markdown Reports** - Generate beautiful reports
- 🎨 **Cross-platform CLI** - Works on Windows, Linux, and macOS

See [search-tools/README.md](search-tools/README.md) for full search documentation.

## Quick Start

### Windows (PowerShell)
```powershell
# One-command setup and run
.\start.ps1
```

### Manual Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
```bash
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Windows CMD
venv\Scripts\activate.bat

# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Full Scrape (All ~6,591 Books)
```bash
python scraper.py
```

Estimated time: ~19 minutes

### Search Downloaded Books
```bash
python utils.py "search term"

# Examples:
python utils.py "Python"
python utils.py "Keltikangas"
```

### What the Scraper Does
1. Fetches all books from kirja.fi collections API
2. Downloads product details for each book
3. Downloads and saves cover images (named by ISBN)
4. Saves complete JSON data with metadata
5. Shows progress every 10 products (no hanging!)

## Output Structure

```
data/
├── books/                          # One JSON file per book
│   ├── hyvat-tyypit-9789510405666.json
│   ├── 90s-cuties-9789510527719.json
│   └── ... (6,591+ files)
├── images/                         # Cover images named by ISBN
│   ├── 9789510405666.jpg
│   ├── 9789510527719.jpg
│   └── ... (6,591+ images)
└── metadata.json                   # Scraping statistics and summary
```

### Book JSON Structure
Each book file contains:
- **id**: Shopify product ID
- **title**: Book title
- **handle**: URL slug (used as filename)
- **vendor**: Publisher name
- **product_type**: Binding type (Kovakantinen, Pehmeäkantinen, etc.)
- **tags**: Categories and subjects
- **variants**: SKU (ISBN), price, availability
- **images**: Cover image URLs
- **_metadata**: Fetch timestamp and URLs

## Configuration

Edit `config.py` to adjust:
- `MAX_CONCURRENT_REQUESTS = 5` - Parallel request limit
- `REQUEST_DELAY = 0.05` - Delay between requests (50ms)
- `MAX_RETRIES = 3` - Retry attempts for failed requests
- `REQUEST_TIMEOUT = 30` - HTTP timeout in seconds
- `DOWNLOAD_IMAGES = True` - Whether to download images

## Performance

- **Throughput**: ~5.7 products/second
- **Full scrape**: ~19 minutes for 6,591 books
- **Bottleneck**: Network latency (~137ms per API call)
- **Progress updates**: Every 10 products (20%, 40%, 60%...)

## Utilities

### Search Books
```python
from utils import search_books, load_all_books

# Search by title
results = search_books("kirja", field='title')
## Search Tools

For advanced searching and reporting, use the search tools:

```bash
cd search-tools

# Install search tool dependencies
pip install -r requirements.txt

# Search books
python search.py search "kirja"

# AI semantic search
python search.py semantic "books about Finnish history"

# Filter by criteria
python search.py filter --publisher WSOY --max-price 20

# View statistics
python search.py stats

# Generate reports
python search.py search "query" --output report.md
```

See [search-tools/README.md](search-tools/README.md) for complete documentation.

## Utilities

### Search Books
```python
from utils import search_books, load_all_books

# Search by title
results = search_books("kirja", field='title')

# Search by publisher
results = search_books("WSOY", field='vendor')

# Load all books
books = load_all_books()
```

### Load Specific Book
```python
from utils import load_book, print_book_info

book = load_book("hyvat-tyypit-9789510405666")
print_book_info(book)
```

## Investigation Report

See [kirja_fi_investigation_report.md](kirja_fi_investigation_report.md) for:
- Detailed API documentation
- Data structure analysis
- Implementation strategies
- Legal considerations

## Legal Notice

This scraper is for educational purposes. Please:
- Respect kirja.fi's terms of service
- Use reasonable rate limits
- Do not republish copyrighted content
- Attribute data to kirja.fi
