#!/usr/bin/env python3
"""Generate /menu/ from menu-data.json, reusing the built About page's
header/footer shell. Run AFTER build-static.py."""
import hashlib
import html as htmlmod
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.normpath(os.path.join(HERE, ".."))

data = json.load(open(os.path.join(HERE, "menu-data.json")))
ORDER_BASE = data["order_base"]
ORDER_ALL = ORDER_BASE + "/menu/all"

shell = open(os.path.join(SITE, "about", "index.html"), encoding="utf-8").read()

# --- split the about page into head+header / (content) / footer ---
p = shell.index('data-elementor-type="wp-page"')
prefix = shell[: shell.rfind("<div", 0, p)]
p2 = shell.index('data-elementor-type="wp-post" data-elementor-id="1030"')
footer = shell[shell.rfind("<div", 0, p2):]

# --- adapt the head for the menu page ---
prefix = prefix.replace("About - Ari - Thai Street Food", "Menu - Ari - Thai Street Food")
prefix = prefix.replace("https://ari-thaistreetfood.com/about/", "https://ari-thaistreetfood.com/menu/")
_menucss = open(os.path.join(HERE, "menu.css"), "rb").read()
_menuver = hashlib.md5(_menucss).hexdigest()[:8]
prefix = prefix.replace(
    "</head>",
    f'<link rel="stylesheet" href="/wp-content/menu.css?ver={_menuver}" media="all">\n</head>',
)
# nav: un-highlight About (the shell page), highlight Menu instead
prefix = prefix.replace("current-menu-item", "").replace("current_page_item", "")
prefix = prefix.replace(
    'class = "hfe-menu-item">Menu',
    'class = "hfe-menu-item" style="color:#f2c519 !important">Menu',
)


def esc(s):
    return htmlmod.escape(s, quote=True)


def card(item):
    order_url = ORDER_BASE + item["href"]
    if item["id"]:
        fig = (
            f'<figure><img src="/wp-content/uploads/menu/{item["id"]}.jpg" '
            f'alt="{esc(item["name"])}" loading="lazy" width="576" height="576"></figure>'
        )
    else:
        fig = (
            '<figure><span class="ari-menu-noimg">'
            '<img src="/wp-content/uploads/ari-logo.png" alt="" loading="lazy"></span></figure>'
        )
    return (
        f'<a class="ari-menu-item" href="{order_url}" target="_blank" rel="noopener">'
        f"{fig}"
        f'<span class="ari-menu-meta"><span class="ari-menu-name">{esc(item["name"])}</span>'
        f'<span class="ari-menu-price">${item["price"]}</span></span>'
        "</a>"
    )


tabs = "".join(
    f'<a href="#cat-{c["slug"]}">{esc(c["title"])}</a>' for c in data["categories"]
)

sections = []
for c in data["categories"]:
    cards = "".join(card(i) for i in c["items"])
    sections.append(
        f'<section class="ari-menu-cat" id="cat-{c["slug"]}"><div class="wrap">'
        f"<h2>{esc(c['title'])}</h2><div class=\"ari-menu-rule\"></div>"
        f'<div class="ari-menu-grid">{cards}</div></div></section>'
    )

content = f"""
<div class="ari-menu">
  <section class="ari-menu-hero">
    <h1>Our Menu</h1>
    <p>Authentic Thai street food, made fresh in Brisbane City. Prices and live availability are always on the order page &mdash; tap any dish to order it online.</p>
    <a class="ari-btn" href="{ORDER_ALL}" target="_blank" rel="noopener">Order Online</a>
  </section>
  <nav class="ari-menu-tabs" aria-label="Menu categories">{tabs}</nav>
  {''.join(sections)}
  <section class="ari-menu-cta">
    <h2>Hungry now?</h2>
    <p>Build your order in our online shop &mdash; takeaway and delivery, handled securely through Clover.</p>
    <a class="ari-btn" href="{ORDER_ALL}" target="_blank" rel="noopener">Order the whole thing online</a>
  </section>
</div>
<script>
(function () {{
  var tabs = document.querySelectorAll(".ari-menu-tabs a");
  var map = {{}};
  tabs.forEach(function (a) {{ map[a.getAttribute("href").slice(1)] = a; }});
  var obs = new IntersectionObserver(function (entries) {{
    entries.forEach(function (e) {{
      if (e.isIntersecting) {{
        tabs.forEach(function (a) {{ a.classList.remove("is-active"); }});
        var a = map[e.target.id];
        if (a) {{ a.classList.add("is-active"); a.scrollIntoView({{block: "nearest", inline: "center"}}); }}
      }}
    }});
  }}, {{ rootMargin: "-80px 0px -70% 0px" }});
  document.querySelectorAll(".ari-menu-cat").forEach(function (s) {{ obs.observe(s); }});
}})();
</script>
"""

out = prefix + content + footer
os.makedirs(os.path.join(SITE, "menu"), exist_ok=True)
with open(os.path.join(SITE, "menu", "index.html"), "w", encoding="utf-8") as fh:
    fh.write(out)
shutil.copy(os.path.join(HERE, "menu.css"), os.path.join(SITE, "wp-content", "menu.css"))
n = sum(len(c["items"]) for c in data["categories"])
print("wrote menu/index.html —", len(data["categories"]), "categories,", n, "items")
