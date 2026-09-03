# codecrew-www

Source for [codecrew.works](https://codecrew.works), the CodeCrew website:
a landing page and a blog for release notes, design decisions and field
reports. A lightweight marketing site, nothing more.

The product itself lives in
[radiusred/gh-codecrew](https://github.com/radiusred/gh-codecrew), which
stays the single source of truth for its documentation: `sync_docs.py`
builds that repo's `docs/` tree, `SPEC.md`, `CONTRIBUTING.md` and
`SECURITY.md` into `/docs/` here on every deploy. Nothing synced is
committed. `www.radiusred.uk` carries only the README as a project landing
page and points here for the rest.

`docs/milestones/` is excluded — see `EXCLUDE` in `sync_docs.py`. The
per-milestone records are the engineering trail, not product documentation;
links into them resolve to GitHub like any other path that does not sync.

## Layout

- `docs/index.md` — landing page
- `docs/blog/posts/` — blog posts; `_drafts/` holds future-dated ones
- `docs/docs/` — the synced upstream docs, generated and git-ignored
- `main.py` — draft promotion, blog nav, archive page and Atom feed
- `sync_docs.py` — the upstream docs sync and its nav block
- `zensical.toml` — site config; the nav blocks between `BEGIN_BLOG_POSTS`
  / `END_BLOG_POSTS` and `BEGIN_DOCS_NAV` / `END_DOCS_NAV` are generated

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

`sync_docs.py` reads the upstream from `$SYNC_SOURCE_BASE/gh-codecrew`,
defaulting to `../gh-codecrew` — so a sibling clone of the hub is all it
needs. Without one it exits nonzero saying what to clone: the site cannot
build without the section, because the home page's "Read the docs" button
targets it. The site-build tests skip for the same reason.

```sh
uv sync
uv run python sync_docs.py   # builds docs/docs/ from ../gh-codecrew
uv run python main.py
uv run zensical serve        # http://localhost:8000
uv run pytest
```

## Deploys

`.github/workflows/site.yml` runs on every push to `main`, daily at 00:05
UTC, and on demand. It checks `radiusred/gh-codecrew` out under `_sources/`,
runs the sync, builds with Zensical and publishes `site/` to GitHub Pages —
so a docs change upstream reaches the site on the next scheduled build. `docs/CNAME` keeps the custom domain attached across deploys.

DNS for `codecrew.works` (a proxied CNAME to `radiusred.github.io`) and
the Cloudflare zone configuration live as code in
[radiusred/infrastructure](https://github.com/radiusred/infrastructure).

## Commits

Conventional commits, checked by commitlint on pull requests. This repo is
a CodeCrew spoke of `radiusred/gh-codecrew` (see `.codecrew.yml`).

Licensed under [Apache 2.0](LICENSE).
