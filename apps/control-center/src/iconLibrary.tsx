import React from "react";
import ReactDOM from "react-dom/client";
import { IconLibraryPanel } from "./components/IconLibraryPanel";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <main className="icon-library-main">
      <IconLibraryPanel />
    </main>
  </React.StrictMode>,
);
