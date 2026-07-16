terraform {
  required_version = ">= 1.7.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "MediConnect"
      Environment = "production"
      ManagedBy   = "terraform"
      Owner       = "Ahmed-Akinola-Salman"
    }
  }
}

# ── S3: Terraform State Bucket ────────────────────────────────
resource "aws_s3_bucket" "terraform_state" {
  bucket = "mediconnect-terraform-state-aak"
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket                  = aws_s3_bucket.terraform_state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ── DynamoDB: Terraform State Lock ───────────────────────────
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "mediconnect-terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"
  attribute {
    name = "LockID"
    type = "S"
  }
}

# ── S3: Medical Documents + Static Assets ─────────────────────
resource "aws_s3_bucket" "mediconnect_assets" {
  bucket = "mediconnect-assets-aak"
}

resource "aws_s3_bucket_versioning" "mediconnect_assets" {
  bucket = aws_s3_bucket.mediconnect_assets.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "mediconnect_assets" {
  bucket = aws_s3_bucket.mediconnect_assets.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "mediconnect_assets" {
  bucket                  = aws_s3_bucket.mediconnect_assets.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ── Route53: DNS Zone ─────────────────────────────────────────
locals {
  route53_zone_id = "Z02876053BLRYYYQ3DNT1"
}

# ── Route53: CNAME Records ────────────────────────────────
resource "aws_route53_record" "sendgrid_em" {
  zone_id = local.route53_zone_id
  name    = "em2873.mediconnect.salman-aak.com"   # ← paste exact value from SendGrid
  type    = "CNAME"
  ttl     = 300
  records = ["u109957178.wl179.sendgrid.net"]        # ← paste exact value from SendGrid
}

resource "aws_route53_record" "sendgrid_s1" {
  zone_id = local.route53_zone_id
  name    = "s1._domainkey.mediconnect.salman-aak.com"
  type    = "CNAME"
  ttl     = 300
  records = ["s1.domainkey.u109957178.wl179.sendgrid.net"]
}

resource "aws_route53_record" "sendgrid_s2" {
  zone_id = local.route53_zone_id
  name    = "s2._domainkey.mediconnect.salman-aak.com"
  type    = "CNAME"
  ttl     = 300
  records = ["s2.domainkey.u109957178.wl179.sendgrid.net"]
}

resource "aws_route53_record" "sendgrid_dmarc" {
  zone_id = local.route53_zone_id
  name    = "_dmarc.mediconnect.salman-aak.com"
  type    = "TXT"
  ttl     = 300
  records = ["v=DMARC1; p=none;"]
}
