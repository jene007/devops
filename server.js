const express = require("express");

const app = express();
const port = process.env.PORT || 3000;

app.get("/", (req, res) => {
  res.json({
    service: "jarvis-app",
    status: "running",
    message: "Autonomous DevOps sample app is live"
  });
});

app.get("/health", (req, res) => {
  res.status(200).json({ status: "ok" });
});

if (require.main === module) {
  app.listen(port, () => {
    // Keep runtime output simple for container logs.
    console.log(`jarvis-app listening on port ${port}`);
  });
}

module.exports = app;
