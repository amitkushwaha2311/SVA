'use client';

import { useEffect, useState, useCallback } from 'react';
import { useSession } from 'next-auth/react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { Zap, Flame, Star, Target, Trophy, Plus, CheckCircle2, Loader2 } from 'lucide-react';
import { getXPProgress, getComboMultiplier } from '@/lib/game-engine';
import { requiredXPForLevel } from '@/lib/constants';

interface Character {
  level: number; xp: number; xpToNextLevel: number; gold: number; archetype: string;
  intellect: number; strength: number; discipline: number; creativity: number; social: number; recovery: number;
  currentStreak: number; longestStreak: number; comboMultiplier: number;
  equippedFrameId: string | null; equippedAuraId: string | null;
}

interface Quest {
  id: string; title: string; attribute: string; difficulty: string;
  xpReward: number; goldReward: number; status: string;
}

interface CompletionResult {
  success: boolean;
  rewards: { xpEarned: number; goldEarned: number; combo: number; attributeGain: number; attribute: string };
  character: Character;
  levelUp: { levelsGained: number; fromLevel: number; toLevel: number; goldBonus: number; newAbilities: Array<{ name: string; icon: string }> } | null;
  newTraits: Array<{ name: string; icon: string; rarity: string }>;
  bossDamage: Array<{ bossId: string; name: string; damage: number; newHP: number; defeated: boolean }>;
}

const ATTR_COLORS: Record<string, string> = {
  INTELLECT: '#7b8cff', STRENGTH: '#ff5c5c', DISCIPLINE: '#c8ff00',
  CREATIVITY: '#ff9500', SOCIAL: '#00e5a0', RECOVERY: '#b066ff',
};

const DIFF_LABELS: Record<string, string> = {
  EASY: 'EASY', MEDIUM: 'MEDIUM', HARD: 'HARD', EPIC: 'EPIC',
};

function XPBar({ xp, xpToNextLevel, level }: { xp: number; xpToNextLevel: number; level: number }) {
  const pct = Math.min(100, Math.floor((xp / xpToNextLevel) * 100));
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
        <span style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#8a8a8a', letterSpacing: '0.1em' }}>XP</span>
        <span style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#00cfff' }}>
          {xp} / {xpToNextLevel}
        </span>
      </div>
      <div style={{ height: 4, background: '#1a1a1a', borderRadius: 2, overflow: 'hidden' }}>
        <motion.div
          animate={{ width: `${pct}%` }}
          transition={{ duration: 1, ease: 'easeOut' }}
          style={{
            height: '100%',
            background: 'linear-gradient(90deg, #00cfff, #c8ff00)',
            borderRadius: 2, position: 'relative',
          }}
        >
          <div style={{
            position: 'absolute', right: 0, top: 0, width: 12, height: '100%',
            background: 'linear-gradient(90deg, transparent, rgba(200,255,0,0.8))',
            animation: 'xp-pulse 2s ease-in-out infinite',
          }} />
        </motion.div>
      </div>
    </div>
  );
}

