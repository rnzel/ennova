import { fireEvent, render } from '@testing-library/react-native'
import { router } from 'expo-router'
import NewEntryScreen from '@/app/entries/new'
import { AppDataProvider } from '@/context/AppDataProvider'
import { AuthProvider } from '@/context/AuthProvider'

jest.mock('expo-router', () => ({
  router: {
    back: jest.fn(),
    replace: jest.fn(),
  },
}))

describe('NewEntryScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('requires a recipient and release date for a Letter of Wishes', async () => {
    const view = await render(
      <AuthProvider>
        <AppDataProvider>
          <NewEntryScreen />
        </AppDataProvider>
      </AuthProvider>,
    )

    expect(view.getByText(/not a legal will/i)).toBeTruthy()
    await fireEvent.press(view.getByRole('button', { name: 'Letter of Wishes' }))
    await fireEvent.changeText(view.getByLabelText('Entry title'), 'Fictional wishes')
    await fireEvent.changeText(view.getByLabelText('Entry content'), 'Fictional test content')
    await fireEvent.press(view.getByRole('button', { name: 'Save entry' }))

    expect(view.getByText('Letters require a recipient and release date.')).toBeTruthy()
    expect(router.replace).not.toHaveBeenCalled()

    await fireEvent.changeText(view.getByLabelText('Letter recipient'), 'sample_person')
    await fireEvent.changeText(view.getByLabelText('Letter release date'), '2040-05-01')
    await fireEvent.press(view.getByRole('button', { name: 'Save entry' }))

    expect(router.replace).toHaveBeenCalledWith('/(tabs)/journal')
  })
})
