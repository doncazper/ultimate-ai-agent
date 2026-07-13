#!/bin/zsh
set -euo pipefail

# Interactive macOS provisioning entrypoint. Run this once from an administrator
# account. Passwords are handled only by sudo/sysadminctl prompts; GitHub runner
# registration tokens are fetched with gh and piped to the unprivileged helper.

umask 077

readonly REPOSITORY="doncazper/ultimate-ai-agent"
readonly REPOSITORY_URL="https://github.com/${REPOSITORY}"
readonly RUNNER_ACCOUNT="uaa-ci"
readonly RUNNER_LABEL="uaa-ci"
readonly DEFAULT_RUNNER_COUNT=4
readonly MAX_RUNNER_COUNT=4
readonly HELPER_INSTALL_PATH="/usr/local/libexec/uaa-ci/bootstrap_self_hosted_macos_runner.sh"
readonly SCRIPT_DIRECTORY="${0:A:h}"
readonly HELPER_SOURCE="${SCRIPT_DIRECTORY}/bootstrap_self_hosted_macos_runner.sh"
readonly PYTHON_BIN="/opt/homebrew/bin/python3.12"
readonly NODE_BIN="/opt/homebrew/opt/node@22/bin/node"

fail() {
  print -u2 -- "runner provisioning blocked: $1"
  exit 1
}

[[ "$(uname -s)" == "Darwin" ]] || fail "macOS is required"
[[ "$(uname -m)" == "arm64" ]] || fail "Apple Silicon arm64 is required"
[[ "$(id -u)" -ne 0 ]] || fail "run this script from the administrator account, not a root shell"
[[ -x "$PYTHON_BIN" ]] || fail "Homebrew python@3.12 is required"
[[ -x "$NODE_BIN" ]] || fail "Homebrew node@22 is required"
[[ "$($PYTHON_BIN -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')" == "3.12" ]] || fail "Homebrew Python must be version 3.12"
[[ "$($NODE_BIN -p 'process.versions.node.split(".")[0]')" == "22" ]] || fail "Homebrew Node must be major version 22"
command -v gh >/dev/null 2>&1 || fail "GitHub CLI is required"
gh auth status >/dev/null 2>&1 || fail "GitHub CLI authentication is required"
[[ -x "$HELPER_SOURCE" ]] || fail "runner bootstrap helper is missing or not executable"
[[ "$(gh api "repos/${REPOSITORY}" --jq .private)" == "true" ]] || fail "self-hosted runners require the UAA repository to remain private"

runner_count="${UAA_RUNNER_COUNT:-$DEFAULT_RUNNER_COUNT}"
[[ "$runner_count" =~ ^[0-9]+$ ]] || fail "UAA_RUNNER_COUNT must be an integer"
(( runner_count >= 1 && runner_count <= MAX_RUNNER_COUNT )) || fail "UAA_RUNNER_COUNT must be between 1 and ${MAX_RUNNER_COUNT}"

if ! /usr/bin/id "$RUNNER_ACCOUNT" >/dev/null 2>&1; then
  print -- "A dedicated standard macOS account named ${RUNNER_ACCOUNT} is required."
  print -- "sudo will request your administrator password, then sysadminctl will securely request a new runner-account password."
  /usr/bin/sudo /usr/sbin/sysadminctl \
    -addUser "$RUNNER_ACCOUNT" \
    -fullName "UAA CI Runner" \
    -shell /bin/zsh \
    -home "/Users/${RUNNER_ACCOUNT}" \
    -password -
  /usr/bin/sudo /usr/sbin/createhomedir -c -u "$RUNNER_ACCOUNT" >/dev/null
fi

if /usr/sbin/dseditgroup -o checkmember -m "$RUNNER_ACCOUNT" admin 2>/dev/null | /usr/bin/grep -q "yes"; then
  fail "${RUNNER_ACCOUNT} must be a standard non-admin account"
fi

/usr/bin/sudo /usr/bin/install -d -o root -g wheel -m 0755 /usr/local/libexec
/usr/bin/sudo /usr/bin/install -d -o root -g wheel -m 0755 /usr/local/libexec/uaa-ci
/usr/bin/sudo /usr/bin/install -o root -g wheel -m 0755 "$HELPER_SOURCE" "$HELPER_INSTALL_PATH"
/usr/bin/sudo /bin/mkdir -p "/Users/${RUNNER_ACCOUNT}/uaa-actions-runners"
/usr/bin/sudo /usr/sbin/chown -R "${RUNNER_ACCOUNT}:staff" "/Users/${RUNNER_ACCOUNT}/uaa-actions-runners"

