# Submission Checklist (Full Marks)

## Completed by automation

- Feature branch pushed: `feature/rubric-full-marks`
- Commits pushed:
  - `617d0bf` feat: complete rubric-aligned devops automation
  - `a96815f` ci: trigger workflow on main and master
- Rubric evidence document prepared: `cicd/RUBRIC_EVIDENCE.md`
- Workflow now triggers on both `main` and `master`
- One-command automation script available: `cicd/automate_everything.ps1`

## One-command mode

If `gh` is authenticated and required secret environment variables are set, run:

```powershell
npm run automate:everything
```

This command performs secrets setup, PR creation, CI wait, merge, main pipeline wait, and log export automatically.

## Required manual steps (GitHub auth needed)

### 1) Open PR and run PR pipeline

- Create PR from `feature/rubric-full-marks` -> `master`
- URL: https://github.com/jene007/devops/pull/new/feature/rubric-full-marks
- Confirm GitHub Actions PR run starts and completes

### 2) Configure repository secrets

Go to repository settings:
- https://github.com/jene007/devops/settings/secrets/actions

Create these secrets:
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_DEFAULT_REGION`
- `KUBE_CONFIG_DATA` (base64 encoded kubeconfig)

### 3) Run main-branch pipeline

- Merge the PR into `master`
- Confirm push workflow runs for `master`
- Actions page: https://github.com/jene007/devops/actions

### 4) Capture proof for evaluation

Capture screenshots/logs of:
- Successful PR workflow run
- Successful `master` workflow run
- Deploy steps: Docker push, Terraform apply, Kubernetes rollout

### 5) Submission package

Attach these files in your submission:
- `cicd/RUBRIC_EVIDENCE.md`
- Action run screenshots/log exports
- PR link and merged commit link
