# Ultimate AI Agent Version

Current active baseline: **v0.37.0**

v0.37.0 implements M33 First Safe Local File Read Proposal, Redacted Preview
Only. It adds a governed redacted file preview proposal tool through the tool
runtime adapter, safe root and relative path policies, bounded text preview
reads, redaction-before-return guarantees, redacted preview result contracts,
no-raw-content receipt plans, documentation, documentation-integrity checks,
static safety verification, and Foundation Gate coverage.

It allows only bounded redacted previews under server-owned safe roots, returns
no raw file content or raw absolute paths, blocks hidden/secret-like paths,
binary files, unsupported encodings, symlinks, traversal, full-file reads,
directory listing, and file mutation, and preserves M34 as future broader file
capability work. It adds no raw file output, file mutation, memory writes,
network calls, model/provider calls, context injection, backend raw-file or
execute routes, Control Center raw-preview or execute controls, dependencies,
or production authority.