function CompletionModal({ result, onClose }: { result: CompletionResult; onClose: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="modal-overlay"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.8, y: 30 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.8, y: 30 }}
        transition={{ type: 'spring', stiffness: 300, damping: 25 }}
        className="modal"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: 440, textAlign: 'center' }}
      >
        {/* Level up headline */}
        {result.levelUp ? (
          <div style={{ marginBottom: '2rem' }}>
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
              style={{ fontSize: '3rem', marginBottom: '0.5rem' }}
            >
              ⬆️
            </motion.div>
            <div style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#4a4a4a', letterSpacing: '0.15em', marginBottom: '0.5rem' }}>
              LEVEL UP
            </div>
            <div style={{ fontFamily: 'Space Grotesk', fontSize: '2.5rem', fontWeight: 700, color: '#c8ff00' }}>
              {result.levelUp.fromLevel} → {result.levelUp.toLevel}
            </div>
            {result.levelUp.newAbilities.map((a) => (
              <div key={a.name} style={{ marginTop: '0.5rem', fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#8a8a8a' }}>
                {a.icon} NEW ABILITY: {a.name}
              </div>
            ))}
          </div>
        ) : (
          <div style={{ marginBottom: '1.5rem' }}>
            <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.2 }} style={{ fontSize: '2.5rem' }}>
              ✓
            </motion.div>
            <div style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#c8ff00', letterSpacing: '0.15em', marginTop: '0.5rem' }}>
              QUEST COMPLETE
            </div>
          </div>
        )}

        {/* Rewards */}
        <div style={{
          background: 'rgba(20,20,20,0.8)', border: '1px solid rgba(255,255,255,0.06)',
          borderRadius: 4, padding: '1.25rem', marginBottom: '1.5rem',
        }}>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '2rem' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontFamily: 'Space Grotesk', fontSize: '1.5rem', fontWeight: 700, color: '#00cfff' }}>
                +{result.rewards.xpEarned}
              </div>
              <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', letterSpacing: '0.1em' }}>XP</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontFamily: 'Space Grotesk', fontSize: '1.5rem', fontWeight: 700, color: '#e8a100' }}>
                +{result.rewards.goldEarned}
              </div>
              <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', letterSpacing: '0.1em' }}>GOLD</div>
            </div>
            {result.rewards.combo > 1 && (
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontFamily: 'Space Grotesk', fontSize: '1.5rem', fontWeight: 700, color: '#c8ff00' }}>
                  ×{result.rewards.combo.toFixed(1)}
                </div>
                <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', letterSpacing: '0.1em' }}>COMBO</div>
              </div>
            )}
          </div>

          <div style={{ marginTop: '0.75rem', fontFamily: 'Space Mono', fontSize: '0.6rem', color: ATTR_COLORS[result.rewards.attribute] ?? '#8a8a8a' }}>
            {result.rewards.attribute} +{result.rewards.attributeGain}
          </div>
        </div>

        {/* Traits */}
        {result.newTraits.length > 0 && (
          <div style={{ marginBottom: '1.5rem' }}>
            {result.newTraits.map((t) => (
              <motion.div
                key={t.name}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                style={{
                  padding: '0.875rem',
                  background: 'rgba(200,255,0,0.04)',
                  border: '1px solid rgba(200,255,0,0.2)',
                  borderRadius: 4,
                }}
              >
                <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', letterSpacing: '0.15em', marginBottom: '0.3rem' }}>
                  TRAIT DISCOVERED
                </div>
                <div style={{ fontFamily: 'Space Grotesk', fontSize: '1rem', fontWeight: 700, color: '#c8ff00' }}>
                  {t.icon} {t.name}
                </div>
              </motion.div>
            ))}
          </div>
        )}

        {/* Boss damage */}
        {result.bossDamage.length > 0 && (
          <div style={{ marginBottom: '1.5rem' }}>
            {result.bossDamage.map((b) => (
              <div key={b.bossId} style={{ fontFamily: 'Space Mono', fontSize: '0.65rem', color: b.defeated ? '#c8ff00' : '#ff4d00', marginBottom: '0.3rem' }}>
                {b.defeated ? `⚔️ ${b.name} DEFEATED!` : `${b.name} took -${b.damage} HP`}
              </div>
            ))}
          </div>
        )}

        <button onClick={onClose} className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
          CONTINUE →
        </button>
      </motion.div>
    </motion.div>
  );
}

