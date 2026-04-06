export async function runCommand(prompt, options = {}) {
  const {
    dryRun = false,
    enableDocker = false,
    provider = "auto",
  } = options;

  // Replace with your real backend endpoint when available.
  const response = await fetch("http://localhost:8000/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      prompt,
      dry_run: dryRun,
      enable_docker: enableDocker,
      provider,
    }),
  });

  if (!response.ok) {
    let detail = "Failed to submit command";
    try {
      const payload = await response.json();
      if (payload?.detail) {
        detail = payload.detail;
      }
    } catch {
      // Keep fallback message if server response is not JSON.
    }

    throw new Error(detail);
  }

  return response.json();
}

export function runCommandStream(prompt, options = {}, handlers = {}) {
  const {
    dryRun = false,
    enableDocker = false,
    provider = "auto",
  } = options;

  const params = new URLSearchParams({
    prompt,
    dry_run: String(dryRun),
    enable_docker: String(enableDocker),
    provider,
  });

  const url = `http://localhost:8000/run/stream?${params.toString()}`;

  return new Promise((resolve, reject) => {
    const source = new EventSource(url);
    let settled = false;

    const safeResolve = (payload) => {
      if (settled) {
        return;
      }
      settled = true;
      resolve(payload);
    };

    const safeReject = (error) => {
      if (settled) {
        return;
      }
      settled = true;
      reject(error);
    };

    source.addEventListener("run_start", (event) => {
      try {
        handlers.onRunStart?.(JSON.parse(event.data));
      } catch {
        // Ignore malformed event payloads.
      }
    });

    source.addEventListener("step", (event) => {
      try {
        handlers.onStep?.(JSON.parse(event.data));
      } catch {
        // Ignore malformed event payloads.
      }
    });

    source.addEventListener("log", (event) => {
      try {
        handlers.onLog?.(JSON.parse(event.data));
      } catch {
        // Ignore malformed event payloads.
      }
    });

    source.addEventListener("result", (event) => {
      try {
        const payload = JSON.parse(event.data);
        handlers.onResult?.(payload);
        safeResolve(payload);
      } catch (err) {
        safeReject(err);
      } finally {
        source.close();
      }
    });

    source.addEventListener("run_error", (event) => {
      try {
        const payload = JSON.parse(event.data);
        safeReject(new Error(payload?.message || "Run failed"));
      } catch {
        safeReject(new Error("Run failed"));
      } finally {
        source.close();
      }
    });

    source.onerror = () => {
      safeReject(new Error("Stream connection failed"));
      source.close();
    };
  });
}
