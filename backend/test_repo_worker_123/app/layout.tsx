import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'LIFE//OS — Turn Your Life Into an RPG',
  description:
    'Turn real-world actions into quests, earn XP, build your character, unlock traits, and evolve. Your real life already has XP.',
  keywords: ['life rpg', 'gamification', 'productivity', 'quests', 'character', 'xp', 'progression'],
  openGraph: {
    title: 'LIFE//OS — Turn Your Life Into an RPG',
    description: 'Your real life already has XP. You just can\'t see it.',
    type: 'website',
  },
};

import { Providers } from '@/components/Providers';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