export default function DashboardPage() {
  const { data: session } = useSession();
  const [character, setCharacter] = useState<Character | null>(null);
  const [quests, setQuests] = useState<Quest[]>([]);
  const [loading, setLoading] = useState(true);
  const [completing, setCompleting] = useState<string | null>(null);
  const [completionResult, setCompletionResult] = useState<CompletionResult | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let isMounted = true;
    Promise.all([
      fetch('/api/character'),
      fetch('/api/quests?status=ACTIVE'),
    ])
      .then(async ([charRes, questsRes]) => {
        const charData = await charRes.json();
        const questsData = await questsRes.json();
        if (!isMounted) return;
        if (charData.character) setCharacter(charData.character);
        if (questsData.quests) setQuests(questsData.quests.slice(0, 5));
      })
      .catch(() => {
        if (isMounted) setError('Failed to load data.');
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => { isMounted = false; };
  }, []);

  const handleCompleteQuest = async (questId: string) => {
    if (completing) return;
    setCompleting(questId);
    setError('');

    // Optimistic update
    setQuests((prev) => prev.filter((q) => q.id !== questId));

    try {
      const res = await fetch(`/api/quests/${questId}/complete`, { method: 'POST' });
      const data = await res.json();

      if (!res.ok) {
        setError(data.error ?? 'Failed to complete quest.');
        // Rollback: re-fetch
        fetch('/api/quests?status=ACTIVE').then(r => r.json()).then(d => { if (d.quests) setQuests(d.quests.slice(0, 5)); });
        return;
      }

      // Update character from server response
      setCharacter(data.character);
      setCompletionResult(data);
    } catch {
      setError('Connection lost. Your progress is safe.');
      fetch('/api/quests?status=ACTIVE').then(r => r.json()).then(d => { if (d.quests) setQuests(d.quests.slice(0, 5)); });
    } finally {
      setCompleting(null);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
        <Loader2 size={24} color="#c8ff00" className="animate-spin" />
      </div>
    );
  }

  const xpPct = character ? Math.min(100, Math.floor((character.xp / character.xpToNextLevel) * 100)) : 0;
  const attrs = character ? [
    { name: 'INTELLECT', value: character.intellect, color: '#7b8cff' },
    { name: 'STRENGTH', value: character.strength, color: '#ff5c5c' },
    { name: 'DISCIPLINE', value: character.discipline, color: '#c8ff00' },
    { name: 'CREATIVITY', value: character.creativity, color: '#ff9500' },
    { name: 'SOCIAL', value: character.social, color: '#00e5a0' },
    { name: 'RECOVERY', value: character.recovery, color: '#b066ff' },
  ] : [];

  return (
    <div style={{ padding: '2rem', maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '2.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div className="sys-label" style={{ marginBottom: '0.3rem' }}>WELCOME BACK, {session?.user?.name?.toUpperCase() ?? 'OPERATOR'}</div>
          <h1 style={{ fontFamily: 'Space Grotesk', fontSize: '2rem', fontWeight: 700, color: '#f0ece4', lineHeight: 1 }}>
            DASHBOARD
          </h1>
        </div>
        <Link href="/quests" style={{ textDecoration: 'none' }}>
          <button className="btn btn-primary btn-sm">
            <Plus size={12} /> NEW QUEST
          </button>
        </Link>
      </div>

      {error && (
        <div style={{ marginBottom: '1.5rem', padding: '0.75rem', background: 'rgba(255,92,92,0.08)', border: '1px solid rgba(255,92,92,0.2)', borderRadius: 4, fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#ff5c5c' }}>
          {error}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '1.5rem' }}>
        {/* Left: Character HUD */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Character Card */}
          <div style={{
            background: 'rgba(10,10,10,0.9)',
            border: '1px solid rgba(200,255,0,0.1)',
            borderRadius: 6, padding: '1.75rem',
            position: 'relative', overflow: 'hidden',
          }}>
            {/* Scanlines */}
            <div style={{
              position: 'absolute', inset: 0, pointerEvents: 'none',
              background: 'repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(0,0,0,0.02) 3px, rgba(0,0,0,0.02) 6px)',
            }} />

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
              <div>
                <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', letterSpacing: '0.15em', marginBottom: '0.3rem' }}>
                  CHARACTER
                </div>
                <div style={{ fontFamily: 'Space Grotesk', fontSize: '2.5rem', fontWeight: 700, color: '#c8ff00', lineHeight: 1 }}>
                  {character?.level ?? 1}
                </div>
                <div style={{ fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#8a8a8a', marginTop: '0.2rem' }}>
                  {character?.archetype ?? 'THE BUILDER'}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontFamily: 'Space Grotesk', fontSize: '1.1rem', fontWeight: 600, color: '#e8a100' }}>
                  {character?.gold ?? 0}
                </div>
                <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', letterSpacing: '0.12em' }}>GOLD</div>
              </div>
            </div>

            {/* XP Bar */}
            {character && (
              <div style={{ marginBottom: '1.5rem' }}>
                <XPBar xp={character.xp} xpToNextLevel={character.xpToNextLevel} level={character.level} />
              </div>
            )}

            {/* Combo + Streak */}
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
              <div style={{
                flex: 1, padding: '0.75rem',
                background: 'rgba(200,255,0,0.04)',
                border: '1px solid rgba(200,255,0,0.1)',
                borderRadius: 3,
              }}>
                <div style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#4a4a4a', letterSpacing: '0.12em', marginBottom: '0.2rem' }}>STREAK</div>
                <div style={{ fontFamily: 'Space Grotesk', fontSize: '1.2rem', fontWeight: 700, color: '#c8ff00' }}>
                  {character?.currentStreak ?? 0}
                  <span style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#8a8a8a', marginLeft: '0.2rem' }}>DAYS</span>
                </div>
              </div>
              <div style={{
                flex: 1, padding: '0.75rem',
                background: 'rgba(255,77,0,0.04)',
                border: '1px solid rgba(255,77,0,0.1)',
                borderRadius: 3,
              }}>
                <div style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#4a4a4a', letterSpacing: '0.12em', marginBottom: '0.2rem' }}>COMBO</div>
                <div style={{ fontFamily: 'Space Grotesk', fontSize: '1.2rem', fontWeight: 700, color: '#ff4d00' }}>
                  ×{(character?.comboMultiplier ?? 1).toFixed(1)}
                </div>
              </div>
            </div>

            {/* Attributes */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.7rem' }}>
              {attrs.map((attr) => (
                <div key={attr.name}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
                    <span style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: attr.color, letterSpacing: '0.1em' }}>{attr.name}</span>
                    <motion.span
                      key={attr.value}
                      initial={{ opacity: 0, y: -4 }}
                      animate={{ opacity: 1, y: 0 }}
                      style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: attr.color }}
                    >
                      {attr.value}
                    </motion.span>
                  </div>
                  <div style={{ height: 2, background: '#1a1a1a', borderRadius: 1, overflow: 'hidden' }}>
                    <motion.div
                      animate={{ width: `${Math.min(100, attr.value)}%` }}
                      transition={{ duration: 1, ease: 'easeOut' }}
                      style={{ height: '100%', background: attr.color, borderRadius: 1, opacity: 0.7 }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Quick links */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
            {[
              { label: 'BOSSES', href: '/bosses', icon: '⚔️' },
              { label: 'CAMPAIGNS', href: '/campaigns', icon: '🗺️' },
              { label: 'SHOP', href: '/shop', icon: '🛍️' },
              { label: 'EVOLUTION', href: '/evolution', icon: '📈' },
            ].map((item) => (
              <Link key={item.href} href={item.href} style={{ textDecoration: 'none' }}>
                <div style={{
                  padding: '0.875rem', background: 'rgba(14,14,14,0.8)',
                  border: '1px solid rgba(255,255,255,0.06)', borderRadius: 4,
                  cursor: 'pointer', transition: 'border-color 0.15s',
                }}
                onMouseEnter={(e) => { (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(255,255,255,0.15)'; }}
                onMouseLeave={(e) => { (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(255,255,255,0.06)'; }}
                >
                  <div style={{ fontSize: '1rem', marginBottom: '0.25rem' }}>{item.icon}</div>
                  <div style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#8a8a8a', letterSpacing: '0.1em' }}>{item.label}</div>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Right: Today's Quests + Activity */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Today's quests */}
          <div style={{
            background: 'rgba(10,10,10,0.9)',
            border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: 6, padding: '1.5rem',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <div>
                <div className="sys-label" style={{ marginBottom: '0.2rem' }}>ACTIVE QUESTS</div>
                <h2 style={{ fontFamily: 'Space Grotesk', fontSize: '1.1rem', fontWeight: 700, color: '#f0ece4' }}>
                  Today&apos;s Battle
                </h2>
              </div>
              <Link href="/quests" style={{ textDecoration: 'none' }}>
                <button className="btn btn-ghost btn-sm" style={{ fontFamily: 'Space Mono', fontSize: '0.6rem' }}>
                  VIEW ALL →
                </button>
              </Link>
            </div>

            {quests.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '3rem 1rem' }}>
                <div style={{ fontFamily: 'Space Mono', fontSize: '0.7rem', color: '#4a4a4a', marginBottom: '1rem' }}>
                  Your adventure begins with one quest.
                </div>
                <Link href="/quests" style={{ textDecoration: 'none' }}>
                  <button className="btn btn-primary btn-sm">
                    <Plus size={12} /> CREATE QUEST
                  </button>
                </Link>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {quests.map((quest) => (
                  <motion.div
                    key={quest.id}
                    layout
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 10, height: 0 }}
                    style={{
                      display: 'flex', alignItems: 'center', gap: '0.875rem',
                      padding: '0.9rem 1rem',
                      background: 'rgba(20,20,20,0.6)',
                      border: `1px solid rgba(255,255,255,0.06)`,
                      borderRadius: 4,
                    }}
                  >
                    {/* Complete button */}
                    <button
                      onClick={() => handleCompleteQuest(quest.id)}
                      disabled={completing === quest.id}
                      aria-label={`Complete: ${quest.title}`}
                      style={{
                        width: 22, height: 22, borderRadius: 3,
                        border: '1px solid rgba(255,255,255,0.15)',
                        background: 'transparent', cursor: 'pointer',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        flexShrink: 0, transition: 'all 0.15s',
                        color: '#4a4a4a',
                      }}
                      onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.borderColor = '#c8ff00'; }}
                      onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(255,255,255,0.15)'; }}
                    >
                      {completing === quest.id ? (
                        <Loader2 size={11} className="animate-spin" color="#c8ff00" />
                      ) : (
                        <CheckCircle2 size={11} />
                      )}
                    </button>

                    {/* Attribute color bar */}
                    <div style={{ width: 3, height: 30, background: ATTR_COLORS[quest.attribute] ?? '#8a8a8a', borderRadius: 2, flexShrink: 0 }} />

                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontFamily: 'Space Grotesk', fontSize: '0.875rem', color: '#f0ece4', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {quest.title}
                      </div>
                      <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', marginTop: '0.15rem', letterSpacing: '0.08em' }}>
                        {quest.attribute} · {quest.difficulty}
                      </div>
                    </div>

                    <div style={{ textAlign: 'right', flexShrink: 0 }}>
                      <div style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#00cfff' }}>+{quest.xpReward} XP</div>
                      <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#e8a100' }}>+{quest.goldReward} G</div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Completion modal */}
      <AnimatePresence>
        {completionResult && (
          <CompletionModal
            result={completionResult}
            onClose={() => setCompletionResult(null)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
