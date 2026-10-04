'use client';

import { useState } from 'react';
import { signIn } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { ARCHETYPES } from '@/lib/constants';

const archetypes = [
  { id: 'THE_BUILDER', name: 'THE BUILDER', icon: '🔨', desc: 'You create systems, products, and solutions.', color: '#c8ff00' },
  { id: 'THE_SCHOLAR', name: 'THE SCHOLAR', icon: '📚', desc: 'Knowledge is your greatest power.', color: '#7b8cff' },
  { id: 'THE_ATHLETE', name: 'THE ATHLETE', icon: '⚡', desc: 'Physical mastery drives you forward.', color: '#ff5c5c' },
  { id: 'THE_CREATOR', name: 'THE CREATOR', icon: '🎨', desc: "You make things that didn't exist before.", color: '#ff9500' },
  { id: 'THE_EXPLORER', name: 'THE EXPLORER', icon: '🧭', desc: 'New experiences, connections, perspectives.', color: '#00e5a0' },
];

export default function SignupPage() {
  const router = useRouter();
  const [step, setStep] = useState<'form' | 'archetype'>('form');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [selectedArchetype, setSelectedArchetype] = useState('THE_BUILDER');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) { setError('What do we call you?'); return; }
    if (!email.includes('@')) { setError('Valid email required.'); return; }
    if (password.length < 6) { setError('Password must be at least 6 characters.'); return; }
    setError('');
    setStep('archetype');
  };

  const handleSignup = async () => {
    setLoading(true);
    setError('');

    try {
      const res = await fetch('/api/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password, archetype: selectedArchetype }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.error ?? 'Failed to create account.');
        setStep('form');
        return;
      }

      // Auto-login
      const loginResult = await signIn('credentials', {
        email,
        password,
        redirect: false,
      });

      if (loginResult?.ok) {
        router.push('/dashboard');
      } else {
        router.push('/login');
      }
    } catch {
      setError('Connection lost. Please try again.');
      setStep('form');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', padding: '2rem',
      background: '#080808',
    }}>
      <div style={{
        position: 'fixed', inset: 0,
        backgroundImage: 'linear-gradient(rgba(200,255,0,0.015) 1px, transparent 1px), linear-gradient(90deg, rgba(200,255,0,0.015) 1px, transparent 1px)',
        backgroundSize: '60px 60px', pointerEvents: 'none', zIndex: 0,
      }} />

      <div style={{ width: '100%', maxWidth: step === 'archetype' ? 640 : 400, position: 'relative', zIndex: 1 }}>
        <Link href="/" style={{ textDecoration: 'none', display: 'block', textAlign: 'center', marginBottom: '3rem' }}>
          <span style={{ fontFamily: 'Space Mono', fontSize: '1.1rem', fontWeight: 700, color: '#f0ece4' }}>
            LIFE<span style={{ color: '#c8ff00' }}>{'//'}</span>OS
          </span>
        </Link>

        <AnimatePresence mode="wait">
          {step === 'form' ? (
            <motion.div
              key="form"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4 }}
            >
              <div style={{
                background: 'rgba(14,14,14,0.9)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: 6, padding: '2rem',
              }}>
                <div style={{ marginBottom: '2rem' }}>
                  <div className="sys-label" style={{ marginBottom: '0.5rem' }}>CREATE ACCOUNT</div>
                  <h1 style={{ fontFamily: 'Space Grotesk', fontSize: '1.5rem', fontWeight: 700, color: '#f0ece4' }}>
                    Your journey starts here.
                  </h1>
                </div>

                <form onSubmit={handleFormSubmit} noValidate>
                  <div style={{ marginBottom: '1rem' }}>
                    <label className="label" htmlFor="name">OPERATOR NAME</label>
                    <input id="name" type="text" className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name" autoComplete="name" required />
                  </div>
                  <div style={{ marginBottom: '1rem' }}>
                    <label className="label" htmlFor="email">EMAIL</label>
                    <input id="email" type="email" className="input" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="operator@life.os" autoComplete="email" required />
                  </div>
                  <div style={{ marginBottom: '1.5rem' }}>
                    <label className="label" htmlFor="password">PASSWORD</label>
                    <input id="password" type="password" className="input" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Min. 6 characters" autoComplete="new-password" required />
                  </div>

                  {error && (
                    <div style={{ marginBottom: '1rem', padding: '0.75rem', background: 'rgba(255,92,92,0.08)', border: '1px solid rgba(255,92,92,0.2)', borderRadius: 4, fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#ff5c5c' }}>
                      {error}
                    </div>
                  )}

                  <button type="submit" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', marginBottom: '1.5rem' }}>
                    CHOOSE YOUR ARCHETYPE →
                  </button>

                  <p style={{ textAlign: 'center', fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#4a4a4a' }}>
                    HAVE AN ACCOUNT?{' '}
                    <Link href="/login" style={{ color: '#c8ff00', textDecoration: 'none' }}>SIGN IN</Link>
                  </p>
                </form>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="archetype"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4 }}
            >
              <div style={{
                background: 'rgba(14,14,14,0.9)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: 6, padding: '2rem',
              }}>
                <div style={{ marginBottom: '2rem' }}>
                  <div className="sys-label" style={{ marginBottom: '0.5rem' }}>ARCHETYPE SELECTION</div>
                  <h2 style={{ fontFamily: 'Space Grotesk', fontSize: '1.5rem', fontWeight: 700, color: '#f0ece4' }}>
                    Who are you?
                  </h2>
                  <p style={{ fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#8a8a8a', marginTop: '0.5rem' }}>
                    Your archetype shapes your starting attributes. It doesn&apos;t limit your future.
                  </p>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '2rem' }}>
                  {archetypes.map((arch) => (
                    <motion.button
                      key={arch.id}
                      onClick={() => setSelectedArchetype(arch.id)}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      style={{
                        padding: '1.25rem',
                        background: selectedArchetype === arch.id ? `${arch.color}10` : 'rgba(20,20,20,0.8)',
                        border: `1px solid ${selectedArchetype === arch.id ? arch.color : 'rgba(255,255,255,0.06)'}`,
                        borderRadius: 4, cursor: 'pointer', textAlign: 'left',
                        transition: 'all 0.2s',
                        gridColumn: arch.id === 'THE_EXPLORER' ? 'span 2' : 'span 1',
                      }}
                    >
                      <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>{arch.icon}</div>
                      <div style={{ fontFamily: 'Space Mono', fontSize: '0.65rem', color: selectedArchetype === arch.id ? arch.color : '#f0ece4', letterSpacing: '0.08em', marginBottom: '0.3rem' }}>
                        {arch.name}
                      </div>
                      <div style={{ fontFamily: 'Space Grotesk', fontSize: '0.75rem', color: '#8a8a8a' }}>
                        {arch.desc}
                      </div>
                    </motion.button>
                  ))}
                </div>

                {error && (
                  <div style={{ marginBottom: '1rem', padding: '0.75rem', background: 'rgba(255,92,92,0.08)', border: '1px solid rgba(255,92,92,0.2)', borderRadius: 4, fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#ff5c5c' }}>
                    {error}
                  </div>
                )}

                <div style={{ display: 'flex', gap: '0.75rem' }}>
                  <button onClick={() => setStep('form')} className="btn btn-secondary" style={{ flex: 1, justifyContent: 'center' }}>
                    ← BACK
                  </button>
                  <button onClick={handleSignup} className="btn btn-primary" disabled={loading} style={{ flex: 2, justifyContent: 'center' }}>
                    {loading ? (
                      <><Loader2 size={14} className="animate-spin" /> CREATING CHARACTER...</>
                    ) : (
                      'BEGIN AS ' + (archetypes.find((a) => a.id === selectedArchetype)?.name ?? 'THE BUILDER') + ' →'
                    )}
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
