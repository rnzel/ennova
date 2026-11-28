import { fireEvent, render, waitFor } from '@testing-library/react-native'
import LoginScreen from '@/app/login'
import { AuthProvider } from '@/context/AuthProvider'

const fetchMock = jest.fn()
const mockReplace = jest.fn()

jest.mock('expo-router', () => ({
  router: { replace: (...args: unknown[]) => mockReplace(...args) },
}))

describe('LoginScreen', () => {
  beforeEach(() => {
    process.env.EXPO_PUBLIC_API_BASE_URL = 'http://localhost:5000'
    fetchMock.mockReset()
    mockReplace.mockReset()
    globalThis.fetch = fetchMock
  })

  const renderScreen = async () => render(
    <AuthProvider>
      <LoginScreen />
    </AuthProvider>,
  )

  it('shows the ENNOVA sign-in form without unrelated navigation', async () => {
    const view = await renderScreen()

    expect(view.queryByText('ENNOVA')).toBeNull()
    expect(view.queryByText('YOUR MEMORIES. YOUR LEGACY.')).toBeNull()
    expect(view.getByText('Welcome Back')).toBeTruthy()
    expect(view.getByLabelText('Username')).toBeTruthy()
    expect(view.getByLabelText('Password')).toBeTruthy()
    expect(view.getByRole('button', { name: 'Create account' })).toBeTruthy()
    expect(view.queryByText('Register with an invitation code')).toBeNull()
  })

  it('validates required fields without making a request', async () => {
    const view = await renderScreen()

    await fireEvent.press(view.getByRole('button', { name: 'Sign in' }))

    expect(view.getByText('Enter your username and password to continue.')).toBeTruthy()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('toggles password visibility', async () => {
    const view = await renderScreen()
    const password = view.getByLabelText('Password')

    expect(password.props.secureTextEntry).toBe(true)
    await fireEvent.press(view.getByRole('button', { name: 'Show password' }))
    expect(view.getByLabelText('Password').props.secureTextEntry).toBe(false)
    expect(view.getByRole('button', { name: 'Hide password' })).toBeTruthy()
  })

  it('uses the existing backend login and navigates to the tabs after success', async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({ access_token: 'test-token', token_type: 'Bearer' }),
    })
    const view = await renderScreen()
    await fireEvent.changeText(view.getByLabelText('Username'), ' sample_owner ')
    await fireEvent.changeText(view.getByLabelText('Password'), 'sample-password')
    await fireEvent.press(view.getByRole('button', { name: 'Sign in' }))

    await waitFor(() => expect(mockReplace).toHaveBeenCalledWith('/(tabs)'))
    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:5000/auth/login',
      expect.objectContaining({
        body: JSON.stringify({ username: 'sample_owner', password: 'sample-password' }),
      }),
    )
  })

  it('displays authentication errors from the existing API', async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 401,
      text: async () => JSON.stringify({ code: 'invalid_credentials' }),
    })
    const view = await renderScreen()
    await fireEvent.changeText(view.getByLabelText('Username'), 'sample_owner')
    await fireEvent.changeText(view.getByLabelText('Password'), 'wrong-password')
    await fireEvent.press(view.getByRole('button', { name: 'Sign in' }))

    expect(await view.findByText('The username or password is incorrect.')).toBeTruthy()
  })

  it('creates an owner account through the existing registration flow', async () => {
    fetchMock
      .mockResolvedValueOnce({
        ok: true,
        status: 201,
        text: async () => JSON.stringify({
          account_id: 'owner-id',
          username: 'new_owner',
          owner_id: 'owner-id',
          person_id: 'new_owner',
          role: 'owner',
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ access_token: 'test-token', token_type: 'Bearer' }),
      })
    const view = await renderScreen()
    await fireEvent.press(view.getByRole('button', { name: 'Create account' }))
    await fireEvent.changeText(view.getByLabelText('Email address'), ' owner@example.com ')
    await fireEvent.changeText(view.getByLabelText('Username'), 'new_owner')
    await fireEvent.changeText(view.getByLabelText('Password'), 'sample-password')
    await fireEvent.press(view.getByRole('button', { name: 'Create account now' }))

    await waitFor(() => expect(mockReplace).toHaveBeenCalledWith('/(tabs)'))
    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      'http://localhost:5000/auth/register-owner',
      expect.objectContaining({
        body: JSON.stringify({
          username: 'new_owner',
          email: 'owner@example.com',
          password: 'sample-password',
        }),
      }),
    )
  })
})
