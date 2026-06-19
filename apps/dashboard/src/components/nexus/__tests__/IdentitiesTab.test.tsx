import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import IdentitiesTab from '../IdentitiesTab';
import type { Persona } from '@/lib/types';

const personA: Persona = {
    id: 'p-1',
    name: 'Alpha Persona',
    reference_image_uri: 'https://example.com/alpha.png',
};
const personB: Persona = {
    _id: 'p-2', // mongo-style id, falls back when `id` is missing
    name: 'Bravo Persona',
    reference_image_uri: 'https://example.com/bravo.png',
};

describe('IdentitiesTab persona card mapping', () => {
    it('renders one card per persona', () => {
        render(<IdentitiesTab personas={[personA, personB]} />);
        expect(screen.getByText('Alpha Persona')).toBeInTheDocument();
        expect(screen.getByText('Bravo Persona')).toBeInTheDocument();
        expect(screen.getAllByRole('img')).toHaveLength(2);
    });

    it('uses persona.id when present', () => {
        render(<IdentitiesTab personas={[personA]} />);
        expect(screen.getByText('ID: p-1')).toBeInTheDocument();
    });

    it('falls back to persona._id when persona.id is missing', () => {
        render(<IdentitiesTab personas={[personB]} />);
        expect(screen.getByText('ID: p-2')).toBeInTheDocument();
    });

    it('renders <img alt={name}> when reference_image_uri is present', () => {
        render(<IdentitiesTab personas={[personA]} />);
        const img = screen.getByRole('img', { name: 'Alpha Persona' });
        expect(img).toHaveAttribute('src', 'https://example.com/alpha.png');
    });

    it('falls back to username icon when reference_image_uri is missing', () => {
        const incomplete = {
            id: 'p-3',
            name: 'No Image Person',
        } as unknown as Persona;
        render(<IdentitiesTab personas={[incomplete]} />);
        expect(screen.getByText('No Image Person')).toBeInTheDocument();
        // No <img> for this card
        expect(screen.queryByRole('img')).not.toBeInTheDocument();
    });

    it('renders the empty state when personas is the empty array', () => {
        render(<IdentitiesTab personas={[]} />);
        expect(screen.getByText(/no neural ids found/i)).toBeInTheDocument();
    });

    it('always renders the header and the "Register New ID" button', () => {
        render(<IdentitiesTab personas={[personA]} />);
        expect(
            screen.getByRole('heading', { name: /neural identity lab/i }),
        ).toBeInTheDocument();
        expect(
            screen.getByRole('button', { name: /register new id/i }),
        ).toBeInTheDocument();
    });

    it('renders one Modify button per persona', () => {
        render(<IdentitiesTab personas={[personA, personB]} />);
        const buttons = screen.getAllByRole('button', { name: /modify/i });
        expect(buttons).toHaveLength(2);
    });
});
