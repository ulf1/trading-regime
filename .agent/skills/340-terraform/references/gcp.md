# GCP Provider Reference

Patterns and gotchas for the `hashicorp/google` and `hashicorp/google-beta` providers.

## Provider configuration

GCP is project-scoped. Most resources require a `project` and a `region` or `zone`. Set them at the provider level rather than repeating per resource.

```hcl
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}
```

Use `google-beta` for resources or features still in beta. You can mix providers on the same resource using `provider = google-beta` per resource.

## Projects and APIs

Most GCP resources require an API to be enabled in the project first. Manage this explicitly:

```hcl
resource "google_project_service" "required" {
  for_each = toset([
    "compute.googleapis.com",
    "container.googleapis.com",
    "iam.googleapis.com",
    "secretmanager.googleapis.com",
  ])
  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}
```

Set `disable_on_destroy = false` unless you really want destroying this state to turn off APIs project-wide — usually you don't.

Add `depends_on = [google_project_service.required]` (or interpolate) on resources that need an API, especially on first apply against a new project.

## IAM

GCP IAM has three resource flavors for the same binding, and they don't compose well:

- `google_<thing>_iam_policy` — **authoritative**, replaces *all* bindings on the resource. Almost always wrong unless Terraform owns the entire resource's IAM.
- `google_<thing>_iam_binding` — authoritative for a single role; replaces all members for that role.
- `google_<thing>_iam_member` — non-authoritative; adds a single member to a role. **Safe default.**

Use `_iam_member` unless you have a specific reason. The other two will silently overwrite bindings created by other tools or humans.

```hcl
resource "google_project_iam_member" "ci_deployer" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.ci.email}"
}
```

## GKE

Use the `terraform-google-modules/kubernetes-engine/google` module for production GKE clusters. Like EKS, raw GKE resources have many fiddly settings that the module gets right.

Key things:

- **Autopilot vs Standard.** Autopilot manages nodes for you; Standard gives you control. The choice changes the module's surface significantly.
- **Workload Identity** is GCP's equivalent of IRSA — bind a Kubernetes service account to a GCP service account. Enable it at cluster creation; retrofitting is painful.
- **Release channels** (`RAPID`, `REGULAR`, `STABLE`) control auto-upgrades. Pin a `min_master_version` if you need reproducible cluster versions, but accept that GKE will upgrade you eventually on `RAPID`/`REGULAR`.

## Cloud SQL

- Set `deletion_protection = true` for production instances and add `prevent_destroy = true` in `lifecycle`.
- `database_version` changes can force-replace. Read the plan.
- Public IP is enabled by default — disable it unless you have a reason (`ip_configuration.ipv4_enabled = false`).

## Secrets

`google_secret_manager_secret` and `google_secret_manager_secret_version`. The secret resource holds metadata; versions hold the actual data. Don't put plaintext in HCL — pass via env var (`TF_VAR_db_password`) or read from another secret manager.

## Common errors

- **`Error 403: ... API has not been used in project ... before or it is disabled`** — enable the API via `google_project_service` (see above).
- **`Error: googleapi: Error 409: ... alreadyExists`** — resource exists outside Terraform. Use `terraform import` or `import` blocks.
- **`Error: googleapi: Error 400: Service account ... does not exist`** — Terraform created the service account in the same apply, but the binding ran before propagation. Add an explicit `depends_on` or a small `time_sleep` resource.
- **Permission errors on first apply** — the credentials used by Terraform need the right roles. `roles/owner` works for bootstrapping; tighten afterward.
