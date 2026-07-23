function stablePortOffset(identity: string): number {
  let hash = 2166136261;
  for (const character of identity) {
    hash ^= character.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0) % 10_000;
}

function configuredPort(name: string, fallback: number): number {
  const configured = process.env[name];
  if (configured !== undefined) return Number(configured);

  const runId = process.env.GITHUB_RUN_ID;
  if (!runId) return fallback;
  const identity = [
    runId,
    process.env.GITHUB_RUN_ATTEMPT ?? "1",
    process.env.RUNNER_NAME ?? "runner",
  ].join(":");
  const offset = stablePortOffset(identity);
  return fallback === 5177 ? 20_000 + offset : 40_000 + offset;
}

export const visualPort = configuredPort("CONTROL_CENTER_VISUAL_PORT", 5177);
export const backendTruthPort = configuredPort(
  "CONTROL_CENTER_BACKEND_TRUTH_PORT",
  18117,
);
