data "aws_cloudfront_distribution" "web" {
  count = var.existing_cloudfront_distribution_id == "" ? 0 : 1
  id    = var.existing_cloudfront_distribution_id
}
