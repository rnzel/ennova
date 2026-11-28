import { useEffect, useState } from 'react'
import {
  Animated,
  Easing,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
} from 'react-native'
import { SymbolView } from 'expo-symbols'
import { useSafeAreaInsets } from 'react-native-safe-area-context'
import { ChatConversation } from '@/components/ChatConversation'
import { colors, minimumTouchTarget, spacing } from '@/constants/theme'
import { useAuth } from '@/context/AuthProvider'

export function FloatingChatWidget() {
  const { accountRole, accessToken, clearRejectedSession } = useAuth()
  const [isOpen, setIsOpen] = useState(false)
  const { width, height } = useWindowDimensions()
  const insets = useSafeAreaInsets()
  const [progress] = useState(() => new Animated.Value(0))
  const isSmallScreen = width < 680

  useEffect(() => {
    Animated.timing(progress, {
      toValue: isOpen ? 1 : 0,
      duration: isOpen ? 220 : 170,
      easing: isOpen ? Easing.out(Easing.cubic) : Easing.in(Easing.cubic),
      useNativeDriver: true,
    }).start()
  }, [isOpen, progress])

  if (!accessToken || !accountRole) return null

  const panelStyle = isSmallScreen
    ? {
        top: Math.max(insets.top, 8),
        bottom: Math.max(insets.bottom, 8),
        left: 8,
        right: 8,
      }
    : {
        right: 20,
        bottom: insets.bottom + 82,
        width: 390,
        height: Math.min(650, height - insets.top - insets.bottom - 120),
      }

  return (
    <View pointerEvents="box-none" style={StyleSheet.absoluteFill}>
      <Animated.View
        accessibilityElementsHidden={!isOpen}
        importantForAccessibility={isOpen ? 'auto' : 'no-hide-descendants'}
        pointerEvents={isOpen ? 'auto' : 'none'}
        style={[
          styles.panel,
          panelStyle,
          {
            opacity: progress,
            transform: [{ scale: progress.interpolate({ inputRange: [0, 1], outputRange: [0.97, 1] }) }],
          },
        ]}
      >
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          style={styles.keyboard}
        >
          <View style={styles.panelTop}>
            <View style={styles.brandMark}><Text style={styles.brandLetter}>E</Text></View>
            <View style={styles.panelHeading}>
              <Text style={styles.panelTitle}>ENNOVA assistant</Text>
              <Text style={styles.panelSubtitle}>
                {accountRole === 'owner' ? 'Your private diary' : 'Policy checked for every question'}
              </Text>
            </View>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Minimize chat"
              onPress={() => setIsOpen(false)}
              style={styles.control}
            >
              <Text style={styles.controlGlyph}>−</Text>
            </Pressable>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Close chat"
              onPress={() => setIsOpen(false)}
              style={styles.control}
            >
              <Text style={styles.controlGlyph}>×</Text>
            </Pressable>
          </View>
          <ChatConversation
            key={`${accessToken}:${accountRole}`}
            compact
            role={accountRole}
            token={accessToken}
            clearRejectedSession={clearRejectedSession}
          />
        </KeyboardAvoidingView>
      </Animated.View>

      {!isOpen ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Open ENNOVA chat"
          accessibilityHint="Opens the floating diary assistant"
          onPress={() => setIsOpen(true)}
          style={[styles.launcher, { right: spacing.md, bottom: insets.bottom + 78 }]}
        >
          <SymbolView
            name={{ ios: 'bubble.left.and.bubble.right.fill', android: 'chat', web: 'chat' }}
            tintColor={colors.surface}
            size={25}
          />
        </Pressable>
      ) : null}
    </View>
  )
}

const styles = StyleSheet.create({
  panel: {
    position: 'absolute',
    zIndex: 20,
    overflow: 'hidden',
    borderRadius: 22,
    backgroundColor: colors.canvas,
    borderWidth: 1,
    borderColor: colors.border,
    shadowColor: colors.navy,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.18,
    shadowRadius: 22,
    elevation: 16,
  },
  keyboard: { flex: 1, minHeight: 0 },
  panelTop: {
    minHeight: 66,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingHorizontal: spacing.md,
    backgroundColor: colors.navy,
  },
  brandMark: {
    width: 36,
    height: 36,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 12,
    backgroundColor: 'rgba(255,255,255,0.12)',
  },
  brandLetter: { color: colors.cyan, fontSize: 17, fontWeight: '800' },
  panelHeading: { flex: 1, gap: 2 },
  panelTitle: { color: colors.surface, fontSize: 14, fontWeight: '800' },
  panelSubtitle: { color: '#C6E5E8', fontSize: 10 },
  control: {
    width: minimumTouchTarget,
    height: minimumTouchTarget,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 12,
  },
  controlGlyph: { color: colors.surface, fontSize: 24, lineHeight: 28 },
  launcher: {
    position: 'absolute',
    zIndex: 21,
    width: 58,
    height: 58,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 29,
    backgroundColor: colors.teal,
    borderWidth: 3,
    borderColor: colors.surface,
    shadowColor: colors.navy,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 9,
  },
})
