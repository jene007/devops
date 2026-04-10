# Contributing

## Branch Strategy
- Use feature branches: `feature/<scope>-<short-name>`
- Use bug-fix branches: `fix/<scope>-<short-name>`
- Open pull requests into `main`
- Rebase branch on latest `main` before requesting review
- Keep PRs small and focused

## Pull Request Policy
- Every PR must use `.github/PULL_REQUEST_TEMPLATE.md`
- At least one CODEOWNER review is required before merge
- PR checks in GitHub Actions must be green
- Squash merge preferred to keep history clean

## Commit Guidelines
- Use Conventional Commits format: `feat:`, `fix:`, `chore:`, `docs:`, `ci:`
- Reference issue IDs where possible
- Keep one logical change per commit

## Local Validation
- Run `python -m compileall ai_engine intent_engine github_analyzer docker_builder k8s_deployer terraform_runner orchestrator cli self_healing monitoring`
- Run `npm test`
- Run `cd frontend; npm run build`

## Review Checklist
- No secrets committed
- Logs remain structured
- New modules include error handling
