'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Loader2, ShoppingBag, Check } from 'lucide-react';

interface Item { id: string; name: string; description: string; category: string; price: number; rarity: string; icon: string; owned: boolean; }

const RARITY_ORDER = ['COMMON', 'RARE', 'EPIC', 'LEGENDARY'];

export default function ShopPage() {
  const [items, setItems] = useState<Item[]>([]);
  const [gold, setGold] = useState(0);
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState<string | null>(null);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [filter, setFilter] = useState('ALL');

  useEffect(() => {
    fetch('/api/shop').then((r) => r.json()).then((d) => {
      setItems(d.items ?? []);
      setGold(d.gold ?? 0);
    }).finally(() => setLoading(false));
  }, []);

  const handlePurchase = async (itemId: string, price: number) => {
    if (purchasing) return;
    setPurchasing(itemId);
    setMessage(null);

    // Optimistic: mark as purchasing
    try {
      const res = await fetch('/api/shop', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ itemId }) });
      const data = await res.json();
      if (!res.ok) { setMessage({ text: data.error ?? 'Purchase failed.', type: 'error' }); return; }
      setGold(data.goldRemaining);
      setItems((prev) => prev.map((item) => item.id === itemId ? { ...item, owned: true } : item));
      setMessage({ text: `${data.item.name} acquired!`, type: 'success' });
    } catch { setMessage({ text: 'Connection lost.', type: 'error' }); }
    finally { setPurchasing(null); }
  };

  const categories = ['ALL', ...new Set(items.map((i) => i.category))];
  const filteredItems = filter === 'ALL' ? items : items.filter((i) => i.category === filter);
  const sortedItems = [...filteredItems].sort((a, b) => RARITY_ORDER.indexOf(a.rarity) - RARITY_ORDER.indexOf(b.rarity));

  if (loading) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}><Loader2 size={24} color="#c8ff00" className="animate-spin" /></div>;

  return (
    <div style={{ padding: '2rem', maxWidth: 1000, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' }}>
        <div>
          <div className="sys-label" style={{ marginBottom: '0.25rem' }}>COSMETIC STORE</div>
          <h1 style={{ fontFamily: 'Space Grotesk', fontSize: '2rem', fontWeight: 700, color: '#f0ece4', lineHeight: 1 }}>SHOP</h1>
        </div>
        <div style={{ background: 'rgba(232,161,0,0.08)', border: '1px solid rgba(232,161,0,0.2)', borderRadius: 4, padding: '0.75rem 1.25rem' }}>
          <div style={{ fontFamily: 'Space Grotesk', fontSize: '1.5rem', fontWeight: 700, color: '#e8a100' }}>{gold}</div>
          <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', letterSpacing: '0.12em' }}>GOLD AVAILABLE</div>
        </div>
      </div>

      {message && (
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} style={{ marginBottom: '1.5rem', padding: '0.75rem 1rem', background: message.type === 'success' ? 'rgba(200,255,0,0.06)' : 'rgba(255,92,92,0.08)', border: `1px solid ${message.type === 'success' ? 'rgba(200,255,0,0.2)' : 'rgba(255,92,92,0.2)'}`, borderRadius: 4, fontFamily: 'Space Mono', fontSize: '0.65rem', color: message.type === 'success' ? '#c8ff00' : '#ff5c5c' }}>
          {message.text}
        </motion.div>
      )}

      {/* Category filter */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
        {categories.map((cat) => (
          <button key={cat} onClick={() => setFilter(cat)} style={{ fontFamily: 'Space Mono', fontSize: '0.6rem', letterSpacing: '0.1em', padding: '0.4rem 0.875rem', border: `1px solid ${filter === cat ? 'rgba(200,255,0,0.3)' : 'rgba(255,255,255,0.06)'}`, background: filter === cat ? 'rgba(200,255,0,0.08)' : 'transparent', color: filter === cat ? '#c8ff00' : '#8a8a8a', borderRadius: 3, cursor: 'pointer', transition: 'all 0.15s' }}>
            {cat}
          </button>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem' }}>
        {sortedItems.map((item, i) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            style={{
              background: 'rgba(10,10,10,0.9)',
              border: `1px solid ${item.owned ? 'rgba(200,255,0,0.2)' : 'rgba(255,255,255,0.06)'}`,
              borderRadius: 6, padding: '1.5rem',
              display: 'flex', flexDirection: 'column', gap: '0.875rem',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '1.75rem' }}>{item.icon}</span>
              <span className={`badge badge-${item.rarity.toLowerCase()}`}>{item.rarity}</span>
            </div>
            <div>
              <div style={{ fontFamily: 'Space Grotesk', fontSize: '0.9rem', fontWeight: 600, color: '#f0ece4', marginBottom: '0.3rem' }}>{item.name}</div>
              <div style={{ fontFamily: 'Space Grotesk', fontSize: '0.75rem', color: '#8a8a8a', lineHeight: 1.5 }}>{item.description}</div>
            </div>
            <div style={{ marginTop: 'auto' }}>
              {item.owned ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#c8ff00', letterSpacing: '0.08em' }}>
                  <Check size={12} /> OWNED
                </div>
              ) : (
                <button
                  onClick={() => handlePurchase(item.id, item.price)}
                  disabled={purchasing === item.id || gold < item.price}
                  className="btn btn-primary btn-sm"
                  style={{ width: '100%', justifyContent: 'center', opacity: gold < item.price ? 0.5 : 1 }}
                >
                  {purchasing === item.id ? <Loader2 size={11} className="animate-spin" /> : `${item.price} GOLD`}
                </button>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
