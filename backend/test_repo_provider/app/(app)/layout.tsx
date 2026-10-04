import { auth } from '@/lib/auth';
import { redirect } from 'next/navigation';
import { AppSidebar } from '@/components/AppSidebar';
import { SessionProvider } from 'next-auth/react';

export default async function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth();
  if (!session?.user) redirect('/login');

  return (
    <SessionProvider session={session}>
      <div style={{ display: 'flex', minHeight: '100vh' }}>
        <AppSidebar />
        <main style={{
          flex: 1, overflow: 'auto',
          background: '#080808',
        }}>
          {children}
        </main>
      </div>
    </SessionProvider>
  );
}
