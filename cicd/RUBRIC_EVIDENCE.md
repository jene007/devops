# Rubric Evidence: Automated Design and Deployment

This document maps implementation artifacts to grading criteria and can be submitted as proof for full marks.

## 1) Version Control and Collaboration (8 marks)

Evidence:
- Branch and commit conventions in `CONTRIBUTING.md`
- Ownership and review routing in `.github/CODEOWNERS`
- Structured pull request checklist in `.github/PULL_REQUEST_TEMPLATE.md`
- Issue templates for bug and feature workflow in `.github/ISSUE_TEMPLATE/`

What to show in evaluation:
- Feature branch -> PR -> CODEOWNER review -> merge into `main`
- PR checks passing before merge
- Clean commit history with descriptive messages

## 2) CI/CD Pipeline Implementation (7 marks)

Evidence:
- End-to-end workflow in `.github/workflows/devops.yml`
- CI job performs:
  - backend dependency install
  - automated backend tests
  - Python compilation checks
  - frontend build
  - Terraform lint/validate
- Deploy job performs:
  - Docker build and push
  - Terraform apply
  - Kubernetes apply and rollout status

What to show in evaluation:
- Pull request run (CI only)
- Push to main run (CI + deploy)
- Logs showing successful gate progression

## 3) Containerization and Deployment (8 marks)

Evidence:
- Container definition in `Dockerfile`
- Runtime hardening:
  - container healthcheck
  - non-root user execution
- Build context optimization in `.dockerignore`
- Kubernetes orchestration manifests in `k8s/`
- Workflow deploys immutable image tag `${GITHUB_SHA}` into deployment

What to show in evaluation:
- Docker image built and pushed from workflow
- Deployment rollout success from Kubernetes stage
- `/health` endpoint green in container and cluster

## 4) Infrastructure as Code (7 marks)

Evidence:
- Terraform modules in `terraform/`:
  - provider config
  - VPC + subnet + IGW + routing
  - security group
  - compute instances
  - optional EKS cluster
- Validation steps in CI:
  - `terraform fmt -check`
  - `terraform init -backend=false`
  - `terraform validate`
- Deployment step:
  - `terraform apply -auto-approve`

What to show in evaluation:
- Successful Terraform validation logs
- Successful Terraform apply logs with output values

## Verification Commands (Local)

```bash
npm install
npm test
npm --prefix frontend ci
npm --prefix frontend run build
python -m compileall ai_engine intent_engine github_analyzer docker_builder k8s_deployer terraform_runner orchestrator cli self_healing monitoring
terraform -chdir=terraform fmt -check
terraform -chdir=terraform init -backend=false
terraform -chdir=terraform validate
```

## Notes

- Deployment stages require configured GitHub secrets.
- Terraform commands require Terraform CLI in PATH.
- Kubernetes deploy requires valid kubeconfig secret in workflow.
