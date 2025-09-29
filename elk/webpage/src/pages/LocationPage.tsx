import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchHazards } from '../services/api';
import { fetchPlaceDetails } from '../services/places';
import { HazardCard } from '../components/HazardCard';
import type { Hazard } from '../types';
import { buildLocationUrl } from '../lib/paths';
import './LocationPage.css';

export default function LocationPage() {
  const { placeId } = useParams<{ placeId: string }>();
  const [shareMessage, setShareMessage] = useState<string | null>(null);
  const shareMessageTimeout = useRef<number>();

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

  useEffect(() => {
    return () => {
      if (shareMessageTimeout.current) {
        window.clearTimeout(shareMessageTimeout.current);
      }
    };
  }, []);

  const shareUrl = useMemo(() => {
    if (!placeId) {
      return '';
    }
    return buildLocationUrl(placeId);
  }, [placeId]);

  function setTimedShareMessage(message: string) {
    setShareMessage(message);
    if (shareMessageTimeout.current) {
      window.clearTimeout(shareMessageTimeout.current);
    }
    shareMessageTimeout.current = window.setTimeout(() => setShareMessage(null), 3200);
  }

  async function handleShare() {
    if (!placeId || !shareUrl) {
      return;
    }

    const navigatorWithShare = navigator as Navigator & {
      share?: (data: ShareData) => Promise<void>;
      clipboard?: Clipboard;
    };

    try {
      if (navigatorWithShare.share) {
        await navigatorWithShare.share({
          title: place?.name ?? 'Elk location',
          url: shareUrl
        });
        setTimedShareMessage('Share dialog opened');
        return;
      }

      if (navigatorWithShare.clipboard?.writeText) {
        await navigatorWithShare.clipboard.writeText(shareUrl);
        setTimedShareMessage('Link copied to your clipboard');
        return;
      }

      throw new Error('No share method available');
    } catch (error) {
      console.error('Failed to share link', error);
      setTimedShareMessage('Unable to share this link');
    }
  }

  return (
    <div className="location-page">
      <Link to="/" className="location-page__back">
        Back to search
      </Link>

      <header className="location-page__header">
        <h1>{heading}</h1>
        {description && <p className="location-page__address">{description}</p>}
        {placeId && (
          <button type="button" className="location-page__share" onClick={handleShare}>
            Share this page
          </button>
        )}
        {shareMessage && <p className="location-page__share-status">{shareMessage}</p>}
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
