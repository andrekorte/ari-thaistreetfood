# Ari - Thai Street Food — static website

Static rebuild of https://ari-thaistreetfood.com/ (originally WordPress + Elementor),
byte-faithful to the live site as of 22 July 2026. No PHP, no database, no plugins —
just the rendered pages with all assets stored locally.

## Pages

| Path | Page |
|---|---|
| `/` | Home |
| `/about/` | About / Our Story |
| `/contact/` | Contact (hours, map, form) |
| `/privacy-policy/` | Privacy Policy |
| `/terms-conditions/` | Terms & Conditions |

Assets live under `wp-content/` and `wp-includes/` (paths kept identical to the
original so every URL on the site keeps working).

## What changed vs. the WordPress original

- All asset URLs rewritten to root-relative and served from this repo.
- WordPress server machinery removed (REST/oEmbed/feed links, emoji loader,
  Contact Form 7 + reCAPTCHA scripts, Astra starter-template script).
- **Contact form** now posts to FormSubmit: `https://formsubmit.co/arithaistreetfood@gmail.com`.
  ⚠️ The first submission triggers an activation email to that inbox — it must be
  confirmed once before messages come through.
- Everything else (FoodBooking order links, Google Maps embed, Google Fonts,
  reviews, photos, layout) is unchanged.
- Canonical/OG/schema.org tags still point at `https://ari-thaistreetfood.com/` —
  correct once the domain is pointed at this site.

## Preview locally

Serve from the repo root (root-relative paths need a server, not `file://`):

```bash
python3 -m http.server 8000
```

then open http://localhost:8000/

## Deploy on GitHub Pages

1. Push this repo to GitHub.
2. Repo Settings → Pages → deploy from `main` branch, root folder.
3. Add the custom domain `ari-thaistreetfood.com` in the Pages settings
   (GitHub writes a `CNAME` file), and point the domain's DNS at GitHub Pages.
   Note: until the custom domain is active, the `username.github.io/repo/`
   preview will have broken styling — the site uses root-relative paths.

## Rebuilding from the mirror

`mirror/` holds the original page snapshots and the build tooling:

- `mirror/*.html` — untouched WordPress page snapshots
- `mirror/build-static.py` — transforms the snapshots into this static site
- `mirror/fetch-assets.sh` + URL lists — asset downloader

`mirror/wp-content` and `mirror/wp-includes` (the pristine asset copies) are
git-ignored to keep the repo small; the same files are committed at the repo root.
