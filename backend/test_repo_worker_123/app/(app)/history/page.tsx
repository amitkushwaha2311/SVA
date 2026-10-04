'use client';

import { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Loader2, Clock, TrendingUp, Zap, Star, Trophy, Award } from 'lucide-react';

interface ActivityEvent {
  id: string; type: string; metadata: Record<string, unknown>; createdAt: string;
}

const EVENT_CONFIG: Record<string, { icon: string; color: string; label: string }> = {
  QUEST_COMPLETED: { icon: '⚔️', color: '#00cfff', label: 'Quest Completed' },
  XP_GAINED: { icon: '⚡', color: '#c8ff00', label: 'XP Gained' },
  LEVEL_UP: { icon: '⬆️', color: '#c8ff00', label: 'Level Up' },
  ATTRIBUTE_INCREASED: { icon: '📈', color: '#7b8cff', label: 'Attribute Up' },
  TRAIT_UNLOCKED: { icon: '🔓', color: '#ff9500', label: 'Trait Unlocked' },
  ITEM_PURCHASED: { icon: '🛍️', color: '#e8a100', label: 'Item Purchased' },
  ITEM_EQUIPPED: { icon: '✨', color: '#e8a100', label: 'Item Equipped' },
  BOSS_DAMAGED: { icon: '⚔️', color: '#ff4d00', label: 'Boss Damaged' },
  BOSS_DEFEATED: { icon: '💀', color: '#ff4d00', label: 'Boss Defeated' },
  CAMPAIGN_COMPLETED: { icon: '🏆', color: '#c8ff00', label: 'Campaign Complete' },
  STREAK_MILESTONE: { icon: '🔥', color: '#ff9500', label: 'Streak Milestone' },
};

function formatEventDescription(event: ActivityEvent): string {
  const m = event.metadata;
  switch (event.type) {
    case 'QUEST_COMPLETED': return `Completed: ${m.questTitle ?? 'Quest'} · +${m.xpEarned ?? 0} XP · +${m.goldEarned ?? 0} G`;
    case 'LEVEL_UP': return `Level ${m.fromLevel} → ${m.toLevel} · +${m.goldBonus} GOLD`;
    case 'ATTRIBUTE_INCREASED': return `${m.attribute} +${m.gain}`;
    case 'TRAIT_UNLOCKED': return `Trait discovered: ${m.traitName}`;
    case 'BOSS_DEFEATED': return `Boss defeated: ${m.bossName} · +${m.rewardXP} XP`;
    case 'ITEM_PURCHASED': return `Purchased: ${m.itemName} · ${m.price} GOLD`;
    case 'STREAK_MILESTONE': return `Streak milestone: ${m.streak} days!`;
    default: return event.type.replace(/_/g, ' ');
  }
}

export default function HistoryPage() {
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);

  const fetchEvents = useCallback(async (cur?: string) => {
    const url = `/api/history?limit=30${cur ? `&cursor=${cur}` : ''}`;
    try {
      const res = await fetch(url);
      const data = await res.json();
      const newEvents = data.events ?? [];
      setEvents((prev) => cur ? [...prev, ...newEvents] : newEvents);
      setCursor(data.nextCursor);
      setHasMore(!!data.nextCursor);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchEvents(); }, [fetchEvents]);

  // Group by date
  const grouped: Record<string, ActivityEvent[]> = {};
  for (const ev of events) {
    const date = new Date(ev.createdAt).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
    if (!grouped[date]) grouped[date] = [];
    grouped[date].push(ev);
  }

  if (loading) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}><Loader2 size={24} color="#c8ff00" className="animate-spin" /></div>;

  return (
    <div style={{ padding: '2rem', maxWidth: 800, margin: '0 auto' }}>
      <div style={{ marginBottom: '2.5rem' }}>
        <div className="sys-label" style={{ marginBottom: '0.25rem' }}>ACTIVITY LOG</div>
        <h1 style={{ fontFamily: 'Space Grotesk', fontSize: '2rem', fontWeight: 700, color: '#f0ece4', lineHeight: 1 }}>LIFE TIMELINE</h1>
      </div>

      {events.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '4rem 2rem' }}>
          <Clock size={40} color="#2a2a2a" style={{ margin: '0 auto 1rem' }} />
          <div style={{ fontFamily: 'Space Mono', fontSize: '0.7rem', color: '#4a4a4a' }}>Your story hasn&apos;t started yet. Complete your first quest.</div>
        </div>
      ) : (
        <div style={{ position: 'relative' }}>
          {/* Timeline line */}
          <div style={{ position: 'absolute', left: 20, top: 0, bottom: 0, width: 1, background: 'rgba(255,255,255,0.04)' }} />

          {Object.entries(grouped).map(([date, dayEvents], di) => (
            <div key={date} style={{ marginBottom: '2rem' }}>
              <div style={{ fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#8a8a8a', letterSpacing: '0.12em', marginBottom: '1rem', paddingLeft: '3rem' }}>
                {date.toUpperCase()}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {dayEvents.map((ev, ei) => {
                  const cfg = EVENT_CONFIG[ev.type] ?? { icon: '●', color: '#4a4a4a', label: ev.type };
                  return (
                    <motion.div
                      key={ev.id}
                      initial={{ opacity: 0, x: -16 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: (di * 0.05 + ei * 0.03) }}
                      style={{ display: 'flex', alignItems: 'center', gap: '1rem', paddingLeft: '3rem', position: 'relative' }}
                    >
                      {/* Timeline dot */}
                      <div style={{
                        position: 'absolute', left: 14, width: 13, height: 13, borderRadius: '50%',
                        background: '#0e0e0e', border: `2px solid ${cfg.color}`,
                        display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                        fontSize: '6px',
                      }}>
                        <div style={{ width: 4, height: 4, borderRadius: '50%', background: cfg.color }} />
                      </div>

                      <div style={{ flex: 1, padding: '0.6rem 0.875rem', background: 'rgba(14,14,14,0.6)', borderRadius: 3, border: '1px solid rgba(255,255,255,0.04)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <div>
                            <span style={{ marginRight: '0.4rem' }}>{cfg.icon}</span>
                            <span style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: cfg.color, letterSpacing: '0.08em' }}>{cfg.label}</span>
                            <div style={{ fontFamily: 'Space Grotesk', fontSize: '0.8rem', color: '#8a8a8a', marginTop: '0.2rem' }}>
                              {formatEventDescription(ev)}
                            </div>
                          </div>
                          <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', flexShrink: 0 }}>
                            {new Date(ev.createdAt).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </div>
          ))}

          {hasMore && (
            <button onClick={() => fetchEvents(cursor ?? undefined)} className="btn btn-secondary" style={{ margin: '0 auto', display: 'flex', justifyContent: 'center' }}>
              LOAD MORE
            </button>
          )}
        </div>
      )}
    </div>
  );
}
