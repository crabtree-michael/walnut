variable "aws_region" {
  description = "AWS region to deploy infrastructure into."
  type        = string
  default     = "us-west-2"
}

variable "project_name" {
  description = "Identifier applied to resources as a name prefix."
  type        = string
  default     = "elk"
}

variable "hosted_zone_id" {
  description = "Route 53 hosted zone ID for macmail.app."
  type        = string
}

variable "api_image" {
  description = "Full URI of the Docker image for the Elk API."
  type        = string
}

variable "google_maps_api_key" {
  description = "Google Maps API key for the frontend."
  type        = string
  sensitive   = true
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.40.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets."
  type        = list(string)
  default     = [
    "10.40.1.0/24",
    "10.40.2.0/24"
  ]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets (databases)."
  type        = list(string)
  default     = [
    "10.40.11.0/24",
    "10.40.12.0/24"
  ]
}

variable "db_instance_class" {
  description = "Instance class for the PostgreSQL database."
  type        = string
  default     = "db.t4g.micro"
}

variable "db_allocated_storage" {
  description = "Allocated storage for the database in GB."
  type        = number
  default     = 20
}

variable "db_name" {
  description = "Database name for the Elk API."
  type        = string
  default     = "elk"
}

variable "db_username" {
  description = "Database master username."
  type        = string
  default     = "elk_admin"
}

variable "api_desired_count" {
  description = "Desired ECS service task count."
  type        = number
  default     = 1
}

variable "api_cpu" {
  description = "CPU units for the ECS task (1024 = 1 vCPU)."
  type        = number
  default     = 512
}

variable "api_memory" {
  description = "Memory (MB) for the ECS task."
  type        = number
  default     = 1024
}

variable "web_bucket_force_destroy" {
  description = "Force destroy the S3 bucket during terraform destroy."
  type        = bool
  default     = false
}

variable "existing_cloudfront_distribution_id" {
  description = "Existing CloudFront distribution ID serving the web domain. Leave empty if none."
  type        = string
  default     = ""
}

variable "api_certificate_arn" {
  description = "ACM certificate ARN in the service region for the API load balancer."
  type        = string
}
