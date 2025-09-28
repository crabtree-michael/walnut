resource "random_password" "db" {
  length  = 20
  special = true
}

resource "aws_secretsmanager_secret" "database_url" {
  name = "${local.project_name}/database-url"
}

resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id     = aws_secretsmanager_secret.database_url.id
  secret_string = "postgresql://${var.db_username}:${random_password.db.result}@${aws_db_instance.api.address}:${aws_db_instance.api.port}/${var.db_name}"
}

resource "aws_ssm_parameter" "web_google_maps_key" {
  name  = "/${local.project_name}/web/google_maps_api_key"
  type  = "SecureString"
  value = var.google_maps_api_key
}

resource "aws_ssm_parameter" "web_api_base_url" {
  name  = "/${local.project_name}/web/api_base_url"
  type  = "String"
  value = "https://${local.api_domain}"
}
