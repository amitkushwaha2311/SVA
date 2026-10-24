'use client';

import React, { useState, useEffect } from 'react';
import { Shield, GitBranch, Server, AlertCircle, Plus, Key, RefreshCw, X } from 'lucide-react';
import { apiFetch } from '@/lib/api';

interface ProviderConnection {
  id: string;
  workspace_id: string;
  provider: string;
  connection_identity: string | null;
  status: string;
  created_at: string;
  last_validated_at: string | null;
}

export function ProviderConnections({ workspaceId }: { workspaceId: string }) {
  const [connections, setConnections] = useState<ProviderConnection[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<'github' | 'gitlab' | null>(null);

  // Form State
  const [repoUrl, setRepoUrl] = useState('');
  const [token, setToken] = useState('');
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchConnections();
  }, [workspaceId]);

  const fetchConnections = async () => {
    setIsLoading(true);
    try {
      const response = await apiFetch<ProviderConnection[]>(`/v1/integrations/${workspaceId}/connections`);
      setConnections(response);
    } catch (err) {
      console.error('Failed to fetch connections', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProvider) return;
    
    setIsConnecting(true);
    setError(null);
    try {
      await apiFetch(`/v1/integrations/${workspaceId}/connections`, {
        method: 'POST',
        body: JSON.stringify({
          provider: selectedProvider,
          repository_url: repoUrl,
          token: token,
        }),
      });
      setIsModalOpen(false);
      setRepoUrl('');
      setToken('');
      fetchConnections();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to connect provider.');
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDisconnect = async (connectionId: string) => {
    if (!confirm('Are you sure you want to revoke this connection?')) return;
    try {
      await apiFetch(`/v1/integrations/${workspaceId}/connections/${connectionId}`, { method: 'DELETE' });
      fetchConnections();
    } catch (err) {
      console.error('Failed to disconnect', err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
        <div>
          <h2 className="text-xl font-serif text-[#F5EFE5] flex items-center gap-2.5">
            <Server className="w-5 h-5 text-[#F4D9A0]" />
            Enterprise Integrations
          </h2>
          <p className="text-sm text-[#B5AA9C] mt-1 font-sans">
            Securely connect external repository providers. Credentials are encrypted at rest and never exposed.
          </p>
        </div>
        <button
          onClick={() => {
            setSelectedProvider('github');
            setIsModalOpen(true);
          }}
          className="bg-[#F4D9A0] hover:bg-[#fae6bb] text-[#17130F] text-sm font-semibold px-4 py-2.5 rounded-xl flex items-center gap-2 transition-all shadow-md shadow-[#F4D9A0]/10 shrink-0 self-start sm:self-auto active:scale-95"
        >
          <Plus className="w-4 h-4" />
          Add Connection
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center items-center h-32">
          <RefreshCw className="w-6 h-6 text-[#F4D9A0] animate-spin" />
        </div>
      ) : connections.length === 0 ? (
        <div className="border border-[#514236] bg-[#211B16] rounded-2xl p-10 text-center shadow-xl">
          <Shield className="w-12 h-12 text-[#847768] mx-auto mb-3 opacity-60" />
          <h3 className="text-[#F5EFE5] font-serif text-base mb-1 font-medium">No Integrations Connected</h3>
          <p className="text-[#B5AA9C] text-sm max-w-sm mx-auto leading-relaxed">
            Connect GitHub or GitLab to enable secure, verified analysis of your repositories and webhook processing.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {connections.map((conn) => (
            <div key={conn.id} className="border border-[#514236] bg-[#211B16] rounded-2xl p-5 shadow-xl relative overflow-hidden group">
              <div className="flex items-start justify-between relative z-10">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-[#2A221B] rounded-xl border border-[#514236]">
                    <GitBranch className="w-5 h-5 text-[#F4D9A0]" />
                  </div>
                  <div>
                    <h3 className="text-[#F5EFE5] font-serif text-base capitalize">{conn.provider}</h3>
                    <p className="text-xs font-mono text-[#847768] truncate max-w-[200px]">{conn.connection_identity}</p>
                  </div>
                </div>
                
                <span className={`px-2.5 py-1 rounded-full text-[10px] font-mono tracking-wider uppercase border font-medium ${
                  conn.status === 'CONNECTED' ? 'bg-[#10B981]/10 text-[#10B981] border-[#10B981]/30' :
                  conn.status === 'REVOKED' ? 'bg-[#EF4444]/10 text-[#EF4444] border-[#EF4444]/30' :
                  'bg-[#9CA3AF]/10 text-[#9CA3AF] border-[#9CA3AF]/30'
                }`}>
                  {conn.status}
                </span>
              </div>

              <div className="mt-6 flex items-center justify-between relative z-10">
                <div className="text-xs font-mono text-[#847768]">
                  Added {new Date(conn.created_at).toLocaleDateString()}
                </div>
                {conn.status === 'CONNECTED' && (
                  <button 
                    onClick={() => handleDisconnect(conn.id)}
                    className="text-xs font-medium text-[#EF4444] hover:text-[#f87171] transition-colors bg-[#EF4444]/10 hover:bg-[#EF4444]/20 border border-[#EF4444]/30 px-3 py-1.5 rounded-lg"
                  >
                    Disconnect
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Connect Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs">
          <div className="bg-[#211B16] border border-[#514236] rounded-2xl w-full max-w-md overflow-hidden shadow-2xl">
            <div className="px-6 py-4.5 border-b border-[#514236] bg-[#2A221B]/40 flex items-center justify-between">
              <h3 className="text-base font-serif text-[#F5EFE5] flex items-center gap-2">
                <GitBranch className="w-4 h-4 text-[#F4D9A0]" />
                Connect {selectedProvider === 'github' ? 'GitHub' : 'GitLab'}
              </h3>
              <button onClick={() => setIsModalOpen(false)} className="text-[#847768] hover:text-[#F5EFE5] transition-colors p-1.5 rounded-lg hover:bg-[#2A221B]">
                <X className="w-4 h-4" />
              </button>
            </div>
            
            <form onSubmit={handleConnect} className="p-6 space-y-4">
              {/* Provider Selection */}
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setSelectedProvider('github')}
                  className={`flex-1 flex flex-col items-center gap-2 py-3.5 rounded-xl border transition-all ${
                    selectedProvider === 'github' 
                      ? 'bg-[#2A221B] border-[#F4D9A0] text-[#F5EFE5] shadow-sm' 
                      : 'bg-[#17130F] border-[#514236] text-[#847768] hover:text-[#B5AA9C]'
                  }`}
                >
                  <GitBranch className="w-5 h-5 text-[#F4D9A0]" />
                  <span className="text-xs font-mono font-medium">GitHub</span>
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedProvider('gitlab')}
                  className={`flex-1 flex flex-col items-center gap-2 py-3.5 rounded-xl border transition-all ${
                    selectedProvider === 'gitlab' 
                      ? 'bg-[#2A221B] border-[#F4D9A0] text-[#F5EFE5] shadow-sm' 
                      : 'bg-[#17130F] border-[#514236] text-[#847768] hover:text-[#B5AA9C]'
                  }`}
                >
                  <GitBranch className="w-5 h-5 text-[#C8792C]" />
                  <span className="text-xs font-mono font-medium">GitLab</span>
                </button>
              </div>

              <div>
                <label className="block text-[10px] font-mono uppercase tracking-widest text-[#847768] mb-1.5 font-medium">Repository URL</label>
                <input
                  type="url"
                  required
                  placeholder={`https://${selectedProvider}.com/owner/repo`}
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  className="w-full bg-[#2A221B] border border-[#514236] rounded-xl px-3.5 py-2.5 text-[#F5EFE5] text-sm focus:outline-none focus:border-[#F4D9A0] focus:ring-1 focus:ring-[#F4D9A0]/30 transition-all placeholder:text-[#847768] font-mono"
                />
              </div>

              <div>
                <label className="block text-[10px] font-mono uppercase tracking-widest text-[#847768] mb-1.5 font-medium flex items-center gap-2">
                  Access Token
                  <Shield className="w-3.5 h-3.5 text-[#10B981]" />
                </label>
                <div className="relative">
                  <Key className="w-4 h-4 text-[#847768] absolute left-3.5 top-3" />
                  <input
                    type="password"
                    required
                    placeholder="Enter Personal Access Token"
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    className="w-full bg-[#2A221B] border border-[#514236] rounded-xl pl-10 pr-4 py-2.5 text-[#F5EFE5] text-sm focus:outline-none focus:border-[#F4D9A0] focus:ring-1 focus:ring-[#F4D9A0]/30 transition-all placeholder:text-[#847768] font-mono"
                  />
                </div>
                <p className="text-[10px] font-mono text-[#847768] mt-2 flex items-start gap-1.5">
                  <AlertCircle className="w-3.5 h-3.5 shrink-0 text-[#C8792C]" />
                  Tokens are encrypted at rest with authenticated encryption and never exposed in UI or logs.
                </p>
              </div>

              {error && (
                <div className="bg-[#EF4444]/10 border border-[#EF4444]/30 text-[#EF4444] text-xs px-3.5 py-2.5 rounded-xl flex items-start gap-2 font-mono">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={isConnecting}
                className="w-full bg-[#F4D9A0] hover:bg-[#fae6bb] disabled:opacity-50 text-[#17130F] font-semibold text-sm py-2.5 rounded-xl transition-all flex items-center justify-center gap-2 shadow-md shadow-[#F4D9A0]/10 mt-4 active:scale-95"
              >
                {isConnecting ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Connecting...
                  </>
                ) : (
                  'Connect Provider'
                )}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
