import dns from "node:dns/promises";
import http from "node:http";
import https from "node:https";
import net from "node:net";

export const HARNESS_ORIGIN = "http://127.0.0.1:18008";
export const MAX_RESPONSE_BYTES = 1024 * 1024;
export const DEFAULT_TIMEOUT_MS = 10_000;
export const MAX_REQUEST_BYTES = 128 * 1024;

export class MatrixTargetPolicyError extends Error {
  constructor(code) {
    super(code);
    this.name = "MatrixTargetPolicyError";
    this.code = code;
  }
}

function ipv4Number(address) {
  return address.split(".").reduce((value, octet) => (value << 8) + Number(octet), 0) >>> 0;
}

function inV4Range(value, start, bits) {
  const mask = bits === 0 ? 0 : (0xffffffff << (32 - bits)) >>> 0;
  return (value & mask) === (ipv4Number(start) & mask);
}

function parseIpv6Words(address) {
  let normalized = address.toLowerCase().replace(/^\[|\]$/g, "");
  if (normalized.includes("%")) return null;
  const dottedTail = normalized.match(/(?:^|:)(\d+\.\d+\.\d+\.\d+)$/)?.[1];
  if (dottedTail) {
    if (net.isIP(dottedTail) !== 4) return null;
    const value = ipv4Number(dottedTail);
    normalized = normalized.slice(0, -dottedTail.length) +
      `${(value >>> 16).toString(16)}:${(value & 0xffff).toString(16)}`;
  }
  const halves = normalized.split("::");
  if (halves.length > 2) return null;
  const left = halves[0] ? halves[0].split(":") : [];
  const right = halves.length === 2 && halves[1] ? halves[1].split(":") : [];
  if (halves.length === 1 && left.length !== 8) return null;
  const fill = halves.length === 2 ? 8 - left.length - right.length : 0;
  if (fill < 1 && halves.length === 2) return null;
  const parts = [...left, ...Array(fill).fill("0"), ...right];
  if (parts.length !== 8 || !parts.every((part) => /^[0-9a-f]{1,4}$/.test(part))) {
    return null;
  }
  return parts.map((part) => Number.parseInt(part, 16));
}

function normalizedHostname(hostname) {
  return hostname.replace(/^\[|\]$/g, "");
}

function embeddedV4(words) {
  const compatible = words.slice(0, 6).every((word) => word === 0);
  const mapped = words.slice(0, 5).every((word) => word === 0) && words[5] === 0xffff;
  const wellKnownNat64 = words[0] === 0x64 && words[1] === 0xff9b &&
    words.slice(2, 6).every((word) => word === 0);
  if (!compatible && !mapped && !wellKnownNat64) return null;
  return `${words[6] >>> 8}.${words[6] & 0xff}.${words[7] >>> 8}.${words[7] & 0xff}`;
}

export function isForbiddenAddress(address) {
  const family = net.isIP(address);
  if (family === 4) {
    const value = ipv4Number(address);
    return [
      ["0.0.0.0", 8], ["10.0.0.0", 8], ["100.64.0.0", 10],
      ["127.0.0.0", 8], ["169.254.0.0", 16], ["172.16.0.0", 12],
      ["192.0.0.0", 24], ["192.0.2.0", 24], ["192.168.0.0", 16],
      ["198.18.0.0", 15], ["198.51.100.0", 24], ["203.0.113.0", 24],
      ["224.0.0.0", 4], ["240.0.0.0", 4],
    ].some(([start, bits]) => inV4Range(value, start, bits));
  }
  if (family === 6) {
    const words = parseIpv6Words(address);
    if (words === null) return true;
    const translated = embeddedV4(words);
    if (translated !== null && isForbiddenAddress(translated)) return true;
    return (
      words[0] === 0 ||
      (words[0] & 0xfe00) === 0xfc00 ||
      (words[0] & 0xffc0) === 0xfe80 ||
      (words[0] & 0xffc0) === 0xfec0 ||
      (words[0] & 0xff00) === 0xff00 ||
      (words[0] === 0x64 && words[1] === 0xff9b && words[2] === 1) ||
      (words[0] === 0x2001 && words[1] === 0) ||
      words[0] === 0x2002 ||
      (words[0] === 0x2001 && words[1] === 0x0db8)
    );
  }
  return true;
}

