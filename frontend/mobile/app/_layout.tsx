// Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)
// Paradigm: n/a (interface navigation)

import { Stack } from 'expo-router'
import { View } from 'react-native'
import { StatusBar } from 'expo-status-bar'
import { AppDataProvider } from '@/context/AppDataProvider'
import { colors } from '@/constants/theme'
import { AuthProvider } from '@/context/AuthProvider'
import { PolicyPublishManager } from '@/components/PolicyPublishManager'
import { FloatingChatWidget } from '@/components/FloatingChatWidget'

export default function RootLayout() {
  return (
    <AuthProvider>
      <AppDataProvider>
        <StatusBar style="dark" />
        <View style={{ flex: 1 }}>
          <PolicyPublishManager />
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
          <FloatingChatWidget />
        </View>
      </AppDataProvider>
    </AuthProvider>
  )
}
