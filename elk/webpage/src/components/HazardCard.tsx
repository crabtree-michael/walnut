import { Hazard } from '../types';
import './HazardCard.css';

const SEVERITY_COLORS: Record<Hazard['severity'], string> = {
  low: '#28a745',
  medium: '#ffb703',
  high: '#d90429'
};

const TYPE_LABELS: Record<Hazard['type'], string> = {
  animal: 'Animal',
  event: 'Event',
  weather: 'Weather',
  disease: 'Disease'
};

interface HazardCardProps {
  hazard: Hazard;
}

export function HazardCard({ hazard }: HazardCardProps) {
  return (
    <article className="hazard-card">
      <header>
        <div className="hazard-card__header">
          <h3>{hazard.name}</h3>
          <span className="hazard-card__severity" style={{ backgroundColor: SEVERITY_COLORS[hazard.severity] }}>
            {hazard.severity.toUpperCase()}
          </span>
        </div>
        <p className="hazard-card__tag">{TYPE_LABELS[hazard.type]}</p>
        {hazard.description && <p className="hazard-card__description">{hazard.description}</p>}
      </header>
      {!!hazard.tips.length && (
        <section className="hazard-card__section">
          <h4>Tips</h4>
          <ul>
            {hazard.tips.map((tip) => (
              <li key={tip.id}>
                <strong>{tip.name}</strong>
                <span>{tip.description}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
      {!!hazard.presentations.length && (
        <section className="hazard-card__section">
          <h4>Where</h4>
          <ul>
            {hazard.presentations.map((presentation) => (
              <li key={presentation.id}>
                {presentation.location ? presentation.location.name : 'Unnamed area'}
                {presentation.notes && <span className="hazard-card__note">{presentation.notes}</span>}
              </li>
            ))}
          </ul>
        </section>
      )}
    </article>
  );
}
