'use client';

import React, { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { motion, useScroll, useTransform, AnimatePresence } from 'framer-motion';

// ─── Particle Canvas ──────────────────────────────────────────────────────────
function ParticleField() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    const particles: Array<{
      x: number; y: number; vx: number; vy: number;
      size: number; opacity: number; life: number; maxLife: number;
    }> = [];

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    const spawn = () => {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.3,
        vy: -Math.random() * 0.5 - 0.1,
        size: Math.random() * 1.5 + 0.3,
        opacity: 0,
        life: 0,
        maxLife: 180 + Math.random() * 120,
      });
    };

    for (let i = 0; i < 80; i++) spawn();

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.life++;
        p.x += p.vx;
        p.y += p.vy;

        const t = p.life / p.maxLife;
        p.opacity = t < 0.2 ? t / 0.2 : t > 0.8 ? (1 - t) / 0.2 : 1;

        ctx.save();
        ctx.globalAlpha = p.opacity * 0.4;
        ctx.fillStyle = Math.random() > 0.7 ? '#c8ff00' : '#ffffff';
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();

        if (p.life >= p.maxLife) {
          particles.splice(i, 1);
          spawn();
        }
      }

      if (particles.length < 80) spawn();
      animId = requestAnimationFrame(draw);
    };

    draw();
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute',
        inset: 0,
        pointerEvents: 'none',
        opacity: 0.6,
      }}
    />
  );
}

