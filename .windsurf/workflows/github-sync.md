---
description: After completing a feature or fix, commit and push to GitHub
---

## GitHub Sync Workflow

After completing each unit of work (feature, fix, test, doc update), follow these steps:

1. **Check what changed**
   ```bash
   git status -s
   ```

2. **Stage relevant files** (exclude data/db/logs which are in .gitignore)
   ```bash
   git add -A
   ```

3. **Commit with a descriptive message**
   ```bash
   git commit -m "<type>: <short description>

   - <detail 1>
   - <detail 2>"
   ```
   Types: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`

4. **Push to GitHub**
   ```bash
   git push
   ```

5. **Verify push succeeded** — if SSL/HTTPS fails, switch to SSH:
   ```bash
   git remote set-url origin git@github.com:godermai/stock-research-foundation.git
   git push
   ```

### Rules
- **Never** commit `.env`, `data/`, `db/`, `logs/`, `*.duckdb`, `*.sqlite` files
- **Always** verify tests pass before committing (`stock-cli accept`)
- Keep commit messages in English, concise
- One logical change per commit
