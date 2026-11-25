// Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)
// Paradigm: Functional (pure policy-source helpers)

const reservedPolicyWords = new Set([
  'protocol',
  'may',
  'see',
  'existence',
  'of',
  'read',
  'summary',
  'verbatim',
  'not',
  'entries',
  'mentioning',
  'tagged',
  'release',
  'letter',
  'to',
  'when',
  'date',
  'transfer',
  'custody',
  'if',
  'trustee',
  'unavailable',
  'for',
  'days',
  'is',
  'default',
  'writing',
  'mode',
  'light_fix',
  'review',
])

export function isPolicyPersonId(value: string): boolean {
  return /^[a-z][a-z0-9_]*$/.test(value) && !reservedPolicyWords.has(value)
}

export function toPolicyPersonId(value: string, fallback = 'person'): string {
  let identifier = value.trim().toLowerCase().replace(/[^a-z0-9_]/g, '_')
  if (!identifier) identifier = fallback
  if (!/^[a-z]/.test(identifier)) identifier = `person_${identifier}`
  if (reservedPolicyWords.has(identifier)) identifier = `person_${identifier}`
  return identifier
}

function releaseTitleFromLine(line: string): string | null {
  const prefix = 'release letter '
  if (!line.startsWith(`${prefix}"`)) return null

  const start = prefix.length
  let escaped = false
  for (let index = start + 1; index < line.length; index += 1) {
    const character = line[index]
    if (escaped) {
      escaped = false
    } else if (character === '\\') {
      escaped = true
    } else if (character === '"') {
      try {
        const title: unknown = JSON.parse(line.slice(start, index + 1))
        return typeof title === 'string' ? title : null
      } catch {
        return null
      }
    }
  }
  return null
}

export function buildReleasePolicySource(
  source: string,
  title: string,
  recipient: string,
  releaseDate: string,
): string {
  const matchingTitle = title.toLowerCase()
  const lines = source.split(/\r?\n/)
  if (source.endsWith('\n')) lines.pop()
  const preservedLines = lines.filter((line) => {
    const existingTitle = releaseTitleFromLine(line)
    return existingTitle === null || existingTitle.toLowerCase() !== matchingTitle
  })
  const rule = `release letter ${JSON.stringify(title)} to ${recipient} when date >= ${releaseDate}`
  const preservedSource = preservedLines.join('\n')
  return preservedSource ? `${preservedSource}\n${rule}` : rule
}

export function isValidReleaseDate(value: string): boolean {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value)
  if (!match) return false

  const year = Number(match[1])
  const month = Number(match[2])
  const day = Number(match[3])
  if (year < 1 || month < 1 || month > 12 || day < 1 || day > 31) return false

  const date = new Date(0)
  date.setUTCHours(0, 0, 0, 0)
  date.setUTCFullYear(year, month - 1, day)
  return (
    date.getUTCFullYear() === year &&
    date.getUTCMonth() === month - 1 &&
    date.getUTCDate() === day
  )
}

export function isPastReleaseDate(value: string, today = new Date()): boolean {
  if (!isValidReleaseDate(value)) return false
  const currentDate = [
    today.getFullYear(),
    String(today.getMonth() + 1).padStart(2, '0'),
    String(today.getDate()).padStart(2, '0'),
  ].join('-')
  return value < currentDate
}
