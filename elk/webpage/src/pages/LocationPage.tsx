import { useMemo } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchHazards } from '../services/api';
import { fetchPlaceDetails } from '../services/places';
import { HazardCard } from '../components/HazardCard';
import type { Hazard } from '../types';
import './LocationPage.css';

export default function LocationPage() {
  const { placeId } = useParams<{ placeId: string }>();

  const {
    data: place,
    isLoading: placeLoading,
    error: placeError
  } = useQuery({
    queryKey: ['place', placeId],
    queryFn: () => fetchPlaceDetails(placeId ?? ''),
    enabled: Boolean(placeId)
  });

  const {
    data: hazards,
    isLoading: hazardsLoading,
    error: hazardsError
  } = useQuery({
    queryKey: ['hazards', place?.location?.lat, place?.location?.lng],
    queryFn: () =>
      fetchHazards({
        latitude: place!.location!.lat,
        longitude: place!.location!.lng
      }),
    enabled: Boolean(place?.location)
  });

  const heading = useMemo(() => {
    if (place?.name) {
      return place.name;
    }
    if (placeLoading) {
      return 'Loading location…';
    }
    return 'Unknown location';
  }, [place, placeLoading]);

  const description = place?.formattedAddress;
  const locationUnavailable = !place && !placeLoading;

  const showEmptyState = !hazardsLoading && !hazardsError && (hazards?.length ?? 0) === 0;

  return (
    <div className="location-page">
      <header className="location-page__header">
        <div>
          <h1>{heading}</h1>
          {description && <p className="location-page__address">{description}</p>}
        </div>
        <Link to="/" className="location-page__back">
          ← Back to search
        </Link>
      </header>

      {placeError && <p className="location-page__error">Unable to load this location right now.</p>}
      {hazardsError && <p className="location-page__error">Unable to load hazards from the API.</p>}
      {locationUnavailable && !placeError && (
        <p className="location-page__error">We couldn’t load map details for this place.</p>
      )}

      {(placeLoading || hazardsLoading) && <div className="location-page__loading">Loading hazard data…</div>}

      {place?.location && (
        <section className="location-page__summary">
          <div>
            <h2>Coordinates</h2>
            <p>{place.location.lat.toFixed(4)}, {place.location.lng.toFixed(4)}</p>
          </div>
          <div>
            <h2>Hazards in area</h2>
            <p>{hazards?.length ?? 0}</p>
          </div>
        </section>
      )}

      {showEmptyState && (
        <p className="location-page__empty">No hazards reported at this location</p>
      )}

      {!!hazards?.length && (
        <section className="location-page__hazards">
          {hazards.map((hazard: Hazard) => (
            <HazardCard key={hazard.id} hazard={hazard} />
          ))}
        </section>
      )}
    </div>
  );
}
