import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./App";
import { consumeLocalApiBearerFromLocation } from "./api/client";
import "./styles.css";

consumeLocalApiBearerFromLocation();

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
