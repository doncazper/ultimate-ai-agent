# Checkpoint M119 Import Notes

Checkpoint M119 implements Production Red-Team Harness as a contract-only,
review-only checkpoint over safe refs.

The product baseline remains v1.7.2. The release tag is checkpoint-m119. M150
remains the planned v1.0.0-alpha target, and beta begins only after alpha UI
and supporting safety/product work are reviewed and promoted.

M119 must not add red-team execution, attack automation, scanner runtime,
external probing, exploit generation, network access, credential handling,
backend routes, Control Center controls, dependencies, M120 work, beta release,
or production authority.
