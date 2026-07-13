#!/bin/zsh
set -euo pipefail

# This helper is installed root-owned by provision_self_hosted_macos_runners.sh
# and then executed as the dedicated, non-admin runner account. It accepts the
# one-hour GitHub registration token on stdin so the token never appears in the
# command line or durable configuration.

umask 077

readonly RUNNER_VERSION="2.335.1"
readonly RUNNER_SHA256="e1a9bc7a3661e06fa0b129d15c2064fe65dc81a431001d8958a9db1409b73769"
readonly RUNNER_ASSET="actions-runner-osx-arm64-${RUNNER_VERSION}.tar.gz"
readonly RUNNER_URL="https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${RUNNER_ASSET}"
readonly TOOLCHAIN_PATH="/opt/homebrew/opt/python@3.12/libexec/bin:/opt/homebrew/opt/node@22/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

fail() {
  print -u2 -- "runner bootstrap blocked: $1"
  exit 1
}

[[ $# -eq 6 ]] || fail "expected account, repository URL, runner name, install directory, label, and remote registration state"

readonly expected_account="$1"
readonly repository_url="$2"
readonly runner_name="$3"
readonly install_directory="$4"
readonly custom_label="$5"
readonly remote_registration_state="$6"

[[ "$(uname -s)" == "Darwin" ]] || fail "macOS is required"
[[ "$(uname -m)" == "arm64" ]] || fail "Apple Silicon arm64 is required"
[[ "$(id -u)" -ne 0 ]] || fail "the runner must not execute as root"
[[ "$(id -un)" == "$expected_account" ]] || fail "unexpected runner account"
[[ "$HOME" == "/Users/${expected_account}" ]] || fail "unexpected runner home"
[[ "$repository_url" == "https://github.com/doncazper/ultimate-ai-agent" ]] || fail "unexpected repository scope"
[[ "$runner_name" == uaa-ci-mac-arm64-[0-9][0-9] ]] || fail "unexpected runner name"
[[ "$install_directory" == "$HOME/uaa-actions-runners/runner-"[0-9][0-9] ]] || fail "unexpected install directory"
[[ "$custom_label" == "uaa-ci" ]] || fail "unexpected custom label"
[[ "$remote_registration_state" == "registered" || "$remote_registration_state" == "absent" ]] || fail "unexpected remote registration state"

if /usr/sbin/dseditgroup -o checkmember -m "$expected_account" admin 2>/dev/null | /usr/bin/grep -q "yes"; then
  fail "the dedicated runner account must not be an administrator"
fi

readonly credential_paths=(
  "$HOME/.netrc"
  "$HOME/.npmrc"
  "$HOME/.pypirc"
  "$HOME/.aws/credentials"
  "$HOME/.azure/accessTokens.json"
  "$HOME/.config/gcloud/application_default_credentials.json"
  "$HOME/.docker/config.json"
  "$HOME/.kube/config"
)
for credential_path in "${credential_paths[@]}"; do
  [[ ! -s "$credential_path" ]] || fail "dedicated runner account contains a credential file"
done
if /usr/bin/find "$HOME/.ssh" -maxdepth 1 -type f \( -name 'id_*' -o -name '*.pem' \) -size +0c -print -quit 2>/dev/null | /usr/bin/grep -q .; then
  fail "dedicated runner account contains SSH private-key material"
fi

IFS= read -r registration_token
[[ -n "$registration_token" ]] || fail "registration token was not provided"

readonly download_directory="$HOME/uaa-actions-runners/downloads"
readonly archive_path="$download_directory/$RUNNER_ASSET"
/bin/mkdir -p "$download_directory"

if [[ ! -f "$archive_path" ]]; then
  /usr/bin/curl --fail --location --proto '=https' --tlsv1.2 \
    --output "$archive_path.part" "$RUNNER_URL"
  /bin/mv "$archive_path.part" "$archive_path"
fi

actual_sha256="$(/usr/bin/shasum -a 256 "$archive_path" | /usr/bin/awk '{print $1}')"
[[ "$actual_sha256" == "$RUNNER_SHA256" ]] || fail "runner archive checksum mismatch"

/bin/mkdir -p "$install_directory"
cd "$install_directory"

if [[ -e .runner || -L .runner ]]; then
  [[ -f .runner && ! -L .runner ]] || fail "local runner registration must be a regular non-symlink file"
  [[ "$remote_registration_state" == "registered" ]] || fail "local runner registration is stale; remove it with an exact GitHub removal token before reprovisioning"
  /opt/homebrew/bin/python3.12 - "$runner_name" "$repository_url" <<'PY' || fail "local runner registration does not match the exact repository scope"
import json
import sys
from pathlib import Path

settings = json.loads(Path(".runner").read_text(encoding="utf-8"))
expected_name, expected_url = sys.argv[1:]
if settings.get("agentName") != expected_name:
    raise SystemExit(1)
if str(settings.get("gitHubUrl", "")).rstrip("/") != expected_url:
    raise SystemExit(1)
if settings.get("workFolder") != "_work":
    raise SystemExit(1)
PY
else
  /usr/bin/tar -xzf "$archive_path" -C "$install_directory"
  ACTIONS_RUNNER_INPUT_TOKEN="$registration_token" ./config.sh \
    --url "$repository_url" \
    --name "$runner_name" \
    --labels "$custom_label" \
    --work _work \
    --unattended \
    --replace
fi

registration_token=""
unset registration_token

/bin/mkdir -p "$HOME/uaa-actions-runners" "$install_directory/_work/_tool"
/usr/bin/touch "$HOME/uaa-actions-runners/.metadata_never_index"
/usr/bin/touch "$install_directory/_work/.metadata_never_index"
print -r -- "$TOOLCHAIN_PATH" > .path

[[ -x ./runsvc.sh ]] || /bin/cp ./bin/runsvc.sh ./runsvc.sh
/bin/chmod u+x ./runsvc.sh

print -- "configured ${runner_name} for the exact UAA repository scope"
