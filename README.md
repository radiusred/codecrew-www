# codecrew-www

Source for [codecrew.works](https://codecrew.works), the CodeCrew website:
a landing page, the reference docs synced from
[radiusred/gh-codecrew](https://github.com/radiusred/gh-codecrew), and a
blog for release notes and field reports.

The product and its docs live in `gh-codecrew`; that repo is the source of
truth for everything under `/docs/`. Edit reference material there. This
repo holds only what is specific to the site.

## Layout

- `docs/index.md` — landing page
- `docs/blog/posts/` — blog posts; `_drafts/` holds future-dated ones
- `docs/docs/` — synced from `gh-codecrew` on every build, never committed
- `sync_docs.py` — the sync (README, SPEC, CHANGELOG, ROADMAP,
  CONTRIBUTING, SECURITY and `docs/`, minus `milestones/`), plus the Docs nav
- `main.py` — draft promotion, blog nav, archive page and Atom feed
- `zensical.toml` — site config; the nav blocks between `BEGIN_*`/`END_*`
  markers are generated

## Writing a post

Create `docs/blog/posts/YYYY-MM-DD-slug.md` with this front matter:

```yaml
---
layout: default
author: Your Name
title: Post title
date: YYYY-MM-DD
description: One-sentence summary, used in the feed and listings
tags: [tag1, tag2]
---
```

Start the body at the first paragraph or a `##` heading; the template
renders the title, byline and date. Future-dated posts are moved to
`_drafts/` at build time and promoted by the daily scheduled build once
their date arrives. Public copy must not reference internal systems,
internal issue trackers or private repositories.

## Local preview

```sh
git clone https://github.com/radiusred/gh-codecrew ../gh-codecrew   # once
uv sync
uv run python sync_docs.py && uv run python main.py
uv run zensical serve        # http://localhost:8000
uv run pytest
```

## Deploys

`.github/workflows/site.yml` runs on every push to `main`, daily at 00:05
UTC, and on demand. It checks out `gh-codecrew`, syncs, builds with
Zensical and publishes `site/` to GitHub Pages. `docs/CNAME` keeps the
custom domain attached across deploys.

DNS for `codecrew.works` (a proxied CNAME to `radiusred.github.io`) and
the Cloudflare zone configuration live as code in
[radiusred/infrastructure](https://github.com/radiusred/infrastructure).

## Commits

Conventional commits, checked by commitlint on pull requests. This repo is
a CodeCrew spoke of `radiusred/gh-codecrew` (see `.codecrew.yml`).

Licensed under [Apache 2.0](LICENSE).
