import { Stack } from 'expo-router'
import { StatusBar } from 'expo-status-bar'
import { AppDataProvider } from '@/context/AppDataProvider'
import { colors } from '@/constants/theme'
import { AuthProvider } from '@/context/AuthProvider'

export default function RootLayout() {
  return (
    <AuthProvider>
      <AppDataProvider>
        <StatusBar style="dark" />
        <Stack
          screenOptions={{
            headerShown: false,
            contentStyle: { backgroundColor: colors.canvas },
          }}
        >
          <Stack.Screen name="index" />
          <Stack.Screen name="login" />
          <Stack.Screen name="(tabs)" />
          <Stack.Screen name="entries/new" options={{ presentation: 'modal' }} />
          <Stack.Screen name="entries/[id]" />
          <Stack.Screen name="assistant" />
          <Stack.Screen name="settings" />
          <Stack.Screen name="beneficiary" />
        </Stack>
      </AppDataProvider>
    </AuthProvider>
  )
}
