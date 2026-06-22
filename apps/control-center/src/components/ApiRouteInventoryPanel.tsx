import type { ApiRouteInventory } from "../api/types";
import { EmptyState } from "./DataState";

export function ApiRouteInventoryPanel({ routes }: { routes: ApiRouteInventory }) {
  return (
    <section className="panel" aria-labelledby="api-routes-heading">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Backend contract</p>
          <h2 id="api-routes-heading">API Routes</h2>
        </div>
        <span>{routes.route_count} listed</span>
      </div>
      <p className="section-copy">
        Read-only and preview-only route inventory. Classification is posture
        evidence only; this shell does not add API routes.
      </p>
      {routes.routes.length > 0 ? (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Path</th>
                <th>Methods</th>
                <th>Operation</th>
                <th>Classification</th>
                <th>Validation only</th>
              </tr>
            </thead>
            <tbody>
              {routes.routes.map((route) => (
                <tr key={`${route.path}-${route.operation_id}`}>
                  <td>{route.path}</td>
                  <td>{route.methods?.join(", ") ?? "not returned"}</td>
                  <td>{route.operation_id}</td>
                  <td>
                    <span>{route.route_classification ?? "missing"}</span>
                    {route.classification_reason ? (
                      <small>{route.classification_reason}</small>
                    ) : null}
                  </td>
                  <td>{route.validation_only ? "yes" : "no"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState
          title="No routes listed"
          message="No API routes were returned by the local backend or mock."
        />
      )}
    </section>
  );
}
