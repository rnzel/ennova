import type { BadgeTone } from '../types'

type StatusBadgeProps = {
  label: string
  tone?: BadgeTone
}

export function StatusBadge({ label, tone = 'neutral' }: StatusBadgeProps) {
  return <span className={`badge badge-${tone}`}>{label}</span>
}
