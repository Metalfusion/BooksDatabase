# Book Database Search Tools

Advanced **content-focused** search and reporting tools for the kirja.fi book database.

## Philosophy

**Search by what books are ABOUT, not just metadata.**

This tool prioritizes:
1. **Book descriptions** - What the book is actually about
2. **Topics and tags** - Subject matter and categories  
3. **Title** - The book's name

Technical details (publisher, ISBN, price) are shown but not used for matching, so you find books that interest you based on their content.

## Features

- 🔍 **Smart Text Search** - Ranks results by relevance to content
- 🧠 **Semantic Search** - AI-powered search that understands meaning (using multilingual embeddings)
- 🎯 **Advanced Filtering** - Filter by price, publisher, type, availability, and tags
- 📊 **Statistics** - Database analytics and insights
- 📝 **Markdown Reports** - Generate beautiful content-focused reports
- 🎨 **Colorized CLI** - Cross-platform colored terminal output
- 🔢 **ISBN Lookup** - Quick lookup by ISBN
- ⚖️ **Compare Books** - Side-by-side comparison

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note:** First-time semantic search will download a ~420MB AI model (happens automatically).

### 2. Verify Installation

```bash
python search.py --help
```

## Usage

### Smart Content Search (Recommended)

The default search intelligently ranks books by how well they match your query:

```bash
# Find books about Finnish history
python search.py search "historia Suomi"

# Self-help and personal growth
python search.py search "hyvinvointi mieli kasvu"

# Family and parenting
python search.py search "lapset perhe kasvatus"

# Save results to markdown report
python search.py search "historia" --output history-books.md
```

**How it works:** Searches book descriptions and topics, shows why each book matched ("description | tags: Historia"), ranks by relevance.

### Semantic Search (AI-Powered)

Understands the meaning of your query, not just keywords:

```bash
# Natural language query
python search.py semantic "books about Finnish winter war"

# Get top 5 most relevant results
python search.py semantic "self-help and personal growth" --top-k 5

# Set minimum similarity threshold
python search.py semantic "programming" --threshold 0.5

# Save results
python search.py semantic "children's books" --output kids.md
```

### ISBN Lookup

Find a specific book by ISBN:

```bash
python search.py isbn 9789510405666

# Save book details
python search.py isbn 9789510405666 --output book-details.md
```

### Advanced Filtering

Filter books by multiple criteria:

```bash
# Price range
python search.py filter --min-price 10 --max-price 30

# Publisher
python search.py filter --publisher WSOY

# Product type
python search.py filter --type Kovakantinen

# Only available books
python search.py filter --available

# Combine filters
python search.py filter --publisher Tammi --available --max-price 25

# Filter by tags
python search.py filter --tag "Tietokirjallisuus" --tag "PRIMARY"

# Save filtered results
python search.py filter --min-price 15 --output affordable-books.md
```

### Database Statistics

View analytics about your book database:

```bash
# Display stats in terminal
python search.py stats

# Save to markdown
python search.py stats --output statistics.md
```

### Compare Books

Compare multiple books side by side:

```bash
# Compare by ISBN
python search.py compare 9789510405666 9789510527719 9789510508701

# Save comparison
python search.py compare 9789510405666 9789510527719 --output comparison.md
```

## Command Reference

### Common Options

- `--output, -o` - Save results to markdown file
- `--limit, -l` - Limit number of results displayed
- `--help` - Show help for any command

### Search Commands

| Command | Description | Example |
|---------|-------------|---------|
| `search` | Text search | `search "Python"` |
| `semantic` | AI semantic search | `semantic "history books"` |
| `isbn` | Lookup by ISBN | `isbn 9789510405666` |
| `filter` | Advanced filtering | `filter --publisher WSOY` |
| `stats` | Database statistics | `stats` |
| `compare` | Compare books | `compare ISBN1 ISBN2` |

### Filter Options

| Option | Type | Description |
|--------|------|-------------|
| `--min-price` | float | Minimum price in EUR |
| `--max-price` | float | Maximum price in EUR |
| `--publisher, -p` | text | Publisher name |
| `--type, -t` | text | Product type |
| `--available` | flag | Only available books |
| `--tag` | text | Required tag (can use multiple) |

## Examples

### Find affordable available books from WSOY

```bash
python search.py filter --publisher WSOY --available --max-price 20
```

### Search for self-help books using AI

```bash
python search.py semantic "self improvement and mental health" --top-k 10 --output self-help.md
```

### Generate a report of all children's books

```bash
python search.py filter --tag "Lastenkirjat" --output children-books-report.md
```

### Get statistics and save to file

```bash
python search.py stats --output db-stats.md
```

## Cross-Platform Support

This tool works on:
- ✅ Windows (PowerShell, CMD)
- ✅ Linux (Bash, Zsh)
- ✅ macOS (Terminal)

Colored output automatically adjusts for terminal capabilities.

## Technical Details

### Semantic Search

Uses `sentence-transformers` with the `paraphrase-multilingual-MiniLM-L12-v2` model:
- Supports Finnish and English
- Creates embeddings for titles, descriptions, and tags
- Uses cosine similarity for ranking
- Model cached after first download

### Performance

- **Text search**: Instant (in-memory)
- **Filter**: Instant (in-memory)
- **Semantic search**: 
  - First run: ~30-60 seconds (model download + embedding generation)
  - Subsequent runs: ~1-2 seconds (embeddings cached)
- **ISBN lookup**: Instant

## Troubleshooting

### Semantic search fails

Make sure you have installed all dependencies:
```bash
pip install -r requirements.txt
```

### Unicode errors on Windows

The tool automatically fixes this, but if you see issues, run:
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

### No colors on Windows

Install colorama (included in requirements.txt):
```bash
pip install colorama
```

## Report Formats

Generated markdown reports include:
- Search query and timestamp
- Number of results
- Formatted book cards with:
  - Title, ISBN, Price
  - Publisher and type
  - Availability status
  - Tags
  - Description
  - Direct link to kirja.fi
  - Similarity score (for semantic search)

## Tips

1. **Semantic search is powerful** - Use natural language queries like "books about Finnish culture" instead of just keywords
2. **Combine filters** - You can use multiple filter options together
3. **Save reports** - Use `--output` to create shareable markdown reports
4. **Check stats first** - Run `stats` to understand your database
5. **Use ISBN for exact matches** - Fastest way to find a specific book

## Future Enhancements

Potential additions:
- Export to CSV/JSON
- Price history tracking
- Recommendation engine
- Web interface
- Database integration

---

For the main scraper documentation, see the parent directory's README.md
