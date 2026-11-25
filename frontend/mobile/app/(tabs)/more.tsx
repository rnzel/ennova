// Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)
// Paradigm: Functional (navigation UI)

import { Link } from 'expo-router'
import { Pressable, StyleSheet, Text, View } from 'react-native'
import { AppScreen } from '@/components/AppScreen'
import { Brand } from '@/components/Brand'
import { PageTitle } from '@/components/PageTitle'
import { PreviewNotice } from '@/components/PreviewNotice'
import { colors } from '@/constants/theme'

const destinations = [
  { title: 'Ask ENNOVA', detail: 'Preview the grounded Q&A experience.', href: '/assistant', marker: '✳' },
  { title: 'Settings', detail: 'Profile, privacy, and writing preferences.', href: '/settings', marker: '⚙' },
  { title: 'Beneficiary preview', detail: 'See the read-only sample beneficiary view.', href: '/beneficiary', marker: '↗' },
] as const

export default function MoreScreen() {
  return (
    <AppScreen>
      <Brand />
      <PageTitle
        eyebrow="MORE"
        title="Explore ENNOVA"
        description="Additional tools and settings for your private legacy vault."
      />
      <View style={styles.list}>
        {destinations.map((destination) => (
          <Link href={destination.href} asChild key={destination.title}>
            <Pressable
              accessibilityRole="link"
              accessibilityLabel={`${destination.title}: ${destination.detail}`}
              style={({ pressed }) => [styles.destination, pressed && styles.pressed]}
            >
              <View style={styles.marker}><Text style={styles.markerText}>{destination.marker}</Text></View>
              <View style={styles.copy}>
                <Text style={styles.title}>{destination.title}</Text>
                <Text style={styles.detail}>{destination.detail}</Text>
              </View>
              <Text style={styles.arrow}>›</Text>
            </Pressable>
          </Link>
        ))}
      </View>
      <PreviewNotice>
        This app uses mock data outside the connected API surfaces. Sign-in, entries, and policy submission are API-backed.
      </PreviewNotice>
    </AppScreen>
  )
}

const styles = StyleSheet.create({
  list: {
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 16,
    backgroundColor: colors.surface,
  },
  destination: {
    minHeight: 76,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingHorizontal: 13,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  marker: {
    width: 38,
    height: 38,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 12,
    backgroundColor: '#E8F7F6',
  },
  markerText: {
    color: colors.teal,
    fontSize: 17,
  },
  copy: {
    flex: 1,
    gap: 4,
  },
  title: {
    color: colors.navy,
    fontSize: 13,
    fontWeight: '700',
  },
  detail: {
    color: colors.muted,
    fontSize: 11,
  },
  arrow: {
    color: colors.teal,
    fontSize: 22,
  },
  pressed: {
    backgroundColor: '#F5FBFB',
  },
})
