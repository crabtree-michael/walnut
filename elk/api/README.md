# Elk API

Django REST API for Elk hazard data. Provides endpoints for retrieving hazards at a specific GPS point and for admins to manage hazards and their presentations.

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Set the following environment variables when running against PostgreSQL:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

When running via Docker, use:

```bash
docker compose up --build
```

## Docker build

For ECS/Fargate deployments build the image for linux/amd64:

```bash
docker build --platform linux/amd64 -t <account-id>.dkr.ecr.<region>.amazonaws.com/elk-api:<tag> .
```

### Running management commands against the deployed database

Use a running ECS task to execute Django commands with the production environment:

```bash
aws ecs execute-command \
  --cluster elk-cluster \
  --task <running-task-id> \
  --container api \
  --command "python manage.py migrate" \
  --interactive

aws ecs execute-command \
  --cluster elk-cluster \
  --task <running-task-id> \
  --container api \
  --command "python manage.py createsuperuser" \
  --interactive
```

The API will listen on port `8000`.

## Endpoints

- `GET /hazards?latitude=<lat>&longitude=<lng>` – List hazards with presentations containing the point.
- `POST /hazards` – Admin-only endpoint for creating a hazard.
- `POST /hazards/<id>/presentations` – Admin-only endpoint for adding a presentation to a hazard (requires `latitude`, `longitude`, `radius_meters`, optional `notes` and `location_id`).
