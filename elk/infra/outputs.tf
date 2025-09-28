output "api_alb_dns" {
  description = "Public DNS name of the API load balancer."
  value       = aws_lb.api.dns_name
}

output "api_domain" {
  description = "Route 53 record for the API."
  value       = local.api_domain
}

output "api_database_endpoint" {
  description = "RDS endpoint for application connections."
  value       = aws_db_instance.api.address
}

output "database_secret_arn" {
  description = "ARN of the Secrets Manager secret containing DATABASE_URL."
  value       = aws_secretsmanager_secret.database_url.arn
  sensitive   = true
}

output "web_bucket_name" {
  description = "S3 bucket hosting the frontend."
  value       = aws_s3_bucket.web.bucket
}

output "web_domain" {
  description = "Route 53 record serving the static site."
  value       = local.web_domain
}

output "web_api_base_url_parameter" {
  description = "SSM parameter storing the API base URL for the frontend."
  value       = aws_ssm_parameter.web_api_base_url.name
}

output "web_google_maps_parameter" {
  description = "SSM parameter storing the Google Maps API key."
  value       = aws_ssm_parameter.web_google_maps_key.name
  sensitive   = true
}
