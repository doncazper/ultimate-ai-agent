#!/bin/bash
# Fetch the pinned relocatable CPython used only to build macOS release bundles.
set -euo pipefail

ARCHITECTURE="${1:-$(uname -m)}"
OUTPUT_ROOT="${2:-.uaa/macos-build/python-runtime}"
RELEASE="20260510"

case "$ARCHITECTURE" in
  arm64|aarch64)
    ARCHITECTURE="arm64"
    ASSET="cpython-3.12.13+20260510-aarch64-apple-darwin-install_only.tar.gz"
    SHA256="5a30271f8d345a5b02b0c9e4e31e0f1e1455a8e4a04fba95cd9762472abc3b17"
    ;;
  x86_64|amd64)
    ARCHITECTURE="x86_64"
    ASSET="cpython-3.12.13+20260510-x86_64-apple-darwin-install_only.tar.gz"
    SHA256="cd369e76973c3179bc578230d8615ab621968ed758c5e32f636eecef4ad79894"
    ;;
  *)
    echo "Unsupported macOS architecture: $ARCHITECTURE" >&2
    exit 2
    ;;
esac

URL="https://github.com/astral-sh/python-build-standalone/releases/download/$RELEASE/${ASSET/+/%2B}"
ARCHIVE="$OUTPUT_ROOT/$ASSET"
EXTRACTED="$OUTPUT_ROOT/extracted"

mkdir -p "$OUTPUT_ROOT"
if [ ! -f "$ARCHIVE" ]; then
  /usr/bin/curl --fail --location --proto '=https' --tlsv1.2 \
    --retry 3 --connect-timeout 15 --max-time 600 \
    --output "$ARCHIVE.partial" "$URL"
  mv "$ARCHIVE.partial" "$ARCHIVE"
fi

ACTUAL_SHA256="$(/usr/bin/shasum -a 256 "$ARCHIVE" | /usr/bin/awk '{print $1}')"
if [ "$ACTUAL_SHA256" != "$SHA256" ]; then
  rm -f "$ARCHIVE"
  echo "Pinned CPython SHA-256 verification failed." >&2
  exit 1
fi

rm -rf "$EXTRACTED"
mkdir -p "$EXTRACTED"
/usr/bin/tar -xzf "$ARCHIVE" -C "$EXTRACTED"

if [ ! -x "$EXTRACTED/python/bin/python3" ]; then
  echo "Pinned CPython archive did not contain python/bin/python3." >&2
  exit 1
fi

printf '%s\n' "$EXTRACTED/python"
