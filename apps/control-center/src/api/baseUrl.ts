import { containsSecretLike, sanitizeForDisplay } from "./redaction";

const LOOPBACK_HOSTS = new Set(["localhost", "127.0.0.1", "::1", "[::1]"]);

export interface ApiBaseUrlPolicy {
  allowed: boolean;
  baseUrl: string;
  label: string;
  safeMessage: string;
  warnings: string[];
}

export function resolveApiBaseUrl(rawBaseUrl: string | undefined): ApiBaseUrlPolicy {
  const raw = (rawBaseUrl ?? "").trim();
  if (!raw) {
    return allowedPolicy("", "relative local API");
  }
  if (containsSecretLike(raw)) {
    return blockedPolicy("blocked secret-like API base", "SECRET_LIKE_API_BASE_URL_REJECTED");
  }
  if (isRelativeApiBase(raw)) {
    return allowedPolicy(normalizeBaseUrl(raw), "relative local API");
  }

  try {
    const url = new URL(raw);
    const hostname = url.hostname.toLowerCase();
    if (!["http:", "https:"].includes(url.protocol) || !LOOPBACK_HOSTS.has(hostname)) {
      return blockedPolicy("blocked non-local API base", "EXTERNAL_API_BASE_URL_BLOCKED");
    }
    if (url.username || url.password || containsSecretLike(url.search)) {
      return blockedPolicy("blocked secret-like API base", "SECRET_LIKE_API_BASE_URL_REJECTED");
    }
    return allowedPolicy(normalizeBaseUrl(url.toString()), localLabel(url));
  } catch {
    return blockedPolicy("blocked unsupported API base", "UNSUPPORTED_API_BASE_URL");
  }
}

function isRelativeApiBase(value: string): boolean {
  return value.startsWith("/") && !value.startsWith("//") && !value.includes("://");
}

function normalizeBaseUrl(value: string): string {
  return value.replace(/\/+$/, "");
}

function localLabel(url: URL): string {
  return `${url.protocol}//${url.host.replace("[::1]", "::1")}`;
}

function allowedPolicy(baseUrl: string, label: string): ApiBaseUrlPolicy {
  return {
    allowed: true,
    baseUrl,
    label,
    safeMessage: "Local API base is allowed for read-only and preview-only Control Center requests.",
    warnings: []
  };
}

function blockedPolicy(label: string, warning: string): ApiBaseUrlPolicy {
  return {
    allowed: false,
    baseUrl: "",
    label,
    safeMessage: sanitizeForDisplay("API base URL is not allowed for this local-only Control Center shell."),
    warnings: [warning]
  };
}
