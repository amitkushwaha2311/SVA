'use client';

import { useState, Suspense } from 'react';
import { signIn } from 'next-auth/react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Eye, EyeOff, Loader2 } from 'lucide-react';

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get('callbackUrl') ?? '/dashboard';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const result = await signIn('credentials', {
        email,
        password,
        redirect: false,
      });

      if (result?.error) {
        setError('Invalid email or password.');
      } else {
        router.push(decodeURIComponent(callbackUrl));
        router.refresh();
      }
    } catch {
      setError('Connection lost. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} noValidate>
      <div style={{ marginBottom: '1rem' }}>
        <label className="label" htmlFor="email">EMAIL</label>
        <input
          id="email"
          type="email"
          className="input"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="operator@life.os"
          autoComplete="email"
          required
        />
      </div>

      <div style={{ marginBottom: '1.5rem' }}>
        <label className="label" htmlFor="password">PASSWORD</label>
        <div style={{ position: 'relative' }}>
          <input
            id="password"
            type={showPw ? 'text' : 'password'}
            className="input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            autoComplete="current-password"
            required
            style={{ paddingRight: '2.5rem' }}
          />
          <button
            type="button"
            onClick={() => setShowPw(!showPw)}
            style={{
              position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)',
              background: 'none', border: 'none', color: '#4a4a4a', cursor: 'pointer',
              padding: 0, display: 'flex', alignItems: 'center',
            }}
            aria-label={showPw ? 'Hide password' : 'Show password'}
          >
            {showPw ? <EyeOff size={14} /> : <Eye size={14} />}
          </button>
        </div>
      </div>

      {error && (
        <div style={{
          marginBottom: '1rem',
          padding: '0.75rem 1rem',
          background: 'rgba(255,92,92,0.08)',
          border: '1px solid rgba(255,92,92,0.2)',
          borderRadius: 4,
          fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#ff5c5c', letterSpacing: '0.05em',
        }}>
          {error}
        </div>
      )}

      <button
        type="submit"
        className="btn btn-primary"
        disabled={loading}
        style={{ width: '100%', justifyContent: 'center', marginBottom: '1.5rem' }}
      >
        {loading ? (
          <>
            <Loader2 size={14} className="animate-spin" />
            AUTHENTICATING...
          </>
        ) : (
          'ENTER SYSTEM →'
        )}
      </button>

      <p style={{ textAlign: 'center', fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#4a4a4a' }}>
        NO ACCOUNT?{' '}
        <Link href="/signup" style={{ color: '#c8ff00', textDecoration: 'none' }}>
          BEGIN YOUR JOURNEY →
        </Link>
      </p>
    </form>
  );
}

export default function LoginPage() {
  return (
    <div style={{
      minHeight: '100vh', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', padding: '2rem',
      background: '#080808',
    }}>
      {/* Background grid */}
      <div style={{
        position: 'fixed', inset: 0,
        backgroundImage: 'linear-gradient(rgba(200,255,0,0.015) 1px, transparent 1px), linear-gradient(90deg, rgba(200,255,0,0.015) 1px, transparent 1px)',
        backgroundSize: '60px 60px', pointerEvents: 'none', zIndex: 0,
      }} />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        style={{ width: '100%', maxWidth: 400, position: 'relative', zIndex: 1 }}
      >
        {/* Logo */}
        <Link href="/" style={{ textDecoration: 'none', display: 'block', textAlign: 'center', marginBottom: '3rem' }}>
          <span style={{ fontFamily: 'Space Mono', fontSize: '1.1rem', fontWeight: 700, color: '#f0ece4', letterSpacing: '0.05em' }}>
            LIFE<span style={{ color: '#c8ff00' }}>{'//'}</span>OS
          </span>
        </Link>

        <div style={{
          background: 'rgba(14,14,14,0.9)',
          border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: 6, padding: '2rem',
        }}>
          <div style={{ marginBottom: '2rem' }}>
            <div className="sys-label" style={{ marginBottom: '0.5rem' }}>SYSTEM ACCESS</div>
            <h1 style={{ fontFamily: 'Space Grotesk', fontSize: '1.5rem', fontWeight: 700, color: '#f0ece4' }}>
              Welcome back.
            </h1>
          </div>

          <Suspense fallback={<div style={{ textAlign: 'center', color: '#888', padding: '2rem' }}>Loading auth...</div>}>
            <LoginForm />
          </Suspense>
        </div>
      </motion.div>
    </div>
  );
}
