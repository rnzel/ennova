import { fireEvent, render } from '@testing-library/react-native'
import type { ReactNode } from 'react'
import LoginScreen from '@/app/login'
import { AuthProvider } from '@/context/AuthProvider'

const fetchMock = jest.fn()

jest.mock('expo-router', () => ({
  Link: ({ children }: { children: ReactNode }) => children,
  router: {
    replace: jest.fn(),
  },
}))

describe('LoginScreen', () => {
  beforeEach(() => {
    process.env.EXPO_PUBLIC_API_BASE_URL = 'http://localhost:5000'
    fetchMock.mockReset()
    globalThis.fetch = fetchMock
  })

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
    expect(view.getByLabelText('Email address')).toBeTruthy()
    expect(view.getByRole('button', { name: 'Register beneficiary' })).toBeTruthy()
    expect(view.getByText(/Username: 3-64 characters/)).toBeTruthy()
  })

  it.each([
    ['empty', ''],
    ['without an at sign', 'person.example.com'],
    ['with multiple at signs', 'person@@example.com'],
    ['longer than 254 characters', `${'a'.repeat(243)}@example.com`],
  ])('rejects an email that is %s before sending a request', async (_case, email) => {
    const view = await render(
      <AuthProvider>
        <LoginScreen />
      </AuthProvider>,
    )

    await fireEvent.press(view.getByText('Create a new owner account'))
    await fireEvent.changeText(view.getByLabelText('Username'), 'sample_owner')
    await fireEvent.changeText(view.getByLabelText('Password'), 'sample-password-123')
    await fireEvent.changeText(view.getByLabelText('Email address'), email)
    await fireEvent.press(view.getByRole('button', { name: 'Create owner account' }))

    expect(
      view.getByText('Enter an email with exactly one @ and no more than 254 characters.'),
    ).toBeTruthy()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('sends a trimmed email for owner registration', async () => {
    fetchMock
      .mockResolvedValueOnce({
        ok: true,
        status: 201,
        text: async () => JSON.stringify({
          account_id: 'owner-id',
          username: 'sample_owner',
          owner_id: 'owner-id',
          person_id: 'sample_owner',
          role: 'owner',
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ access_token: 'test-token', token_type: 'Bearer' }),
      })
    const view = await render(
      <AuthProvider>
        <LoginScreen />
      </AuthProvider>,
    )

    await fireEvent.press(view.getByText('Create a new owner account'))
    await fireEvent.changeText(view.getByLabelText('Username'), 'sample_owner')
    await fireEvent.changeText(view.getByLabelText('Password'), 'sample-password-123')
    await fireEvent.changeText(view.getByLabelText('Email address'), ' person@example.com ')
    await fireEvent.press(view.getByRole('button', { name: 'Create owner account' }))

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      'http://localhost:5000/auth/register-owner',
      expect.objectContaining({
        body: JSON.stringify({
          username: 'sample_owner',
          email: 'person@example.com',
          password: 'sample-password-123',
        }),
      }),
    )
  })

  it('sends a trimmed email for beneficiary registration', async () => {
    fetchMock
      .mockResolvedValueOnce({
        ok: true,
        status: 201,
        text: async () => JSON.stringify({
          account_id: 'beneficiary-id',
          username: 'sample_beneficiary',
          owner_id: 'owner-id',
          person_id: 'sample_person',
          role: 'beneficiary',
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ access_token: 'test-token', token_type: 'Bearer' }),
      })
    const view = await render(
      <AuthProvider>
        <LoginScreen />
      </AuthProvider>,
    )

    await fireEvent.press(view.getByText('Register with an invitation code'))
    await fireEvent.changeText(view.getByLabelText('Invitation code'), 'SAMPLE-CODE')
    await fireEvent.changeText(view.getByLabelText('Username'), 'sample_beneficiary')
    await fireEvent.changeText(view.getByLabelText('Password'), 'sample-password-123')
    await fireEvent.changeText(view.getByLabelText('Email address'), ' person@example.com ')
    await fireEvent.press(view.getByRole('button', { name: 'Register beneficiary' }))

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      'http://localhost:5000/auth/register-beneficiary',
      expect.objectContaining({
        body: JSON.stringify({
          invitation_code: 'SAMPLE-CODE',
          username: 'sample_beneficiary',
          email: 'person@example.com',
          password: 'sample-password-123',
        }),
      }),
    )
  })
})
