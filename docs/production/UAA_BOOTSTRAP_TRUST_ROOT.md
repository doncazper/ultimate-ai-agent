# UAA Bootstrap Trust Root

Status: M167 local-dev trust root for the bounded GitHub bootstrap slice.

This document is the repo-owned trust root for `uaa setup bootstrap`. It is
intentionally narrow: it allows only a pinned GitHub Release artifact from the
UAA repository to be verified, unpacked into a temporary directory, and invoked
as the reviewed local installer path for the designated OpenWebUI local-dev UI.

## Trusted Source

Allowed repository:

```text
https://github.com/doncazper/ultimate-ai-agent
```

Allowed ref form:

- explicit immutable release tag supplied with `--release-tag`
- exact release asset name supplied with `--asset`
- exact SHA-256 digest supplied with `--sha256`
- exact signature/provenance manifest supplied with `--signature`
- explicit provenance mode supplied with `--provenance-mode`

Denied ref form:

- mutable `main`, `master`, branch refs, pull request refs, or moving aliases
- `latest`
- `raw.githubusercontent.com`
- arbitrary GitHub repos, forks, gists, snippets, or caller-provided script URLs
- pipe-to-shell patterns such as `curl | bash` or `bash <(...)`

## Provenance Modes

Public bootstrap mode is `minisign`. It requires a repo-pinned public key or
equivalent Sigstore trust identity, detached signature, digest binding, and a
deterministic verifier before any installer code runs. This slice fails closed
in `minisign` mode until that key and verifier are configured.

Local-dev test mode is `local-dev-json`. It accepts the JSON provenance
manifest below only after the operator explicitly selects
`--provenance-mode local-dev-json`. This mode is not cryptographic public
distribution provenance.

## Local-Dev Provenance Format

The local-dev implementation path uses a provenance manifest named by
`--signature`. The manifest is JSON with this schema:

```json
{
  "schema": "uaa.bootstrap.provenance.v1",
  "repo": "https://github.com/doncazper/ultimate-ai-agent",
  "release_tag": "v0.102.0-m167",
  "asset": "uaa-bootstrap-darwin-arm64.tar.gz",
  "sha256": "<64 lowercase hex characters>",
  "target": "openwebui",
  "installer": "uaa-bootstrap",
  "trust_root": "docs/production/UAA_BOOTSTRAP_TRUST_ROOT.md",
  "authority": "openwebui-local-dev-bootstrap-only"
}
```

The manifest is not an authority expansion and is not public cryptographic
signing. It is a fail-closed local-dev provenance check that binds the approved
repo, release tag, asset name, SHA-256 digest, installer filename, target, and
trust-root document before local execution. Public bootstrap mode must not
fall back to this JSON format.

## Verification Rules

Before execution, `uaa setup bootstrap` must verify:

- supported platform is in the M167 matrix
- release tag is explicit and not a mutable alias
- asset and signature/provenance inputs are exact asset names or safe local
  user-scope paths, never arbitrary URLs
- downloaded artifact SHA-256 equals `--sha256`
- public `minisign` mode fails closed unless cryptographic verification is
  configured and passes
- local-dev JSON mode manifest fields exactly match repo, release tag, asset,
  digest, target, installer filename, trust root, and authority boundary
- archive extraction stays inside a temporary installer directory
- archive entries are regular files or directories only
- executable path is the verified `uaa-bootstrap` file inside that temporary
  directory
- local installer argv is structured and shell-free

Any mismatch must abort before installer code runs.

## Approval Token Binding

Noninteractive `--yes` requires a chmod `0600`, single-use approval token whose
preview hash matches the current bootstrap preview. Tokens bind release tag,
asset, digest, signature reference, provenance mode, target, safe path
summaries, milestone ref, approved repo, and pinned OpenWebUI image. Tokens
expire after 15 minutes and are marked used before any download.

## Authority Boundary

Allowed:

- download the exact release artifact and exact provenance artifact from the
  approved GitHub Release URL derived from the explicit release tag
- read a local provenance file only after canonical user-scope validation
- unpack the verified artifact into a temporary directory
- run only the verified local `uaa-bootstrap install --target openwebui` argv
- write a redacted chmod `0600` receipt

Denied:

- Python, Node, npm, Homebrew, Docker Desktop, llama.cpp, provider, model,
  plugin, browser, mobile, remote, daemon, launch-agent, or credential setup
- OpenWebUI admin/plugin/database mutation
- raw prompt, response, provider payload, raw log, environment dump, cookie,
  credential, provider key, username, or shell-history output
- shell strings, `sudo`, pipe-to-shell, `raw.githubusercontent.com`, mutable
  `main`, `latest`, arbitrary URL execution, or unverified script execution

## Receipt And Rollback Binding

Receipts must be safe summaries only and chmod `0600`. They may include release
tag, asset name, digest status, provenance status, target, safe path summaries,
safe command previews, result status, timestamp, and rollback hints. They must
not contain secrets, environment values, usernames, raw logs, or full home-path
expansions.

Rollback instructions and any future rollback command may remove or restore
only receipt-bound or marker-owned files named in a receipt or carrying an
installer-owned marker. This trust root does not authorize removal of unrelated
user files.
