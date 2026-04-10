import React from "react";

export default function TimelinePage({ timeline, stepIcons }) {
  return (
    <section className="panel timeline-panel">
      <div className="panel-title-row">
        <h2>Execution Timeline</h2>
        <span className="chip">Live</span>
      </div>
      <div className="timeline-list">
        {timeline.length === 0 ? (
          <p className="timeline-empty">Start a run to see Parse to Plan to Terraform to K8s to Monitor.</p>
        ) : (
          timeline.map((step) => (
            <article key={step.id} className={`timeline-step timeline-${step.state}`}>
              <span className="timeline-dot">{stepIcons[step.state]}</span>
              <div className="timeline-content">
                <strong>{step.name}</strong>
                <small>{step.detail}</small>
              </div>
            </article>
          ))
        )}
      </div>
    </section>
  );
}
