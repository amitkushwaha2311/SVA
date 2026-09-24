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

  if (!health) return <div>Loading...</div>;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'HEALTHY': return <ShieldCheck className="text-green-500 w-5 h-5" />;
      case 'DEGRADED': return <ShieldAlert className="text-yellow-500 w-5 h-5" />;
      case 'UNAVAILABLE': return <ShieldX className="text-red-500 w-5 h-5" />;
      default: return <HelpCircle className="text-gray-500 w-5 h-5" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'HEALTHY': return 'bg-green-100 text-green-800 border-green-200';
      case 'DEGRADED': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'UNAVAILABLE': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold tracking-tight">Diagnostics & Observability</h2>
      
      <div className="border border-white/10 rounded-xl overflow-hidden bg-white/5">
        <div className="px-5 py-4 border-b border-white/10 flex items-center justify-between">
          <h3 className="text-sm font-medium text-white flex items-center gap-2">
            System Health 
            <span className={`px-2 py-0.5 rounded text-xs font-mono border ${getStatusColor(health.status)}`}>
              {health.status}
            </span>
          </h3>
        </div>
        <div className="p-5">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(health.components).map(([name, status]) => (
              <div key={name} className="flex items-center justify-between p-3 border border-white/10 rounded-lg bg-black/40">
                <span className="capitalize font-medium text-gray-200 text-sm">{name}</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-gray-400">{status}</span>
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
