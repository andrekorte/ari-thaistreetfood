#!/usr/bin/env python3
"""Transform mirrored WordPress pages into a clean static site under ../site/."""
import os
import re
import shutil

MIRROR = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.normpath(os.path.join(MIRROR, ".."))  # repo root
DOMAIN = "https://ari-thaistreetfood.com/"

PAGES = {
    "home.html": "index.html",
    "about.html": "about/index.html",
    "contact.html": "contact/index.html",
    "privacy-policy.html": "privacy-policy/index.html",
    "terms-conditions.html": "terms-conditions/index.html",
}

ASSET_PREFIXES = ("wp-content/", "wp-includes/")
PAGE_PATHS = {"", "about/", "contact/", "privacy-policy/", "terms-conditions/"}


def local_path(path):
    """Map a site-absolute path (no domain) to its root-relative static URL."""
    path = path.split("?")[0]
    # keep fragment if any
    frag = ""
    if "#" in path:
        path, frag = path.split("#", 1)
        frag = "#" + frag
    if path.startswith(ASSET_PREFIXES):
        return "/" + path + frag
    if path in PAGE_PATHS:
        return "/" + path + frag
    return "/" + path + frag


def rewrite_html(html):
    # --- protect canonical link (keep absolute for SEO) ---
    html = html.replace(
        '<link rel="canonical" href="' + DOMAIN,
        '<link rel="canonical" href="__KEEPDOMAIN__',
    )

    # --- remove WP head cruft ---
    removals = [
        r"<link rel='dns-prefetch' href='//s\.w\.org' />\n?",
        r'<link rel="alternate"[^>]*application/rss\+xml[^>]*/>\n?',
        r'<link rel="alternate"[^>]*oembed[^>]*/>\n?',
        r'<link rel="alternate"[^>]*application/json"[^>]*wp-json[^>]*/>\n?',
        r'<link rel="https://api\.w\.org/"[^>]*/>\n?',
        r'<link rel="EditURI"[^>]*/>\n?',
        r"<link rel='shortlink'[^>]*/>\n?",
        # emoji machinery (settings JSON + inlined loader script)
        r'<script id="wp-emoji-settings"[^>]*>.*?</script>\n?',
        r'<script[^>]*>(?:(?!</script>).)*wpEmojiSettingsSupports.*?</script>\n?',
        # contact-form-7 + recaptcha scripts (form is rewired to FormSubmit)
        r'<script[^>]*id="swv-js"[^>]*></script>\n?',
        r'<script[^>]*id="contact-form-7-js-translations"[^>]*>.*?</script>\n?',
        r'<script[^>]*id="contact-form-7-js-before"[^>]*>.*?</script>\n?',
        r'<script[^>]*id="contact-form-7-js"[^>]*></script>\n?',
        r'<script[^>]*id="google-recaptcha-js"[^>]*></script>\n?',
        r'<script[^>]*id="wpcf7-recaptcha-js-before"[^>]*>.*?</script>\n?',
        r'<script[^>]*id="wpcf7-recaptcha-js"[^>]*></script>\n?',
        # astra-sites template-preview lib (WP onboarding leftover)
        r'<script[^>]*id="starter-templates-zip-preview-js-extra"[^>]*>.*?</script>\n?',
        r'<script[^>]*id="starter-templates-zip-preview-js"[^>]*></script>\n?',
    ]
    for pat in removals:
        html = re.sub(pat, "", html, flags=re.DOTALL)

    # --- rewire the contact form to FormSubmit ---
    def form_repl(m):
        return (
            '<form action="https://formsubmit.co/arithaistreetfood@gmail.com" '
            'method="post" class="wpcf7-form init" aria-label="Contact form" '
            'data-status="init">'
            '<input type="hidden" name="_subject" value="Website contact form">'
        )

    html = re.sub(r'<form action="/contact/#wpcf7[^>]*>', form_repl, html)
    # drop CF7 hidden bookkeeping fields and the akismet honeypot block
    html = re.sub(r'<input type="hidden" name="_wpcf7[^>]*/?>\n?', "", html)
    html = re.sub(
        r'<p style="display: none !important;" class="akismet-fields-container".*?</p>\n?',
        "",
        html,
        flags=re.DOTALL,
    )
    # make browser enforce the required fields CF7 used to validate
    html = html.replace('aria-required="true"', 'aria-required="true" required')

    # --- rewrite same-domain URLs in href/src/action/poster attributes ---
    def attr_repl(m):
        attr, quote, path = m.group(1), m.group(2), m.group(3)
        return attr + "=" + quote + local_path(path) + quote

    html = re.sub(
        r'\b(href|src|action|poster)=(["\'])' + re.escape(DOMAIN) + r'([^"\']*)\2',
        attr_repl,
        html,
    )

    # --- srcset attributes (multiple URLs per value) ---
    def srcset_repl(m):
        quote, value = m.group(1), m.group(2)
        value = value.replace(DOMAIN, "/")
        return "srcset=" + quote + value + quote

    html = re.sub(r'srcset=(["\'])([^"\']*)\1', srcset_repl, html)

    # --- CSS url(...) in style blocks/attributes ---
    html = html.replace("url(" + DOMAIN, "url(/")
    html = html.replace("url('" + DOMAIN, "url('/")
    html = html.replace('url("' + DOMAIN, 'url("/')

    # --- windows tile icon: point at the local copy ---
    html = html.replace(
        '<meta name="msapplication-TileImage" content="' + DOMAIN,
        '<meta name="msapplication-TileImage" content="/',
    )

    # --- JSON-escaped URLs inside inline JS configs ---
    html = html.replace("https:\\/\\/ari-thaistreetfood.com\\/", "\\/")

    # restore protected canonical
    html = html.replace("__KEEPDOMAIN__", DOMAIN)
    return html


def main():
    # refresh only the generated trees, never the whole repo root
    for tree in ("wp-content", "wp-includes"):
        dest = os.path.join(SITE, tree)
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(os.path.join(MIRROR, tree), dest)

    # rewrite domain in all CSS files to root-relative
    for tree in ("wp-content", "wp-includes"):
      for root, _dirs, files in os.walk(os.path.join(SITE, tree)):
        for f in files:
            if f.endswith(".css"):
                p = os.path.join(root, f)
                with open(p, "r", encoding="utf-8", errors="replace") as fh:
                    css = fh.read()
                css = css.replace(DOMAIN, "/")
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(css)

    # transform pages
    for src, dest in PAGES.items():
        with open(os.path.join(MIRROR, src), encoding="utf-8") as fh:
            html = fh.read()
        html = rewrite_html(html)
        dest_path = os.path.join(SITE, dest)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "w", encoding="utf-8") as fh:
            fh.write(html)
        print("wrote", dest)

    # sanity: report any leftover same-domain refs outside canonical/og/schema
    for src, dest in PAGES.items():
        p = os.path.join(SITE, dest)
        with open(p, encoding="utf-8") as fh:
            html = fh.read()
        leftovers = [
            line.strip()[:120]
            for line in html.splitlines()
            if DOMAIN in line
            and "canonical" not in line
            and "og:" not in line
            and "twitter:" not in line
            and "yoast" not in line
            and "application/ld+json" not in line
        ]
        if leftovers:
            print("LEFTOVER refs in", dest)
            for l in leftovers[:10]:
                print("   ", l)


if __name__ == "__main__":
    main()
