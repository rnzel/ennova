import { fireEvent, render } from '@testing-library/react-native'
import type { ReactNode } from 'react'
import JournalScreen from '@/app/(tabs)/journal'
import { AppDataProvider } from '@/context/AppDataProvider'
import { AuthProvider } from '@/context/AuthProvider'

jest.mock('expo-router', () => ({
  Link: ({ children }: { children: ReactNode }) => children,
}))

describe('JournalScreen', () => {
  it('searches and filters the mock journal entries', async () => {
    const view = await render(
      <AuthProvider>
        <AppDataProvider>
          <JournalScreen />
        </AppDataProvider>
      </AuthProvider>,
    )

    await fireEvent.changeText(view.getByLabelText('Search entries'), 'garden')
    expect(view.getByText('The garden after the rain')).toBeTruthy()
    expect(view.queryByText('Sunday lunch traditions')).toBeNull()

    await fireEvent.changeText(view.getByLabelText('Search entries'), '')
    await fireEvent.press(view.getByRole('button', { name: 'Shared' }))
    expect(view.getByText('Sunday lunch traditions')).toBeTruthy()
    expect(view.queryByText('The garden after the rain')).toBeNull()
  })
})
