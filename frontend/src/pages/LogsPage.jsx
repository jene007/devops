import React from "react";

export default function LogsPage({ logs }) {
  return (
    <section className="panel logs-panel">
      <h2>Pipeline Logs</h2>
      <pre>{logs.join("\n")}</pre>
    </section>
  );
}
