import { AppScreen } from '@/components/AppScreen'
import { ChatConversation } from '@/components/ChatConversation'
import { useAuth } from '@/context/AuthProvider'

export default function AssistantScreen() {
  const { accountRole, accessToken, clearRejectedSession } = useAuth()
  return (
    <AppScreen scroll={false}>
      {accountRole ? (
        <ChatConversation
          key={`${accessToken}:${accountRole}`}
          role={accountRole}
          token={accessToken}
          clearRejectedSession={clearRejectedSession}
        />
      ) : (
        <ChatConversation
          role="owner"
          token={null}
          clearRejectedSession={clearRejectedSession}
        />
      )}
    </AppScreen>
  )
}
