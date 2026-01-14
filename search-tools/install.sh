#!/bin/bash
# Quick installer for search tools

echo "📚 Installing Book Database Search Tools..."
echo ""

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "❌ Error: pip not found. Please install Python and pip first."
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Installation complete!"
    echo ""
    echo "Quick start:"
    echo "  python search.py --help          # Show all commands"
    echo "  python search.py search 'query'  # Search books"
    echo "  python search.py stats           # View statistics"
    echo ""
    echo "For full documentation, see README.md"
else
    echo ""
    echo "❌ Installation failed. Please check the error messages above."
    exit 1
fi
