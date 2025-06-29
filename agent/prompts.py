# System prompt reused in all generations
SYSTEM = """
You are an expert Python developer specialized in building FastAPI applications.
When asked to generate code:
  • Use FastAPI and Pydantic only (never Django or any other framework).
  • Import all required modules at top of file.
  • Return **only** raw Python source—no markdown fences, no comments, no explanation.
  • The code must pass flake8 linting.
"""

# 1) Models
CODE_GEN_MODELS = """
{system}
Given this OpenAPI schema definitions snippet:
{spec}

Generate Python code defining Pydantic models for each schema.
Use `from pydantic import BaseModel`, and place all classes in this file.
Return only the Python code.
"""

# 2) Router for a specific tag
CODE_GEN_ROUTER = """
{system}
Given this OpenAPI Paths snippet for tag "{tag}":
{spec}

Generate a fully working FastAPI `APIRouter` for tag "{tag}":
  Import `APIRouter`, `HTTPException`, and any models from `app.models`.
  Initialize an in-memory store (e.g. `items = []` or `dict()`) to back these endpoints.
  router = APIRouter(prefix="/api/{tag_lower}", tags=["{tag}"])
  For **each** operation:
    Implement the handler to update/query the in-memory store.
    Use correct `response_model`, `status_code`, and raise `HTTPException` for 404s.
    e.g. for GET `/api/{tag_lower}`, return the full list; for POST, append and return the new item.
    Ensure path parameters (like `{id}`) are handled and converted to the right types.

Return only the Python code—no fences or commentary.
"""

# 3) Main application entrypoint
CODE_GEN_MAIN = """
{system}
Given these servers and tags:
servers: {servers}
tags: {tags}

Generate a FastAPI application entrypoint:
  • from fastapi import FastAPI
  • import each router module under app.routes (one per tag)
  • include each router on `app` with proper prefixes and tags
  • configure bearerAuth if specified
  • add an `if __name__ == "__main__":` block with `uvicorn.run()`
Return only the Python code.
"""

# 4) requirements.txt
CODE_GEN_REQS = """
Generate a pip requirements.txt file listing exactly these packages:
{deps}
Return only the requirements content.
"""

# 5) Dockerfile
CODE_GEN_DOCKER = """
Generate a Dockerfile for a Python 3.10+ FastAPI application:
  • Use `python:3.10-slim` base image
  • Copy `requirements.txt` and install
  • Copy the `app/` directory
  • Expose port 8000
  • Run `uvicorn app.main:app --host 0.0.0.0 --port 8000`
Return only the Dockerfile contents.
"""

# Generic refine prompt (can be reused for any file)
REFINE = """
{system}
The code for "{filename}" failed with these errors:
{errors}

Here’s the original snippet used to generate it:
{spec}

Please provide corrected, working code for "{filename}" only—no fences or commentary.
"""
