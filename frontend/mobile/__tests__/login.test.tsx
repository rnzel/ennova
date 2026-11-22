import { fireEvent, render } from '@testing-library/react-native'
import type { ReactNode } from 'react'
import LoginScreen from '@/app/login'
import { AuthProvider } from '@/context/AuthProvider'

jest.mock('expo-router', () => ({
  Link: ({ children }: { children: ReactNode }) => children,
  router: {
    replace: jest.fn(),
  },
}))

describe('LoginScreen', () => {
  it('shows field-level guidance rather than submitting an empty form', async () => {
    const view = await render(
      <AuthProvider>
        <LoginScreen />
      </AuthProvider>,
    )

    await fireEvent.press(view.getByRole('button', { name: 'Sign in' }))

    expect(view.getByText('Enter a username and password.')).toBeTruthy()
  })

  it('labels the invitation field when beneficiary registration is selected', async () => {
    const view = await render(
      <AuthProvider>
        <LoginScreen />
      </AuthProvider>,
    )

    await fireEvent.press(view.getByText('Register with an invitation code'))

    expect(view.getByLabelText('Invitation code')).toBeTruthy()
    expect(view.getByRole('button', { name: 'Register beneficiary' })).toBeTruthy()
  })
})
