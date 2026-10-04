'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Loader2, TrendingUp } from 'lucide-react';

interface Report {
  weekNumber: number; totalXP: number; totalGold: number; questsCompleted: number;
  bestAttr: string | null; weakestAttr: string | null; bestDay: string | null;
  currentStreak: number; longestStreak: number;
  newTraits: Array<{ name: string; icon: string; rarity: string }>;
  attrBreakdown: Record<string, number>;
  recommendation: { title: string; attribute: string; xp: number } | null;
  dayXP: Record<string, number>;
}

interface Character {
  level: number; xp: number; xpToNextLevel: number; gold: number; archetype: string;
  intellect: number; strength: number; discipline: number; creativity: number; social: number; recovery: number;
  currentStreak: number; longestStreak: number;
}

const ATTR_COLORS: Record<string, string> = {
  INTELLECT: '#7b8cff', STRENGTH: '#ff5c5c', DISCIPLINE: '#c8ff00',
  CREATIVITY: '#ff9500', SOCIAL: '#00e5a0', RECOVERY: '#b066ff',
};

export default function EvolutionPage() {
  const [report, setReport] = useState<Report | null>(null);
  const [character, setCharacter] = useState<Character | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch('/api/report').then((r) => r.json()),
      fetch('/api/character').then((r) => r.json()),
    ]).then(([r, c]) => {
      setReport(r);
      setCharacter(c.character);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}><Loader2 size={24} color="#c8ff00" className="animate-spin" /></div>;

  const attrs = character ? [
    { name: 'INTELLECT', value: character.intellect },
    { name: 'STRENGTH', value: character.strength },
    { name: 'DISCIPLINE', value: character.discipline },
    { name: 'CREATIVITY', value: character.creativity },
    { name: 'SOCIAL', value: character.social },
    { name: 'RECOVERY', value: character.recovery },
  ] : [];

  // Build week day XP chart data
  const dayLabels = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];
  const dayData = report?.dayXP ?? {};
  const maxDayXP = Math.max(...Object.values(dayData), 1);

  return (
    <div style={{ padding: '2rem', maxWidth: 1000, margin: '0 auto' }}>
      <div style={{ marginBottom: '2.5rem' }}>
        <div className="sys-label" style={{ marginBottom: '0.25rem' }}>CHARACTER REPORT</div>
        <h1 style={{ fontFamily: 'Space Grotesk', fontSize: '2rem', fontWeight: 700, color: '#f0ece4', lineHeight: 1 }}>
          EVOLUTION
          {report && (
            <span style={{ fontFamily: 'Space Mono', fontSize: '0.9rem', color: '#4a4a4a', marginLeft: '1rem', fontWeight: 400 }}>
              WEEK {String(report.weekNumber).padStart(2, '0')}
            </span>
          )}
        </h1>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
        {/* Weekly Stats */}
        <div style={{ background: 'rgba(10,10,10,0.9)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 6, padding: '1.75rem' }}>
          <div className="sys-label" style={{ marginBottom: '1.25rem' }}>THIS WEEK</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            {[
              { label: 'XP EARNED', value: (report?.totalXP ?? 0).toLocaleString(), color: '#00cfff' },
              { label: 'GOLD EARNED', value: (report?.totalGold ?? 0).toLocaleString(), color: '#e8a100' },
              { label: 'QUESTS', value: report?.questsCompleted ?? 0, color: '#f0ece4' },
              { label: 'STREAK', value: `${character?.currentStreak ?? 0}d`, color: '#c8ff00' },
            ].map((s) => (
              <div key={s.label} style={{ padding: '1rem', background: 'rgba(20,20,20,0.6)', borderRadius: 4, border: '1px solid rgba(255,255,255,0.04)' }}>
                <div style={{ fontFamily: 'Space Grotesk', fontSize: '1.5rem', fontWeight: 700, color: s.color }}>{s.value}</div>
                <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', letterSpacing: '0.12em', marginTop: '0.2rem' }}>{s.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Attribute Snapshot */}
        <div style={{ background: 'rgba(10,10,10,0.9)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 6, padding: '1.75rem' }}>
          <div className="sys-label" style={{ marginBottom: '1.25rem' }}>ATTRIBUTES</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
            {attrs.map((attr) => (
              <div key={attr.name}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
                  <span style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: ATTR_COLORS[attr.name], letterSpacing: '0.1em' }}>{attr.name}</span>
                  <span style={{ fontFamily: 'Space Grotesk', fontSize: '0.875rem', fontWeight: 700, color: ATTR_COLORS[attr.name] }}>{attr.value}</span>
                </div>
                <div style={{ height: 2, background: '#1a1a1a', borderRadius: 1, overflow: 'hidden' }}>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(100, attr.value)}%` }}
                    transition={{ duration: 1.2, ease: 'easeOut' }}
                    style={{ height: '100%', background: ATTR_COLORS[attr.name], opacity: 0.75, borderRadius: 1 }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Weekly XP Chart */}
      <div style={{ background: 'rgba(10,10,10,0.9)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 6, padding: '1.75rem', marginBottom: '1.5rem' }}>
        <div className="sys-label" style={{ marginBottom: '1.5rem' }}>DAILY XP THIS WEEK</div>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: '0.5rem', height: 80 }}>
          {Object.entries(dayData).slice(0, 7).map(([date, xp], i) => {
            const pct = (xp / maxDayXP) * 100;
            const label = new Date(date).toLocaleDateString('en-US', { weekday: 'short' }).toUpperCase();
            return (
              <div key={date} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.3rem', height: '100%', justifyContent: 'flex-end' }}>
                <span style={{ fontFamily: 'Space Mono', fontSize: '0.5rem', color: '#4a4a4a' }}>{xp}</span>
                <motion.div
                  initial={{ height: 0 }}
                  animate={{ height: `${Math.max(4, pct)}%` }}
                  transition={{ delay: i * 0.08, duration: 0.8 }}
                  style={{ width: '100%', background: '#c8ff00', borderRadius: '2px 2px 0 0', opacity: 0.75 }}
                />
                <span style={{ fontFamily: 'Space Mono', fontSize: '0.5rem', color: '#4a4a4a' }}>{label}</span>
              </div>
            );
          })}
          {Object.keys(dayData).length === 0 && (
            <div style={{ width: '100%', textAlign: 'center', fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#4a4a4a' }}>No data yet this week</div>
          )}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        {/* Intelligence Report */}
        <div style={{ background: 'rgba(10,10,10,0.9)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 6, padding: '1.75rem' }}>
          <div className="sys-label" style={{ marginBottom: '1.25rem' }}>ANALYSIS</div>
          {report?.bestAttr && (
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#4a4a4a', letterSpacing: '0.1em', marginBottom: '0.25rem' }}>STRONGEST THIS WEEK</div>
              <div style={{ fontFamily: 'Space Grotesk', fontSize: '1.1rem', fontWeight: 700, color: ATTR_COLORS[report.bestAttr] }}>{report.bestAttr}</div>
            </div>
          )}
          {report?.weakestAttr && (
            <div style={{ marginBottom: '1.5rem' }}>
              <div style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#4a4a4a', letterSpacing: '0.1em', marginBottom: '0.25rem' }}>NEEDS ATTENTION</div>
              <div style={{ fontFamily: 'Space Grotesk', fontSize: '1.1rem', fontWeight: 700, color: '#ff4d00' }}>{report.weakestAttr}</div>
            </div>
          )}

          {/* Recommendation */}
          {report?.recommendation && (
            <div style={{ background: 'rgba(200,255,0,0.04)', border: '1px solid rgba(200,255,0,0.12)', borderRadius: 4, padding: '1rem' }}>
              <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', letterSpacing: '0.12em', marginBottom: '0.5rem' }}>RECOMMENDED QUEST</div>
              <div style={{ fontFamily: 'Space Grotesk', fontSize: '0.875rem', color: '#f0ece4', marginBottom: '0.5rem' }}>{report.recommendation.title}</div>
              <div style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#c8ff00' }}>+{report.recommendation.xp} XP · {report.recommendation.attribute}</div>
            </div>
          )}
        </div>

        {/* Traits discovered */}
        <div style={{ background: 'rgba(10,10,10,0.9)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 6, padding: '1.75rem' }}>
          <div className="sys-label" style={{ marginBottom: '1.25rem' }}>TRAITS THIS WEEK ({report?.newTraits?.length ?? 0})</div>
          {(report?.newTraits ?? []).length === 0 ? (
            <div style={{ fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#4a4a4a' }}>No new traits discovered this week. Keep going.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {(report?.newTraits ?? []).map((t) => (
                <div key={t.name} style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', padding: '0.75rem', background: 'rgba(200,255,0,0.04)', border: '1px solid rgba(200,255,0,0.1)', borderRadius: 3 }}>
                  <span style={{ fontSize: '1.25rem' }}>{t.icon}</span>
                  <div>
                    <div style={{ fontFamily: 'Space Grotesk', fontSize: '0.85rem', fontWeight: 600, color: '#c8ff00' }}>{t.name}</div>
                    <span className={`badge badge-${t.rarity.toLowerCase()}`}>{t.rarity}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Longest streak */}
          <div style={{ marginTop: '1.5rem', paddingTop: '1.25rem', borderTop: '1px solid rgba(255,255,255,0.04)' }}>
            <div style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#4a4a4a', letterSpacing: '0.1em', marginBottom: '0.3rem' }}>LONGEST STREAK</div>
            <div style={{ fontFamily: 'Space Grotesk', fontSize: '2rem', fontWeight: 700, color: '#ff4d00' }}>{character?.longestStreak ?? 0}<span style={{ fontFamily: 'Space Mono', fontSize: '0.7rem', color: '#4a4a4a', marginLeft: '0.3rem' }}>DAYS</span></div>
          </div>
        </div>
      </div>
    </div>
  );
}
