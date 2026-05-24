# AWS Provider Reference

Patterns and gotchas specific to the `hashicorp/aws` provider. Read this when the user is working with AWS resources beyond trivial cases.

## Provider configuration

Always pin the account and region. Drifting into the wrong account is the most expensive mistake in this provider.

```hcl
provider "aws" {
  region              = var.region
  allowed_account_ids = [var.account_id]

  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "terraform"
      Repo        = "github.com/acme/infra"
    }
  }
}
```

`default_tags` applies to every taggable resource in the provider — much cleaner than threading a `tags` local through every resource. Resource-level `tags` merge with these.

For multi-region or multi-account deployments, use provider aliases:

```hcl
provider "aws" {
  alias  = "us_west"
  region = "us-west-2"
}

resource "aws_s3_bucket" "replica" {
  provider = aws.us_west
  bucket   = "acme-replica"
}
```

## VPC

Don't write VPCs from scratch unless you have a reason. The `terraform-aws-modules/vpc/aws` registry module covers the standard pattern (public/private subnets across AZs, NAT gateways, route tables) and is battle-tested.

If you do write one, key principles:

- One NAT gateway per AZ for production (HA); one shared NAT for dev (cost). Make this a variable.
- Don't put RDS or ElastiCache in public subnets. Ever.
- Tag subnets with `kubernetes.io/role/elb = 1` (public) or `kubernetes.io/role/internal-elb = 1` (private) if EKS will use them — the AWS load balancer controller relies on these.

## IAM

**Use `aws_iam_policy_document` data sources instead of inline JSON.** They're validated at plan time, support interpolation, and diff cleanly.

```hcl
data "aws_iam_policy_document" "s3_read" {
  statement {
    actions   = ["s3:GetObject", "s3:ListBucket"]
    resources = [
      aws_s3_bucket.data.arn,
      "${aws_s3_bucket.data.arn}/*",
    ]
  }
}

resource "aws_iam_policy" "s3_read" {
  name   = "s3-read-${var.environment}"
  policy = data.aws_iam_policy_document.s3_read.json
}
```

**Use IRSA (IAM Roles for Service Accounts) for EKS workloads**, not node-level IAM roles. Node roles grant permissions to every pod; IRSA scopes them per service account.

**Trust policies are easy to get wrong.** When granting a role to another AWS account, the *trusting* account writes a role that allows the *trusted* account's principal. Both sides are required: the role here, and the permission to assume it on the caller side.

## EKS

Use the `terraform-aws-modules/eks/aws` module. Writing EKS from raw resources is a multi-week exercise that gets every cluster wrong in different ways.

Things that bite people:

- **Node groups don't update in place for AMI changes.** You need to roll them: create a new launch template version and let the node group replace nodes. The module handles this if `update_config` is set.
- **`aws-auth` ConfigMap is fragile.** EKS 1.23+ supports the Access Entries API, which Terraform manages cleanly via `aws_eks_access_entry`. Prefer it.
- **Cluster autoscaler vs Karpenter.** Both work; Karpenter is generally a better experience for new clusters. Either way, the IAM permissions need to be precise — copy from the official examples.

## RDS

- **Always set `deletion_protection = true` for production databases.** Use `prevent_destroy = true` in `lifecycle` for an extra guardrail.
- **Snapshots before destroy:** `skip_final_snapshot = false` and set `final_snapshot_identifier`. Default is to skip — a footgun.
- **Master password handling:** don't put it in HCL or `.tfvars`. Use `aws_secretsmanager_secret` with a `random_password` resource, and reference it via `manage_master_user_password = true` (RDS-managed) for new deployments.
- **Engine version upgrades may force-replace** depending on engine and version. Always read the plan carefully.

## S3

The S3 resource model was split into many sub-resources in AWS provider 4.x. Bucket policy, versioning, encryption, lifecycle, and public access block are all separate resources now. This is more verbose but lets each be managed independently.

```hcl
resource "aws_s3_bucket" "data" {
  bucket = "acme-data-${var.environment}"
}

resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket                  = aws_s3_bucket.data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

Always include the public access block. Default-public S3 is the source of more breach headlines than any other AWS service.

## Common errors

- **`Error: error creating ...: AccessDenied`** — the credentials in scope don't have permission. Check `aws sts get-caller-identity` and the role/policy.
- **`Error: timeout while waiting for state to become 'available'`** — usually a downstream issue (resource quota, VPC limit, AZ capacity). Check the AWS console for the actual error on the resource.
- **`InvalidParameterCombination: ...`** — provider request was malformed for the API. Compare your HCL to the AWS API docs for the resource.
- **`ResourceInUseException`** when destroying — something outside Terraform's view references this resource. Find and remove the reference first.
