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

############################################################

# SendGrid Domain Authentication

############################################################
# Add these to terraform/environments/production/main.tf

resource "aws_route53_record" "sendgrid_em" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "em2873.mediconnect.salman-aak.com"   # ← paste exact value from SendGrid
  type    = "CNAME"
  ttl     = 300
  records = ["u109957178.wl179.sendgrid.net"]        # ← paste exact value from SendGrid
}

resource "aws_route53_record" "sendgrid_s1" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "s1._domainkey.mediconnect.salman-aak.com"
  type    = "CNAME"
  ttl     = 300
  records = ["s1.domainkey.u109957178.wl179.sendgrid.net"]
}

resource "aws_route53_record" "sendgrid_s2" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "s2._domainkey.mediconnect.salman-aak.com"
  type    = "CNAME"
  ttl     = 300
  records = ["s2.domainkey.u109957178.wl179.sendgrid.net"]
}

resource "aws_route53_record" "sendgrid_dmarc" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "_dmarc.mediconnect.salman-aak.com"
  type    = "TXT"
  ttl     = 300
  records = ["v=DMARC1; p=none;"]
}
