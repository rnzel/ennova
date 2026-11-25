// Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)
// Paradigm: Functional (fictional preview fixtures)

import type { Beneficiary, DiaryEntry } from '../types'

export const initialEntries: DiaryEntry[] = [
  {
    id: 'entry-garden',
    title: 'The garden after the rain',
    date: 'Nov 14, 2026',
    summary: 'A quiet morning, a familiar garden, and a reminder to make time for small things.',
    content:
      'The garden looked different after the rain. The old lemon tree held drops of water on every leaf, and the path smelled like wet earth. I sat there longer than I planned and remembered that the best parts of a day are often the quiet ones.',
    visibility: 'Private',
    writingMode: 'Verbatim',
  },
  {
    id: 'entry-sunday',
    title: 'Sunday lunch traditions',
    date: 'Nov 10, 2026',
    summary: 'Notes on a family tradition and the stories that keep it meaningful.',
    content:
      'Sunday lunch has always been a reason to slow down and gather. I hope the tradition stays flexible, welcoming, and focused on being together rather than getting everything perfect.',
    visibility: 'Shared',
    writingMode: 'Light fix',
  },
  {
    id: 'entry-letter',
    title: 'A letter for another day',
    date: 'Nov 02, 2026',
    summary: 'A personal letter with a release date and a named recipient in the owner policy.',
    content:
      'This is a private sample letter. Its contents should only be available to its designated recipient after its release conditions are satisfied.',
    visibility: 'Restricted',
    writingMode: 'Review',
  },
  {
    id: 'entry-lessons',
    title: 'Things I hope you remember',
    date: 'Oct 26, 2026',
    summary: 'A short collection of lessons about patience, kindness, and asking for help.',
    content:
      'Be patient with yourself while you learn. Be kind when you can, and ask for help before a small problem grows into a heavy one.',
    visibility: 'Shared',
    writingMode: 'Verbatim',
  },
]

export const initialBeneficiaries: Beneficiary[] = [
  {
    id: 'beneficiary-amelia',
    name: 'Amelia Chen',
    email: 'amelia@example.test',
    relation: 'Daughter',
    status: 'Granted',
    lastSeen: 'Today',
  },
  {
    id: 'beneficiary-marcus',
    name: 'Marcus Lee',
    email: 'marcus@example.test',
    relation: 'Son',
    status: 'Review',
    lastSeen: 'Yesterday',
  },
  {
    id: 'beneficiary-sarah',
    name: 'Sarah Patel',
    email: 'sarah@example.test',
    relation: 'Friend',
    status: 'Pending',
    lastSeen: 'Not yet',
  },
]

export const initialPolicy = `protocol family:
    may see existence of entries tagged "Family"
    may read summary of entries tagged "Family"
release letter "A letter for another day" to amelia when date >= 2040-05-01
default writing mode: light_fix`
