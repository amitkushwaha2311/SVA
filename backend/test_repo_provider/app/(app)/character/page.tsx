'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Loader2, Zap, Shield, Star } from 'lucide-react';

interface Character {
  level: number; xp: number; xpToNextLevel: number; gold: number; archetype: string;
  intellect: number; strength: number; discipline: number; creativity: number; social: number; recovery: number;
  currentStreak: number; longestStreak: number; comboMultiplier: number;
}
interface Trait { id: string; name: string; icon: string; rarity: string; description: string; }
interface Ability { id: string; name: string; icon: string; description: string; requiredLevel: number; }

const ATTRS = [
  { key: 'intellect', name: 'INTELLECT', desc: 'Learning, analysis, and intellectual mastery', color: '#7b8cff' },
  { key: 'strength', name: 'STRENGTH', desc: 'Physical capability and endurance', color: '#ff5c5c' },
  { key: 'discipline', name: 'DISCIPLINE', desc: 'Consistency, focus, and willpower', color: '#c8ff00' },
  { key: 'creativity', name: 'CREATIVITY', desc: 'Innovation, expression, and originality', color: '#ff9500' },
  { key: 'social', name: 'SOCIAL', desc: 'Connection, communication, and impact', color: '#00e5a0' },
  { key: 'recovery', name: 'RECOVERY', desc: 'Rest, restoration, and resilience', color: '#b066ff' },
];

