
#!/bin/bash
# Run tests with coverage

# Install test requirements
pip install -r test-requirements.txt

# Set Python path to include the project root
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Run the tests with coverage
pytest --cov=app tests/ -v
