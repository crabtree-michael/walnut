#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: ./deploy.sh [options]

Builds and deploys the Elk API container image.

Options:
  --tag <number>        Use the provided numeric tag instead of auto-incrementing.
  --skip-build          Skip the Docker build step.
  --skip-push           Skip pushing the image to ECR.
  --skip-terraform      Skip updating Terraform state.
  --help                Show this message.

Environment variables:
  AWS_REGION        AWS region (default: us-west-2)
  ECR_REGISTRY      ECR registry host (default derived from AWS account)
  ECR_REPOSITORY    ECR repository name (default: elk-api)
  TERRAFORM_DIR     Relative path to Terraform config (default: infra)
USAGE
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
API_DIR="$REPO_ROOT/api"
TERRAFORM_DIR_REL=${TERRAFORM_DIR:-infra}
TERRAFORM_DIR_ABS="$REPO_ROOT/$TERRAFORM_DIR_REL"

AWS_REGION=${AWS_REGION:-us-west-2}
ECR_REPOSITORY=${ECR_REPOSITORY:-elk-api}

TAG=""
SKIP_BUILD=false
SKIP_PUSH=false
SKIP_TERRAFORM=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tag)
      [[ $# -ge 2 ]] || { echo "--tag requires a value" >&2; exit 1; }
      TAG="$2"
      shift 2
      continue
      ;;
    --skip-build)
      SKIP_BUILD=true
      ;;
    --skip-push)
      SKIP_PUSH=true
      ;;
    --skip-terraform)
      SKIP_TERRAFORM=true
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift
done

require_cmd docker
require_cmd aws
if [[ "$SKIP_TERRAFORM" != true ]]; then
  require_cmd terraform
  require_cmd python3
fi

if [[ -z ${ECR_REGISTRY:-} ]]; then
  ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text 2>/dev/null || true)
  if [[ -z "$ACCOUNT_ID" ]]; then
    echo "Unable to determine AWS account ID; set ECR_REGISTRY explicitly." >&2
    exit 1
  fi
  ECR_REGISTRY="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
fi

if [[ -z "$TAG" ]]; then
  IMAGE_TAGS=$(aws ecr describe-images \
    --region "$AWS_REGION" \
    --repository-name "$ECR_REPOSITORY" \
    --query 'imageDetails[].imageTags[]' \
    --output text 2>/dev/null || true)
  LAST_TAG=$(printf '%s\n' "$IMAGE_TAGS" | tr '\t' '\n' | grep -E '^[0-9]+$' | sort -n | tail -n1 || true)
  if [[ -z "$LAST_TAG" ]]; then
    TAG=1
  else
    TAG=$((LAST_TAG + 1))
  fi
fi
if ! [[ "$TAG" =~ ^[0-9]+$ ]]; then
  echo "Tag must be numeric, got: $TAG" >&2
  exit 1
fi

IMAGE_FULL="$ECR_REGISTRY/$ECR_REPOSITORY:$TAG"

if [[ "$SKIP_BUILD" != true ]]; then
  docker build --platform linux/amd64 -t "$IMAGE_FULL" "$API_DIR"
fi

if [[ "$SKIP_PUSH" != true ]]; then
  aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_REGISTRY"
  docker push "$IMAGE_FULL"
fi

if [[ "$SKIP_TERRAFORM" != true ]]; then
  TF_VARS_FILE="$TERRAFORM_DIR_ABS/dev.auto.tfvars"
  if [[ -f "$TF_VARS_FILE" ]]; then
    python3 - "$TF_VARS_FILE" "$IMAGE_FULL" <<'PY'
import re
import sys
from pathlib import Path

tfvars_path = Path(sys.argv[1])
image_uri = sys.argv[2]
pattern = re.compile(r'(api_image\s*=\s*")[^"]*(")')
content = tfvars_path.read_text()
replacement = r"\g<1>" + image_uri + r"\g<2>"
updated, count = pattern.subn(replacement, content)
if count == 0:
    raise SystemExit(f"Failed to update api_image in {tfvars_path}")
tfvars_path.write_text(updated)
PY
  fi
  terraform -chdir="$TERRAFORM_DIR_ABS" apply -auto-approve
fi

echo "Deployed image: $IMAGE_FULL"
