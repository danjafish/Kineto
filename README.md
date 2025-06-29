# Kineto

**AI-Driven FastAPI Backend Generator**

This is a test assignment implementation that scaffolds a FastAPI backend from an OpenAPI v3 specification.

## Prerequisites

* Python 3.10+
* OpenAI API Key (optional, set via `OPENAI_API_KEY`)

## Installation

1. Clone the repo and install dependencies:

   ```bash
   git clone <repo-url>
   cd Kineto
   pip install -r requirements.txt
   ```

2. Configure environment variables (optional):

   ```bash
   export OPENAI_API_KEY="sk-..."
   export OPENAI_MODEL="gpt-4"
   export MAX_TOKENS=8192
   export TEMPERATURE=0.1
   ```

## Usage

Run the generator with an OpenAPI spec:

```bash
python generator.py <path/to/openapi.yaml> -o <output_dir>
```

* `<path/to/openapi.yaml>`: your OpenAPI YAML file
* `-o <output_dir>`: directory for generated code

Example:

```bash
python generator.py test_task/task1/openapi.yaml -o generated/task1
```

## Generated Output

The output directory will contain:

```
output_dir/
├── app/
│   ├── models.py       # Pydantic models
│   ├── routes/         # Routers per API tag
│   │   └── <tag>.py
│   └── main.py         # FastAPI entrypoint
├── requirements.txt    # dependencies
├── Dockerfile          # container setup
└── metadata.json       # prompts and responses log
```

## How It Works

1. **Spec Parsing**: loads `openapi.yaml` into a Python dict.
2. **File Specs**: dynamically determines which files to generate (models, routers, main, requirements, Dockerfile).
3. **LLM Generation**: sends tailored prompts to OpenAI, receives code snippets.
4. **Review**: agent reviews its own code against the spec and refines if needed.
5. **Output**: writes code files and a `metadata.json` log.

## Verification

To test the generated app manually:

```bash
cd <output_dir>
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then visit [http://localhost:8000/docs](http://localhost:8000/docs) to verify endpoints.


