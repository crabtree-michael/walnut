# Elk System Overview

Elk centralizes park safety information so users can quickly understand the hazards, tips, and locations that matter. The platform is composed of three cooperating systems:

- **API** – A Django and Postgres service that stores hazards, tips, and their presentations. It exposes endpoints for discovering hazards around a GPS point and for administrators to add hazards and presentations. The API is packaged as a Docker image (`elk-api:{number}`) and is expected to run migrations and serve traffic via Gunicorn.
- **Webpage** – A React application that lets visitors search locations (restricted to Colorado) via Google Maps, review summaries, and browse hazard lists. Key flows include the homepage search and a shareable location page that queries the API for hazard and tip data.
- **Scraper** – A Python toolchain (with downloader, parser, and future inserter components) that collects open-source safety information, converts it into structured hazards, tips, and locations using an on-device LLM, and prepares data for the API.

Infrastructure is defined separately to deploy the API to AWS (RDS, ECS, Route53) and publish the compiled webpage to S3, wiring configuration such as database connectivity, allowed hosts, and API base URLs.

## Configuration-Driven Development

Every capability above is specified through `.llm.yaml` configuration files. These files are the single source of truth for requirements; developers should refine *only* the `.llm.yaml` files and avoid editing implementation code directly.

- `index.llm.yaml` maps the overall Elk objective, lists each system, and links them to their detailed specifications.
- `api.llm.yaml` defines the API service: framework expectations, environment variables, Docker build rules, environments, exposed requirements, and the hazard/tip models it relies on.
- `webpage.llm.yaml` captures the React app structure, page behaviors, styling direction, external dependencies (API and Google Maps), and routing expectations for homepage and location experiences.
- `scraper.llm.yaml` outlines the scraping pipeline, component responsibilities, commands, LLM integration, and data handling rules for transforming source HTML into the shared data models.
- `models.llm.yaml` standardizes the hazard, tip, and location schemas so every subsystem (API, parser, inserter) works against consistent data contracts.
- `infra.llm.yaml` documents the AWS deployment plan, including how infrastructure components consume outputs from the API and webpage builds and which secrets or environment values must be provided.

Keeping these configuration files accurate ensures generators and tooling can build or adjust the underlying code safely. When changes are required, update the relevant `.llm.yaml` specification and let the automated build processes regenerate or adapt the implementation as needed.
