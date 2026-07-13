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

const UNSAFE_ERROR_TEXT_PATTERNS = [
  /(?:^|\s)\/(?:Users|home|private|var)\//i,
  /[a-z]:\\/i,
  /\b(?:file|https?):\/\//i,
  /<(?:html|body|script)\b/i,
  /\b(?:raw[_ -]?(?:prompt|response|page|payload|log)|provider[_ -]?payload)\s*[:=]/i,
];
const MAX_SAFE_API_ERROR_LENGTH = 320;

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

export function safeApiErrorMessage(value: unknown, fallback: string): string {
  if (typeof value !== "object" || value === null) {
    return fallback;
  }
  const envelope = value as Record<string, unknown>;
  const error = envelope.error;
  const detail = envelope.detail;
  let candidate: unknown;
  if (
    typeof error === "object" &&
    error !== null &&
    (error as Record<string, unknown>).details_redacted === true
  ) {
    candidate = (error as Record<string, unknown>).safe_message;
  } else if (typeof detail === "object" && detail !== null) {
    const detailRecord = detail as Record<string, unknown>;
    const code = detailRecord.code;
    if (
      typeof code === "string" &&
      /^[A-Z][A-Z0-9_]{2,127}$/.test(code)
    ) {
      candidate = detailRecord.safe_message;
    }
  }
  if (typeof candidate !== "string") {
    return fallback;
  }
  const trimmed = candidate.trim();
  if (
    trimmed.length === 0 ||
    trimmed.length > MAX_SAFE_API_ERROR_LENGTH ||
    containsSecretLike(trimmed) ||
    UNSAFE_ERROR_TEXT_PATTERNS.some((pattern) => pattern.test(trimmed))
  ) {
    return fallback;
  }
  const sanitized = sanitizeForDisplay(trimmed);
  return sanitized === trimmed ? sanitized : fallback;
}
