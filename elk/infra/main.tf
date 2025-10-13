locals {
  project_name = var.project_name
  default_tags = {
    Project = local.project_name
    Managed = "terraform"
  }
  api_domain = "elk-api.macmail.app"
  web_domain = "elk.macmail.app"
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

data "aws_availability_zones" "available" {
  state = "available"
}