export function validateMatrixDelegatedOrigin(rawUrl, { allowHarness = false } = {}) {
  let parsed;
  try {
    parsed = new URL(rawUrl);
  } catch {
    throw new MatrixTargetPolicyError("MATRIX_TARGET_URL_INVALID");
  }
  if (parsed.username || parsed.password || parsed.hash || parsed.search) {
    throw new MatrixTargetPolicyError("MATRIX_TARGET_AUTHORITY_COMPONENT_DENIED");
  }
  const hostname = normalizedHostname(parsed.hostname);
  if (hostname.includes("%")) {
    throw new MatrixTargetPolicyError("MATRIX_TARGET_ZONE_IDENTIFIER_DENIED");
  }
  if (parsed.origin === HARNESS_ORIGIN && allowHarness) return parsed;
  if (parsed.protocol !== "https:" || parsed.port && parsed.port !== "443") {
    throw new MatrixTargetPolicyError("MATRIX_TARGET_HTTPS_REQUIRED");
  }
  if (hostname.toLowerCase() === "localhost") {
    throw new MatrixTargetPolicyError("MATRIX_TARGET_LOCALHOST_DENIED");
  }
  const literalFamily = net.isIP(hostname);
  if (literalFamily && isForbiddenAddress(hostname)) {
    throw new MatrixTargetPolicyError("MATRIX_TARGET_PRIVATE_ADDRESS_DENIED");
  }
  return parsed;
}

export async function validateMatrixTarget(rawUrl, { lookup = dns.lookup, allowHarness = false } = {}) {
  let parsed;
  try {
    parsed = new URL(rawUrl);
  } catch {
    throw new MatrixTargetPolicyError("MATRIX_TARGET_URL_INVALID");
  }
  if (parsed.username || parsed.password || parsed.hash || parsed.search) {
    throw new MatrixTargetPolicyError("MATRIX_TARGET_AUTHORITY_COMPONENT_DENIED");
  }
  const hostname = normalizedHostname(parsed.hostname);
  if (hostname.includes("%")) {
    throw new MatrixTargetPolicyError("MATRIX_TARGET_ZONE_IDENTIFIER_DENIED");
  }
  const origin = parsed.origin;
  if (origin === HARNESS_ORIGIN && allowHarness) return parsed;
  if (parsed.protocol !== "https:" || parsed.port && parsed.port !== "443") {
    throw new MatrixTargetPolicyError("MATRIX_TARGET_HTTPS_REQUIRED");
  }
  if (hostname.toLowerCase() === "localhost") {
    throw new MatrixTargetPolicyError("MATRIX_TARGET_LOCALHOST_DENIED");
  }
  const literalFamily = net.isIP(hostname);
  if (literalFamily && isForbiddenAddress(hostname)) {
    throw new MatrixTargetPolicyError("MATRIX_TARGET_PRIVATE_ADDRESS_DENIED");
  }
  if (!literalFamily) {
    let records;
    try {
      records = await lookup(hostname, { all: true, verbatim: true });
    } catch {
      throw new MatrixTargetPolicyError("MATRIX_TARGET_DNS_FAILED");
    }
    if (!records.length || records.some(({ address }) => isForbiddenAddress(address))) {
      throw new MatrixTargetPolicyError("MATRIX_TARGET_DNS_SCOPE_DENIED");
    }
  }
  return parsed;
}

async function resolvePinnedAddress(target, lookup) {
  if (target.origin === HARNESS_ORIGIN) {
    return { address: "127.0.0.1", family: 4 };
  }
  const hostname = normalizedHostname(target.hostname);
  const literalFamily = net.isIP(hostname);
  if (literalFamily) {
    if (isForbiddenAddress(hostname)) {
      throw new MatrixTargetPolicyError("MATRIX_TARGET_PRIVATE_ADDRESS_DENIED");
    }
    return { address: hostname, family: literalFamily };
  }
  let records;
  try {
    records = await lookup(hostname, { all: true, verbatim: true });
  } catch {
    throw new MatrixTargetPolicyError("MATRIX_TARGET_DNS_FAILED");
  }
  if (!records.length || records.some(({ address }) => isForbiddenAddress(address))) {
    throw new MatrixTargetPolicyError("MATRIX_TARGET_DNS_SCOPE_DENIED");
  }
  return records[0];
}

async function requestBody(request) {
  if (request.method === "GET" || request.method === "HEAD") return null;
  const bytes = new Uint8Array(await request.arrayBuffer());
  if (bytes.byteLength > MAX_REQUEST_BYTES) {
    throw new MatrixTargetPolicyError("MATRIX_HTTP_REQUEST_TOO_LARGE");
  }
  return bytes;
}

