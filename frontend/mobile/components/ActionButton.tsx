import {
  Pressable,
  StyleSheet,
  Text,
  type PressableProps,
  type StyleProp,
  type ViewStyle,
} from 'react-native'
import { colors } from '@/constants/theme'

type ActionButtonProps = Omit<PressableProps, 'style'> & {
  label: string
  variant?: 'primary' | 'secondary'
  style?: StyleProp<ViewStyle>
}

export function ActionButton({
  label,
  variant = 'primary',
  style,
  disabled,
  ...props
}: ActionButtonProps) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled }}
      disabled={disabled}
      style={({ pressed }) => [
        styles.button,
        variant === 'primary' ? styles.primary : styles.secondary,
        pressed && styles.pressed,
        style,
      ]}
      {...props}
    >
      <Text style={[styles.label, variant === 'secondary' && styles.secondaryLabel]}>
        {label}
      </Text>
    </Pressable>
  )
}

const styles = StyleSheet.create({
  button: {
    minHeight: 48,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 16,
    borderWidth: 1,
    borderRadius: 13,
  },
  primary: {
    borderColor: colors.cyan,
    backgroundColor: colors.cyan,
  },
  secondary: {
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  label: {
    color: colors.navy,
    fontSize: 14,
    fontWeight: '700',
  },
  secondaryLabel: {
    color: colors.navy,
  },
  pressed: {
    opacity: 0.8,
  },
})
