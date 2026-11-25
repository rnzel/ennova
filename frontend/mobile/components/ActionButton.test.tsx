// Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)
// Paradigm: Functional (accessibility component tests)

import { render } from '@testing-library/react-native'
import { ActionButton } from './ActionButton'

describe('ActionButton', () => {
  it('exposes its visible label as the accessible button name', async () => {
    const view = await render(<ActionButton label="Save policy" onPress={jest.fn()} />)

    expect(view.getByRole('button', { name: 'Save policy' })).toBeTruthy()
  })
})