async function pinnedNodeFetch(target, init, lookup) {
  const request = new Request(target, init);
  const body = await requestBody(request);
  const pinned = await resolvePinnedAddress(target, lookup);
  const transport = target.protocol === "https:" ? https : http;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);
  if (request.signal) {
    if (request.signal.aborted) controller.abort();
    else request.signal.addEventListener("abort", () => controller.abort(), { once: true });
  }
  try {
    return await new Promise((resolve, reject) => {
      const outgoing = transport.request(target, {
        method: request.method,
        headers: Object.fromEntries(request.headers.entries()),
        signal: controller.signal,
        lookup(_hostname, _options, callback) {
          callback(null, pinned.address, pinned.family);
        },
        ...(target.protocol === "https:" ? { servername: normalizedHostname(target.hostname) } : {}),
      }, (incoming) => {
        const status = incoming.statusCode || 0;
        if (status >= 300 && status < 400) {
          incoming.resume();
          reject(new MatrixTargetPolicyError("MATRIX_HTTP_REDIRECT_DENIED"));
          return;
        }
        const declared = Number(incoming.headers["content-length"] || 0);
        if (declared > MAX_RESPONSE_BYTES) {
          incoming.destroy();
          reject(new MatrixTargetPolicyError("MATRIX_HTTP_RESPONSE_TOO_LARGE"));
          return;
        }
        const chunks = [];
        let size = 0;
        incoming.on("data", (chunk) => {
          size += chunk.byteLength;
          if (size > MAX_RESPONSE_BYTES) {
            incoming.destroy(new MatrixTargetPolicyError("MATRIX_HTTP_RESPONSE_TOO_LARGE"));
            return;
          }
          chunks.push(chunk);
        });
        incoming.on("error", reject);
        incoming.on("end", () => resolve(new Response(Buffer.concat(chunks), {
          status,
          headers: incoming.headers,
        })));
      });
      outgoing.on("error", reject);
      if (body) outgoing.write(body);
      outgoing.end();
    });
  } finally {
    clearTimeout(timeout);
  }
}

export function createBoundedFetch({
  fetchImpl,
  lookup = dns.lookup,
  allowHarness = false,
  allowedRequests = [],
} = {}) {
  const requestPolicy = new Set(allowedRequests);
  return async (input, init = {}) => {
    const sourceRequest = input instanceof Request ? input : null;
    const inputUrl = typeof input === "string" || input instanceof URL ? String(input) : input.url;
    const target = await validateMatrixTarget(inputUrl, { lookup, allowHarness });
    const method = String(init.method || sourceRequest?.method || "GET").toUpperCase();
    if (method !== "GET") {
      throw new MatrixTargetPolicyError("MATRIX_HTTP_METHOD_DENIED");
    }
    if (!requestPolicy.has(`${method} ${target.pathname}`)) {
      throw new MatrixTargetPolicyError("MATRIX_HTTP_OPERATION_SCOPE_DENIED");
    }
    let response;
    const effectiveInit = {
      ...(sourceRequest ? {
        body: method === "GET" ? undefined : sourceRequest.body,
        headers: sourceRequest.headers,
        method: sourceRequest.method,
        signal: sourceRequest.signal,
        duplex: sourceRequest.body ? "half" : undefined,
      } : {}),
      ...init,
      method,
      redirect: "manual",
    };
    if (fetchImpl) {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);
      try {
        response = await fetchImpl(target, { ...effectiveInit, signal: controller.signal });
      } finally {
        clearTimeout(timeout);
      }
    } else {
      response = await pinnedNodeFetch(target, effectiveInit, lookup);
    }
    if (response.status >= 300 && response.status < 400) {
      throw new MatrixTargetPolicyError("MATRIX_HTTP_REDIRECT_DENIED");
    }
    const declared = Number(response.headers.get("content-length") || 0);
    if (declared > MAX_RESPONSE_BYTES) {
      throw new MatrixTargetPolicyError("MATRIX_HTTP_RESPONSE_TOO_LARGE");
    }
    return response;
  };
}

export async function boundedJson(response) {
  const bytes = new Uint8Array(await response.arrayBuffer());
  if (bytes.byteLength > MAX_RESPONSE_BYTES) {
    throw new MatrixTargetPolicyError("MATRIX_HTTP_RESPONSE_TOO_LARGE");
  }
  if (!response.ok) {
    throw new MatrixTargetPolicyError(
      response.status === 429 ? "MATRIX_RATE_LIMITED" : "MATRIX_HTTP_REQUEST_FAILED",
    );
  }
  try {
    return JSON.parse(new TextDecoder().decode(bytes));
  } catch {
    throw new MatrixTargetPolicyError("MATRIX_HTTP_JSON_INVALID");
  }
}
