# Documentation

This file contains steps to build documentation for PySysInfo.

## Building Documentation

- Optional: Make a venv
```bash
cd PySysInfo
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
````
- Build the documentation
```bash
cd docs
pip install sphinx
pip install autodoc_pydantic
sphinx-build -M html source build
```
