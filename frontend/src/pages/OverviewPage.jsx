import React from "react";

export default function OverviewPage({ completionRate, timelineStats, logStats, levelColors, statusText, lastRunAt, mockStatus, commandPresets, onApplyPreset }) {
  return (
    <>
      <section className="panel mission-panel">
        <div className="panel-title-row">
          <h2>Mission Profiles</h2>
          <span className="chip">Adaptive</span>
        </div>
        <div className="preset-row">
          {commandPresets.map((item) => (
            <button key={item} type="button" className="preset-pill" onClick={() => onApplyPreset(item)}>
              {item}
            </button>
          ))}
        </div>
        <div className="intel-grid">
          <article className="intel-card">
            <span>Completion</span>
            <strong>{completionRate}</strong>
          </article>
          <article className="intel-card">
            <span>Steps Cleared</span>
            <strong>{timelineStats.done}/{timelineStats.total}</strong>
          </article>
          <article className="intel-card">
            <span>Error Count</span>
            <strong>{timelineStats.error}</strong>
          </article>
          <article className="intel-card">
            <span>Last Signal</span>
            <strong className={`signal-${levelColors[logStats.lastLevel] ?? "neutral"}`}>{logStats.lastLevel}</strong>
          </article>
        </div>
      </section>

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
    </>
  );
}
