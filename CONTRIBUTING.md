# Contributing

Thanks for contributing to spread_automation.

## Setup
1. Create and activate a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Run the app with `python main.py`.

## Branching
1. Work from `main`.
2. Create one branch per task using `lane/issue-slug`.
3. Keep pull requests focused and small.

## Pull Request Checklist
1. Explain the problem and the solution.
2. Reference related issue(s) when available.
3. List files changed and expected impact.
4. Confirm no generated binaries were added (for example files under `data/examples/`).
5. Confirm manual validation result (example dataset and expected output).

## Code Style
1. Keep modules focused (`app`, `core`, `processing`).
2. Prefer explicit names and pure helpers for data transforms.
3. Avoid unrelated refactors in the same pull request.

## Data and Artifacts
1. Do not commit virtual environments.
2. Do not commit generated spreadsheets, zips, or logs.
3. Keep domain reference docs in `docs/` when relevant to mapping rules.

## Documentation
1. Update `README.md` when setup or usage changes.
2. Update `CONTEXT.md` for architecture or domain-rule changes.
3. Append key decisions and validation evidence to `MEMORIADASIA.md`.
