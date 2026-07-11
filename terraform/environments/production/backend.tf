terraform {
  backend "s3" {
    bucket         = "mediconnect-terraform-state-aak"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "mediconnect-terraform-locks"
    encrypt        = true
  }
}
