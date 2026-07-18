#!/bin/bash
# Long-lived Ultimate AI Agent macOS installer bootstrap.
set -euo pipefail

REPOSITORY="doncazper/ultimate-ai-agent"
BOOTSTRAP_TAG="uaa-installer-v1"
CHANNEL="newest"
LOCAL_ARCHIVE=""
LOCAL_DESCRIPTOR=""
LAUNCH_AFTER_INSTALL="false"
SCRIPT_DIR="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(CDPATH='' cd -- "$SCRIPT_DIR/../.." && pwd)"

usage() {
  /bin/cat <<'EOF'
Usage: install.sh [options]

Installs the newest valid stable or dev GitHub Release, whichever tagged commit
is newer. The repository is private, so `gh auth login` must already be ready
unless a local release artifact is supplied.

Options:
  --channel newest|stable|dev
  --launch
  --install-root PATH
  --applications-dir PATH
  --bin-dir PATH
  --local-archive PATH --local-descriptor PATH
  --help
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --channel)
      CHANNEL="${2:-}"
      shift 2
      ;;
    --launch)
      LAUNCH_AFTER_INSTALL="true"
      shift
      ;;
    --install-root)
      export UAA_INSTALL_ROOT="${2:-}"
      shift 2
      ;;
    --applications-dir)
      export UAA_APPLICATIONS_DIR="${2:-}"
      shift 2
      ;;
    --bin-dir)
      export UAA_INSTALL_BIN_DIR="${2:-}"
      shift 2
      ;;
    --local-archive)
      LOCAL_ARCHIVE="${2:-}"
      shift 2
      ;;
    --local-descriptor)
      LOCAL_DESCRIPTOR="${2:-}"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown installer option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "$CHANNEL" in
  newest|stable|dev) ;;
  *)
    echo "Channel must be newest, stable, or dev." >&2
    exit 2
    ;;
esac

if { [ -n "$LOCAL_ARCHIVE" ] && [ -z "$LOCAL_DESCRIPTOR" ]; } ||
   { [ -z "$LOCAL_ARCHIVE" ] && [ -n "$LOCAL_DESCRIPTOR" ]; }; then
  echo "Local installation requires both --local-archive and --local-descriptor." >&2
  exit 2
fi

run_installed_doctor() {
  INSTALL_ROOT="${UAA_INSTALL_ROOT:-$HOME/Library/Application Support/Ultimate AI Agent}"
  UAA_EXECUTABLE="$INSTALL_ROOT/current/Ultimate AI Agent.app/Contents/MacOS/Ultimate AI Agent"
  if [ ! -x "$UAA_EXECUTABLE" ]; then
    echo "Installed application executable is missing." >&2
    exit 1
  fi
  "$UAA_EXECUTABLE" doctor
  if [ "$LAUNCH_AFTER_INSTALL" = "true" ]; then
    "$UAA_EXECUTABLE" launch
  fi
}

if [ -n "$LOCAL_ARCHIVE" ]; then
  PYTHON=""
  if [ -x "$REPO_ROOT/.venv/bin/python" ]; then
    PYTHON="$REPO_ROOT/.venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON="$(command -v python3)"
  fi
  if [ -z "$PYTHON" ]; then
    echo "A repository Python is required for --local-archive installation." >&2
    exit 1
  fi
  PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}" \
    "$PYTHON" -m ultimate_ai_agent.distribution.macos.runtime \
    install-local --archive "$LOCAL_ARCHIVE" --descriptor "$LOCAL_DESCRIPTOR"
  run_installed_doctor
  exit 0
fi

case "$(uname -m)" in
  arm64|aarch64) ARCHITECTURE="arm64" ;;
  x86_64|amd64) ARCHITECTURE="x86_64" ;;
  *)
    echo "This Mac architecture is not supported." >&2
    exit 1
    ;;
esac

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI is required for this private repository." >&2
  echo "Install it once, run 'gh auth login', then rerun this installer." >&2
  exit 1
fi
if ! gh auth status --hostname github.com >/dev/null 2>&1; then
  echo "GitHub CLI is not authenticated for the private UAA repository." >&2
  echo "Run 'gh auth login', then rerun this installer." >&2
  exit 1
fi

TEMP_ROOT="$(/usr/bin/mktemp -d "${TMPDIR:-/tmp}/uaa-installer.XXXXXX")"
cleanup() {
  rm -rf "$TEMP_ROOT"
}
trap cleanup EXIT INT TERM HUP

BOOTSTRAP_ASSET="uaa-installer-macos-$ARCHITECTURE.tar.gz"
CHECKSUM_ASSET="$BOOTSTRAP_ASSET.sha256"
gh release download "$BOOTSTRAP_TAG" \
  --repo "$REPOSITORY" \
  --pattern "$BOOTSTRAP_ASSET" \
  --pattern "$CHECKSUM_ASSET" \
  --dir "$TEMP_ROOT"

(
  cd "$TEMP_ROOT"
  /usr/bin/shasum -a 256 -c "$CHECKSUM_ASSET"
)

while IFS= read -r entry; do
  case "$entry" in
    /*|../*|*/../*|*/..)
      echo "Installer bootstrap archive contains an unsafe path." >&2
      exit 1
      ;;
  esac
done < <(/usr/bin/tar -tzf "$TEMP_ROOT/$BOOTSTRAP_ASSET")

/usr/bin/tar -xzf "$TEMP_ROOT/$BOOTSTRAP_ASSET" -C "$TEMP_ROOT"
BOOTSTRAP_PYTHON="$TEMP_ROOT/bootstrap/python/bin/python3"
if [ ! -x "$BOOTSTRAP_PYTHON" ]; then
  echo "Installer bootstrap runtime is missing." >&2
  exit 1
fi

set +e
"$BOOTSTRAP_PYTHON" -m ultimate_ai_agent.distribution.macos.runtime \
  update --channel "$CHANNEL"
UPDATE_STATUS=$?
set -e
if [ "$UPDATE_STATUS" -ne 0 ] && [ "$UPDATE_STATUS" -ne 10 ]; then
  echo "Ultimate AI Agent installation did not complete." >&2
  exit "$UPDATE_STATUS"
fi

run_installed_doctor
