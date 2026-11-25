// Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)
// Paradigm: n/a (interface)

import { Link, Stack } from 'expo-router';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { colors, minimumTouchTarget } from '@/constants/theme';

export default function NotFoundScreen() {
  return (
    <>
      <Stack.Screen options={{ title: 'Oops!' }} />
      <ScrollView contentContainerStyle={styles.container}>
        <View>
          <Text style={styles.title}>This screen doesn&apos;t exist.</Text>

          <Link
            href="/"
            accessibilityRole="link"
            accessibilityLabel="Go to sign in"
            style={styles.link}
          >
            <Text style={styles.linkText}>Go to sign in</Text>
          </Link>
        </View>
      </ScrollView>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  link: {
    minHeight: minimumTouchTarget,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 15,
  },
  linkText: {
    fontSize: 14,
    color: colors.teal,
  },
});
