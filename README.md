# Backend Generator

This tool generates a FastAPI backend application from an OpenAPI YAML specification.

## Requirements

- Python 3.10+
- `pip install jinja2 pyyaml`

## Usage

```bash
python generator.py path/to/openapi.yaml -o output_directory
```

This will create:

- `app/models.py`: Pydantic models.
- `app/main.py`: FastAPI application with stub endpoints.
- `requirements.txt`
- `Dockerfile`
- `metadata.json`: Info about the generated project.

Run the app:

```bash
uvicorn app.main:app --reload
```

Build and run with Docker:

```bash
docker build -t my-backend .
docker run -p 8000:8000 my-backend
```