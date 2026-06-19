# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python automation scripts and tools project.

## Common Commands

```bash
# Run a script
python <script_name>.py

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run a single test
pytest tests/test_<name>.py::test_<function>

# Lint
flake8 .
# or
ruff check .

# Format code
black .
# or
ruff format .
```

## Git Workflow

**コードを変更するたびに必ずGitHubにプッシュすること。**

Every code change must be committed and pushed to GitHub immediately after completion.

```bash
git add <changed_files>
git commit -m "Brief description of the change"
git push origin main
```

- Commit each logical change as a separate commit.
- Always push after committing — do not let local commits accumulate unpushed.
- Use descriptive commit messages in Japanese or English (either is fine).