for index in $(/usr/bin/seq 1 "$runner_count"); do
  instance="$(printf '%02d' "$index")"
  runner_name="uaa-ci-mac-arm64-${instance}"
  install_directory="/Users/${RUNNER_ACCOUNT}/uaa-actions-runners/runner-${instance}"
  service_label="com.github.actions.runner.uaa-ci-${instance}"
  service_path="/Library/LaunchDaemons/${service_label}.plist"
  log_directory="/Users/${RUNNER_ACCOUNT}/Library/Logs/${service_label}"

  registration_token="$(gh api --method POST "repos/${REPOSITORY}/actions/runners/registration-token" --jq .token)"
  [[ -n "$registration_token" ]] || fail "GitHub did not return a runner registration token"
  printf '%s\n' "$registration_token" | /usr/bin/sudo -H -u "$RUNNER_ACCOUNT" \
    "$HELPER_INSTALL_PATH" \
    "$RUNNER_ACCOUNT" \
    "$REPOSITORY_URL" \
    "$runner_name" \
    "$install_directory" \
    "$RUNNER_LABEL"
  registration_token=""
  unset registration_token

  /usr/bin/sudo /bin/mkdir -p "$log_directory"
  /usr/bin/sudo /usr/sbin/chown -R "${RUNNER_ACCOUNT}:staff" "$log_directory"

  temporary_plist="$(/usr/bin/mktemp -t uaa-ci-runner-plist)"
  trap '/bin/rm -f "$temporary_plist"' EXIT
  /usr/bin/tee "$temporary_plist" >/dev/null <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${service_label}</string>
  <key>UserName</key>
  <string>${RUNNER_ACCOUNT}</string>
  <key>WorkingDirectory</key>
  <string>${install_directory}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${install_directory}/runsvc.sh</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>HOME</key>
    <string>/Users/${RUNNER_ACCOUNT}</string>
    <key>LANG</key>
    <string>en_US.UTF-8</string>
    <key>PATH</key>
    <string>/opt/homebrew/opt/python@3.12/libexec/bin:/opt/homebrew/opt/node@22/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    <key>RUNNER_TOOL_CACHE</key>
    <string>${install_directory}/_work/_tool</string>
  </dict>
  <key>KeepAlive</key>
  <true/>
  <key>RunAtLoad</key>
  <true/>
  <key>ProcessType</key>
  <string>Background</string>
  <key>StandardOutPath</key>
  <string>${log_directory}/stdout.log</string>
  <key>StandardErrorPath</key>
  <string>${log_directory}/stderr.log</string>
</dict>
</plist>
PLIST
  /usr/bin/plutil -lint "$temporary_plist" >/dev/null
  /usr/bin/sudo /usr/bin/install -o root -g wheel -m 0644 "$temporary_plist" "$service_path"
  /bin/rm -f "$temporary_plist"
  trap - EXIT

  /usr/bin/sudo /bin/launchctl bootout "system/${service_label}" >/dev/null 2>&1 || true
  if ! /usr/bin/sudo /bin/launchctl bootstrap system "$service_path"; then
    print -u2 -- "launchd did not settle after bootout for ${service_label}; retrying once"
    /usr/bin/sudo /bin/launchctl bootout "system/${service_label}" >/dev/null 2>&1 || true
    /bin/sleep 2
    /usr/bin/sudo /bin/launchctl bootstrap system "$service_path"
  fi
  /usr/bin/sudo /bin/launchctl enable "system/${service_label}"
  /usr/bin/sudo /bin/launchctl kickstart -k "system/${service_label}"
  /usr/bin/sudo /bin/launchctl print "system/${service_label}" >/dev/null
done

print -- "Provisioned ${runner_count} repo-scoped UAA runner instance(s)."
print -- "Confirm online status with: gh api repos/${REPOSITORY}/actions/runners --jq '.runners[] | [.name,.status,.busy,.labels[].name]'"
