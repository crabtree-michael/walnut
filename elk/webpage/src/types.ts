export type HazardSeverity = 'low' | 'medium' | 'high';
export type HazardType = 'animal' | 'event' | 'weather' | 'disease';

export interface Tip {
  id: number;
  name: string;
  description: string;
}

export interface LocationSummary {
  id: number;
  name: string;
  type: string;
  latitude: number;
  longitude: number;
  description?: string;
  image?: string;
}

export interface HazardPresentation {
  id: number;
  boundary: unknown;
  notes?: string;
  location?: LocationSummary;
}

export interface Hazard {
  id: number;
  name: string;
  severity: HazardSeverity;
  type: HazardType;
  description?: string;
  tips: Tip[];
  presentations: HazardPresentation[];
}

export interface HazardQueryParams {
  latitude: number;
  longitude: number;
}
