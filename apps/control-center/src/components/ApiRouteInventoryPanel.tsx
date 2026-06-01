import type { ApiRouteInventory } from "../api/types";

export function ApiRouteInventoryPanel({ routes }: { routes: ApiRouteInventory }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>API Routes</h2>
        <span>{routes.route_count} listed</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Path</th>
              <th>Methods</th>
              <th>Operation</th>
              <th>Validation only</th>
            </tr>
          </thead>
          <tbody>
            {routes.routes.map((route) => (
              <tr key={`${route.path}-${route.operation_id}`}>
                <td>{route.path}</td>
                <td>{route.methods.join(", ")}</td>
                <td>{route.operation_id}</td>
                <td>{route.validation_only ? "yes" : "no"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
