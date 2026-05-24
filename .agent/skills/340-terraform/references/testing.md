# Testing Terraform

Three layers of testing are common; pick what fits the team and the change.

## 1. `terraform validate` and `terraform plan` (always)

Every CI run for a PR should at minimum:

1. `terraform fmt -check -recursive` — fails on unformatted files.
2. `terraform init -backend=false` — checks providers and modules resolve, without touching real state.
3. `terraform validate` — schema-level validation.
4. `terraform plan` against a real (dev) backend — reviewer sees the diff before merge.

The plan output is the most useful artifact a reviewer can see. Pipe it into a PR comment if your CI supports it (`tfcmt`, `atlantis`, native GitHub Actions, Terraform Cloud).

## 2. `terraform test` (built-in, Terraform 1.6+)

The `terraform test` command runs `.tftest.hcl` files. It can do real applies in a temp workspace, or plan-only assertions.

```hcl
# tests/network.tftest.hcl

variables {
  environment = "test"
  cidr_block  = "10.0.0.0/16"
}

run "vpc_has_correct_cidr" {
  command = plan

  assert {
    condition     = aws_vpc.main.cidr_block == "10.0.0.0/16"
    error_message = "VPC CIDR did not match expected value."
  }
}

run "creates_three_private_subnets" {
  command = plan

  assert {
    condition     = length(aws_subnet.private) == 3
    error_message = "Expected exactly 3 private subnets."
  }
}
```

`command = plan` is fast and free; `command = apply` actually creates resources (and tears them down at the end of the run). Use apply tests sparingly — they cost real money and time.

`terraform test` is the right answer for module testing. Tests live with the module; the module can declare what shape it produces given inputs.

## 3. Terratest (Go-based, for full end-to-end)

Terratest is a Go library that runs `terraform apply`, asserts against the deployed infrastructure (HTTP calls, SSH, AWS SDK queries), then runs `terraform destroy`. Heavy but thorough.

Use it for:
- Modules where the *behavior* matters, not just the plan shape (e.g., does the load balancer actually serve traffic?).
- Compliance-style checks that need to query the cloud.

Don't use it for:
- Things `terraform test` can cover. Terratest is much slower.

## Policy as code

For organization-wide guardrails (no public S3, all RDS must be encrypted, etc.), use a policy layer:

- **OPA / Conftest** — generic, plan JSON as input, Rego as the policy language.
- **Sentinel** — Terraform Cloud/Enterprise only, but tightly integrated.
- **Checkov, tfsec, terrascan** — built-in rulesets for common security mistakes. Run in CI.

Run these against `terraform plan -out=tfplan` then `terraform show -json tfplan > plan.json`. They evaluate the planned change, not just static HCL.

## What good test coverage looks like

For a module:
- A `terraform test` file that exercises the public inputs in a few representative configurations.
- Plan-mode tests for shape (resource counts, computed names, key attributes).
- Optionally one apply-mode test in CI on a schedule (nightly) to catch provider drift.

For a root module (env):
- CI runs `validate` and `plan` on every PR.
- A policy-as-code check runs against the plan.
- Apply happens through a controlled pipeline (Atlantis, Terraform Cloud, GitHub Actions with environment protection), not from anyone's laptop.
