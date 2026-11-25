// Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)
// Paradigm: Functional (auth session tests)

import { act, render } from '@testing-library/react-native'
import { Text, View } from 'react-native'
import { AuthProvider, useAuth } from './AuthProvider'

let authContext: ReturnType<typeof useAuth> | null = null

function AuthProbe() {
  const context = useAuth()
  const { accessToken, isLoading } = context
  authContext = context

  return (
    <View>
      <Text>{accessToken ? 'Authenticated' : 'Signed out'}</Text>
      <Text>{isLoading ? 'Loading' : 'Ready'}</Text>
    </View>
  )
}

describe('AuthProvider', () => {
  beforeEach(() => {
    process.env.EXPO_PUBLIC_API_BASE_URL = 'http://localhost:5000'
    authContext = null
    globalThis.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        access_token: 'memory-only-token',
        token_type: 'Bearer',
      }),
    })
  })

  it('keeps the session in memory and clears it on sign out', async () => {
    const view = await render(
      <AuthProvider>
        <AuthProbe />
      </AuthProvider>,
    )

    if (!authContext) throw new Error('Auth probe did not render')
    await act(async () => {
      await authContext?.login('sample-user', 'fictional-password')
    })
    expect(view.getByText('Authenticated')).toBeTruthy()
    expect(view.getByText('Ready')).toBeTruthy()

    await act(async () => {
      authContext?.logout()
    })
    expect(view.getByText('Signed out')).toBeTruthy()
  })
})
