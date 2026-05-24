# Azure Provider Reference

Patterns and gotchas for the `hashicorp/azurerm` provider.

## Provider configuration

```hcl
provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = true
    }
    key_vault {
      purge_soft_delete_on_destroy    = false
      recover_soft_deleted_key_vaults = true
    }
  }
  subscription_id = var.subscription_id
  tenant_id       = var.tenant_id
}
```

The empty-but-required `features {}` block is unique to AzureRM. The nested settings are real toggles — read them; the defaults are not always what you want, especially for Key Vault.

For multi-subscription deployments, use aliases (same pattern as AWS).

## Resource groups

Almost everything in Azure lives inside a resource group. Design them deliberately — a resource group is also an access-control boundary and a destruction boundary.

```hcl
resource "azurerm_resource_group" "main" {
  name     = "rg-${var.app}-${var.environment}"
  location = var.location

  lifecycle {
    prevent_destroy = true
  }
}
```

`prevent_destroy` is cheap insurance — `terraform destroy` on a resource group cascades to everything inside it.

## Naming

Azure has strict naming rules that vary by resource: storage account names must be globally unique, lowercase, 3-24 chars, no hyphens; key vault names must be globally unique, alphanumeric and hyphens. Use a `local` to build names consistently:

```hcl
locals {
  name_prefix = "${var.app}-${var.environment}"
  storage_name = lower(replace("${var.app}${var.environment}st", "-", ""))
}
```

`azurerm_naming` modules exist but are often more trouble than building names locally.

## RBAC and identities

Azure has two parallel access systems: classic Azure AD (now Entra ID) RBAC, and resource-specific access policies (mostly legacy, e.g. Key Vault access policies). Prefer RBAC.

```hcl
resource "azurerm_role_assignment" "kv_reader" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
}
```

For workloads needing to access Azure resources, prefer **user-assigned managed identities** over service principals with client secrets. They have no secret to leak and are scoped to the identity's lifecycle.

For AKS, **Workload Identity** federates a Kubernetes service account to an Azure managed identity — the AKS equivalent of IRSA/Workload Identity in AWS/GCP.

## AKS

Use the AKS module from the registry, or write it carefully. The fiddly settings:

- **Default node pool can't be deleted** — only replaced. Plan its sizing carefully on first creation, or accept a cluster recreation later.
- **Network plugin choice (`kubenet`, `azure`, `azure-cni-overlay`)** is sticky. Switching requires cluster recreation. `azure-cni-overlay` is the modern default for most cases.
- **Auto-upgrade channels** behave like GKE's release channels. Pin or accept upgrades.

## Key Vault

- **Soft delete is enabled by default** and can't be disabled. The provider feature `purge_soft_delete_on_destroy = false` (default) keeps deleted vaults recoverable; set to `true` only for ephemeral envs.
- **Access via RBAC, not access policies.** Set `enable_rbac_authorization = true` on the vault.
- Reference secrets from other resources via `data "azurerm_key_vault_secret"` — don't put secrets directly in HCL.

## Common errors

- **`Error: A resource with the ID ... already exists`** — resource exists in Azure but not in state. Use `terraform import` or an `import` block.
- **`Error: waiting for ... : Code="..."`** — Azure ARM operation failed asynchronously. The plan succeeded; the API rejected the change. Check the Activity Log on the resource in the portal for the underlying error.
- **`AuthorizationFailed`** — the principal Terraform is authenticating as lacks the role at the scope. Check `az account show` and the role assignments on the target scope.
- **`SubscriptionNotRegistered` for a resource provider** — register the provider once: `az provider register --namespace Microsoft.X`. Manage this in Terraform via `azurerm_resource_provider_registration` if you want it codified.
