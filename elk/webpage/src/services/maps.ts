
const MOCK_LOCATIONS = [
  {
    name: 'Rocky Mountain National Park',
    placeId: 'mock-rocky-mountain-national-park',
    description: 'Estes Park, Colorado',
    latitude: 40.3428,
    longitude: -105.6836
  },
  {
    name: 'Garden of the Gods',
    placeId: 'mock-garden-of-the-gods',
    description: 'Colorado Springs, Colorado',
    latitude: 38.8784,
    longitude: -104.8690
  },
  {
    name: 'Great Sand Dunes National Park',
    placeId: 'mock-great-sand-dunes',
    description: 'Mosca, Colorado',
    latitude: 37.7327,
    longitude: -105.5130
  },
  {
    name: 'Mesa Verde National Park',
    placeId: 'mock-mesa-verde',
    description: 'Montezuma County, Colorado',
    latitude: 37.2309,
    longitude: -108.4618
  },
  {
    name: 'Black Canyon of the Gunnison',
    placeId: 'mock-black-canyon',
    description: 'Montrose County, Colorado',
    latitude: 38.5754,
    longitude: -107.7418
  }
];

export interface MockSuggestion {
  name: string;
  placeId: string;
  description: string;
  latitude: number;
  longitude: number;
}

export function queryMockLocations(search: string): MockSuggestion[] {
  if (!search) {
    return [];
  }

  const term = search.toLowerCase();
  return MOCK_LOCATIONS.filter((location) => location.name.toLowerCase().includes(term)).slice(0, 5);
}

export function getMockLocation(placeId: string) {
  return MOCK_LOCATIONS.find((location) => location.placeId === placeId) ?? null;
}
