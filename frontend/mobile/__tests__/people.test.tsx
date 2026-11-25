// Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)
// Paradigm: Scripting (beneficiary and invitation screen tests)

import { act, fireEvent, render, waitFor } from '@testing-library/react-native'
import PeopleScreen from '@/app/(tabs)/people'
import { AppDataProvider } from '@/context/AppDataProvider'
import { AuthProvider, useAuth } from '@/context/AuthProvider'

let authContext: ReturnType<typeof useAuth> | null = null
let requests: Array<{ path: string; method: string; body?: string }> = []
let invitationFailure: { status: number; payload: unknown } | null = null

function AuthCapture() {
  authContext = useAuth()
  return null
}

function response(payload: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    text: async () => JSON.stringify(payload),
  } as Response
}

function TestApp() {
  return (
    <AuthProvider>
      <AppDataProvider>
        <AuthCapture />
        <PeopleScreen />
      </AppDataProvider>
    </AuthProvider>
  )
}

describe('PeopleScreen', () => {
  beforeEach(() => {
    process.env.EXPO_PUBLIC_API_BASE_URL = 'http://localhost:5000'
    authContext = null
    requests = []
    invitationFailure = null
    globalThis.fetch = jest.fn().mockImplementation(async (url: string, options?: RequestInit) => {
      const path = new URL(url).pathname
      const method = options?.method ?? 'GET'
      const body = typeof options?.body === 'string' ? options.body : undefined
      requests.push({ path, method, body })

      if (path === '/auth/login') {
        return response({ access_token: 'fictional-token', token_type: 'Bearer' })
      }
      if (path === '/entries') return response({ entries: [] })
      if (path === '/invitations' && invitationFailure) {
        return response(invitationFailure.payload, invitationFailure.status)
      }
      if (path === '/invitations') {
        return response({
          invitation_code: 'FICTIONAL-INVITE',
          person_id: 'sample_person',
          expires_at: '2040-01-01T00:00:00Z',
        }, 201)
      }
      throw new Error('Unexpected mocked request')
    })
  })

  it('adds fictional beneficiary details to the local preview', async () => {
    const view = await render(<TestApp />)

    await fireEvent.press(view.getByRole('button', { name: 'Add beneficiary' }))
    await fireEvent.changeText(view.getByLabelText('Full name'), 'Sample Person')
    await fireEvent.changeText(view.getByLabelText('Email'), 'person@example.com')
    await fireEvent.changeText(view.getByLabelText('Relationship'), 'Friend')
    await fireEvent.press(view.getByRole('button', { name: 'Add beneficiary to preview' }))

    expect(view.getByText('Added to this preview session only.')).toBeTruthy()
    expect(view.getByText('Sample Person')).toBeTruthy()
    expect(requests).toHaveLength(0)
  })

  it('issues an invitation and shows the returned code', async () => {
    const view = await render(<TestApp />)
    await act(async () => {
      if (!authContext) throw new Error('Auth context was not captured')
      await authContext.login('fictional-owner', 'fictional-password')
    })

    await fireEvent.press(view.getByRole('button', { name: 'Add beneficiary' }))
    await fireEvent.changeText(view.getByLabelText('Full name'), 'Sample Person')
    await fireEvent.changeText(view.getByLabelText('Email'), 'person@example.com')
    await fireEvent.changeText(view.getByLabelText('Relationship'), 'Friend')
    await fireEvent.changeText(view.getByLabelText('Person identifier'), 'Sample_Person')
    await fireEvent.changeText(view.getByLabelText('Invitation expiry'), '2040-01-01T00:00:00Z')
    await fireEvent.press(view.getByRole('button', { name: 'Issue invitation' }))

    await waitFor(() => expect(view.getByText('FICTIONAL-INVITE')).toBeTruthy())
    expect(view.getByText(/Invitation issued for sample_person/)).toBeTruthy()
    expect(requests.find((request) => request.path === '/invitations')).toMatchObject({
      method: 'POST',
      body: JSON.stringify({
        person_id: 'sample_person',
        expires_at: '2040-01-01T00:00:00Z',
      }),
    })
  })

  it('shows the safe API message when invitation issuance fails', async () => {
    invitationFailure = {
      status: 409,
      payload: {
        code: 'conflict',
        message: 'Private backend detail for person@example.com',
      },
    }
    const view = await render(<TestApp />)
    await act(async () => {
      if (!authContext) throw new Error('Auth context was not captured')
      await authContext.login('fictional-owner', 'fictional-password')
    })

    await fireEvent.press(view.getByRole('button', { name: 'Add beneficiary' }))
    await fireEvent.changeText(view.getByLabelText('Full name'), 'Sample Person')
    await fireEvent.changeText(view.getByLabelText('Email'), 'person@example.com')
    await fireEvent.changeText(view.getByLabelText('Relationship'), 'Friend')
    await fireEvent.changeText(view.getByLabelText('Person identifier'), 'sample_person')
    await fireEvent.changeText(view.getByLabelText('Invitation expiry'), '2040-01-01T00:00:00Z')
    await fireEvent.press(view.getByRole('button', { name: 'Issue invitation' }))

    expect(await view.findByText('The requested resource already exists.')).toBeTruthy()
    expect(view.queryByText(/Private backend detail|person@example\.com/)).toBeNull()
  })
})
