resource "aws_s3_bucket" "web" {
  bucket        = local.web_domain
  force_destroy = var.web_bucket_force_destroy

  tags = {
    Name = local.web_domain
  }
}

resource "aws_s3_bucket_public_access_block" "web" {
  bucket = aws_s3_bucket.web.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_website_configuration" "web" {
  bucket = aws_s3_bucket.web.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}

resource "aws_s3_bucket_policy" "web_public" {
  bucket = aws_s3_bucket.web.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect    = "Allow",
        Principal = "*",
        Action    = ["s3:GetObject"],
        Resource  = "${aws_s3_bucket.web.arn}/*"
      }
    ]
  })
}

resource "aws_route53_record" "web_cloudfront" {
  count   = var.existing_cloudfront_distribution_id == "" ? 0 : 1
  zone_id = var.hosted_zone_id
  name    = local.web_domain
  type    = "A"

  alias {
    name                   = data.aws_cloudfront_distribution.web[0].domain_name
    zone_id                = data.aws_cloudfront_distribution.web[0].hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "web_s3" {
  count   = var.existing_cloudfront_distribution_id == "" ? 1 : 0
  zone_id = var.hosted_zone_id
  name    = local.web_domain
  type    = "CNAME"
  ttl     = 300
  records = [aws_s3_bucket_website_configuration.web.website_endpoint]
}
