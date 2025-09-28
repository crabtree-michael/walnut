import { FormEvent, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePlacesAutocomplete } from '../hooks/usePlacesAutocomplete';
import './SearchPanel.css';

export function SearchPanel() {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();
  const { suggestions, loading, error } = usePlacesAutocomplete(query);

  const disabled = useMemo(() => !query || loading, [query, loading]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const firstSuggestion = suggestions[0];
    if (firstSuggestion) {
      navigate(`/location/${firstSuggestion.placeId}`);
    }
  }

  return (
    <section className="search-panel">
      <h1 className="search-panel__headline">Safety insights for wherever you roam</h1>
      <p className="search-panel__subtitle">
        Search for Colorado parks, towns, and wild spaces to see active hazards and tips before you head out.
      </p>
      <form className="search-panel__form" onSubmit={handleSubmit}>
        <input
          className="search-panel__input"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search Colorado locations"
          aria-label="Search Colorado locations"
        />
        <button className="search-panel__submit" type="submit" disabled={disabled}>
          Explore
        </button>
      </form>
      {error && <div className="search-panel__error">{error}</div>}
      {!!suggestions.length && (
        <ul className="search-panel__suggestions" role="listbox">
          {suggestions.map((suggestion) => (
            <li key={suggestion.placeId}>
              <button
                type="button"
                className="search-panel__suggestion"
                onClick={() => navigate(`/location/${suggestion.placeId}`)}
              >
                {suggestion.description}
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
