export function buildLocationPath(placeId: string): string {
  return `/location/${encodeURIComponent(placeId)}`;
}

export function buildLocationUrl(placeId: string, origin?: string): string {
  const base = origin ?? (typeof window !== 'undefined' ? window.location.origin : '');
  if (!base) {
    return buildLocationPath(placeId);
  }

  return new URL(buildLocationPath(placeId), base).toString();
}
