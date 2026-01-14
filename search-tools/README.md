# Book database search tools

Command-line search and reporting tools for the JSON data produced by the kirja.fi scraper.

## Requirements

- Python 3.8+
- A populated `data/books/` directory (run the scraper first)

## Installation

From this directory:

```bash
pip install -r requirements.txt
```

Verify the CLI is available:

```bash
python search.py --help
```

Note: the first semantic search run will download a `sentence-transformers` model and may take a while.

## Usage

Text search (content-focused ranking):

```bash
python search.py search "historia Suomi"
python search.py search "lapset perhe kasvatus" --output family-books.md
```

Semantic search (multilingual embeddings, model: `paraphrase-multilingual-MiniLM-L12-v2`):

```bash
python search.py semantic "books about Finnish winter war"
python search.py semantic "programming" --threshold 0.5
```

ISBN lookup:

```bash
python search.py isbn 9789510405666
python search.py isbn 9789510405666 --output book-details.md
```

Filtering:

```bash
python search.py filter --min-price 10 --max-price 30
python search.py filter --publisher WSOY --available --max-price 20
python search.py filter --tag "Tietokirjallisuus" --tag "PRIMARY"
```

Statistics:

```bash
python search.py stats
python search.py stats --output statistics.md
```

Compare books:

```bash
python search.py compare 9789510405666 9789510527719
python search.py compare 9789510405666 9789510527719 --output comparison.md
```

## Common options

- `--output, -o`: write results to a Markdown file
- `--limit, -l`: limit terminal output

## Report output

Markdown reports include the query, timestamp, result count, and formatted book entries (title, ISBN, price, publisher/type, availability, tags, description, and a kirja.fi link). Semantic search reports also include a similarity score.

## Troubleshooting

Unicode issues on Windows PowerShell:

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

No colors on Windows:

```bash
pip install colorama
```

---

Main scraper documentation: see the parent directory README.
