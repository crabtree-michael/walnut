import { useEffect, useRef, useState } from 'react';
import { getAutocompleteService } from '../lib/googleMaps';
import { queryMockLocations } from '../services/maps';

export interface PlaceSuggestion {
  description: string;
  placeId: string;
  types: string[];
}

const COLORADO_BOUNDS: google.maps.places.LocationBias = {
  north: 41.0,
  south: 36.992424,
  east: -102.041524,
  west: -109.060253
};

export function usePlacesAutocomplete(query: string) {
  const [suggestions, setSuggestions] = useState<PlaceSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pendingRequest = useRef<number | null>(null);

  useEffect(() => {
    let active = true;

    async function fetchSuggestions() {
      if (!query) {
        setSuggestions([]);
        setError(null);
        return;
      }

      setLoading(true);
      setError(null);

      const service = await getAutocompleteService();
      if (!service || !active) {
        setLoading(false);
        setSuggestions(
          queryMockLocations(query).map((item) => ({
            description: `${item.name} — ${item.description}`.trim(),
            placeId: item.placeId,
            types: ['geocode']
          }))
        );
        return;
      }

      pendingRequest.current = window.requestAnimationFrame(() => {
        service.getPlacePredictions(
          {
            input: query,
            locationBias: COLORADO_BOUNDS,
            componentRestrictions: { country: 'us' },
            types: ['establishment', 'geocode']
          },
          (predictions, status) => {
            if (!active) {
              return;
            }
            setLoading(false);
            if (status !== google.maps.places.PlacesServiceStatus.OK || !predictions) {
              setSuggestions([]);
              if (status !== google.maps.places.PlacesServiceStatus.ZERO_RESULTS) {
                setError('Unable to fetch suggestions right now.');
              }
              return;
            }

            setSuggestions(
              predictions.slice(0, 5).map((item) => ({
                description: item.description ?? '',
                placeId: item.place_id ?? '',
                types: item.types ?? []
              }))
            );
          }
        );
      });
    }

    fetchSuggestions();

    return () => {
      active = false;
      if (pendingRequest.current) {
        cancelAnimationFrame(pendingRequest.current);
      }
    };
  }, [query]);

  return { suggestions, loading, error };
}
