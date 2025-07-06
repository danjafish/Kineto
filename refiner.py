#!/usr/bin/env python3
import sys
import os
import json
import yaml
from datetime import datetime
from agent.llm_client import chat
from agent.prompts import SYSTEM, REFINE_ROUTER


def load_spec(path):
    with open(path, 'r') as f:
        if path.endswith(('.yaml', '.yml')):
            return yaml.safe_load(f)
        return json.load(f)


def main():
    if len(sys.argv) != 4:
        print("Usage: refiner.py <path/to/openapi.yaml> <app_dir> <test_log>")
        sys.exit(1)

    spec_path, app_dir, log_path = sys.argv[1], sys.argv[2], sys.argv[3]
    spec = load_spec(spec_path)
    errors = open(log_path, 'r').read()

    routes_dir = os.path.join(app_dir, 'app', 'routes')
    if not os.path.isdir(routes_dir):
        print(f"[REFINER] No routes directory at {routes_dir}, skipping refinement.")
        return

    log_entries = []
    # Always attempt to refine each router file when errors exist
    for fname in sorted(os.listdir(routes_dir)):
        if not fname.endswith('.py'):
            continue
        rel_path = os.path.join('app', 'routes', fname)
        file_path = os.path.join(app_dir, rel_path)
        code = open(file_path, 'r').read()

        prompt = REFINE_ROUTER.format(
            filename=rel_path,
            code=code,
            spec=json.dumps(spec, indent=2),
            errors=errors
        )
        print(f"[REFINER] Refining router {rel_path} due to test errors...")
        messages = [
            {'role': 'system', 'content': SYSTEM},
            {'role': 'user', 'content': prompt}
        ]
        updated = chat(messages)

        changed = updated.strip() != code.strip()
        if changed:
            print(f"[REFINER] Updating {rel_path}")
            with open(file_path, 'w') as f:
                f.write(updated)
        else:
            print(f"[REFINER] No changes needed for {rel_path}")

        log_entries.append({
            'filename': rel_path,
            'changed': changed,
            'prompt': prompt,
            'response': updated,
            'errors': errors,
            'timestamp': datetime.utcnow().isoformat()
        })

    # Write refinement log
    ref_log = os.path.join(app_dir, 'refiner_log.json')
    with open(ref_log, 'w') as f:
        json.dump(log_entries, f, indent=2)
    print(f"[REFINER] Written {len(log_entries)} entries to {ref_log}")


if __name__ == '__main__':
    main()
