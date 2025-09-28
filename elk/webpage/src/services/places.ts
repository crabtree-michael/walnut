import { getMockLocation } from './maps';
import { getGeocoder, getPlacesService } from '../lib/googleMaps';

export interface PlaceDetails {
  placeId: string;
  name: string;
  formattedAddress?: string;
  location?: {
    lat: number;
    lng: number;
  };
}

export async function fetchPlaceDetails(placeId: string): Promise<PlaceDetails | null> {
  const mock = getMockLocation(placeId);
  if (mock) {
    return {
      placeId: mock.placeId,
      name: mock.name,
      formattedAddress: mock.description,
      location: { lat: mock.latitude, lng: mock.longitude }
    };
  }

  const service = await getPlacesService();
  if (!service) {
    return null;
  }

  return new Promise((resolve) => {
    service.getDetails(
      {
        placeId,
        fields: ['place_id', 'name', 'formatted_address', 'geometry']
      },
      (result, status) => {
        if (status !== google.maps.places.PlacesServiceStatus.OK || !result) {
          resolve(null);
          return;
        }

        resolve({
          placeId: result.place_id ?? placeId,
          name: result.name ?? 'Unknown place',
          formattedAddress: result.formatted_address ?? undefined,
          location: result.geometry?.location
            ? {
                lat: result.geometry.location.lat(),
                lng: result.geometry.location.lng()
              }
            : undefined
        });
      }
    );
  });
}

export async function geocodeLatLng(lat: number, lng: number) {
  const geocoder = await getGeocoder();
  if (!geocoder) {
    return null;
  }

  return new Promise<string | null>((resolve) => {
    geocoder.geocode({ location: { lat, lng } }, (results, status) => {
      if (status === google.maps.GeocoderStatus.OK && results?.length) {
        resolve(results[0].formatted_address ?? null);
      } else {
        resolve(null);
      }
    });
  });
}
