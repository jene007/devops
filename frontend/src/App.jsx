import React, { useMemo, useState } from "react";
import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { runCommandStream } from "./api";
import OverviewPage from "./pages/OverviewPage";
import CommandPage from "./pages/CommandPage";
import TimelinePage from "./pages/TimelinePage";
import LogsPage from "./pages/LogsPage";

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

const COMMAND_PRESETS = [
  "Deploy my app globally with autoscaling",
  "Provision staging on aws us-east-1 with dry run",
  "Deploy from repo with docker image build and kubernetes rollout",
  "Run Terraform plan then apply and verify monitoring",
];

const LEVEL_COLORS = {
  INFO: "neutral",
  PLAN: "neutral",
  DONE: "ok",
  ERROR: "error",
  BOOT: "neutral",
  USER: "neutral",
  MODE: "neutral",
  AI: "warn",
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

  const timelineStats = useMemo(() => {
    return timeline.reduce(
      (acc, item) => {
        acc.total += 1;
        acc[item.state] = (acc[item.state] || 0) + 1;
        return acc;
      },
      { total: 0, pending: 0, active: 0, done: 0, error: 0 }
    );
  }, [timeline]);

  const logStats = useMemo(() => {
    return logs.reduce(
      (acc, entry) => {
        const match = entry.match(/^\[([A-Z]+)\]/);
        const level = match?.[1] || "INFO";
        acc[level] = (acc[level] || 0) + 1;
        acc.total += 1;
        acc.lastLevel = level;
        return acc;
      },
      { total: 0, lastLevel: "INFO" }
    );
  }, [logs]);

  const statusText = useMemo(() => (isRunning ? "Executing" : "Idle"), [isRunning]);

  const completionRate = useMemo(() => {
    if (!timelineStats.total) {
      return "0%";
    }
    const value = Math.round((timelineStats.done / timelineStats.total) * 100);
    return `${value}%`;
  }, [timelineStats]);

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

  const applyPreset = (value) => {
    setPrompt(value);
    setLogs((prev) => [...prev, `[INFO] Preset loaded: ${value}`]);
  };

  const createRunBrief = async () => {
    const recent = logs.slice(-8).join("\n");
    const brief = [
      "JARVIS Deployment Brief",
      `Run time: ${lastRunAt ?? "N/A"}`,
      `Status: ${statusText}`,
      `Mode: dry_run=${dryRun} provider=${provider} docker=${enableDocker}`,
      `Timeline: total=${timelineStats.total} done=${timelineStats.done} active=${timelineStats.active} error=${timelineStats.error}`,
      `Completion: ${completionRate}`,
      "Recent logs:",
      recent || "No logs captured.",
    ].join("\n");

    try {
      await navigator.clipboard.writeText(brief);
      setLogs((prev) => [...prev, "[DONE] Deployment brief copied to clipboard"]);
    } catch {
      setLogs((prev) => [...prev, "[ERROR] Clipboard unavailable, copy from logs panel"]);
      setLogs((prev) => [...prev, `[INFO] ${brief}`]);
    }
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
        <p className="hero-kicker">AUTONOMOUS MISSION CONTROL</p>
        <h1>JARVIS DevOps Control Grid</h1>
        <p>Natural-language infrastructure automation with self-healing intelligence.</p>
      </header>

      <nav className="panel nav-panel">
        <div className="nav-links">
          <NavLink to="/overview" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
            Overview
          </NavLink>
          <NavLink to="/command" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
            Command
          </NavLink>
          <NavLink to="/timeline" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
            Timeline
          </NavLink>
          <NavLink to="/logs" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
            Logs
          </NavLink>
        </div>
      </nav>

      <Routes>
        <Route path="/" element={<Navigate to="/overview" replace />} />
        <Route
          path="/overview"
          element={
            <OverviewPage
              completionRate={completionRate}
              timelineStats={timelineStats}
              logStats={logStats}
              levelColors={LEVEL_COLORS}
              statusText={statusText}
              lastRunAt={lastRunAt}
              mockStatus={mockStatus}
              commandPresets={COMMAND_PRESETS}
              onApplyPreset={applyPreset}
            />
          }
        />
        <Route
          path="/command"
          element={
            <CommandPage
              prompt={prompt}
              setPrompt={setPrompt}
              dryRun={dryRun}
              setDryRun={setDryRun}
              enableDocker={enableDocker}
              setEnableDocker={setEnableDocker}
              provider={provider}
              setProvider={setProvider}
              isRunning={isRunning}
              onSubmit={submit}
              onCreateRunBrief={createRunBrief}
              onClearLogs={() => setLogs(["[BOOT] Logs cleared", "[INFO] Waiting for deployment command"])}
            />
          }
        />
        <Route path="/timeline" element={<TimelinePage timeline={timeline} stepIcons={STEP_ICONS} />} />
        <Route path="/logs" element={<LogsPage logs={logs} />} />
      </Routes>
    </div>
  );
}
