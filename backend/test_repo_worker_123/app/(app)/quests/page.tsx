'use client';

import { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, X, Loader2, CheckCircle2, Trash2, Target } from 'lucide-react';

interface Quest {
  id: string; title: string; description: string; attribute: string;
  difficulty: string; xpReward: number; goldReward: number; status: string;
  dueDate: string | null; createdAt: string;
}

const ATTRS = ['INTELLECT', 'STRENGTH', 'DISCIPLINE', 'CREATIVITY', 'SOCIAL', 'RECOVERY'];
const DIFFS = ['EASY', 'MEDIUM', 'HARD', 'EPIC'];
const ATTR_COLORS: Record<string, string> = {
  INTELLECT: '#7b8cff', STRENGTH: '#ff5c5c', DISCIPLINE: '#c8ff00',
  CREATIVITY: '#ff9500', SOCIAL: '#00e5a0', RECOVERY: '#b066ff',
};
const DIFF_COLORS: Record<string, string> = {
  EASY: '#00e5a0', MEDIUM: '#00cfff', HARD: '#ff9500', EPIC: '#ff4d00',
};

function CreateQuestModal({ onClose, onCreated }: { onClose: () => void; onCreated: (q: Quest) => void }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [attribute, setAttribute] = useState('INTELLECT');
  const [difficulty, setDifficulty] = useState('MEDIUM');
  const [dueDate, setDueDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) { setError('Every quest needs a name.'); return; }
    setLoading(true); setError('');

    try {
      const res = await fetch('/api/quests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: title.trim(), description, attribute, difficulty, dueDate: dueDate || null }),
      });
      const data = await res.json();
      if (!res.ok) { setError(data.error ?? 'Failed to create quest.'); return; }
      onCreated(data.quest);
      onClose();
    } catch {
      setError('Connection lost. Try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div className="modal-overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose}>
      <motion.div className="modal" initial={{ scale: 0.9, y: 20 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.9, y: 20 }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <div>
            <div className="sys-label" style={{ marginBottom: '0.25rem' }}>QUEST FORGE</div>
            <h2 style={{ fontFamily: 'Space Grotesk', fontSize: '1.25rem', fontWeight: 700, color: '#f0ece4' }}>New Quest</h2>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#4a4a4a' }}><X size={16} /></button>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label className="label" htmlFor="quest-title">QUEST TITLE</label>
            <input id="quest-title" className="input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="What will you conquer?" autoFocus />
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <label className="label" htmlFor="quest-desc">DESCRIPTION</label>
            <textarea id="quest-desc" className="input" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional details..." rows={2} style={{ resize: 'vertical' }} />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label className="label">ATTRIBUTE</label>
              <select className="input select" value={attribute} onChange={(e) => setAttribute(e.target.value)}>
                {ATTRS.map((a) => <option key={a} value={a}>{a}</option>)}
              </select>
            </div>
            <div>
              <label className="label">DIFFICULTY</label>
              <select className="input select" value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
                {DIFFS.map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label className="label" htmlFor="quest-due">DUE DATE (OPTIONAL)</label>
            <input id="quest-due" type="datetime-local" className="input" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
          </div>

          {/* Rewards preview */}
          <div style={{ padding: '0.75rem', background: 'rgba(20,20,20,0.6)', borderRadius: 4, marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-around' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontFamily: 'Space Mono', fontSize: '0.7rem', color: '#00cfff' }}>
                +{difficulty === 'EASY' ? 30 : difficulty === 'MEDIUM' ? 60 : difficulty === 'HARD' ? 120 : 250} XP
              </div>
              <div className="sys-label">REWARD</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontFamily: 'Space Mono', fontSize: '0.7rem', color: '#e8a100' }}>
                +{difficulty === 'EASY' ? 10 : difficulty === 'MEDIUM' ? 25 : difficulty === 'HARD' ? 60 : 150} G
              </div>
              <div className="sys-label">GOLD</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontFamily: 'Space Mono', fontSize: '0.7rem', color: ATTR_COLORS[attribute] }}>
                {attribute.slice(0, 4)}
              </div>
              <div className="sys-label">ATTR</div>
            </div>
          </div>

          {error && <div style={{ marginBottom: '1rem', fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#ff5c5c', padding: '0.5rem', background: 'rgba(255,92,92,0.08)', borderRadius: 3 }}>{error}</div>}

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button type="button" onClick={onClose} className="btn btn-secondary" style={{ flex: 1, justifyContent: 'center' }}>CANCEL</button>
            <button type="submit" className="btn btn-primary" disabled={loading} style={{ flex: 2, justifyContent: 'center' }}>
              {loading ? <><Loader2 size={12} className="animate-spin" /> FORGING...</> : 'FORGE QUEST →'}
            </button>
          </div>
        </form>
      </motion.div>
    </motion.div>
  );
}

export default function QuestsPage() {
  const [quests, setQuests] = useState<Quest[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [completing, setCompleting] = useState<string | null>(null);
  const [filter, setFilter] = useState<'ACTIVE' | 'COMPLETED'>('ACTIVE');
  const fetchQuests = useCallback(async () => {
    try {
      const res = await fetch(`/api/quests?status=${filter}`);
      const data = await res.json();
      setQuests(data.quests ?? []);
    } catch {
      // handle fetch error
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    let mounted = true;
    fetch(`/api/quests?status=${filter}`)
      .then((res) => res.json())
      .then((data) => {
        if (mounted) {
          setQuests(data.quests ?? []);
          setLoading(false);
        }
      })
      .catch(() => {
        if (mounted) setLoading(false);
      });
    return () => { mounted = false; };
  }, [filter]);

  const handleComplete = async (questId: string) => {
    if (completing) return;
    setCompleting(questId);
    setQuests((prev) => prev.filter((q) => q.id !== questId));
    try {
      const res = await fetch(`/api/quests/${questId}/complete`, { method: 'POST' });
      if (!res.ok) { fetchQuests(); }
    } catch { fetchQuests(); }
    finally { setCompleting(null); }
  };

  const handleDelete = async (questId: string) => {
    if (!confirm('Delete this quest?')) return;
    setQuests((prev) => prev.filter((q) => q.id !== questId));
    await fetch(`/api/quests/${questId}`, { method: 'DELETE' });
  };

  return (
    <div style={{ padding: '2rem', maxWidth: 900, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' }}>
        <div>
          <div className="sys-label" style={{ marginBottom: '0.25rem' }}>QUEST LOG</div>
          <h1 style={{ fontFamily: 'Space Grotesk', fontSize: '2rem', fontWeight: 700, color: '#f0ece4', lineHeight: 1 }}>QUESTS</h1>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn btn-primary">
          <Plus size={14} /> FORGE QUEST
        </button>
      </div>

      {/* Filter tabs */}
      <div style={{ display: 'flex', gap: '0', marginBottom: '1.5rem', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 4, overflow: 'hidden', width: 'fit-content' }}>
        {(['ACTIVE', 'COMPLETED'] as const).map((tab) => (
          <button key={tab} onClick={() => setFilter(tab)} style={{
            fontFamily: 'Space Mono', fontSize: '0.65rem', letterSpacing: '0.1em',
            padding: '0.5rem 1.25rem', border: 'none', cursor: 'pointer',
            background: filter === tab ? 'rgba(200,255,0,0.12)' : 'transparent',
            color: filter === tab ? '#c8ff00' : '#8a8a8a',
            transition: 'all 0.15s',
          }}>{tab}</button>
        ))}
      </div>

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}><Loader2 size={24} color="#c8ff00" className="animate-spin" /></div>
      ) : quests.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '4rem 2rem' }}>
          <Target size={40} color="#2a2a2a" style={{ margin: '0 auto 1rem' }} />
          <div style={{ fontFamily: 'Space Mono', fontSize: '0.7rem', color: '#4a4a4a', marginBottom: '1rem' }}>
            {filter === 'ACTIVE' ? 'Your adventure begins with one quest.' : 'No completed quests yet.'}
          </div>
          {filter === 'ACTIVE' && (
            <button onClick={() => setShowCreate(true)} className="btn btn-primary btn-sm">
              <Plus size={12} /> CREATE QUEST
            </button>
          )}
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <AnimatePresence>
            {quests.map((quest, i) => (
              <motion.div
                key={quest.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                transition={{ delay: i * 0.04 }}
                style={{
                  display: 'flex', alignItems: 'center', gap: '1rem',
                  padding: '1.1rem 1.25rem',
                  background: quest.status === 'COMPLETED' ? 'rgba(14,14,14,0.5)' : 'rgba(14,14,14,0.8)',
                  border: `1px solid ${quest.status === 'COMPLETED' ? 'rgba(200,255,0,0.08)' : 'rgba(255,255,255,0.06)'}`,
                  borderRadius: 4,
                }}
              >
                {/* Complete button or check */}
                {filter === 'ACTIVE' ? (
                  <button
                    onClick={() => handleComplete(quest.id)}
                    disabled={completing === quest.id}
                    aria-label={`Complete: ${quest.title}`}
                    style={{
                      width: 24, height: 24, borderRadius: 4, flexShrink: 0,
                      border: '1px solid rgba(255,255,255,0.15)',
                      background: 'transparent', cursor: 'pointer', display: 'flex',
                      alignItems: 'center', justifyContent: 'center',
                    }}
                  >
                    {completing === quest.id ? <Loader2 size={12} className="animate-spin" color="#c8ff00" /> : <CheckCircle2 size={12} color="#4a4a4a" />}
                  </button>
                ) : (
                  <div style={{ width: 24, height: 24, borderRadius: 4, background: 'rgba(200,255,0,0.1)', border: '1px solid rgba(200,255,0,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <span style={{ fontSize: 10, color: '#c8ff00' }}>✓</span>
                  </div>
                )}

                {/* Attr color bar */}
                <div style={{ width: 3, height: 32, background: ATTR_COLORS[quest.attribute] ?? '#8a8a8a', borderRadius: 2, flexShrink: 0, opacity: quest.status === 'COMPLETED' ? 0.4 : 1 }} />

                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontFamily: 'Space Grotesk', fontSize: '0.95rem', color: quest.status === 'COMPLETED' ? '#4a4a4a' : '#f0ece4', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', textDecoration: quest.status === 'COMPLETED' ? 'line-through' : 'none' }}>
                    {quest.title}
                  </div>
                  <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', marginTop: '0.2rem', letterSpacing: '0.08em', display: 'flex', gap: '0.75rem' }}>
                    <span style={{ color: ATTR_COLORS[quest.attribute] }}>{quest.attribute}</span>
                    <span style={{ color: DIFF_COLORS[quest.difficulty] }}>{quest.difficulty}</span>
                    {quest.dueDate && <span>DUE {new Date(quest.dueDate).toLocaleDateString()}</span>}
                  </div>
                </div>

                <div style={{ textAlign: 'right', flexShrink: 0 }}>
                  <div style={{ fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#00cfff' }}>+{quest.xpReward} XP</div>
                  <div style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', color: '#e8a100' }}>+{quest.goldReward} G</div>
                </div>

                {filter === 'ACTIVE' && (
                  <button
                    onClick={() => handleDelete(quest.id)}
                    aria-label="Delete quest"
                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#4a4a4a', flexShrink: 0, padding: '0.25rem' }}
                    onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.color = '#ff5c5c'; }}
                    onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.color = '#4a4a4a'; }}
                  >
                    <Trash2 size={14} />
                  </button>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      <AnimatePresence>
        {showCreate && <CreateQuestModal onClose={() => setShowCreate(false)} onCreated={(q) => setQuests((prev) => [q, ...prev])} />}
      </AnimatePresence>
    </div>
  );
}
