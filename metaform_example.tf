terraform {
  required_providers {
      aws = {
      source  = "hashicorp/aws"
      version = "~> 0.1"
    }
      databricks = {
      source  = "databricks/databricks"
      version = "0.0.1"
    }
  }
}

provider "aws" {
  region = "us-east-1a"
}

data "aws_ssm_parameter" "dbrx_host" {
  name = "dbrx_host"
}

data "aws_ssm_parameter" "dbrx_token" {
  name = "dbrx_token"
}

provider "databricks" {
  alias = "mws"
  host  = data.aws_ssm_parameter.dbrx_host.value
  token = data.aws_ssm_parameter.dbrx_token.value
}

resource "databricks_job" "dbrx_job" {
  name    = "dbrx_job"
  host    = data.aws_ssm_parameter.dbrx_host.value
  token   = data.aws_ssm_parameter.dbrx_token.value
  library {
    location    = "s3://bucket"
    entry_point = "src.main"
  }
}