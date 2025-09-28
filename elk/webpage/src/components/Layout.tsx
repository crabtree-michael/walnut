import { PropsWithChildren } from 'react';
import { Link } from 'react-router-dom';
import './Layout.css';

export function Layout({ children }: PropsWithChildren) {
  return (
    <div className="layout">
      <header className="layout__header">
        <Link to="/" className="logo">
          Elk
        </Link>
      </header>
      <main className="layout__content">{children}</main>
      <footer className="layout__footer">Stay informed. Stay safe.</footer>
    </div>
  );
}
