const SECRET_PATTERNS = [
  /(?:^|[?&\s])(?:auth|credential|key)\s*[:=]\s*[\w./:-]{8,}/gi,
  /api[_-]?key\s*[:=]\s*[\w./:-]{8,}/gi,
  /token\s*[:=]\s*[\w./:-]{8,}/gi,
  /password\s*[:=]\s*\S{6,}/gi,
  /secret\s*[:=]\s*\S{6,}/gi,
  /authorization\s*[:=]\s*\S+/gi,
  /cookie\s*[:=]\s*\S+/gi,
  new RegExp("-".repeat(5) + "BEGIN[\\s\\S]*?PRIVATE" + " KEY" + "-".repeat(5), "gi"),
];

export function sanitizeForDisplay(value: unknown): string {
  const text = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  if (!text) {
    return "";
  }
  return SECRET_PATTERNS.reduce((safe, pattern) => safe.replace(pattern, "[redacted]"), text);
}

export function containsSecretLike(value: unknown): boolean {
  const text = typeof value === "string" ? value : JSON.stringify(value);
  if (!text) {
    return false;
  }
  return SECRET_PATTERNS.some((pattern) => {
    pattern.lastIndex = 0;
    return pattern.test(text);
  });
}
