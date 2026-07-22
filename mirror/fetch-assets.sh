#!/bin/bash
# Download every URL in the given list file, preserving the path under the site root.
# Query strings are stripped from the local filename.
set -u
LIST="$1"
FAIL=0
while IFS= read -r url; do
  [ -z "$url" ] && continue
  path="${url#https://ari-thaistreetfood.com/}"
  path="${path%%\?*}"
  [ -f "$path" ] && continue
  mkdir -p "$(dirname "$path")"
  code=$(curl -sL -w '%{http_code}' -o "$path" "$url")
  if [ "$code" != "200" ]; then
    echo "FAIL $code $url"
    FAIL=$((FAIL+1))
    rm -f "$path"
  fi
done < "$LIST"
echo "done, failures: $FAIL"
