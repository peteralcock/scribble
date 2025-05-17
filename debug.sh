#!/bin/bash
# Run tests with verbose output to debug test discovery issues

echo "Python version:"
python --version

echo "Installed packages:"
pip list

echo "Directory structure:"
find . -type f -name "*.py" | sort

echo "Checking pytest plugins:"
pytest --trace-config

echo "Running tests with verbose discovery:"
PYTHONPATH=. pytest -v --collect-only

echo "Running tests with coverage:"
PYTHONPATH=. pytest --cov=app tests/ -v
