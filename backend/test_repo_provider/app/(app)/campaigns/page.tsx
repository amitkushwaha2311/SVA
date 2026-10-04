'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, X, Loader2, Map, Zap } from 'lucide-react';

interface CampaignStage { id: string; name: string; description: string; order: number; status: string; }
interface Campaign { id: string; name: string; description: string; status: string; progress: number; stages: CampaignStage[]; createdAt: string; }

function ForgeModal({ onClose, onCreated }: { onClose: () => void; onCreated: (c: Campaign) => void }) {
  const [goal, setGoal] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleForge = async () => {
    if (!goal.trim()) { setError('Describe your goal.'); return; }
    setLoading(true); setError('');
    try {
      const res = await fetch('/api/forge', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ goal, createCampaign: true }) });
      const data = await res.json();
      if (!res.ok) { setError(data.error ?? 'Failed.'); return; }
      onCreated(data.campaign);
      onClose();
    } catch { setError('Failed. Try again.'); }
    finally { setLoading(false); }
  };

  return (
    <motion.div className="modal-overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose}>
      <motion.div className="modal" initial={{ scale: 0.9 }} animate={{ scale: 1 }} exit={{ scale: 0.9 }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
          <div>
            <div className="sys-label" style={{ marginBottom: '0.25rem' }}>QUEST FORGE</div>
            <h2 style={{ fontFamily: 'Space Grotesk', fontSize: '1.25rem', fontWeight: 700, color: '#f0ece4' }}>Generate Campaign</h2>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#4a4a4a' }}><X size={16} /></button>
        </div>
        <p style={{ fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#8a8a8a', marginBottom: '1.5rem', lineHeight: 1.6 }}>
          Describe your goal and QUEST FORGE will generate a full campaign with stages and quests.
        </p>
        <label className="label">YOUR GOAL</label>
        <textarea className="input" value={goal} onChange={(e) => setGoal(e.target.value)} placeholder="I want to become a full-stack developer..." rows={3} style={{ marginBottom: '1.5rem', resize: 'vertical' }} />
        {error && <div style={{ marginBottom: '1rem', fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#ff5c5c' }}>{error}</div>}
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button onClick={onClose} className="btn btn-secondary" style={{ flex: 1, justifyContent: 'center' }}>CANCEL</button>
          <button onClick={handleForge} className="btn btn-primary" disabled={loading} style={{ flex: 2, justifyContent: 'center' }}>
            {loading ? <><Loader2 size={12} className="animate-spin" /> FORGING...</> : '⚡ FORGE CAMPAIGN →'}
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

const STAGE_STATUS_STYLES: Record<string, { color: string; bg: string }> = {
  LOCKED: { color: '#4a4a4a', bg: 'rgba(255,255,255,0.03)' },
  ACTIVE: { color: '#c8ff00', bg: 'rgba(200,255,0,0.06)' },
  COMPLETED: { color: '#00e5a0', bg: 'rgba(0,229,160,0.06)' },
};

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForge, setShowForge] = useState(false);

  useEffect(() => {
    fetch('/api/campaigns').then((r) => r.json()).then((d) => setCampaigns(d.campaigns ?? [])).finally(() => setLoading(false));
  }, []);

  return (
    <div style={{ padding: '2rem', maxWidth: 900, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2.5rem' }}>
        <div>
          <div className="sys-label" style={{ marginBottom: '0.25rem' }}>LONG-TERM GOALS</div>
          <h1 style={{ fontFamily: 'Space Grotesk', fontSize: '2rem', fontWeight: 700, color: '#f0ece4', lineHeight: 1 }}>CAMPAIGNS</h1>
        </div>
        <button onClick={() => setShowForge(true)} className="btn btn-primary"><Zap size={14} /> QUEST FORGE</button>
      </div>

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}><Loader2 size={24} color="#c8ff00" className="animate-spin" /></div>
      ) : campaigns.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '4rem 2rem' }}>
          <Map size={40} color="#2a2a2a" style={{ margin: '0 auto 1rem' }} />
          <div style={{ fontFamily: 'Space Mono', fontSize: '0.7rem', color: '#4a4a4a', marginBottom: '1rem' }}>Choose a long-term goal and begin your campaign.</div>
          <button onClick={() => setShowForge(true)} className="btn btn-primary btn-sm"><Zap size={12} /> FORGE WITH AI</button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {campaigns.map((campaign, i) => (
            <motion.div key={campaign.id} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }} style={{ background: 'rgba(10,10,10,0.9)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 6, padding: '1.75rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
                <div>
                  <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', letterSpacing: '0.15em', marginBottom: '0.3rem' }}>
                    CAMPAIGN {String(i + 1).padStart(2, '0')}
                  </div>
                  <h2 style={{ fontFamily: 'Space Grotesk', fontSize: '1.25rem', fontWeight: 700, color: '#f0ece4' }}>{campaign.name}</h2>
                  {campaign.description && <p style={{ fontFamily: 'Space Grotesk', fontSize: '0.8rem', color: '#8a8a8a', marginTop: '0.25rem' }}>{campaign.description}</p>}
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontFamily: 'Space Grotesk', fontSize: '1.5rem', fontWeight: 700, color: '#c8ff00' }}>{campaign.progress}%</div>
                  <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', letterSpacing: '0.1em' }}>COMPLETE</div>
                </div>
              </div>

              {/* Progress bar */}
              <div style={{ marginBottom: '1.5rem' }}>
                <div style={{ height: 4, background: '#1a1a1a', borderRadius: 2, overflow: 'hidden' }}>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${campaign.progress}%` }}
                    transition={{ duration: 1.2, ease: 'easeOut' }}
                    style={{ height: '100%', background: 'linear-gradient(90deg, #c8ff00, #00cfff)', borderRadius: 2 }}
                  />
                </div>
              </div>

              {/* Stages */}
              {campaign.stages.length > 0 && (
                <div style={{ display: 'flex', gap: '0', flexWrap: 'wrap' }}>
                  {campaign.stages.map((stage, si) => {
                    const style = STAGE_STATUS_STYLES[stage.status] ?? STAGE_STATUS_STYLES.LOCKED;
                    return (
                      <div key={stage.id} style={{ flex: 1, minWidth: 100, padding: '0.75rem', background: style.bg, borderRight: si < campaign.stages.length - 1 ? '1px solid rgba(255,255,255,0.04)' : 'none', borderTop: '1px solid rgba(255,255,255,0.04)' }}>
                        <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', letterSpacing: '0.1em', marginBottom: '0.2rem' }}>STAGE {stage.order.toString().padStart(2, '0')}</div>
                        <div style={{ fontFamily: 'Space Grotesk', fontSize: '0.75rem', color: style.color, fontWeight: 500 }}>{stage.name}</div>
                        <div style={{ fontFamily: 'Space Mono', fontSize: '0.5rem', color: '#4a4a4a', marginTop: '0.2rem', letterSpacing: '0.1em' }}>
                          {stage.status === 'COMPLETED' ? '✓ DONE' : stage.status === 'ACTIVE' ? '● ACTIVE' : '○ LOCKED'}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </motion.div>
          ))}
        </div>
      )}

      <AnimatePresence>
        {showForge && <ForgeModal onClose={() => setShowForge(false)} onCreated={(c) => setCampaigns((prev) => [c, ...prev])} />}
      </AnimatePresence>
    </div>
  );
}
