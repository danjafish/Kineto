# agent/orchestrator.py

import os
import json
import yaml
import logging

from .llm_client import chat
from .prompts import (
    SYSTEM,
    CODE_GEN_MODELS,
    CODE_GEN_ROUTER,
    CODE_GEN_MAIN,
    CODE_GEN_REQS,
    CODE_GEN_DOCKER,
    CODE_GEN_TESTS,
    REFINE
)

# configure logging
logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MAX_RETRIES = 2
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}


def load_openapi(path: str) -> dict:
    """Load OpenAPI spec from a YAML file."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def build_file_specs(spec: dict) -> list:
    specs = []

    # 1) Pydantic models
    specs.append((
        'app/models.py',
        'models.py',
        lambda s: s.get('components', {}).get('schemas', {})
    ))

    # 2) Discover tags on operations
    tags = sorted({
        tag
        for path_item in spec.get('paths', {}).values()
        for method, op in path_item.items()
        if method.lower() in HTTP_METHODS and isinstance(op, dict)
        for tag in op.get('tags', [])
    })

    # If no tags, derive resource names from /api/<resource>
    if not tags:
        tags = sorted({
            path.strip('/').split('/')[1]
            for path in spec.get('paths', {})
            if path.startswith('/api/')
        })

    # One router per tag
    for tag in tags:
        filename = f'{tag}.py' if tags != ['default'] else 'routes.py'
        relpath  = f'app/routes/{filename}'
        specs.append((
            relpath,
            filename,
            lambda s, tag=tag: {
                'paths': (
                    s.get('paths', {}) if tag == 'default'
                    else {
                        p: {
                            m: d
                            for m, d in s['paths'][p].items()
                            if m.lower() in HTTP_METHODS
                            and isinstance(d, dict)
                            and tag in d.get('tags', [])
                        }
                        for p in s.get('paths', {})
                        if any(
                            m.lower() in HTTP_METHODS
                            and isinstance(d, dict)
                            and tag in d.get('tags', [])
                            for m, d in s['paths'][p].items()
                        )
                    }
                ),
                # <-- Add schemas here so router prompt knows about all models
                'schemas': s.get('components', {}).get('schemas', {})
            }
        ))

    # Main entrypoint, requirements, Dockerfile
    specs.append((
        'app/main.py',
        'main.py',
        lambda s: {'servers': s.get('servers', []), 'tags': tags}
    ))
    specs.append((
        'requirements.txt',
        'requirements.txt',
        lambda s: ['fastapi', 'uvicorn', 'pydantic']
    ))
    specs.append((
        'Dockerfile',
        'Dockerfile',
        lambda s: {}
    ))

    return specs


def run(spec_path: str, output_dir: str):
    logger.info(f"Loading OpenAPI spec from {spec_path}")
    spec = load_openapi(spec_path)

    logger.info(f"Creating output directory at {output_dir}")
    os.makedirs(output_dir, exist_ok=True)

    logger.info("Preparing metadata container")
    metadata = {
        'stack': 'Python 3.10+ + FastAPI',
        'files': []
    }

    file_specs = build_file_specs(spec)
    logger.info(f"Will generate {len(file_specs)} files based on spec")

    for rel_path, filename, snippet_fn in file_specs:
        logger.info(f"=== Generating file: {rel_path} ===")
        snippet = snippet_fn(spec)
        spec_json = json.dumps(snippet, indent=2)

        # Select the correct prompt template
        if filename == 'models.py':
            prompt = CODE_GEN_MODELS.format(system=SYSTEM, spec=spec_json)
        elif rel_path.startswith('app/routes/'):
            base = os.path.splitext(filename)[0]
            tag_lower = base.lower()
            tag_cap = base.capitalize()
            prompt = CODE_GEN_ROUTER.format(
                paths=json.dumps(snippet['paths'], indent=2),
                schemas=json.dumps(snippet['schemas'], indent=2),
                tag=tag_cap,
                tag_lower=tag_lower,
            )
        elif filename == 'main.py':
            prompt = CODE_GEN_MAIN.format(
                servers=json.dumps(snippet.get('servers', []), indent=2),
                tags=json.dumps(snippet.get('tags', []), indent=2)
            )
        elif filename == 'requirements.txt':
            prompt = CODE_GEN_REQS.format(deps="\n".join(snippet))
        elif filename == 'Dockerfile':
            prompt = CODE_GEN_DOCKER
        else:
            raise RuntimeError(f"Unknown file type for prompt: {filename}")

        # Send initial prompt
        messages = [
            {'role': 'system', 'content': SYSTEM},
            {'role': 'user', 'content': prompt}
        ]
        logger.info(f"Sending initial prompt for {filename} ({len(prompt)} chars)")
        code = chat(messages)
        entry = {
            'filename': rel_path,
            'initial_prompt': prompt,
            'initial_response': code,
            'refinements': []
        }

        # Write generated code to file
        out_path = os.path.join(output_dir, rel_path)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'w') as f:
            f.write(code)
        logger.info(f"Wrote {rel_path}")

        # Review & refine generated code against the spec
        with open(out_path, 'r') as f:
            current_code = f.read()

        review_prompt = REFINE.format(
            system=SYSTEM,
            filename=filename,
            code=current_code,
            spec=spec_json
        )
        messages = [
            {'role': 'system', 'content': SYSTEM},
            {'role': 'user', 'content': review_prompt}
        ]
        logger.info(f"Sending review prompt for {filename}")
        reviewed = chat(messages)

        entry['refinements'].append({
            'prompt': review_prompt,
            'response': reviewed
        })
        with open(out_path, 'w') as f:
            f.write(reviewed)
        logger.info(f"Applied review/refinement for {filename}")

        metadata['files'].append(entry)

    # Write metadata.json
    meta_file = os.path.join(output_dir, 'metadata.json')
    with open(meta_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    tests_dir = os.path.join(output_dir, 'tests')
    os.makedirs(tests_dir, exist_ok=True)
    full_spec = json.dumps(spec, indent=2)
    prompt = CODE_GEN_TESTS.format(spec=full_spec)
    messages = [
        {'role': 'system', 'content': SYSTEM},
        {'role': 'user', 'content': prompt}
    ]
    tests_code = chat(messages)
    with open(os.path.join(tests_dir, 'test_api.py'), 'w') as f:
        f.write(tests_code)
    logger.info("Generated tests at tests/test_api.py")
    logger.info(f"Generation complete. Metadata written to {meta_file}")
    print(f"Generation complete: see `{meta_file}` for details.")
