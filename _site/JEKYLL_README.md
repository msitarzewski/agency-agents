# Agency Agents Catalog

A Jekyll-powered static site that lists all 124 AI agents with search and filtering capabilities.

## Features

- Search agents by name or description
- Filter by category
- English/Chinese language toggle
- Responsive design
- Dark theme with category color coding

## Development

### Prerequisites

- Ruby 3.0+
- Bundler

### Setup

```bash
# Install dependencies
bundle install

# Start local server
bundle exec jekyll serve

# Build for production
bundle exec jekyll build
```

### Update Agents Data

When `AGENTS_LIST.md` or `AGENTS_LIST_CN.md` is updated, regenerate the agents data:

```bash
python3 scripts/generate_agents_data.py > _data/agents.yml
```

## Deployment

The site is automatically deployed to GitHub Pages via GitHub Actions when changes are pushed to the `main` branch.

## Structure

```
├── _config.yml          # Jekyll configuration
├── _data/
│   ├── agents.yml      # Agent data (generated)
│   └── categories.yml  # Category definitions
├── _layouts/           # Page templates
├── assets/
│   ├── css/           # Stylesheets
│   └── js/            # JavaScript
├── index.md           # Main page
└── scripts/           # Build scripts
```
