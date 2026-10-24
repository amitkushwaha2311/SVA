import React, { useEffect, useState } from 'react';
import { ShieldCheck, ShieldAlert, ShieldX, HelpCircle } from 'lucide-react';

interface HealthData {
  status: string;
  components: Record<string, string>;
  timestamp: string;
}

export function Diagnostics() {
  const [health, setHealth] = useState<HealthData | null>(null);

  useEffect(() => {
    // In real app, fetch from /api/v1/observability/health
    const mockHealth: HealthData = {
      status: "HEALTHY",
      components: {
        api: "HEALTHY",
        database: "HEALTHY",
        worker: "HEALTHY",
        sandbox: "HEALTHY"
      },
      timestamp: new Date().toISOString()
    };
    setHealth(mockHealth);
  }, []);

  if (!health) {
    return (
      <div className="p-8 text-center text-[#B5AA9C] font-mono text-sm">
        Loading system diagnostics...
      </div>
    );
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'HEALTHY': return <ShieldCheck className="text-[#10B981] w-4 h-4" />;
      case 'DEGRADED': return <ShieldAlert className="text-[#F59E0B] w-4 h-4" />;
      case 'UNAVAILABLE': return <ShieldX className="text-[#EF4444] w-4 h-4" />;
      default: return <HelpCircle className="text-[#9CA3AF] w-4 h-4" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'HEALTHY': return 'bg-[#10B981]/15 text-[#34D399] border-[#10B981]/30';
      case 'DEGRADED': return 'bg-[#F59E0B]/15 text-[#FBBF24] border-[#F59E0B]/30';
      case 'UNAVAILABLE': return 'bg-[#EF4444]/15 text-[#F87171] border-[#EF4444]/30';
      default: return 'bg-[#2A221B] text-[#9CA3AF] border-[#514236]';
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-serif text-[#F5EFE5] tracking-tight">Diagnostics & Observability</h2>
      
      <div className="border border-[#514236] rounded-xl overflow-hidden bg-[#211B16] shadow-sm">
        <div className="px-5 py-4 border-b border-[#514236] flex items-center justify-between bg-[#2A221B]/40">
          <h3 className="text-sm font-medium text-[#F5EFE5] flex items-center gap-2.5">
            System Health 
            <span className={`px-2 py-0.5 rounded text-[11px] font-mono border ${getStatusColor(health.status)}`}>
              {health.status}
            </span>
          </h3>
        </div>
        <div className="p-5">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(health.components).map(([name, status]) => (
              <div key={name} className="flex items-center justify-between p-3.5 border border-[#514236]/80 rounded-lg bg-[#2A221B]/60">
                <span className="capitalize font-medium text-[#F5EFE5] text-sm">{name}</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-medium text-[#B5AA9C]">{status}</span>
                  {getStatusIcon(status)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
