#!/bin/bash
# Find url(...) refs inside downloaded CSS, resolve them to site URLs, download missing files.
set -u
OUT="css-refs.txt"
: > "$OUT"
find wp-content wp-includes -name '*.css' | while IFS= read -r css; do
  dir=$(dirname "$css")
  grep -ohE 'url\((["'"'"']?)[^)"'"'"']+\1\)' "$css" | sed -E 's/^url\((["'"'"']?)//; s/(["'"'"']?)\)$//' | while IFS= read -r ref; do
    case "$ref" in
      data:*|http://*|//*) continue ;;
      https://ari-thaistreetfood.com/*) echo "$ref" >> "$OUT" ;;
      https://*) continue ;;
      *)
        # resolve relative to css dir
        ref="${ref%%\?*}"; ref="${ref%%#*}"
        abs=$(cd "$dir" 2>/dev/null && python3 -c "import os,sys; print(os.path.normpath(os.path.join('$dir', '$ref')))")
        echo "https://ari-thaistreetfood.com/$abs" >> "$OUT"
        ;;
    esac
  done
done
sort -u "$OUT" -o "$OUT"
wc -l "$OUT"
