'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Loader2, Package, Check } from 'lucide-react';

interface Item { id: string; name: string; description: string; category: string; price: number; rarity: string; icon: string; }
interface InventoryItem { id: string; equipped: boolean; purchasedAt: string; item: Item; }

export default function InventoryPage() {
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [equipping, setEquipping] = useState<string | null>(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetch('/api/inventory').then((r) => r.json()).then((d) => setInventory(d.inventory ?? [])).finally(() => setLoading(false));
  }, []);

  const handleEquip = async (itemId: string, currentlyEquipped: boolean) => {
    if (equipping) return;
    setEquipping(itemId);
    // Optimistic
    setInventory((prev) => prev.map((inv) => {
      const item = inv.item;
      if (inv.item.id === itemId) return { ...inv, equipped: !currentlyEquipped };
      // unequip others in same category
      if (!currentlyEquipped && item.category === prev.find((p) => p.item.id === itemId)?.item.category) {
        return { ...inv, equipped: false };
      }
      return inv;
    }));

    try {
      const res = await fetch('/api/inventory', { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ itemId, equip: !currentlyEquipped }) });
      if (!res.ok) {
        // Rollback
        fetch('/api/inventory').then((r) => r.json()).then((d) => setInventory(d.inventory ?? []));
        setMessage('Failed to update equipment.');
      } else {
        setMessage(!currentlyEquipped ? 'Item equipped.' : 'Item unequipped.');
      }
    } catch {
      setMessage('Connection lost.');
    } finally {
      setEquipping(null);
      setTimeout(() => setMessage(''), 2000);
    }
  };

  if (loading) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}><Loader2 size={24} color="#c8ff00" className="animate-spin" /></div>;

  return (
    <div style={{ padding: '2rem', maxWidth: 900, margin: '0 auto' }}>
      <div style={{ marginBottom: '2rem' }}>
        <div className="sys-label" style={{ marginBottom: '0.25rem' }}>OWNED ITEMS</div>
        <h1 style={{ fontFamily: 'Space Grotesk', fontSize: '2rem', fontWeight: 700, color: '#f0ece4', lineHeight: 1 }}>INVENTORY</h1>
      </div>

      {message && (
        <div style={{ marginBottom: '1rem', fontFamily: 'Space Mono', fontSize: '0.65rem', color: '#c8ff00', padding: '0.5rem 0.875rem', background: 'rgba(200,255,0,0.06)', borderRadius: 3, border: '1px solid rgba(200,255,0,0.15)' }}>
          {message}
        </div>
      )}

      {inventory.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '4rem 2rem' }}>
          <Package size={40} color="#2a2a2a" style={{ margin: '0 auto 1rem' }} />
          <div style={{ fontFamily: 'Space Mono', fontSize: '0.7rem', color: '#4a4a4a', marginBottom: '1rem' }}>Your inventory is empty. Complete quests to earn Gold.</div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '1rem' }}>
          {inventory.map((inv, i) => (
            <motion.div
              key={inv.id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.04 }}
              style={{
                background: inv.equipped ? 'rgba(200,255,0,0.04)' : 'rgba(10,10,10,0.9)',
                border: `1px solid ${inv.equipped ? 'rgba(200,255,0,0.25)' : 'rgba(255,255,255,0.06)'}`,
                borderRadius: 6, padding: '1.25rem',
                display: 'flex', flexDirection: 'column', gap: '0.75rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '1.5rem' }}>{inv.item.icon}</span>
                {inv.equipped && <Check size={14} color="#c8ff00" />}
              </div>
              <div>
                <div style={{ fontFamily: 'Space Grotesk', fontSize: '0.85rem', fontWeight: 600, color: '#f0ece4', marginBottom: '0.2rem' }}>{inv.item.name}</div>
                <div style={{ fontFamily: 'Space Mono', fontSize: '0.55rem', color: '#4a4a4a', letterSpacing: '0.08em' }}>{inv.item.category}</div>
              </div>
              <button
                onClick={() => handleEquip(inv.item.id, inv.equipped)}
                disabled={equipping === inv.item.id}
                className={inv.equipped ? 'btn btn-secondary btn-sm' : 'btn btn-primary btn-sm'}
                style={{ width: '100%', justifyContent: 'center' }}
              >
                {equipping === inv.item.id ? <Loader2 size={11} className="animate-spin" /> : inv.equipped ? 'UNEQUIP' : 'EQUIP'}
              </button>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
