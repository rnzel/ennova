import type { BadgeTone, EntryVisibility } from '../types'

export function visibilityTone(visibility: EntryVisibility): BadgeTone {
  switch (visibility) {
    case 'Private':
      return 'private'
    case 'Shared':
      return 'shared'
    case 'Restricted':
      return 'restricted'
  }
}
