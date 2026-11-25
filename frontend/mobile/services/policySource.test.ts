import {
  buildReleasePolicySource,
  isPastReleaseDate,
  isPolicyPersonId,
  isValidReleaseDate,
  toPolicyPersonId,
} from './policySource'

describe('policy source helpers', () => {
  it('creates valid person IDs and rejects reserved or malformed IDs', () => {
    expect(toPolicyPersonId('123 Sample')).toBe('person_123_sample')
    expect(toPolicyPersonId('release')).toBe('person_release')
    expect(isPolicyPersonId('sample_person_2')).toBe(true)
    expect(isPolicyPersonId('2sample')).toBe(false)
    expect(isPolicyPersonId('release')).toBe(false)
    expect(isPolicyPersonId('Sample')).toBe(false)
  })

  it('replaces matching top-level release rules case-insensitively', () => {
    const source = [
      'protocol family:',
      '    may see existence of entries tagged "Family"',
      'release letter "Fictional Letter" to sample_person when date >= 2040-05-01',
      'default writing mode: light_fix',
    ].join('\n')

    expect(
      buildReleasePolicySource(source, 'fictional letter', 'new_person', '2042-06-07'),
    ).toBe(
      [
        'protocol family:',
        '    may see existence of entries tagged "Family"',
        'default writing mode: light_fix',
        'release letter "fictional letter" to new_person when date >= 2042-06-07',
      ].join('\n'),
    )
  })

  it('appends a release rule when no matching title exists', () => {
    const source = 'default writing mode: light_fix'
    expect(
      buildReleasePolicySource(source, 'Another Letter', 'sample_person', '2040-05-01'),
    ).toBe(
      `${source}\nrelease letter "Another Letter" to sample_person when date >= 2040-05-01`,
    )
  })

  it('preserves unparseable and indented release lines before appending', () => {
    const source = [
      'release letter "Broken \\q" to sample_person when date >= 2040-05-01',
      '    release letter "Fictional Letter" to sample_person when date >= 2040-05-01',
    ].join('\n')
    const result = buildReleasePolicySource(
      source,
      'Fictional Letter',
      'new_person',
      '2040-06-01',
    )

    expect(result).toBe(
      `${source}\nrelease letter "Fictional Letter" to new_person when date >= 2040-06-01`,
    )
  })

  it('JSON-escapes titles and validates real calendar dates', () => {
    expect(
      buildReleasePolicySource('', 'A "quoted"\nletter', 'sample_person', '2040-05-01'),
    ).toBe(
      'release letter "A \\"quoted\\"\\nletter" to sample_person when date >= 2040-05-01',
    )
    expect(isValidReleaseDate('2040-02-29')).toBe(true)
    expect(isValidReleaseDate('2041-02-29')).toBe(false)
    expect(isValidReleaseDate('2040-13-01')).toBe(false)
    expect(isValidReleaseDate('2040-5-01')).toBe(false)
    expect(isPastReleaseDate('2040-01-01', new Date(2040, 0, 2))).toBe(true)
    expect(isPastReleaseDate('2040-01-02', new Date(2040, 0, 2))).toBe(false)
  })
})
