import subprocess
import os


def lint_project(project_dir: str) -> str:
    """
    Run flake8 on the project directory.
    Returns combined stdout+stderr as a string.
    """
    # Only lint Python code under app/
    code_dir = os.path.join(project_dir, 'app')
    result = subprocess.run(
        ['flake8', code_dir],
        capture_output=True, text=True
    )

    return result.stdout + result.stderr


def evaluate(project_dir: str) -> dict:
    """
    Evaluate the generated project.
    Currently only runs linting.
    Returns a dict of error sections, e.g. {'lint': '<errors>'},
    or an empty dict if no errors.
    """
    errors = {}
    lint_errors = lint_project(project_dir)
    if lint_errors.strip():
        errors['lint'] = lint_errors
    return errors
