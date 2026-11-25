// Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)
// Paradigm: n/a (interface navigation)

import { SymbolView } from 'expo-symbols'
import { Tabs } from 'expo-router'
import { colors } from '@/constants/theme'

const iconNames = {
  home: { ios: 'house.fill', android: 'home', web: 'home' },
  journal: { ios: 'book.closed.fill', android: 'menu_book', web: 'menu_book' },
  people: { ios: 'person.2.fill', android: 'people', web: 'people' },
  policy: { ios: 'lock.shield.fill', android: 'policy', web: 'policy' },
  more: { ios: 'ellipsis', android: 'more_horiz', web: 'more_horiz' },
} as const

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.teal,
        tabBarInactiveTintColor: colors.muted,
        tabBarLabelStyle: { fontSize: 10, fontWeight: '600' },
        tabBarStyle: {
          minHeight: 63,
          paddingTop: 6,
          paddingBottom: 7,
          borderTopColor: colors.border,
          backgroundColor: colors.surface,
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          tabBarIcon: ({ color }) => <SymbolView name={iconNames.home} tintColor={color} size={22} />,
        }}
      />
      <Tabs.Screen
        name="journal"
        options={{
          title: 'Journal',
          tabBarIcon: ({ color }) => <SymbolView name={iconNames.journal} tintColor={color} size={22} />,
        }}
      />
      <Tabs.Screen
        name="people"
        options={{
          title: 'People',
          tabBarIcon: ({ color }) => <SymbolView name={iconNames.people} tintColor={color} size={22} />,
        }}
      />
      <Tabs.Screen
        name="policy"
        options={{
          title: 'Policy',
          tabBarIcon: ({ color }) => <SymbolView name={iconNames.policy} tintColor={color} size={22} />,
        }}
      />
      <Tabs.Screen
        name="more"
        options={{
          title: 'More',
          tabBarIcon: ({ color }) => <SymbolView name={iconNames.more} tintColor={color} size={22} />,
        }}
      />
    </Tabs>
  )
}
