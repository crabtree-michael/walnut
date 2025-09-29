import type { Hazard, HazardQueryParams } from '../types';

const baseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || 'Request failed');
  }
  return response.json() as Promise<T>;
}

export async function fetchHazards(params: HazardQueryParams): Promise<Hazard[]> {
  const url = new URL('/hazards/', baseUrl);
  url.searchParams.set('latitude', params.latitude.toString());
  url.searchParams.set('longitude', params.longitude.toString());
  const response = await fetch(url.toString(), {
    headers: {
      'Content-Type': 'application/json'
    }
  });
  return handleResponse<Hazard[]>(response);
}
