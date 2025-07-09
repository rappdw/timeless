#!/bin/bash
# Script to run CI checks locally before committing

set -e  # Exit on error

echo "🔍 Running local CI checks..."

# Ensure we're in the project root
cd "$(dirname "$0")/.."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "⚠️ Virtual environment not found. Creating one..."
    uv venv
    echo "📦 Installing dependencies..."
    uv pip install -e ".[dev]"
fi

echo "🧹 Running ruff linting..."
.venv/bin/ruff check .

echo "🎨 Checking formatting with black..."
.venv/bin/black --check .

echo "📋 Checking imports with isort..."
.venv/bin/isort --check .

echo "🔤 Type checking with mypy..."
.venv/bin/mypy --strict .

echo "🧪 Running tests with pytest..."
.venv/bin/pytest --cov=timeless_py

echo "✅ All checks passed! Safe to commit and push."
