#!/usr/bin/env python3
"""Transform mirrored WordPress pages into a clean static site under ../site/."""
import hashlib
import os
import re
import shutil

MIRROR = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.normpath(os.path.join(MIRROR, ".."))  # repo root
DOMAIN = "https://ari-thaistreetfood.com/"

# The old FoodBooking ordering account is dead; all menu/order links go to Clover now.
FOODBOOKING_URL = (
    "https://www.foodbooking.com/ordering/restaurant/menu"
    "?restaurant_uid=05536531-9a25-444d-a449-9b3cfe07d7da"
)
CLOVER_URL = "https://arithaistreetfood-brisbane-city.cloveronline.com.au/menu/all"

# New header logo (from the Clover ordering site) replaces the old white/red one
# everywhere it appears (header, footer, favicons).
OLD_LOGO_URLS = (
    "/wp-content/uploads/2025/04/cropped-website-logo.webp",
    "/wp-content/uploads/2025/04/cropped-website-logo-300x300.webp",
    "/wp-content/uploads/2025/04/cropped-website-logo-150x150.webp",
)
NEW_LOGO_URL = "/wp-content/uploads/ari-logo.png"

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
    # --- nav "Menu" item -> our own /menu/ page (before the Clover rewrite) ---
    html = re.sub(
        r'(<a href=")[^"]*(" (?:itemprop="url" )?class = "hfe-menu-item">Menu)',
        r"\1/menu/\2",
        html,
    )

    # --- menu/order links: dead FoodBooking account -> Clover ordering ---
    html = html.replace(FOODBOOKING_URL, CLOVER_URL)

    # --- phone number: old mobile -> restaurant landline ---
    html = html.replace("tel:+61452643155", "tel:+61739057358")
    html = html.replace("+61452643155", "(07) 3905 7358")

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

    # --- header logo links to /home (WP redirect page that doesn't exist here) ---
    html = html.replace('href="/home"', 'href="/"')

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

    # --- swap in the new logo (runs after URL rewriting, so paths are local) ---
    for old in OLD_LOGO_URLS:
        html = html.replace(old, NEW_LOGO_URL)

    # --- custom overrides stylesheet, last so it wins the cascade ---
    # (content-hash version param so browsers pick up changes immediately)
    css = open(os.path.join(MIRROR, "custom.css"), "rb").read()
    ver = hashlib.md5(css).hexdigest()[:8]
    html = html.replace(
        "</head>",
        f'<link rel="stylesheet" href="/wp-content/custom.css?ver={ver}" media="all">\n</head>',
    )

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

    # site-specific additions on top of the mirrored assets
    shutil.copy(os.path.join(MIRROR, "custom.css"), os.path.join(SITE, "wp-content", "custom.css"))
    shutil.copy(os.path.join(MIRROR, "ari-logo.png"), os.path.join(SITE, "wp-content", "uploads", "ari-logo.png"))

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
        if src == "home.html":
            # hero background: replace the 3-image slideshow with a single
            # static Pad Kra Pow photo (the lower slideshow keeps its images)
            html = re.sub(
                r'background_slideshow_gallery&quot;:\[[^\]]*1136[^\]]*\]',
                "background_slideshow_gallery&quot;:[{&quot;id&quot;:1145,"
                "&quot;url&quot;:&quot;https:\\\\/\\\\/ari-thaistreetfood.com"
                "\\\\/wp-content\\\\/uploads\\\\/pad-kra-pow-hero.jpg&quot;}]",
                html,
            )
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
