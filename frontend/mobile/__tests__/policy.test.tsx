import { fireEvent, render } from '@testing-library/react-native'
import PolicyScreen from '@/app/(tabs)/policy'
import { AppDataProvider } from '@/context/AppDataProvider'
import { AuthProvider } from '@/context/AuthProvider'

describe('PolicyScreen', () => {
  it('generates policy source text for a deny rule', async () => {
    const view = await render(
      <AuthProvider>
        <AppDataProvider>
          <PolicyScreen />
        </AppDataProvider>
      </AuthProvider>,
    )

    await fireEvent.press(view.getByRole('button', { name: 'deny verbatim' }))
    await fireEvent.press(view.getByRole('button', { name: 'Generate policy text' }))

    expect(view.getByLabelText('Policy source').props.value).toContain(
      'may not read verbatim of entries tagged "Family"',
    )
  })
})
