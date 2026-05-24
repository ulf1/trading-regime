---
name: 340-terraform
description: >
  Use this skill whenever the user is working with Terraform or HCL — writing,
  reviewing, refactoring, or troubleshooting `.tf`, `.tfvars`, or `.tfstate`
  files, modules, providers, or infrastructure code. Triggers include any
  mention of `terraform plan/apply/destroy/import`, providers (AWS, GCP, Azure,
  Kubernetes, Helm, etc.), state files or remote backends (S3, GCS, Azure blob,
  Terraform Cloud), workspaces, modules, lock files, or HCL syntax; requests to
  convert CloudFormation, ARM, Pulumi, or CDK code to Terraform; debugging plan
  diffs, state drift, force-replacement, or `terraform import` workflows;
  designing or reviewing reusable modules; managing secrets in Terraform; and any
  infrastructure-as-code task where Terraform (or OpenTofu) is a reasonable fit —
  including when the user only describes the desired infrastructure ("spin up an
  EKS cluster", "give me a VPC with three private subnets") without naming
  Terraform explicitly.
compatibility: Requires Terraform 1.5+ or OpenTofu.
metadata:
  author: "skill-maintainer"
  version: "1.0"
---

# Terraform

Terraform is declarative: the user describes the desired state, Terraform computes a plan to reach it, and applies it. Most mistakes come from forgetting that the *plan* is the contract — not the HCL, not the cloud console — and that *state* is what Terraform thinks it owns. This skill encodes the patterns that keep that contract clean.

## Goal
Help the user safely write, review, refactor, test, and troubleshoot declarative infrastructure configurations using Terraform or OpenTofu, ensuring standard-compliant HCL, clean state management, and minimised blast-radius/risk.

## Instructions

### 1. Core Workflow
For every change, follow this order. Skipping steps is the most common source of avoidable damage:
1. **Write or edit HCL.** Group changes that belong together; resist mixing refactors with behavior changes in one diff.
2. **Format HCL.** Run `terraform fmt -recursive` to canonicalize formatting.
3. **Validate syntax.** Run `terraform validate` to catch syntax and basic schema errors locally before they hit a plan.
4. **Generate plan.** Run `terraform plan -out=tfplan` and read the output. Every `+`, `-`, `~`, and especially `-/+` (force-replace) matters.
5. **Apply plan.** Run `terraform apply tfplan` to apply exactly what was planned.
6. **Commit changes.** Commit the HCL and the lock file (`.terraform.lock.hcl`).

### 2. Project Structure
A small project can live in one directory. Anything larger must separate concerns to keep the blast radius small:
```
infra/
├── envs/
│   ├── dev/        # backend.tf, terraform.tfvars, main.tf (calls modules)
│   ├── staging/
│   └── prod/
└── modules/
    ├── network/
    ├── eks-cluster/
    └── rds-instance/
```
Each environment directory is a root module with its own state. Avoid Terraform workspaces (`terraform workspace new`) for environment separation.

### 3. HCL Essentials
- **Resources** declare infrastructure. **Data sources** read existing infrastructure. **Variables** are inputs to a module. **Outputs** are exposed values. **Locals** are internal expressions for readability.
- Prefer `for_each` whenever items have stable identities. Use `count` only for boolean "create this or don't" toggles (`count = var.enabled ? 1 : 0`).
- Reach for explicit `depends_on` only when there's a side-effect dependency Terraform can't see (e.g. IAM policy propagation).
- Always declare a `terraform` block to pin the required version and required provider versions.

### 4. Importing Existing Resources
Don't recreate existing resources. Use one of two paths:
- **Declarative (Terraform 1.5+):** Use `import` blocks:
  ```hcl
  import {
    to = aws_s3_bucket.logs
    id = "acme-prod-logs"
  }
  ```
  Run `terraform plan -generate-config-out=generated.tf` to scaffold the resource block from the live resource, then refine it.
- **Classic CLI:** Use `terraform import <addr> <id>`.

## Gotchas
- **Force-replace (`-/+`) surprises:** Some attributes cannot be changed in place. For stateful resources, force-replace means data loss unless handled appropriately (snapshots, blue-green).
- **Implicit conversions in `for_each`:** `for_each` requires a `set(string)` or `map(any)` with keys known at plan time. If keys are computed from other resources, Terraform will complain. Fix with `toset(var.azs)` or a static map.
- **Provider authentication:** Providers read credentials from env vars, shared configs, or instance metadata. Pin allowed account IDs explicitly to prevent applying against the wrong account.
- **`null` vs empty string:** Setting an optional argument to `null` is the same as not setting it. Setting it to `""` is an explicit empty string.
- **Provider version upgrades:** Minor bumps can deprecate or rename attributes. Always read the upgrade guide.
- **OpenTofu Compatibility:** OpenTofu is drop-in compatible with the 1.5.x feature set. When the user is on OpenTofu, prefer `tofu` as the command; otherwise use `terraform`.
- **Provider References:** For specific provider-related quirks, consult:
  - [AWS Provider Reference](references/aws.md)
  - [Azure Provider Reference](references/azure.md)
  - [GCP Provider Reference](references/gcp.md)
  - [Testing Reference](references/testing.md)

## Output format
- Surface exact `terraform plan` output rather than guessing. Identify the resource and attributes being changed.
- Present HCL blocks inside clean markdown code fences with syntax highlighting.
- If an error is returned, pinpoint the resource block and highlight whether it is an in-place update (`~`), a destroy (`-`), a create (`+`), or a force-replace (`-/+`).

## Constraints
- **Do not hardcode secrets** in `.tf` files. Use `sensitive = true` on variables and outputs. State will still contain them, so state encryption is critical.
- **Do not edit `.tfstate` by hand.** Use `terraform state` subcommands (`list`, `show`, `mv`, `rm`, `pull`, `push`).
- **Do not use workspaces** for separating environments. Use the directory-per-env pattern instead.
- **Do not build a module** when it merely wraps a single resource with no added value (indirection), or when you're abstracting away things that genuinely differ.
- **Do not use floating `main` references** in shared modules. Pin module sources by version (e.g. `ref=v1.4.0` or version `1.4.0`).
- **Do not commit sensitive files** (`*.tfstate`, `*.tfvars` with secrets, or `.terraform/` folders). Ensure they are in `.gitignore`.
