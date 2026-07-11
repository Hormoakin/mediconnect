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