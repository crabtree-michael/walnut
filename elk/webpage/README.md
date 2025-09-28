# Elk Webpage

React single-page application for discovering hazards and safety tips around Colorado locations. Search uses Google Places Autocomplete for rich suggestions (with an offline-friendly mock fallback) and the Elk API to surface hazard intel.

## Getting started

```bash
cd webpage
npm install
cp envs/local.env .env.local
npm run dev
```

The app expects:

- `VITE_API_BASE_URL` – URL of the Elk API (defaults to `http://localhost:8000`).
- `VITE_GOOGLE_MAPS_API_KEY` – Google Maps API key with Places access.

## Scripts

- `npm run dev` – Start Vite dev server on port 5173.
- `npm run build` – Build production assets.
- `npm run preview` – Preview the production build.
- `npm run lint` – Check TypeScript/React patterns.

## Structure

- `src/components` – Reusable UI pieces (layout, search, hazard cards).
- `src/pages` – Route-level views for the homepage and location detail.
- `src/services` – API clients for Elk and Google, plus mock location data.
- `src/hooks` – Hooks for autocomplete and other data flows.

Search falls back to curated Colorado destinations when Google Places is unavailable so the experience remains testable without external calls.
