import React, { useMemo, useState } from "react";
import { runCommandStream } from "./api";

const mockStatus = [
  { label: "Terraform", state: "Ready", tone: "neutral" },
  { label: "Kubernetes", state: "Connected", tone: "ok" },
  { label: "Self-Healing", state: "Armed", tone: "warn" },
  { label: "Prometheus", state: "Scraping", tone: "ok" },
];

const STEP_ICONS = {
  pending: "○",
  active: "◉",
  done: "●",
  error: "✕",
};

export default function App() {
  const [prompt, setPrompt] = useState("");
  const [dryRun, setDryRun] = useState(false);
  const [enableDocker, setEnableDocker] = useState(false);
  const [provider, setProvider] = useState("auto");
  const [lastRunAt, setLastRunAt] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [logs, setLogs] = useState([
    "[BOOT] JARVIS dashboard initialized",
    "[INFO] Waiting for deployment command",
  ]);
  const [isRunning, setIsRunning] = useState(false);

  const statusText = useMemo(() => (isRunning ? "Executing" : "Idle"), [isRunning]);

  const initializeTimeline = (steps) => {
    const items = steps.map((name, index) => ({
      id: `${name}-${index}`,
      name,
      state: "pending",
      detail: index === 0 ? "Queued" : "Queued",
    }));
    setTimeline(items);
    return items;
  };

  const updateStepState = (stepName, state, detail) => {
    setTimeline((prev) =>
      prev.map((step) => {
        if (step.name === stepName) {
          return { ...step, state, detail: detail || step.detail };
        }
        return step;
      })
    );
  };

  const markError = (message) => {
    setTimeline((prev) => {
      const activeIndex = prev.findIndex((step) => step.state === "active");
      if (activeIndex === -1 && prev.length > 0) {
        return prev.map((step, idx) =>
          idx === prev.length - 1
            ? { ...step, state: "error", detail: message }
            : step
        );
      }

      return prev.map((step, idx) =>
        idx === activeIndex ? { ...step, state: "error", detail: message } : step
      );
    });
  };

  const submit = async (e) => {
    e.preventDefault();
    const runTime = new Date().toLocaleTimeString();
    setLastRunAt(runTime);
    setTimeline([]);
    setIsRunning(true);
    setLogs((prev) => [
      ...prev,
      `[USER] ${prompt}`,
      `[MODE] dry_run=${dryRun} provider=${provider} docker=${enableDocker}`,
      "[INFO] Submitting pipeline request...",
    ]);

    try {
      const result = await runCommandStream(
        prompt,
        { dryRun, enableDocker, provider },
        {
          onRunStart: (data) => initializeTimeline(data.steps ?? []),
          onStep: (data) => updateStepState(data.step, data.state, data.detail),
          onLog: (data) => {
            const level = data?.level || "INFO";
            const message = data?.message || "";
            if (!message) {
              return;
            }
            setLogs((prev) => [...prev, `[${level}] ${message}`]);
          },
        }
      );

      if (result.status === "incomplete") {
        const questions = (result.questions ?? []).map((q) => `- ${q}`);
        setLogs((prev) => [
          ...prev,
          "[INFO] More information required:",
          ...questions,
        ]);
        return;
      }

      if (result.status === "error" || result.ok === false) {
        throw new Error(result.message || "Pipeline request failed");
      }

      const planned = (result.planned_steps ?? []).map((step) => `[PLAN] ${step}`);
      setLogs((prev) => [
        ...prev,
        `[INFO] ${result.message ?? "Request accepted"}`,
        `[AI] ${JSON.stringify(result.config ?? {}, null, 2)}`,
        ...planned,
        "[DONE] Pipeline finished successfully",
      ]);
    } catch (error) {
      markError(error.message);
      setLogs((prev) => [...prev, `[ERROR] ${error.message}`]);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="page">
      <header className="hero">
        <h1>JARVIS DevOps Control Grid</h1>
        <p>Natural-language infrastructure automation with self-healing intelligence.</p>
      </header>

      <section className="panel status-panel">
        <div className="panel-title-row">
          <h2>System Status: {statusText}</h2>
          <span className="chip">Last Run: {lastRunAt ?? "N/A"}</span>
        </div>
        <div className="status-grid">
          {mockStatus.map((item) => (
            <article key={item.label} className={`status-card status-${item.tone}`}>
              <span>{item.label}</span>
              <strong>{item.state}</strong>
            </article>
          ))}
        </div>
      </section>

      <section className="panel command-panel">
        <h2>Command Center</h2>
        <form onSubmit={submit}>
          <div className="control-grid">
            <label className="control-item checkbox-item">
              <input
                type="checkbox"
                checked={dryRun}
                onChange={(e) => setDryRun(e.target.checked)}
              />
              Dry Run
            </label>

            <label className="control-item checkbox-item">
              <input
                type="checkbox"
                checked={enableDocker}
                onChange={(e) => setEnableDocker(e.target.checked)}
              />
              Build Docker
            </label>

            <label className="control-item">
              Provider
              <select value={provider} onChange={(e) => setProvider(e.target.value)}>
                <option value="auto">Auto</option>
                <option value="openai">OpenAI</option>
                <option value="huggingface">Hugging Face</option>
                <option value="heuristic">Heuristic</option>
              </select>
            </label>
          </div>

          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={4}
            placeholder="Deploy my app globally with autoscaling"
          />
          <div className="button-row">
            <button type="submit" disabled={isRunning || !prompt.trim()}>
              {isRunning ? "Executing..." : "Run Autonomous Pipeline"}
            </button>
            <button
              type="button"
              className="ghost"
              onClick={() => setLogs(["[BOOT] Logs cleared", "[INFO] Waiting for deployment command"])}
              disabled={isRunning}
            >
              Clear Logs
            </button>
          </div>
        </form>
      </section>

      <section className="panel timeline-panel">
        <div className="panel-title-row">
          <h2>Execution Timeline</h2>
          <span className="chip">Live</span>
        </div>
        <div className="timeline-list">
          {timeline.length === 0 ? (
            <p className="timeline-empty">Start a run to see Parse &rarr; Plan &rarr; Terraform &rarr; K8s &rarr; Monitor.</p>
          ) : (
            timeline.map((step) => (
              <article key={step.id} className={`timeline-step timeline-${step.state}`}>
                <span className="timeline-dot">{STEP_ICONS[step.state]}</span>
                <div className="timeline-content">
                  <strong>{step.name}</strong>
                  <small>{step.detail}</small>
                </div>
              </article>
            ))
          )}
        </div>
      </section>

      <section className="panel logs-panel">
        <h2>Pipeline Logs</h2>
        <pre>{logs.join("\n")}</pre>
      </section>
    </div>
  );
}
