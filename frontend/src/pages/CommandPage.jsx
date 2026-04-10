import React from "react";

export default function CommandPage({
  prompt,
  setPrompt,
  dryRun,
  setDryRun,
  enableDocker,
  setEnableDocker,
  provider,
  setProvider,
  isRunning,
  onSubmit,
  onCreateRunBrief,
  onClearLogs,
}) {
  return (
    <section className="panel command-panel">
      <h2>Command Center</h2>
      <form onSubmit={onSubmit}>
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
          placeholder="Deploy https://github.com/<owner>/<repo> to aws us-east-1 as python app with docker build and kubernetes rollout"
        />
        <small className="input-hint">
          Include: repo URL, cloud, region, app type (node/python/java), and action.
        </small>
        <small className="input-hint">
          For AWS deploy: set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_DEFAULT_REGION.
        </small>
        <div className="button-row">
          <button type="submit" disabled={isRunning || !prompt.trim()}>
            {isRunning ? "Executing..." : "Run Autonomous Pipeline"}
          </button>
          <button type="button" className="ghost" onClick={onCreateRunBrief}>
            Copy Run Brief
          </button>
          <button
            type="button"
            className="ghost"
            onClick={onClearLogs}
            disabled={isRunning}
          >
            Clear Logs
          </button>
        </div>
      </form>
    </section>
  );
}
