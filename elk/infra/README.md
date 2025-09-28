# Elk Infrastructure

Terraform configuration that provisions the Elk API and web frontend on AWS.

## Stack overview

- **API**
  - Amazon ECS Fargate service running the Docker image published from `api/`.
  - Application Load Balancer fronted by Route 53 record `elk-api.macmail.app`.
  - Amazon RDS PostgreSQL instance sized for a small production footprint.
  - Secrets Manager entry exposing a `DATABASE_URL` string to the task definition.
- **Webpage**
  - S3 bucket with static website hosting for the compiled Vite build.
  - Public access policy and Route 53 record `elk.macmail.app` pointing to the site.
  - SSM Parameter storing the Google Maps API key supplied during deployment.

## Getting started

```bash
cd infra
terraform init
terraform plan \
  -var="aws_region=us-west-2" \
  -var="hosted_zone_id=Z123456789" \
  -var="api_image=123456789012.dkr.ecr.us-west-2.amazonaws.com/elk-api:latest" \
  -var="google_maps_api_key=YOUR_KEY_HERE"
terraform apply # review plan before confirming
```

Required variables:

- `aws_region` – AWS region for all resources (default `us-west-2`).
- `hosted_zone_id` – Route 53 hosted zone containing `macmail.app`.
- `api_image` – Full name of the Docker image pushed from the API project.
- `google_maps_api_key` – Google Maps key stored securely for the web app.

Optional variables map to project naming, DB sizing, and network CIDR ranges (see `variables.tf`).

## Deploy process

1. Push the API image to ECR (`aws ecr get-login-password | docker login ...`).
2. Run `terraform apply` with the variables above.
3. Build the React app (`npm run build`) and sync `webpage/dist` to the S3 bucket output (`aws s3 sync webpage/dist s3://elk.macmail.app`).
4. Distribute the API `.env`/Secrets values to operations teams for local debugging (Terraform outputs redact secrets by default).

Terraform outputs include the ALB URL, Route 53 records, S3 bucket name, and ARNs for secrets/SSM parameters.
