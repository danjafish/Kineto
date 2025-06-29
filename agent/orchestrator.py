# agent/orchestrator.py

import os
import json
import yaml
import logging
from .llm_client import chat
from .evaluator import evaluate
from .prompts import (
    SYSTEM,
    CODE_GEN_MODELS,
    CODE_GEN_ROUTER,
    CODE_GEN_MAIN,
    CODE_GEN_REQS,
    CODE_GEN_DOCKER,
    REFINE
)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(name)
MAX_RETRIES = 2
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}


def load_openapi(path: str) -> dict:
    """Load OpenAPI spec from a YAML file."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def build_file_specs(spec: dict) -> list:
    """
    Construct the list of (relative_path, filename, snippet_fn)
    based on the OpenAPI spec.
    """
    specs = []

    # 1) Pydantic models
    specs.append((
        'app/models.py',
        'models.py',
        lambda s: s.get('components', {}).get('schemas', {})
    ))

    # Collect all tags only from actual HTTP operations
    tags = sorted({
        tag
        for path_item in spec.get('paths', {}).values()
        for method, op in path_item.items()
        if method.lower() in HTTP_METHODS
        for tag in op.get('tags', [])
    })

    for tag in tags:
        specs.append((
            f'app/routes/{tag.lower()}.py',
            f'{tag}.py',
            lambda s, tag=tag: {
                'paths': {
                    p: {
                        m: d
                        for m, d in s['paths'][p].items()
                        if m.lower() in HTTP_METHODS and tag in d.get('tags', [])
                    }
                    for p in s.get('paths', {})
                    if any(
                        (m.lower() in HTTP_METHODS and tag in d.get('tags', []))
                        for m, d in s['paths'][p].items()
                    )
                }
            }
        ))

    # Main entrypoint
    specs.append((
        'app/main.py',
        'main.py',
        lambda s: {
            'servers': s.get('servers', []),
            'tags': tags
        }
    ))

    # 4) requirements.txt
    specs.append((
        'requirements.txt',
        'requirements.txt',
        lambda s: ['fastapi', 'uvicorn', 'pydantic']
    ))

    # 5) Dockerfile
    specs.append((
        'Dockerfile',
        'Dockerfile',
        lambda s: {}
    ))

    return specs


def run(spec_path: str, output_dir: str):
    # 1) Load the spec
    spec = load_openapi(spec_path)
    logger.info(f"Loading OpenAPI spec from {spec_path}")
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Creating output directory at {output_dir}")
    # 2) Prepare metadata container
    metadata = {
        'stack': 'Python 3.10+ + FastAPI',
        'files': []
    }

    # 3) Generate each file according to spec
    for rel_path, filename, snippet_fn in build_file_specs(spec):
        snippet = snippet_fn(spec)
        spec_json = json.dumps(snippet, indent=2)

        # Select the appropriate prompt
        if filename == 'models.py':
            prompt = CODE_GEN_MODELS.format(system=SYSTEM, spec=spec_json)

        elif rel_path.startswith('app/routes/'):
            # Derive the tag name from the filename (e.g. "notes.py" → "notes")
            base = os.path.splitext(filename)[0]
            tag_lower = base.lower()
            tag_cap = base.capitalize()
            prompt = CODE_GEN_ROUTER.format(
                system=SYSTEM,
                tag=tag_cap,
                tag_lower=tag_lower,
                spec=spec_json
            )

        elif filename == 'main.py':
            prompt = CODE_GEN_MAIN.format(
                system=SYSTEM,
                servers=json.dumps(snippet.get('servers', []), indent=2),
                tags=json.dumps(snippet.get('tags', []), indent=2)
            )

        elif filename == 'requirements.txt':
            prompt = CODE_GEN_REQS.format(deps="\n".join(snippet))

        elif filename == 'Dockerfile':
            prompt = CODE_GEN_DOCKER

        else:
            raise RuntimeError(f"Unknown file type for prompt: {filename}")

        # 4) Initial generation
        messages = [
            {'role': 'system', 'content': SYSTEM},
            {'role': 'user',   'content': prompt}
        ]
        code = chat(messages)

        entry = {
            'filename': rel_path,
            'initial_prompt': prompt,
            'initial_response': code,
            'refinements': []
        }

        # Write out the file
        out_path = os.path.join(output_dir, rel_path)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'w') as f:
            f.write(code)

        # 5) Evaluate + optional refinements
        for attempt in range(MAX_RETRIES):
            errors = evaluate(output_dir)
            lint_errors = errors.get('lint', '')
            if not lint_errors:
                break

            refine_prompt = REFINE.format(
                system=SYSTEM,
                filename=filename,
                errors=lint_errors,
                spec=spec_json
            )
            messages = [
                {'role': 'system', 'content': SYSTEM},
                {'role': 'user',   'content': refine_prompt}
            ]
            refined = chat(messages)

            entry['refinements'].append({
                'attempt': attempt + 1,
                'prompt': refine_prompt,
                'response': refined,
                'errors': lint_errors
            })

            # Overwrite with refined code
            with open(out_path, 'w') as f:
                f.write(refined)

        metadata['files'].append(entry)

    # 6) Write metadata.json
    meta_file = os.path.join(output_dir, 'metadata.json')
    with open(meta_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"Generation complete: see `{meta_file}` for details.")
