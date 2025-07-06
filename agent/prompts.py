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
Given these OpenAPI snippets for tag "{tag}":
PATHS:
{paths}
SCHEMAS:
{schemas}

Generate a fully working FastAPI `APIRouter` for tag "{tag}", implementing:

1. Pydantic models:
   • For creation: a `{tag}Create` model with only required fields.
   • For update: a `{tag}Update` model with all optional fields.
   • For responses: a `{tag}Response` model matching the schema (including `createdAt` etc.).
   • An `ErrorResponse` model for error bodies.

2. APIRouter setup:
   router = APIRouter(prefix="/api/{tag_lower}", tags=["{tag}"])

3. Endpoints:
   • `@router.get("/", response_model=List[{tag}Response])` to *list* all items.
   • `@router.post("/", response_model={tag}Response, status_code=201)` to *create*.
       – Handler signature: `(item: {tag}Create)`.
   • `@router.get("/{{id}}", response_model={tag}Response)` to *retrieve* by `id`.
       – Use path parameter named `id`.
   • `@router.patch("/{{id}}", response_model={tag}Response)` to *update* by `id`.
       – Handler signature: `(id: str, item: {tag}Update)`.
   • `@router.delete("/{{id}}", status_code=204)` to *delete* by `id`.

4. In‐memory store:
   • Use a `Dict[str, {tag}Response]` named `{tag_lower}_store` as your backing store.
   • For create, generate a UUID for `id` and set `createdAt=datetime.utcnow()`.
   • On errors (e.g. missing item), raise `HTTPException(status_code=…, detail=ErrorResponse(error=…).dict())`.

5. Import statements:
   • `from fastapi import APIRouter, HTTPException, status`
   • `from typing import List, Dict`
   • `from datetime import datetime`
   • `from uuid import uuid4`
   • `from app.models import {tag}Create, {tag}Update, {tag}Response, ErrorResponse`

Return only the raw Python code—no markdown fences or commentary.
"""

# 3) Main application entrypoint
CODE_GEN_MAIN = """
Generate the contents of `app/main.py` as follows:
  • Import `FastAPI` from `fastapi` and `uvicorn`.
  • Given these tags: {tags}
  • For each tag in that list, import its router module under `app.routes`:
      e.g. for tag "Notes":
        `from app.routes.notes import router as notes_router`
  • Instantiate the FastAPI app:
      `app = FastAPI()`
  • Include each router:
      `app.include_router(notes_router)`
      (repeat for each tag)
  • Add the startup block:
      ```python
      if __name__ == "__main__":
          uvicorn.run(app, host="127.0.0.1", port=8000)
      ```
Add a root endpoint, something like:
   @app.get("/", include_in_schema=False)
   def root():
       return "message": "Welcome – see /docs for API docs"

Return only the Python source code—no fences or commentary.
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
Here is the current implementation of "{filename}":
{code}

Ensure that this implementation is correct, runnable, and performs all the required tasks as specified by the following OpenAPI snippet:
{spec}

If any changes are needed to meet the spec, return only the corrected code; otherwise, you may return the original implementation.
"""

# Generates pytest for all CRUD operations in your spec
CODE_GEN_TESTS = """
Generate a pytest module that exercises every operation in this OpenAPI spec:

{spec}

Requirements:
  • Use `requests` and `pytest`.  
  • One test function per endpoint+method (e.g. `test_get_items`, `test_post_item`).  
  • For GETs without body: send GET, assert status code matches spec, and response JSON shape.  
  • For POSTs: construct a minimal JSON body from the schema, send POST, assert 201 and response matches.  
  • For path‐parameter operations: reuse an ID from a prior POST.  
  • For error cases: e.g. GET non‐existent ID yields 404 and `{{\"error\": ...}}`.

Return one `.py` file content—no fences or commentary.
"""

# Prompt to refine a single endpoint handler
REFINE_ENDPOINT = """
You are an expert Python developer specializing in FastAPI.

Tests for the `{method} {path}` endpoint failed with these errors:
{errors}

Here is the current router code:
{code}

OpenAPI operation spec:
{snippet}

Please fix **only** the handler function for `{method} {path}` so that tests will pass.
Return the **full updated** router file content, raw Python only.
"""


REFINE_ROUTER = """
You are an expert FastAPI developer.

All tests against this router failed to pass. Here’s the test error log:
{errors}

Here is the full router file "{filename}":
{code}

Here is the OpenAPI spec:
{spec}

Apply only the minimal changes needed to make this router pass the tests.
Return the complete updated router file (raw Python only).
"""
