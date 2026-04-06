# Contributing

## Branch Strategy
- Use feature branches: feature/<name>
- Open pull requests into `main`
- Keep PRs small and focused

## Commit Guidelines
- Use clear commit messages
- Reference issue IDs where possible

## Local Validation
- Run `python -m compileall ai_engine intent_engine github_analyzer docker_builder k8s_deployer terraform_runner orchestrator cli self_healing monitoring`
- Run `cd frontend; npm run build`

## Review Checklist
- No secrets committed
- Logs remain structured
- New modules include error handling
