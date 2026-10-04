'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { signOut } from 'next-auth/react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard, Target, User, Map, Sword, Package,
  ShoppingBag, TrendingUp, Clock, Settings, LogOut, Menu, X, ChevronRight, Zap,
} from 'lucide-react';

const navItems = [
  { label: 'DASHBOARD', href: '/dashboard', icon: LayoutDashboard },
  { label: 'QUESTS', href: '/quests', icon: Target },
  { label: 'CHARACTER', href: '/character', icon: User },
  { label: 'CAMPAIGNS', href: '/campaigns', icon: Map },
  { label: 'BOSSES', href: '/bosses', icon: Sword },
  { label: 'INVENTORY', href: '/inventory', icon: Package },
  { label: 'SHOP', href: '/shop', icon: ShoppingBag },
  { label: 'EVOLUTION', href: '/evolution', icon: TrendingUp },
  { label: 'HISTORY', href: '/history', icon: Clock },
];

export function AppSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleSignOut = async () => {
    await signOut({ redirect: false });
    router.push('/');
  };

  const renderSidebarContent = () => (
    <div style={{
      display: 'flex', flexDirection: 'column',
      height: '100%', padding: '1.5rem 0',
    }}>
      {/* Logo */}
      <div style={{ padding: '0 1.5rem', marginBottom: '2.5rem' }}>
        <Link href="/dashboard" style={{ textDecoration: 'none' }}>
          <span style={{ fontFamily: 'Space Mono', fontSize: '0.9rem', fontWeight: 700, color: '#f0ece4', letterSpacing: '0.05em' }}>
            LIFE<span style={{ color: '#c8ff00' }}>{'//'}</span>OS
          </span>
        </Link>
        <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', marginTop: '0.2rem', letterSpacing: '0.15em' }}>
          PERSONAL OPERATING SYSTEM
        </div>
      </div>

      {/* Nav Items */}
      <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.125rem', padding: '0 0.75rem' }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href || pathname.startsWith(item.href + '/');

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMobileOpen(false)}
              style={{ textDecoration: 'none' }}
            >
              <div style={{
                display: 'flex', alignItems: 'center', gap: '0.75rem',
                padding: '0.6rem 0.875rem',
                borderRadius: 4,
                background: active ? 'rgba(200,255,0,0.08)' : 'transparent',
                border: `1px solid ${active ? 'rgba(200,255,0,0.15)' : 'transparent'}`,
                transition: 'all 0.15s',
                cursor: 'pointer',
              }}
              onMouseEnter={(e) => {
                if (!active) {
                  (e.currentTarget as HTMLDivElement).style.background = 'rgba(255,255,255,0.04)';
                }
              }}
              onMouseLeave={(e) => {
                if (!active) {
                  (e.currentTarget as HTMLDivElement).style.background = 'transparent';
                }
              }}
              >
                <Icon
                  size={14}
                  color={active ? '#c8ff00' : '#4a4a4a'}
                  strokeWidth={active ? 2 : 1.5}
                />
                <span style={{
                  fontFamily: 'Space Mono', fontSize: '0.65rem', letterSpacing: '0.08em',
                  color: active ? '#f0ece4' : '#8a8a8a',
                  fontWeight: active ? 700 : 400,
                }}>
                  {item.label}
                </span>
                {active && (
                  <ChevronRight size={10} color="#c8ff00" style={{ marginLeft: 'auto' }} />
                )}
              </div>
            </Link>
          );
        })}
      </nav>

      {/* Bottom */}
      <div style={{ padding: '0 0.75rem', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '1rem', marginTop: '1rem' }}>
        <Link href="/settings" onClick={() => setMobileOpen(false)} style={{ textDecoration: 'none', display: 'block', marginBottom: '0.125rem' }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '0.75rem',
            padding: '0.6rem 0.875rem', borderRadius: 4, cursor: 'pointer',
            transition: 'all 0.15s',
          }}
          onMouseEnter={(e) => { (e.currentTarget as HTMLDivElement).style.background = 'rgba(255,255,255,0.04)'; }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLDivElement).style.background = 'transparent'; }}
          >
            <Settings size={14} color="#4a4a4a" />
            <span style={{ fontFamily: 'Space Mono', fontSize: '0.65rem', letterSpacing: '0.08em', color: '#8a8a8a' }}>SETTINGS</span>
          </div>
        </Link>

        <button
          onClick={handleSignOut}
          style={{
            display: 'flex', alignItems: 'center', gap: '0.75rem', width: '100%',
            padding: '0.6rem 0.875rem', borderRadius: 4, cursor: 'pointer',
            background: 'transparent', border: 'none', transition: 'all 0.15s',
          }}
          onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.background = 'rgba(255,92,92,0.06)'; }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.background = 'transparent'; }}
        >
          <LogOut size={14} color="#4a4a4a" />
          <span style={{ fontFamily: 'Space Mono', fontSize: '0.65rem', letterSpacing: '0.08em', color: '#8a8a8a' }}>LOGOUT</span>
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <aside style={{
        width: 220, flexShrink: 0, height: '100vh', position: 'sticky', top: 0,
        background: '#0a0a0a', borderRight: '1px solid rgba(255,255,255,0.05)',
        display: 'flex', flexDirection: 'column',
      }}>
        {renderSidebarContent()}
      </aside>

      {/* Mobile Toggle */}
      <button
        onClick={() => setMobileOpen(true)}
        aria-label="Open navigation"
        style={{
          display: 'none', position: 'fixed', bottom: '1.5rem', right: '1.5rem',
          zIndex: 500, width: 48, height: 48, borderRadius: '50%',
          background: '#c8ff00', border: 'none', cursor: 'pointer',
          alignItems: 'center', justifyContent: 'center',
        }}
        className="mobile-menu-btn"
      >
        <Menu size={20} color="#080808" />
      </button>

      {/* Mobile Drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileOpen(false)}
              style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', zIndex: 499, backdropFilter: 'blur(4px)' }}
            />
            <motion.aside
              initial={{ x: -240 }}
              animate={{ x: 0 }}
              exit={{ x: -240 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              style={{
                position: 'fixed', top: 0, left: 0, bottom: 0, width: 240,
                background: '#0a0a0a', borderRight: '1px solid rgba(255,255,255,0.08)',
                zIndex: 500, overflowY: 'auto',
              }}
            >
              <button
                onClick={() => setMobileOpen(false)}
                style={{
                  position: 'absolute', top: '1rem', right: '1rem',
                  background: 'none', border: 'none', cursor: 'pointer', color: '#8a8a8a',
                }}
                aria-label="Close navigation"
              >
                <X size={18} />
              </button>
              {renderSidebarContent()}
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      <style>{`
        @media (max-width: 768px) {
          .mobile-menu-btn { display: flex !important; }
        }
      `}</style>
    </>
  );
}
