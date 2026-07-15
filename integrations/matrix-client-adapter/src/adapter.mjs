import crypto from "node:crypto";
import { createClient } from "matrix-js-sdk";
import { logger as matrixLogger } from "matrix-js-sdk/lib/logger.js";
import { validateAuthMetadata } from "matrix-js-sdk/lib/oidc/validate.js";

import {
  boundedJson,
  createBoundedFetch,
  validateMatrixDelegatedOrigin,
  validateMatrixTarget,
} from "./target-policy.mjs";

const SDK_VERSION = "41.9.0";
const MAX_LOGIN_FLOWS = 16;

matrixLogger.disableAll();

function stableRef(prefix, value) {
  return `${prefix}:sha256:${crypto.createHash("sha256").update(JSON.stringify(value)).digest("hex")}`;
}

function safeCapabilities(flows, oauthAdvertised) {
  const types = new Set(flows.slice(0, MAX_LOGIN_FLOWS).map((flow) => flow?.type));
  return {
    credential_auth: types.has("m.login.password"),
    browser_sso: types.has("m.login.sso"),
    oauth: Boolean(oauthAdvertised),
  };
}

function client(baseUrl, fetchFn, credentials = {}) {
  return createClient({
    baseUrl,
    fetchFn,
    useAuthorizationHeader: true,
    localTimeoutMs: 10_000,
    ...credentials,
  });
}

function targetDependencies(input, dependencies) {
  return {
    ...dependencies,
    allowHarness: input.endpoint_class_ref === "endpoint-class-ref:matrix:local-harness",
  };
}

async function discovery(input, dependencies) {
  const targetPolicy = targetDependencies(input, dependencies);
  const fetchFn = createBoundedFetch({
    ...targetPolicy,
    allowedRequests: ["GET /.well-known/matrix/client"],
  });
  const discoveryTarget = await validateMatrixTarget(input.discovery_origin, targetPolicy);
  if (discoveryTarget.pathname !== "/" || discoveryTarget.search || discoveryTarget.hash) {
    throw new Error("MATRIX_DISCOVERY_ORIGIN_SCOPE_INVALID");
  }
  const wellKnownTarget = await validateMatrixTarget(
    `${discoveryTarget.origin}/.well-known/matrix/client`,
    targetPolicy,
  );
  const wellKnown = await boundedJson(await fetchFn(wellKnownTarget));
  const baseUrl = wellKnown?.["m.homeserver"]?.base_url;
  if (typeof baseUrl !== "string") throw new Error("MATRIX_WELL_KNOWN_HOMESERVER_MISSING");
  const validatedBase = validateMatrixDelegatedOrigin(baseUrl, targetPolicy);
  const homeserverObservationRef = stableRef(
    "observation-ref:matrix-homeserver",
    validatedBase.origin,
  );
  return {
    runtime_status: "discovered",
    homeserver_observation_ref: homeserverObservationRef,
    discovery_freshness_ref: stableRef("freshness-ref:matrix-discovery", {
      homeserver_observation_ref: homeserverObservationRef,
    }),
    sdk_version_ref: "version-ref:matrix-js-sdk:41-9-0",
  };
}

async function readBoundedAuthMetadata(base, versions, fetchFn) {
  const supportedVersions = Array.isArray(versions?.versions) ? versions.versions : [];
  const path = supportedVersions.includes("v1.15")
    ? "/_matrix/client/v1/auth_metadata"
    : "/_matrix/client/unstable/org.matrix.msc2965/auth_metadata";
  const response = await fetchFn(new URL(path, base.origin));
  if (response.status === 404) return null;
  return boundedJson(response);
}

async function authMethods(input, dependencies) {
  const targetPolicy = targetDependencies(input, dependencies);
  const fetchFn = createBoundedFetch({
    ...targetPolicy,
    allowedRequests: [
      "GET /_matrix/client/versions",
      "GET /_matrix/client/v3/login",
      "GET /_matrix/client/v1/auth_metadata",
      "GET /_matrix/client/unstable/org.matrix.msc2965/auth_metadata",
    ],
  });
  const base = await validateMatrixTarget(input.base_url, targetPolicy);
  const matrixClient = client(base.origin, fetchFn);
  const [versions, login] = await Promise.all([
    matrixClient.getVersions(),
    matrixClient.loginFlows(),
  ]);
  const authMetadata = await readBoundedAuthMetadata(base, versions, fetchFn);
  let oauthCompatible = false;
  if (authMetadata !== null) {
    try {
      validateAuthMetadata(authMetadata);
      oauthCompatible = true;
    } catch {
      // Invalid metadata remains observed evidence, never a callable auth claim.
    }
  }
  return {
    runtime_status: "ready_for_authentication",
    homeserver_observation_ref: stableRef("observation-ref:matrix-homeserver", base.origin),
    versions_ref: stableRef("version-set-ref:matrix-homeserver", versions),
    login_flows_ref: stableRef("login-flow-set-ref:matrix-homeserver", login?.flows || []),
    auth_metadata_ref: authMetadata
      ? stableRef("auth-metadata-ref:matrix-homeserver", authMetadata)
      : undefined,
    // Local schema compatibility is evidence only; issuer/key validation is separate.
    capabilities: safeCapabilities(login?.flows || [], oauthCompatible),
    sdk_version_ref: "version-ref:matrix-js-sdk:41-9-0",
  };
}

export async function executeMatrixAdapter(input, dependencies = {}) {
  switch (input.operation) {
    case "discovery_read": return discovery(input, dependencies);
    case "auth_methods_read": return authMethods(input, dependencies);
    case "credential_auth_create":
    case "sso_launch":
    case "sso_callback_consume":
    case "refresh":
    case "logout":
    case "revoke_all":
    case "credential_store_rotate":
    case "credential_delete":
      throw new Error("MATRIX_ADAPTER_OPERATION_BLOCKED_PENDING_AUTHENTICATED_BROKER");
    default: throw new Error("MATRIX_ADAPTER_OPERATION_UNSUPPORTED");
  }
}

export { SDK_VERSION, stableRef };
