# Context policy

## Always
- Obey AGENTS.md setup/test commands.
- Prefer source and tests over notes in this pack.

## Before feature or architecture work
1. Search `.context/decisions/` for keywords from the task.
2. Read at most 3 matching decisions, newest first.
3. If a decision `supersedes` another, ignore the older one.

## Before editing style-sensitive code
- Open `.context/prefs/` files whose names match the language or area.

## After significant work
Write durable notes only if a future agent would otherwise re-learn a non-obvious constraint
and it is not obvious from code, tests, or README.

## Never store
- API keys, tokens, customer data
- generated dumps of source files
- facts already obvious from the repository

## Conflicts
User > private/ > this file > decisions > prefs > guesses from code.
