'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, X, Loader2, Sword, Trophy } from 'lucide-react';

interface DamageEvent { id: string; damage: number; createdAt: string; quest: { title: string; attribute: string } | null; }
interface Boss { id: string; name: string; description: string; maxHP: number; currentHP: number; rewardXP: number; rewardGold: number; status: string; damageEvents: DamageEvent[]; createdAt: string; }

function CreateBossModal({ onClose, onCreated }: { onClose: () => void; onCreated: (b: Boss) => void }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [maxHP, setMaxHP] = useState(1000);
  const [rewardXP, setRewardXP] = useState(500);
  const [rewardGold, setRewardGold] = useState(200);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) { setError('Every boss needs a name.'); return; }
    setLoading(true); setError('');
    try {
      const res = await fetch('/api/bosses', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: name.trim(), description, maxHP, rewardXP, rewardGold }) });
      const data = await res.json();
      if (!res.ok) { setError(data.error ?? 'Failed.'); return; }
      onCreated(data.boss);
      onClose();
    } catch { setError('Failed.'); }
    finally { setLoading(false); }
  };

  return (
    <motion.div className="modal-overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose}>
      <motion.div className="modal" initial={{ scale: 0.9 }} animate={{ scale: 1 }} exit={{ scale: 0.9 }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
          <div><div className="sys-label" style={{ marginBottom: '0.25rem' }}>SUMMON BOSS</div><h2 style={{ fontFamily: 'Space Grotesk', fontSize: '1.25rem', fontWeight: 700, color: '#f0ece4' }}>Create Boss</h2></div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#4a4a4a' }}><X size={16} /></button>
        </div>
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}><label className="label">BOSS NAME</label><input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="PROCRASTINATION" autoFocus /></div>
          <div style={{ marginBottom: '1rem' }}><label className="label">DESCRIPTION</label><textarea className="input" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="What are you fighting against?" rows={2} style={{ resize: 'vertical' }} /></div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.75rem', marginBottom: '1.5rem' }}>
            <div><label className="label">MAX HP</label><input type="number" className="input" value={maxHP} onChange={(e) => setMaxHP(Number(e.target.value))} min={100} max={10000} step={100} /></div>
            <div><label className="label">REWARD XP</label><input type="number" className="input" value={rewardXP} onChange={(e) => setRewardXP(Number(e.target.value))} min={0} /></div>
            <div><label className="label">REWARD GOLD</label><input type="number" className="input" value={rewardGold} onChange={(e) => setRewardGold(Number(e.target.value))} min={0} /></div>
          </div>
          {error && <div style={{ marginBottom: '1rem', fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#ff5c5c' }}>{error}</div>}
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button type="button" onClick={onClose} className="btn btn-secondary" style={{ flex: 1, justifyContent: 'center' }}>CANCEL</button>
            <button type="submit" className="btn btn-primary" disabled={loading} style={{ flex: 2, justifyContent: 'center' }}>
              {loading ? <><Loader2 size={12} className="animate-spin" /> SUMMONING...</> : 'SUMMON BOSS →'}
            </button>
          </div>
        </form>
      </motion.div>
    </motion.div>
  );
}

export default function BossesPage() {
  const [bosses, setBosses] = useState<Boss[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);

  useEffect(() => {
    fetch('/api/bosses').then((r) => r.json()).then((d) => setBosses(d.bosses ?? [])).finally(() => setLoading(false));
  }, []);

  const activeBosses = bosses.filter((b) => b.status === 'ACTIVE');
  const defeatedBosses = bosses.filter((b) => b.status === 'DEFEATED');

  return (
    <div style={{ padding: '2rem', maxWidth: 900, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2.5rem' }}>
        <div>
          <div className="sys-label" style={{ marginBottom: '0.25rem' }}>BOSS ENCOUNTERS</div>
          <h1 style={{ fontFamily: 'Space Grotesk', fontSize: '2rem', fontWeight: 700, color: '#f0ece4', lineHeight: 1 }}>BOSSES</h1>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn btn-primary"><Plus size={14} /> SUMMON BOSS</button>
      </div>

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}><Loader2 size={24} color="#c8ff00" className="animate-spin" /></div>
      ) : (
        <>
          {/* Active Bosses */}
          {activeBosses.length > 0 && (
            <div style={{ marginBottom: '2rem' }}>
              <div className="sys-label" style={{ marginBottom: '1rem' }}>ACTIVE — {activeBosses.length}</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {activeBosses.map((boss, i) => {
                  const hpPct = Math.max(0, Math.min(100, (boss.currentHP / boss.maxHP) * 100));
                  return (
                    <motion.div key={boss.id} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }} style={{ background: 'rgba(10,10,10,0.9)', border: '1px solid rgba(255,77,0,0.15)', borderRadius: 6, padding: '1.75rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
                        <div>
                          <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', letterSpacing: '0.15em', marginBottom: '0.25rem' }}>BOSS</div>
                          <h2 style={{ fontFamily: 'Space Grotesk', fontSize: '1.75rem', fontWeight: 700, color: '#ff4d00' }}>{boss.name}</h2>
                          {boss.description && <p style={{ fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#8a8a8a', marginTop: '0.25rem' }}>{boss.description}</p>}
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <div style={{ fontFamily: 'Space Grotesk', fontSize: '1.5rem', fontWeight: 700, color: '#ff4d00' }}>{boss.currentHP}</div>
                          <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a' }}>/ {boss.maxHP} HP</div>
                        </div>
                      </div>

                      {/* HP Bar */}
                      <div style={{ marginBottom: '1.5rem' }}>
                        <div style={{ height: 6, background: '#1a1a1a', borderRadius: 3, overflow: 'hidden' }}>
                          <motion.div
                            animate={{ width: `${hpPct}%` }}
                            transition={{ duration: 0.8, ease: 'easeOut' }}
                            style={{ height: '100%', background: hpPct > 60 ? '#ff4d00' : hpPct > 30 ? '#ff9500' : '#c8ff00', borderRadius: 3 }}
                          />
                        </div>
                        <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', marginTop: '0.3rem' }}>{hpPct.toFixed(1)}% HP remaining</div>
                      </div>

                      {/* Recent damage */}
                      {boss.damageEvents.length > 0 && (
                        <div>
                          <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', letterSpacing: '0.12em', marginBottom: '0.5rem' }}>RECENT HITS</div>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                            {boss.damageEvents.slice(0, 3).map((ev) => (
                              <div key={ev.id} style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#8a8a8a', display: 'flex', justifyContent: 'space-between' }}>
                                <span>{ev.quest?.title ?? 'Quest'}</span>
                                <span style={{ color: '#ff4d00' }}>-{ev.damage} HP</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <div style={{ marginTop: '1rem', fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#4a4a4a' }}>
                        Complete quests to deal damage. Defeat by reaching 0 HP.
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Defeated Bosses */}
          {defeatedBosses.length > 0 && (
            <div>
              <div className="sys-label" style={{ marginBottom: '1rem' }}>DEFEATED — {defeatedBosses.length}</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {defeatedBosses.map((boss) => (
                  <div key={boss.id} style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem 1.25rem', background: 'rgba(14,14,14,0.5)', border: '1px solid rgba(200,255,0,0.08)', borderRadius: 4 }}>
                    <Trophy size={16} color="#c8ff00" />
                    <div style={{ flex: 1 }}>
                      <span style={{ fontFamily: 'Space Grotesk', fontSize: '0.95rem', color: '#4a4a4a', textDecoration: 'line-through' }}>{boss.name}</span>
                    </div>
                    <span style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#c8ff00', letterSpacing: '0.1em' }}>DEFEATED</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {bosses.length === 0 && (
            <div style={{ textAlign: 'center', padding: '4rem 2rem' }}>
              <Sword size={40} color="#2a2a2a" style={{ margin: '0 auto 1rem' }} />
              <div style={{ fontFamily: 'Space Mono', fontSize: '0.7rem', color: '#4a4a4a', marginBottom: '1rem' }}>No bosses yet. Every goal has one.</div>
              <button onClick={() => setShowCreate(true)} className="btn btn-primary btn-sm"><Plus size={12} /> SUMMON FIRST BOSS</button>
            </div>
          )}
        </>
      )}

      <AnimatePresence>
        {showCreate && <CreateBossModal onClose={() => setShowCreate(false)} onCreated={(b) => setBosses((prev) => [b, ...prev])} />}
      </AnimatePresence>
    </div>
  );
}
