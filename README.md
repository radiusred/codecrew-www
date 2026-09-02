# codecrew-www

Source for [codecrew.works](https://codecrew.works), the CodeCrew website:
a landing page and a blog for release notes, design decisions and field
reports. A lightweight marketing site, nothing more.

The product, its reference docs and its specification live in
[radiusred/gh-codecrew](https://github.com/radiusred/gh-codecrew); the site
links there rather than mirroring them. Radius Red's own site,
[www.radiusred.uk](https://www.radiusred.uk/), also carries a synced copy
of the docs.

## Layout

- `docs/index.md` — landing page
- `docs/blog/posts/` — blog posts; `_drafts/` holds future-dated ones
- `main.py` — draft promotion, blog nav, archive page and Atom feed
- `zensical.toml` — site config; the nav block between `BEGIN_BLOG_POSTS`
  and `END_BLOG_POSTS` is generated

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
uv sync
uv run python main.py
uv run zensical serve        # http://localhost:8000
uv run pytest
```

## Deploys

`.github/workflows/site.yml` runs on every push to `main`, daily at 00:05
UTC, and on demand. It builds with Zensical and publishes `site/` to
GitHub Pages. `docs/CNAME` keeps the custom domain attached across deploys.

DNS for `codecrew.works` (a proxied CNAME to `radiusred.github.io`) and
the Cloudflare zone configuration live as code in
[radiusred/infrastructure](https://github.com/radiusred/infrastructure).

## Commits

Conventional commits, checked by commitlint on pull requests. This repo is
a CodeCrew spoke of `radiusred/gh-codecrew` (see `.codecrew.yml`).

Licensed under [Apache 2.0](LICENSE).
