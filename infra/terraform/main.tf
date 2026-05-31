terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment to use remote state (recommended for teams)
  # backend "s3" {
  #   bucket = "your-tfstate-bucket"
  #   key    = "game-backend-platform/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = var.aws_region
}
