#!/usr/bin/env python3
import argparse
from agent.orchestrator import run

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='AI-driven FastAPI generator from OpenAPI spec'
    )
    parser.add_argument('spec', help='Path to openapi.yaml')
    parser.add_argument('-o', '--output', default='generated_app', help='Output directory')
    args = parser.parse_args()

    run(args.spec, args.output)
