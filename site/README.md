# Agent catalog (GitHub Pages)

A static, searchable page listing every agent in the repository: search by
name, description and vibe, filter by division, open an agent's source, or copy
the command that installs just that agent.

| File | Role |
| --- | --- |
| `site/index.html` | Page template: inline CSS and vanilla JS, no frameworks, CDNs or web fonts. Committed. |
| `scripts/build-catalog.py` | Reads the agents and `divisions.json`, writes the site. Python 3 standard library only. |
| `_site/` | Build output (`index.html`, `agents.json`). Gitignored; never commit it. |
| `.github/workflows/pages.yml` | Builds and deploys to GitHub Pages on pushes to `main` that touch agents, `divisions.json`, `site/` or the build script. |

## Build and preview locally

```bash
python3 scripts/build-catalog.py     # Windows: py scripts/build-catalog.py
```

Then open `_site/index.html` in a browser, or serve it:

```bash
python3 -m http.server --directory _site 8000   # http://localhost:8000
```

Options:

- `--out DIR`: write somewhere other than `_site/`.
- `--repo-url URL`: base URL for "View source" links (default
  `https://github.com/msitarzewski/agency-agents/blob/main/`). CI passes the
  current repository and branch, so a fork links to itself.
- `--check`: parse and validate everything and write nothing. CI runs this on
  pull requests (the `catalog` job in `lint-agents.yml`). It fails if an agent
  is missing `name`, `description`, `color` or `emoji`, if a `.md` in a division
  has no frontmatter, or if two agents share a filename slug or an install slug.

## What the build reads

- Divisions and their labels and colors come from `divisions.json`.
- Agents are the `*.md` files under each division directory, the same set
  `scripts/lint-agents.sh` checks. Frontmatter is read the way `scripts/lib.sh`
  `get_field` reads it, so the catalog shows the same text the converters use.
- Each entry has two slugs. `slug` is the filename stem. `install_slug` is the
  slugified `name:`, which is what `./scripts/install.sh --agent` accepts
  (for example `--agent frontend-developer`, not `engineering-frontend-developer`).

The page inlines the index as JSON (with `<`, `>` and `&` escaped), builds all
agent text into the DOM with `textContent`, and ships a Content-Security-Policy
that allows only its own inline style and script, by hash.

## One-time setup: enable GitHub Pages

A maintainer has to turn Pages on once: **Settings -> Pages -> Build and
deployment -> Source: GitHub Actions**. Then run the "Deploy Agent Catalog"
workflow (Actions tab -> Run workflow) or push to `main`.

When you add a division, also add its directory to the `paths:` list in
`.github/workflows/pages.yml`. `check-divisions.sh` does not check that file.
