'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { Loader2, User, Bell, Shield, Save } from 'lucide-react';
import { motion } from 'framer-motion';

export default function SettingsPage() {
  const { data: session } = useSession();
  const [name, setName] = useState(session?.user?.name ?? '');

  return (
    <div style={{ padding: '2rem', maxWidth: 700, margin: '0 auto' }}>
      <div style={{ marginBottom: '2.5rem' }}>
        <div className="sys-label" style={{ marginBottom: '0.25rem' }}>SYSTEM CONFIG</div>
        <h1 style={{ fontFamily: 'Space Grotesk', fontSize: '2rem', fontWeight: 700, color: '#f0ece4', lineHeight: 1 }}>SETTINGS</h1>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {/* Profile */}
        <div style={{ background: 'rgba(10,10,10,0.9)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 6, padding: '1.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
            <User size={16} color="#8a8a8a" />
            <div className="sys-label">PROFILE</div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label className="label">OPERATOR NAME</label>
              <input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name" />
            </div>
            <div>
              <label className="label">EMAIL</label>
              <input className="input" value={session?.user?.email ?? ''} disabled style={{ opacity: 0.5 }} />
              <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', marginTop: '0.25rem' }}>Email cannot be changed.</div>
            </div>
          </div>
        </div>

        {/* Data */}
        <div style={{ background: 'rgba(10,10,10,0.9)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 6, padding: '1.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
            <Shield size={16} color="#8a8a8a" />
            <div className="sys-label">DATA & PRIVACY</div>
          </div>
          <div style={{ fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#8a8a8a', lineHeight: 1.8 }}>
            <p>All your data is stored locally in an SQLite database on this server.</p>
            <p style={{ marginTop: '0.5rem' }}>Your progress is persistent across sessions and devices.</p>
          </div>
        </div>

        {/* About */}
        <div style={{ background: 'rgba(10,10,10,0.9)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 6, padding: '1.75rem' }}>
          <div className="sys-label" style={{ marginBottom: '1rem' }}>ABOUT</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {[
              ['SYSTEM', 'LIFE//OS'],
              ['VERSION', '1.0.0'],
              ['ENGINE', 'Next.js 16 · Auth.js v5 · Prisma 5 · SQLite'],
              ['PHILOSOPHY', 'Your real life already has XP.'],
            ].map(([k, v]) => (
              <div key={k} style={{ display: 'flex', gap: '2rem' }}>
                <span style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#4a4a4a', letterSpacing: '0.12em', width: 80, flexShrink: 0 }}>{k}</span>
                <span style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#8a8a8a' }}>{v}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