// ─── Live HUD ─────────────────────────────────────────────────────────────────
function LiveHUD() {
  const [xp, setXP] = useState(72);
  const [intellect, setIntellect] = useState(78);
  const [strength, setStrength] = useState(61);
  const [discipline, setDiscipline] = useState(84);
  const [pulse, setPulse] = useState(false);
  const [telemetry, setTelemetry] = useState('NOMINAL');

  useEffect(() => {
    const interval = setInterval(() => {
      setXP((v) => {
        const delta = (Math.random() - 0.3) * 0.5;
        return Math.min(95, Math.max(60, v + delta));
      });
      setIntellect((v) => Math.min(99, Math.max(70, v + (Math.random() > 0.8 ? 1 : 0))));
      setStrength((v) => Math.min(99, Math.max(55, v + (Math.random() > 0.9 ? 1 : 0))));
      setDiscipline((v) => Math.min(99, Math.max(78, v + (Math.random() > 0.85 ? 1 : 0))));
      setPulse((p) => !p);
      const statuses = ['NOMINAL', 'PROCESSING', 'EVOLVING', 'ACTIVE'];
      if (Math.random() > 0.7) setTelemetry(statuses[Math.floor(Math.random() * statuses.length)]);
    }, 2400);
    return () => clearInterval(interval);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 1.2, duration: 0.8 }}
      style={{
        background: 'rgba(8,8,8,0.92)',
        border: '1px solid rgba(200,255,0,0.15)',
        borderRadius: 6,
        padding: '2rem',
        width: '100%',
        maxWidth: 360,
        backdropFilter: 'blur(16px)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Scanlines */}
      <div style={{
        position: 'absolute', inset: 0, pointerEvents: 'none',
        background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.04) 2px, rgba(0,0,0,0.04) 4px)',
      }} />

      {/* Status line */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
        <span style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#4a4a4a', letterSpacing: '0.12em' }}>
          LIFE//OS / CHARACTER
        </span>
        <span style={{
          fontFamily: 'Space Mono', fontSize: '0.6rem',
          color: pulse ? '#c8ff00' : '#5a6a00',
          letterSpacing: '0.12em',
          transition: 'color 1.2s ease',
        }}>
          ● {telemetry}
        </span>
      </div>

      {/* Level + Archetype */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#4a4a4a', letterSpacing: '0.12em', marginBottom: '0.3rem' }}>
          LEVEL
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.75rem' }}>
          <span style={{ fontFamily: 'Space Grotesk', fontSize: '3.5rem', fontWeight: 700, color: '#c8ff00', lineHeight: 1 }}>
            18
          </span>
          <div>
            <div style={{ fontFamily: 'Space Grotesk', fontSize: '1rem', color: '#f0ece4', fontWeight: 600 }}>
              THE BUILDER
            </div>
            <div style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#4a4a4a', letterSpacing: '0.08em', marginTop: '0.1rem' }}>
              ARCHETYPE_04
            </div>
          </div>
        </div>
      </div>

      {/* XP Bar */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
          <span style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#8a8a8a', letterSpacing: '0.1em' }}>XP</span>
          <span style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#c8ff00', letterSpacing: '0.1em' }}>
            {Math.floor(xp)}%
          </span>
        </div>
        <div style={{ height: 4, background: '#1a1a1a', borderRadius: 2, overflow: 'hidden' }}>
          <motion.div
            animate={{ width: `${xp}%` }}
            transition={{ duration: 1.5, ease: 'easeInOut' }}
            style={{
              height: '100%',
              background: 'linear-gradient(90deg, #00cfff, #c8ff00)',
              borderRadius: 2,
            }}
          />
        </div>
        <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', marginTop: '0.3rem', letterSpacing: '0.08em' }}>
          {Math.floor(xp * 38)} / 3800 XP
        </div>
      </div>

      {/* Attributes */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
        {[
          { name: 'INTELLECT', value: intellect, color: '#7b8cff' },
          { name: 'STRENGTH', value: strength, color: '#ff5c5c' },
          { name: 'DISCIPLINE', value: discipline, color: '#c8ff00' },
        ].map((attr) => (
          <div key={attr.name}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
              <span style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#8a8a8a', letterSpacing: '0.1em' }}>
                {attr.name}
              </span>
              <motion.span
                key={attr.value}
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: attr.color, letterSpacing: '0.08em' }}
              >
                {attr.value}
              </motion.span>
            </div>
            <div style={{ height: 2, background: '#1a1a1a', borderRadius: 1, overflow: 'hidden' }}>
              <motion.div
                animate={{ width: `${attr.value}%` }}
                transition={{ duration: 1.2, ease: 'easeInOut' }}
                style={{ height: '100%', background: attr.color, borderRadius: 1, opacity: 0.7 }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Bottom status */}
      <div style={{ marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.05)', display: 'flex', justifyContent: 'space-between' }}>
        <span style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', letterSpacing: '0.1em' }}>
          STREAK_07
        </span>
        <span style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', letterSpacing: '0.1em' }}>
          COMBO_×1.2
        </span>
        <span style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', letterSpacing: '0.1em' }}>
          GOLD_620
        </span>
      </div>
    </motion.div>
  );
}

// ─── Nav ──────────────────────────────────────────────────────────────────────
function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const { data: session } = useSession();
  const router = useRouter();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 60);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const handleNavClick = (link: string) => {
    if (link === 'SYSTEM') {
      if (session?.user) {
        router.push('/dashboard');
      } else {
        router.push('/login');
      }
    } else if (link === 'EVOLUTION') {
      router.push('/evolution');
    } else if (link === 'FEATURES') {
      const el = document.getElementById('features');
      if (el) {
        el.scrollIntoView({ behavior: 'smooth' });
      }
    }
  };

  return (
    <motion.nav
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100,
        padding: scrolled ? '0.75rem 2rem' : '1.5rem 2rem',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: scrolled ? 'rgba(8,8,8,0.94)' : 'transparent',
        backdropFilter: scrolled ? 'blur(16px)' : 'none',
        borderBottom: scrolled ? '1px solid rgba(255,255,255,0.05)' : 'none',
        transition: 'all 0.3s ease',
      }}
    >
      <Link href="/" style={{ textDecoration: 'none' }}>
        <span style={{ fontFamily: 'Space Mono', fontSize: '0.85rem', fontWeight: 700, color: '#f0ece4', letterSpacing: '0.05em' }}>
          LIFE<span style={{ color: '#c8ff00' }}>{'//'}</span>OS
        </span>
      </Link>

      <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
        <div style={{ display: 'flex', gap: '2rem' }}>
          <button
            onClick={() => router.push(session?.user ? '/dashboard' : '/login')}
            style={{ background: 'none', border: 'none', padding: 0, fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#8a8a8a', letterSpacing: '0.1em', cursor: 'pointer', transition: 'color 0.15s' }}
            onMouseEnter={(e) => (e.currentTarget.style.color = '#f0ece4')}
            onMouseLeave={(e) => (e.currentTarget.style.color = '#8a8a8a')}
          >
            SYSTEM
          </button>
          <Link href="/evolution" style={{ textDecoration: 'none' }}>
            <button
              style={{ background: 'none', border: 'none', padding: 0, fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#8a8a8a', letterSpacing: '0.1em', cursor: 'pointer', transition: 'color 0.15s' }}
              onMouseEnter={(e) => (e.currentTarget.style.color = '#f0ece4')}
              onMouseLeave={(e) => (e.currentTarget.style.color = '#8a8a8a')}
            >
              EVOLUTION
            </button>
          </Link>
          <button
            onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}
            style={{ background: 'none', border: 'none', padding: 0, fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#8a8a8a', letterSpacing: '0.1em', cursor: 'pointer', transition: 'color 0.15s' }}
            onMouseEnter={(e) => (e.currentTarget.style.color = '#f0ece4')}
            onMouseLeave={(e) => (e.currentTarget.style.color = '#8a8a8a')}
          >
            FEATURES
          </button>
        </div>
        <Link href={session?.user ? "/dashboard" : "/login"} style={{ textDecoration: 'none' }}>
          <button className="btn btn-primary btn-sm">
            ENTER SYSTEM →
          </button>
        </Link>
      </div>
    </motion.nav>
  );
}

// ─── SECTION: Hero ────────────────────────────────────────────────────────────
function HeroSection() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 200);
    return () => clearTimeout(t);
  }, []);

  return (
    <section style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      position: 'relative',
      overflow: 'hidden',
      padding: '8rem 2rem 4rem',
    }}>
      <ParticleField />

      {/* Grid overlay */}
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: 'linear-gradient(rgba(200,255,0,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(200,255,0,0.02) 1px, transparent 1px)',
        backgroundSize: '80px 80px',
        pointerEvents: 'none',
      }} />

      {/* Radial glow */}
      <div style={{
        position: 'absolute', top: '40%', left: '50%', transform: 'translate(-50%,-50%)',
        width: 600, height: 600,
        background: 'radial-gradient(circle, rgba(200,255,0,0.03) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />

      <div style={{
        maxWidth: 1200, margin: '0 auto', width: '100%',
        display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4rem', alignItems: 'center',
      }}>
        {/* Left: Editorial text */}
        <div>
          {/* System text */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: visible ? 1 : 0 }}
            transition={{ delay: 0.3, duration: 0.6 }}
            style={{ marginBottom: '2rem' }}
          >
            <div style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#4a4a4a', letterSpacing: '0.2em', marginBottom: '0.3rem' }}>
              LIFE//OS / PERSONAL OPERATING SYSTEM
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#c8ff00', display: 'inline-block', animation: 'glow-pulse 2s ease-in-out infinite' }} />
              <span style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#c8ff00', letterSpacing: '0.2em' }}>ONLINE</span>
            </div>
          </motion.div>

          {/* Hero headline */}
          <div style={{ marginBottom: '2rem', overflow: 'hidden' }}>
            <motion.div
              initial={{ y: 80, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.5, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
            >
              <h1 style={{
                fontFamily: 'Space Grotesk',
                fontSize: 'clamp(3.5rem, 8vw, 7rem)',
                fontWeight: 700,
                lineHeight: 0.95,
                color: '#f0ece4',
                letterSpacing: '-0.02em',
                marginBottom: '0.1em',
              }}>
                YOUR LIFE
              </h1>
            </motion.div>
            <motion.div
              initial={{ y: 80, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.65, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
            >
              <h1 style={{
                fontFamily: 'Space Grotesk',
                fontSize: 'clamp(3.5rem, 8vw, 7rem)',
                fontWeight: 700,
                lineHeight: 0.95,
                color: '#c8ff00',
                letterSpacing: '-0.02em',
              }}>
                ALREADY
              </h1>
            </motion.div>
            <motion.div
              initial={{ y: 80, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.8, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
            >
              <h1 style={{
                fontFamily: 'Space Grotesk',
                fontSize: 'clamp(3.5rem, 8vw, 7rem)',
                fontWeight: 700,
                lineHeight: 0.95,
                color: '#f0ece4',
                letterSpacing: '-0.02em',
              }}>
                HAS XP.
              </h1>
            </motion.div>
          </div>

          {/* Subline */}
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.1, duration: 0.6 }}
            style={{ fontFamily: 'Space Mono', fontSize: '0.85rem', color: '#8a8a8a', marginBottom: '2.5rem', letterSpacing: '0.05em' }}
          >
            You just can&apos;t see it.
          </motion.p>

          {/* CTAs */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.3, duration: 0.6 }}
            style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}
          >
            <Link href="/signup" style={{ textDecoration: 'none' }}>
              <button className="btn btn-primary btn-lg" style={{ fontSize: '0.75rem' }}>
                BEGIN YOUR JOURNEY →
              </button>
            </Link>
            <button
              onClick={() => document.getElementById('demo')?.scrollIntoView({ behavior: 'smooth' })}
              className="btn btn-secondary btn-lg"
              style={{ fontSize: '0.75rem', cursor: 'pointer' }}
            >
              EXPLORE SYSTEM
            </button>
          </motion.div>
        </div>

        {/* Right: Live HUD */}
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <LiveHUD />
        </div>
      </div>

      {/* Scroll indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 2, duration: 0.6 }}
        style={{
          position: 'absolute', bottom: '2rem', left: '50%', transform: 'translateX(-50%)',
          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem',
        }}
      >
        <span style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', letterSpacing: '0.2em' }}>SCROLL</span>
        <motion.div
          animate={{ y: [0, 6, 0] }}
          transition={{ duration: 1.5, repeat: Infinity }}
          style={{ width: 1, height: 40, background: 'linear-gradient(to bottom, #4a4a4a, transparent)' }}
        />
      </motion.div>
    </section>
  );
}

// ─── SECTION: Invisible Progression ──────────────────────────────────────────
function InvisibleProgressionSection() {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start end', 'end start'] });
  const opacity = useTransform(scrollYProgress, [0, 0.2, 0.8, 1], [0, 1, 1, 0]);

  const days = [
    { day: 'DAY 01', xp: 0, label: 'LVL 1', stat: '10' },
    { day: 'DAY 14', xp: 28, label: 'LVL 4', stat: '22' },
    { day: 'DAY 30', xp: 55, label: 'LVL 8', stat: '36' },
    { day: 'DAY 100', xp: 88, label: 'LVL 18', stat: '78' },
  ];

  return (
    <motion.section
      id="features"
      ref={ref}
      style={{ opacity }}
      className="section-dark"
    >
      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '8rem 2rem' }}>
        {/* Headline */}
        <div style={{ marginBottom: '5rem', maxWidth: 600 }}>
          <div className="sys-label" style={{ marginBottom: '1rem' }}>SECTION_01 / INVISIBLE PROGRESSION</div>
          <h2 style={{
            fontFamily: 'Space Grotesk',
            fontSize: 'clamp(2.5rem, 5vw, 4.5rem)',
            fontWeight: 700,
            lineHeight: 1,
            letterSpacing: '-0.02em',
            color: '#f0ece4',
          }}>
            YOU&apos;VE BEEN<br />
            <span style={{ color: '#c8ff00' }}>LEVELING UP</span><br />
            THIS WHOLE TIME.
          </h2>
        </div>

        {/* Timeline */}
        <div style={{ position: 'relative', display: 'flex', gap: '0', alignItems: 'flex-end' }}>
          {/* Connecting line */}
          <div style={{
            position: 'absolute', bottom: 40, left: 0, right: 0, height: 1,
            background: 'linear-gradient(90deg, transparent, rgba(200,255,0,0.2), rgba(200,255,0,0.6), transparent)',
          }} />

          {days.map((d, i) => (
            <motion.div
              key={d.day}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.2, duration: 0.7 }}
              style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}
            >
              {/* Character visualization */}
              <div style={{
                width: 48 + i * 16,
                height: 48 + i * 16,
                borderRadius: '50%',
                background: `rgba(200,255,0,${0.05 + i * 0.05})`,
                border: `1px solid rgba(200,255,0,${0.1 + i * 0.1})`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                marginBottom: '1rem',
                fontSize: `${0.6 + i * 0.2}rem`,
              }}>
                <span style={{ fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#c8ff00' }}>{d.label}</span>
              </div>

              {/* XP bar */}
              <div style={{ width: '100%', padding: '0 1rem', marginBottom: '1.5rem' }}>
                <div style={{ height: 3, background: '#1a1a1a', borderRadius: 2, overflow: 'hidden' }}>
                  <motion.div
                    initial={{ width: 0 }}
                    whileInView={{ width: `${d.xp}%` }}
                    viewport={{ once: true }}
                    transition={{ delay: i * 0.2 + 0.4, duration: 1, ease: 'easeOut' }}
                    style={{ height: '100%', background: 'linear-gradient(90deg, #00cfff, #c8ff00)', borderRadius: 2 }}
                  />
                </div>
              </div>

              {/* Day label */}
              <div style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#4a4a4a', letterSpacing: '0.12em' }}>
                {d.day}
              </div>
              <div style={{ fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#c8ff00', marginTop: '0.2rem' }}>
                INTELLECT_{d.stat}
              </div>
            </motion.div>
          ))}
        </div>

        {/* Flow labels */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.8, duration: 0.6 }}
          style={{ marginTop: '4rem', display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap' }}
        >
          {['REAL LIFE', 'ACTIONS', 'XP', 'CHARACTER', 'EVOLUTION'].map((label, i) => (
            <React.Fragment key={label}>
              <span style={{ fontFamily: 'Space Mono', fontSize: '0.7rem', color: i === 4 ? '#c8ff00' : '#8a8a8a', letterSpacing: '0.08em' }}>
                {label}
              </span>
              {i < 4 && (
                <span style={{ color: '#4a4a4a', fontSize: '1rem' }}>→</span>
              )}
            </React.Fragment>
          ))}
        </motion.div>
      </div>
    </motion.section>
  );
}

// ─── SECTION: Real Life → Game ────────────────────────────────────────────────
function RealLifeSection() {
  const activities = [
    { label: 'CODING', xp: '+80 XP', attr: 'INTELLECT', gain: '+2', color: '#7b8cff' },
    { label: 'GYM', xp: '+45 XP', attr: 'STRENGTH', gain: '+1', color: '#ff5c5c' },
    { label: 'READ', xp: '+20 XP', attr: 'INTELLECT', gain: '+1', color: '#7b8cff' },
    { label: 'SLEEP', xp: '+35 XP', attr: 'RECOVERY', gain: '+1', color: '#b066ff' },
  ];

  return (
    <section style={{ padding: '8rem 2rem' }}>
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6rem', alignItems: 'center' }}>
          {/* Left: Activities */}
          <div>
            <div className="sys-label" style={{ marginBottom: '1rem' }}>SECTION_02 / GAME LOOP</div>
            <h2 style={{
              fontFamily: 'Space Grotesk',
              fontSize: 'clamp(2rem, 4vw, 3.5rem)',
              fontWeight: 700,
              lineHeight: 1.1,
              letterSpacing: '-0.02em',
              color: '#f0ece4',
              marginBottom: '3rem',
            }}>
              REAL LIFE<br />
              <span style={{ color: '#c8ff00' }}>BECOMES</span><br />
              THE GAME.
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {activities.map((act, i) => (
                <motion.div
                  key={act.label}
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1, duration: 0.5 }}
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '0.9rem 1.2rem',
                    background: 'rgba(20,20,20,0.6)',
                    border: '1px solid rgba(255,255,255,0.06)',
                    borderRadius: 4,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ width: 3, height: 24, background: act.color, borderRadius: 2 }} />
                    <span style={{ fontFamily: 'Space Mono', fontSize: '0.75rem', color: '#f0ece4', letterSpacing: '0.1em' }}>
                      {act.label}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <span style={{ fontFamily: 'Space Mono', fontSize: '0.7rem', color: '#00cfff' }}>{act.xp}</span>
                    <span style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: act.color }}>
                      {act.attr} {act.gain}
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Right: Character Updated */}
          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7 }}
          >
            <div style={{
              background: 'rgba(8,8,8,0.8)',
              border: '1px solid rgba(200,255,0,0.12)',
              borderRadius: 6,
              padding: '2rem',
            }}>
              <div style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#4a4a4a', letterSpacing: '0.15em', marginBottom: '1.5rem' }}>
                CHARACTER UPDATED
              </div>
              {[
                { attr: 'INTELLECT', from: 78, to: 80, color: '#7b8cff' },
                { attr: 'STRENGTH', from: 61, to: 62, color: '#ff5c5c' },
                { attr: 'RECOVERY', from: 45, to: 46, color: '#b066ff' },
              ].map((a) => (
                <div key={a.attr} style={{ marginBottom: '1.2rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                    <span style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#8a8a8a', letterSpacing: '0.1em' }}>{a.attr}</span>
                    <span style={{ fontFamily: 'Space Mono', fontSize: '0.6rem' }}>
                      <span style={{ color: '#4a4a4a' }}>{a.from}</span>
                      <span style={{ color: '#8a8a8a' }}> → </span>
                      <span style={{ color: a.color }}>{a.to}</span>
                    </span>
                  </div>
                  <div style={{ height: 2, background: '#1a1a1a', borderRadius: 1 }}>
                    <motion.div
                      initial={{ width: `${a.from}%` }}
                      whileInView={{ width: `${a.to}%` }}
                      viewport={{ once: true }}
                      transition={{ duration: 1.2, ease: 'easeOut' }}
                      style={{ height: '100%', background: a.color, borderRadius: 1, opacity: 0.7 }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

// ─── SECTION: Quests Demo ─────────────────────────────────────────────────────
function QuestsDemoSection() {
  const [completed, setCompleted] = useState<number[]>([]);
  const [showReward, setShowReward] = useState(false);

  const quests = [
    { id: 0, title: 'Ship portfolio feature', xp: 120, attr: 'INTELLECT' },
    { id: 1, title: '45 min workout', xp: 60, attr: 'STRENGTH' },
    { id: 2, title: 'Read 20 pages', xp: 30, attr: 'INTELLECT' },
  ];

  const handleComplete = (id: number) => {
    if (completed.includes(id)) return;
    setCompleted((prev) => [...prev, id]);
    if (!showReward) {
      setTimeout(() => setShowReward(true), 600);
      setTimeout(() => setShowReward(false), 3000);
    }
  };

  return (
    <section id="demo" style={{ padding: '8rem 2rem', background: 'rgba(14,14,14,0.6)' }}>
      <div style={{ maxWidth: 900, margin: '0 auto' }}>
        <div className="sys-label" style={{ marginBottom: '1rem' }}>SECTION_03 / QUESTS</div>
        <h2 style={{
          fontFamily: 'Space Grotesk', fontSize: 'clamp(2rem, 4vw, 3.5rem)',
          fontWeight: 700, lineHeight: 1, letterSpacing: '-0.02em', color: '#f0ece4', marginBottom: '3rem',
        }}>
          TODAY&apos;S<br />
          <span style={{ color: '#c8ff00' }}>QUESTS.</span>
        </h2>

        <div style={{ position: 'relative' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {quests.map((q, i) => (
              <motion.div
                key={q.id}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                onClick={() => handleComplete(q.id)}
                style={{
                  display: 'flex', alignItems: 'center', gap: '1rem',
                  padding: '1rem 1.5rem',
                  background: completed.includes(q.id) ? 'rgba(200,255,0,0.04)' : 'rgba(14,14,14,0.8)',
                  border: `1px solid ${completed.includes(q.id) ? 'rgba(200,255,0,0.2)' : 'rgba(255,255,255,0.06)'}`,
                  borderRadius: 4, cursor: 'pointer',
                  transition: 'all 0.3s ease',
                }}
                whileHover={{ borderColor: 'rgba(255,255,255,0.15)', x: 4 }}
              >
                {/* Checkbox */}
                <div style={{
                  width: 18, height: 18,
                  border: `1px solid ${completed.includes(q.id) ? '#c8ff00' : 'rgba(255,255,255,0.15)'}`,
                  borderRadius: 2,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  background: completed.includes(q.id) ? '#c8ff00' : 'transparent',
                  transition: 'all 0.2s ease', flexShrink: 0,
                }}>
                  {completed.includes(q.id) && (
                    <span style={{ fontSize: 10, color: '#080808', fontWeight: 700 }}>✓</span>
                  )}
                </div>

                <span style={{
                  fontFamily: 'Space Grotesk', fontSize: '0.95rem', color: completed.includes(q.id) ? '#8a8a8a' : '#f0ece4',
                  textDecoration: completed.includes(q.id) ? 'line-through' : 'none',
                  flex: 1, transition: 'all 0.3s',
                }}>
                  {q.title}
                </span>

                <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                  <span style={{ fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#00cfff' }}>+{q.xp} XP</span>
                  <span style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: q.attr === 'INTELLECT' ? '#7b8cff' : '#ff5c5c' }}>
                    {q.attr}
                  </span>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Reward popup */}
          <AnimatePresence>
            {showReward && (
              <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10, scale: 0.95 }}
                style={{
                  position: 'absolute', right: 0, top: -70,
                  background: 'rgba(8,8,8,0.95)',
                  border: '1px solid rgba(200,255,0,0.3)',
                  borderRadius: 4, padding: '0.75rem 1.25rem',
                }}
              >
                <div style={{ fontFamily: 'Space Mono', fontSize: '0.7rem', color: '#c8ff00', letterSpacing: '0.08em' }}>
                  +120 XP
                </div>
                <div style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#8a8a8a', marginTop: '0.2rem' }}>
                  INTELLECT 78 → 80
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.5 }}
          style={{ marginTop: '2rem', fontFamily: 'Space Mono', fontSize: '0.7rem', color: '#4a4a4a', letterSpacing: '0.08em' }}
        >
          ↑ Click a quest to complete it.
        </motion.p>
      </div>
    </section>
  );
}

// ─── SECTION: Character Stats ─────────────────────────────────────────────────
function CharacterStatsSection() {
  const attrs = [
    { name: 'INTELLECT', value: 78, color: '#7b8cff', desc: 'Learning & Analysis' },
    { name: 'STRENGTH', value: 61, color: '#ff5c5c', desc: 'Physical & Endurance' },
    { name: 'DISCIPLINE', value: 84, color: '#c8ff00', desc: 'Consistency & Focus' },
    { name: 'CREATIVITY', value: 53, color: '#ff9500', desc: 'Innovation & Expression' },
    { name: 'SOCIAL', value: 42, color: '#00e5a0', desc: 'Connections & Impact' },
    { name: 'RECOVERY', value: 67, color: '#b066ff', desc: 'Rest & Restoration' },
  ];

  return (
    <section style={{ padding: '8rem 2rem' }}>
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6rem', alignItems: 'center' }}>
          {/* Left headline */}
          <div>
            <div className="sys-label" style={{ marginBottom: '1rem' }}>SECTION_04 / ATTRIBUTES</div>
            <h2 style={{
              fontFamily: 'Space Grotesk', fontSize: 'clamp(2rem, 4vw, 3.5rem)',
              fontWeight: 700, lineHeight: 1, letterSpacing: '-0.02em', color: '#f0ece4', marginBottom: '2rem',
            }}>
              YOUR HABITS<br />
              <span style={{ color: '#c8ff00' }}>BECOME</span><br />
              YOUR STATS.
            </h2>
            <p style={{ fontFamily: 'Space Mono', fontSize: '0.75rem', color: '#8a8a8a', lineHeight: 1.7 }}>
              Six core attributes reflect how you actually spend your time. Every completed quest moves the numbers — permanently.
            </p>
          </div>

          {/* Right: Attribute meters */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
            {attrs.map((attr, i) => (
              <motion.div
                key={attr.name}
                initial={{ opacity: 0, x: 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08, duration: 0.5 }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <div>
                    <span style={{ fontFamily: 'Space Mono', fontSize: '0.65rem', color: attr.color, letterSpacing: '0.1em' }}>
                      {attr.name}
                    </span>
                    <span style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', marginLeft: '0.5rem' }}>
                      {attr.desc}
                    </span>
                  </div>
                  <span style={{ fontFamily: 'Space Mono', fontSize: '0.8rem', color: attr.color, fontWeight: 700 }}>
                    {attr.value}
                  </span>
                </div>
                <div style={{ height: 3, background: '#1a1a1a', borderRadius: 2, overflow: 'hidden' }}>
                  <motion.div
                    initial={{ width: 0 }}
                    whileInView={{ width: `${attr.value}%` }}
                    viewport={{ once: true }}
                    transition={{ delay: i * 0.08 + 0.3, duration: 1, ease: 'easeOut' }}
                    style={{ height: '100%', background: attr.color, borderRadius: 2, opacity: 0.8 }}
                  />
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── SECTION: Emergent Traits ─────────────────────────────────────────────────
function TraitsSection() {
  const [revealed, setRevealed] = useState(false);

  return (
    <section style={{ padding: '8rem 2rem', background: 'rgba(14,14,14,0.6)', overflow: 'hidden' }}>
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>
        <div className="sys-label" style={{ marginBottom: '1rem' }}>SECTION_05 / EMERGENT TRAITS</div>
        <h2 style={{
          fontFamily: 'Space Grotesk', fontSize: 'clamp(2rem, 4vw, 3.5rem)',
          fontWeight: 700, lineHeight: 1, letterSpacing: '-0.02em', color: '#f0ece4', marginBottom: '4rem',
        }}>
          YOUR CHARACTER<br />
          <span style={{ color: '#c8ff00' }}>LEARNS</span> WHO YOU ARE.
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '3rem', alignItems: 'start' }}>
          {/* Left: Analysis */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            onViewportEnter={() => setTimeout(() => setRevealed(true), 800)}
            viewport={{ once: true }}
            style={{
              background: 'rgba(8,8,8,0.8)',
              border: '1px solid rgba(255,255,255,0.06)',
              borderRadius: 6, padding: '2rem',
            }}
          >
            <div style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#4a4a4a', letterSpacing: '0.15em', marginBottom: '1.5rem' }}>
              SYSTEM ANALYSIS
            </div>
            <div style={{ fontFamily: 'Space Mono', fontSize: '0.75rem', color: '#8a8a8a', marginBottom: '0.5rem' }}>
              47 FOCUS SESSIONS DETECTED
            </div>
            <div style={{ fontFamily: 'Space Mono', fontSize: '0.7rem', color: '#4a4a4a', marginBottom: '2rem' }}>
              PATTERN IDENTIFIED ↓
            </div>

            <AnimatePresence>
              {revealed && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9, y: 10 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  transition={{ duration: 0.6 }}
                  style={{
                    background: 'rgba(200,255,0,0.04)',
                    border: '1px solid rgba(200,255,0,0.2)',
                    borderRadius: 4, padding: '1.5rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ fontSize: '1.5rem' }}>⚡</span>
                      <span style={{ fontFamily: 'Space Grotesk', fontSize: '1.1rem', fontWeight: 700, color: '#c8ff00' }}>
                        DEEP WORKER
                      </span>
                    </div>
                    <span className="badge badge-rare">RARE</span>
                  </div>
                  <p style={{ fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#8a8a8a', lineHeight: 1.6 }}>
                    &quot;Long-form focus has become part of your pattern.&quot;
                  </p>
                  <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', marginTop: '1rem', letterSpacing: '0.12em' }}>
                    TRAIT DISCOVERED — NOT SELECTED
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>

          {/* Right: More traits */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {[
              { icon: '🔥', name: 'RELENTLESS', rarity: 'EPIC', desc: 'Consistency detected across 30 days.', color: '#ff9500' },
              { icon: '🧠', name: 'FAST LEARNER', rarity: 'RARE', desc: 'Level 10 reached in under 30 days.', color: '#7b8cff' },
              { icon: '⚖️', name: 'BALANCED', rarity: 'COMMON', desc: 'All attributes growing in harmony.', color: '#f0ece4' },
            ].map((trait, i) => (
              <motion.div
                key={trait.name}
                initial={{ opacity: 0, x: 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15 + 0.3 }}
                style={{
                  background: 'rgba(8,8,8,0.6)',
                  border: '1px solid rgba(255,255,255,0.06)',
                  borderRadius: 4, padding: '1.25rem',
                  display: 'flex', alignItems: 'center', gap: '1rem',
                }}
              >
                <span style={{ fontSize: '1.5rem', flexShrink: 0 }}>{trait.icon}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
                    <span style={{ fontFamily: 'Space Grotesk', fontSize: '0.9rem', fontWeight: 600, color: '#f0ece4' }}>
                      {trait.name}
                    </span>
                    <span className={`badge badge-${trait.rarity.toLowerCase()}`}>{trait.rarity}</span>
                  </div>
                  <p style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#8a8a8a' }}>{trait.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── SECTION: Boss Battles ────────────────────────────────────────────────────
function BossSection() {
  const [hp, setHP] = useState(720);
  const [attacks, setAttacks] = useState<Array<{ label: string; damage: number; color: string }>>([]);
  const [defeated, setDefeated] = useState(false);

  const maxHP = 1000;

  const attack = (type: string, damage: number, color: string) => {
    if (defeated) return;
    const newHP = Math.max(0, hp - damage);
    setHP(newHP);
    setAttacks((prev) => [{ label: type, damage, color }, ...prev.slice(0, 2)]);
    if (newHP === 0) setTimeout(() => setDefeated(true), 500);
  };

  return (
    <section style={{ padding: '8rem 2rem', overflow: 'hidden' }}>
      <div style={{ maxWidth: 900, margin: '0 auto' }}>
        <div className="sys-label" style={{ marginBottom: '1rem' }}>SECTION_07 / BOSS BATTLES</div>
        <h2 style={{
          fontFamily: 'Space Grotesk', fontSize: 'clamp(2rem, 4vw, 3.5rem)',
          fontWeight: 700, lineHeight: 1, letterSpacing: '-0.02em', color: '#f0ece4', marginBottom: '4rem',
        }}>
          EVERY GOAL<br />
          HAS A <span style={{ color: '#ff4d00' }}>BOSS.</span>
        </h2>

        <div style={{
          background: 'rgba(8,8,8,0.9)',
          border: '1px solid rgba(255,77,0,0.2)',
          borderRadius: 6, padding: '2.5rem',
          position: 'relative',
        }}>
          <AnimatePresence>
            {!defeated ? (
              <motion.div key="boss" exit={{ opacity: 0, scale: 0.9 }}>
                <div style={{ marginBottom: '0.5rem' }}>
                  <span style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#4a4a4a', letterSpacing: '0.15em' }}>BOSS</span>
                </div>
                <div style={{ fontFamily: 'Space Grotesk', fontSize: '2.5rem', fontWeight: 700, color: '#ff4d00', marginBottom: '0.5rem' }}>
                  PROCRASTINATION
                </div>

                {/* HP Bar */}
                <div style={{ marginBottom: '2rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#8a8a8a' }}>HP</span>
                    <span style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#ff4d00' }}>
                      {hp} / {maxHP}
                    </span>
                  </div>
                  <div style={{ height: 6, background: '#1a1a1a', borderRadius: 3, overflow: 'hidden' }}>
                    <motion.div
                      animate={{ width: `${(hp / maxHP) * 100}%` }}
                      transition={{ duration: 0.6, ease: 'easeOut' }}
                      style={{ height: '100%', background: 'linear-gradient(90deg, #ff4d00, #ff2200)', borderRadius: 3 }}
                    />
                  </div>
                </div>

                {/* Attack buttons */}
                <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
                  {[
                    { label: 'CODING', damage: 180, color: '#7b8cff' },
                    { label: 'WORKOUT', damage: 100, color: '#ff5c5c' },
                    { label: 'READING', damage: 70, color: '#c8ff00' },
                  ].map((a) => (
                    <button
                      key={a.label}
                      onClick={() => attack(a.label, a.damage, a.color)}
                      disabled={defeated}
                      style={{
                        fontFamily: 'Space Mono', fontSize: '0.65rem', letterSpacing: '0.1em',
                        padding: '0.6rem 1.2rem', background: 'transparent',
                        border: `1px solid ${a.color}40`, color: a.color,
                        borderRadius: 3, cursor: 'pointer', transition: 'all 0.15s',
                      }}
                      onMouseEnter={(e) => { e.currentTarget.style.background = `${a.color}15`; }}
                      onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
                    >
                      {a.label} -{a.damage} HP
                    </button>
                  ))}
                </div>

                {/* Attack log */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  <AnimatePresence>
                    {attacks.map((atk, i) => (
                      <motion.div
                        key={`${atk.label}-${i}`}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1 - i * 0.4, x: 0 }}
                        exit={{ opacity: 0 }}
                        style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: atk.color, letterSpacing: '0.08em' }}
                      >
                        {atk.label} dealt -{atk.damage} HP
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="defeated"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
                style={{ textAlign: 'center', padding: '2rem 0' }}
              >
                <div style={{ fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#4a4a4a', letterSpacing: '0.15em', marginBottom: '1rem' }}>
                  BOSS DEFEATED
                </div>
                <div style={{
                  fontFamily: 'Space Grotesk', fontSize: '3.5rem', fontWeight: 700,
                  color: '#c8ff00', lineHeight: 1, marginBottom: '1.5rem',
                }}>
                  PROCRASTINATION<br />ELIMINATED
                </div>
                <div style={{ fontFamily: 'Space Mono', fontSize: '0.7rem', color: '#8a8a8a' }}>
                  +500 XP · +200 GOLD · TRAIT UNLOCKED
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
}

// ─── SECTION: Final CTA ───────────────────────────────────────────────────────
function FinalCTA() {
  return (
    <section style={{
      minHeight: '80vh',
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      padding: '8rem 2rem',
      position: 'relative', overflow: 'hidden',
    }}>
      <ParticleField />

      {/* Grid */}
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: 'linear-gradient(rgba(200,255,0,0.015) 1px, transparent 1px), linear-gradient(90deg, rgba(200,255,0,0.015) 1px, transparent 1px)',
        backgroundSize: '60px 60px', pointerEvents: 'none',
      }} />

      <div style={{ textAlign: 'center', position: 'relative', zIndex: 1 }}>
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          style={{ fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#4a4a4a', letterSpacing: '0.2em', marginBottom: '2rem' }}
        >
          YOUR CHARACTER IS WAITING.
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        >
          <h2 style={{
            fontFamily: 'Space Grotesk', fontSize: 'clamp(4rem, 10vw, 9rem)',
            fontWeight: 700, lineHeight: 0.9, letterSpacing: '-0.02em', color: '#f0ece4', marginBottom: '1rem',
          }}>
            READY<br />
            <span style={{ color: '#c8ff00' }}>TO LEVEL</span><br />
            UP?
          </h2>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.4 }}
          style={{ marginTop: '3rem' }}
        >
          <Link href="/signup" style={{ textDecoration: 'none' }}>
            <button className="btn btn-primary" style={{ fontSize: '0.85rem', padding: '1rem 2.5rem' }}>
              BEGIN YOUR JOURNEY →
            </button>
          </Link>
          <div style={{ marginTop: '2rem', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
            {['No productivity hacks.', 'No meaningless checklists.', 'Just progress you can see.'].map((line) => (
              <p key={line} style={{ fontFamily: 'Space Mono', fontSize: '0.7rem', color: '#4a4a4a', letterSpacing: '0.06em' }}>
                {line}
              </p>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}

// ─── Landing Page ─────────────────────────────────────────────────────────────
export default function LandingPage() {
  return (
    <main>
      <Nav />
      <HeroSection />
      <InvisibleProgressionSection />
      <RealLifeSection />
      <QuestsDemoSection />
      <CharacterStatsSection />
      <TraitsSection />
      <BossSection />
      <FinalCTA />

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid rgba(255,255,255,0.04)',
        padding: '2rem',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <span style={{ fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#4a4a4a' }}>
          LIFE<span style={{ color: '#8a8a8a' }}>{'//'}</span>OS · PERSONAL OPERATING SYSTEM
        </span>
        <span style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#4a4a4a' }}>
          YOUR REAL LIFE ALREADY HAS XP.
        </span>
      </footer>
    </main>
  );
}
