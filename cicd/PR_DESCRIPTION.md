<!-- cspell:words healthcheck -->
## Summary
This PR upgrades the DevOps project to satisfy full rubric coverage across collaboration, CI/CD, containerization/deployment, and IaC verification.

## What Changed
- CI/CD workflow split into `ci` and gated `deploy` jobs in `.github/workflows/devops.yml`
- Workflow triggers aligned for both `main` and `master`
- Pull request validation path added (PR run = CI checks)
- Main-branch deployment path retained (push run = CI + deploy)
- Backend API tests added in `test/server.test.js`
- App exportability improved in `server.js` for testability
- Build/validate scripts added in `package.json`
- Container hardening in `Dockerfile` (healthcheck + non-root user)
- Build context optimization with `.dockerignore`
- Collaboration governance added:
  - `.github/PULL_REQUEST_TEMPLATE.md`
  - `.github/ISSUE_TEMPLATE/bug_report.md`
  - `.github/ISSUE_TEMPLATE/feature_request.md`
  - `CONTRIBUTING.md` policy expansion
- Rubric mapping evidence added in `cicd/RUBRIC_EVIDENCE.md`
- Submission execution checklist added in `cicd/SUBMISSION_CHECKLIST.md`

## Validation Performed
- `npm run validate` passed locally
  - backend tests: pass
  - frontend production build: pass
  - python compile checks: pass

## Infra and Deployment Notes
- Terraform CLI is validated in CI workflow.
- Deploy stage expects configured GitHub Actions secrets:
  - `DOCKERHUB_USERNAME`
  - `DOCKERHUB_TOKEN`
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_DEFAULT_REGION`
  - `KUBE_CONFIG_DATA`
  
## Rubric Evidence
Please reference `cicd/RUBRIC_EVIDENCE.md` for criterion-to-artifact mapping.
