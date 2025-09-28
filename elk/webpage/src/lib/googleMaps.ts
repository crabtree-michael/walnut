import { Loader } from '@googlemaps/js-api-loader';

const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY as string | undefined;

if (!apiKey) {
  // eslint-disable-next-line no-console
  console.warn('Missing VITE_GOOGLE_MAPS_API_KEY environment variable. Places search will be disabled.');
}

const loader = new Loader({
  apiKey: apiKey ?? '',
  libraries: ['places']
});

export async function getAutocompleteService(): Promise<google.maps.places.AutocompleteService | null> {
  if (!apiKey) {
    return null;
  }

  await loader.load();
  return new google.maps.places.AutocompleteService();
}

export async function getGeocoder(): Promise<google.maps.Geocoder | null> {
  if (!apiKey) {
    return null;
  }

  await loader.load();
  return new google.maps.Geocoder();
}

export async function getPlacesService(): Promise<google.maps.places.PlacesService | null> {
  if (!apiKey) {
    return null;
  }

  await loader.load();
  const container = document.createElement('div');
  return new google.maps.places.PlacesService(container);
}