export default function CharacterPage() {
  const [character, setCharacter] = useState<Character | null>(null);
  const [traits, setTraits] = useState<Trait[]>([]);
  const [abilities, setAbilities] = useState<Ability[]>([]);
  const [questsCompleted, setQuestsCompleted] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/character')
      .then((r) => r.json())
      .then((d) => {
        setCharacter(d.character);
        setTraits(d.traits ?? []);
        setAbilities(d.abilities ?? []);
        setQuestsCompleted(d.questsCompleted ?? 0);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}><Loader2 size={24} color="#c8ff00" className="animate-spin" /></div>;
  if (!character) return null;

  const xpPct = Math.min(100, Math.floor((character.xp / character.xpToNextLevel) * 100));

  return (
    <div style={{ padding: '2rem', maxWidth: 1000, margin: '0 auto' }}>
      <div style={{ marginBottom: '2.5rem' }}>
        <div className="sys-label" style={{ marginBottom: '0.25rem' }}>OPERATOR PROFILE</div>
        <h1 style={{ fontFamily: 'Space Grotesk', fontSize: '2rem', fontWeight: 700, color: '#f0ece4', lineHeight: 1 }}>CHARACTER</h1>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '1.5rem' }}>
        {/* Left: Main character panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ background: 'rgba(10,10,10,0.9)', border: '1px solid rgba(200,255,0,0.1)', borderRadius: 6, padding: '2rem', position: 'relative', overflow: 'hidden' }}>
            <div style={{ position: 'absolute', inset: 0, background: 'repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(0,0,0,0.02) 3px, rgba(0,0,0,0.02) 6px)', pointerEvents: 'none' }} />

            {/* Level */}
            <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
              <div className="sys-label" style={{ marginBottom: '0.5rem' }}>LEVEL</div>
              <motion.div
                key={character.level}
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                style={{ fontFamily: 'Space Grotesk', fontSize: '5rem', fontWeight: 700, color: '#c8ff00', lineHeight: 1 }}
              >
                {character.level}
              </motion.div>
              <div style={{ fontFamily: 'Space Mono', fontSize: '0.75rem', color: '#8a8a8a', marginTop: '0.5rem', letterSpacing: '0.1em' }}>
                {character.archetype}
              </div>
            </div>

            {/* XP */}
            <div style={{ marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#8a8a8a', letterSpacing: '0.1em' }}>EXPERIENCE</span>
                <span style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#00cfff' }}>{xpPct}%</span>
              </div>
              <div style={{ height: 5, background: '#1a1a1a', borderRadius: 3, overflow: 'hidden' }}>
                <motion.div animate={{ width: `${xpPct}%` }} transition={{ duration: 1.2 }} style={{ height: '100%', background: 'linear-gradient(90deg, #00cfff, #c8ff00)', borderRadius: 3 }} />
              </div>
              <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', marginTop: '0.3rem' }}>{character.xp} / {character.xpToNextLevel} XP</div>
            </div>

            {/* Stats grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              {[
                { label: 'GOLD', value: character.gold, color: '#e8a100', icon: '🪙' },
                { label: 'QUESTS', value: questsCompleted, color: '#f0ece4', icon: '⚔️' },
                { label: 'STREAK', value: `${character.currentStreak}d`, color: '#c8ff00', icon: '🔥' },
                { label: 'COMBO', value: `×${character.comboMultiplier.toFixed(1)}`, color: '#ff4d00', icon: '⚡' },
              ].map((stat) => (
                <div key={stat.label} style={{ background: 'rgba(20,20,20,0.8)', borderRadius: 4, padding: '0.875rem', border: '1px solid rgba(255,255,255,0.04)' }}>
                  <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', letterSpacing: '0.12em', marginBottom: '0.25rem' }}>{stat.icon} {stat.label}</div>
                  <div style={{ fontFamily: 'Space Grotesk', fontSize: '1.2rem', fontWeight: 700, color: stat.color }}>{stat.value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Attributes + Traits + Abilities */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Attributes */}
          <div style={{ background: 'rgba(10,10,10,0.9)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 6, padding: '1.5rem' }}>
            <div className="sys-label" style={{ marginBottom: '1.25rem' }}>ATTRIBUTES</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>
              {ATTRS.map((attr) => {
                const val = (character as unknown as Record<string, number>)[attr.key] ?? 0;
                return (
                  <motion.div key={attr.key} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                      <div>
                        <span style={{ fontFamily: 'Space Mono', fontSize: '0.65rem', color: attr.color, letterSpacing: '0.1em' }}>{attr.name}</span>
                        <span style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', marginLeft: '0.5rem' }}>{attr.desc}</span>
                      </div>
                      <span style={{ fontFamily: 'Space Grotesk', fontSize: '1rem', fontWeight: 700, color: attr.color }}>{val}</span>
                    </div>
                    <div style={{ height: 3, background: '#1a1a1a', borderRadius: 2, overflow: 'hidden' }}>
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.min(100, val)}%` }}
                        transition={{ duration: 1.2, ease: 'easeOut' }}
                        style={{ height: '100%', background: attr.color, borderRadius: 2, opacity: 0.75 }}
                      />
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>

          {/* Traits */}
          <div style={{ background: 'rgba(10,10,10,0.9)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 6, padding: '1.5rem' }}>
            <div className="sys-label" style={{ marginBottom: '1.25rem' }}>DISCOVERED TRAITS ({traits.length})</div>
            {traits.length === 0 ? (
              <div style={{ fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#4a4a4a', textAlign: 'center', padding: '1.5rem' }}>
                Your story hasn&apos;t revealed any traits yet.
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                {traits.map((t) => (
                  <div key={t.id} style={{ padding: '1rem', background: 'rgba(200,255,0,0.03)', border: '1px solid rgba(200,255,0,0.1)', borderRadius: 4 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                      <span style={{ fontSize: '1.2rem' }}>{t.icon}</span>
                      <span className={`badge badge-${t.rarity.toLowerCase()}`}>{t.rarity}</span>
                    </div>
                    <div style={{ fontFamily: 'Space Grotesk', fontSize: '0.8rem', fontWeight: 600, color: '#f0ece4', marginBottom: '0.3rem' }}>{t.name}</div>
                    <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#8a8a8a', lineHeight: 1.5 }}>{t.description}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Abilities */}
          {abilities.length > 0 && (
            <div style={{ background: 'rgba(10,10,10,0.9)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 6, padding: '1.5rem' }}>
              <div className="sys-label" style={{ marginBottom: '1.25rem' }}>UNLOCKED ABILITIES ({abilities.length})</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {abilities.map((a) => (
                  <div key={a.id} style={{ display: 'flex', alignItems: 'center', gap: '0.875rem', padding: '0.75rem', background: 'rgba(20,20,20,0.6)', borderRadius: 3, border: '1px solid rgba(255,255,255,0.04)' }}>
                    <span style={{ fontSize: '1.2rem', flexShrink: 0 }}>{a.icon}</span>
                    <div>
                      <div style={{ fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#c8ff00', letterSpacing: '0.08em' }}>{a.name}</div>
                      <div style={{ fontFamily: 'Space Grotesk', fontSize: '0.75rem', color: '#8a8a8a', marginTop: '0.1rem' }}>{a.description}</div>
                    </div>
                    <div style={{ marginLeft: 'auto', fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', letterSpacing: '0.1em' }}>LVL {a.requiredLevel}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
