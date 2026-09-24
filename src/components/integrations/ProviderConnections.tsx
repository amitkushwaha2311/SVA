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
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-medium text-white flex items-center gap-2">
            <Server className="w-5 h-5 text-indigo-400" />
            Enterprise Integrations
          </h2>
          <p className="text-sm text-gray-400 mt-1">
            Securely connect external repository providers. Credentials are encrypted at rest and never exposed.
          </p>
        </div>
        <button
          onClick={() => {
            setSelectedProvider('github');
            setIsModalOpen(true);
          }}
          className="bg-indigo-500 hover:bg-indigo-600 text-white text-sm font-medium px-4 py-2 rounded-lg flex items-center gap-2 transition-colors shadow-lg shadow-indigo-500/20 border border-indigo-400/30"
        >
          <Plus className="w-4 h-4" />
          Add Connection
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center items-center h-32">
          <RefreshCw className="w-6 h-6 text-indigo-400 animate-spin" />
        </div>
      ) : connections.length === 0 ? (
        <div className="border border-white/10 bg-white/5 rounded-xl p-8 text-center backdrop-blur-xl">
          <Shield className="w-12 h-12 text-gray-500 mx-auto mb-3 opacity-50" />
          <h3 className="text-gray-300 font-medium mb-1">No Integrations Connected</h3>
          <p className="text-gray-500 text-sm max-w-sm mx-auto">
            Connect GitHub or GitLab to enable secure, agentic analysis of your repositories and automatic webhook processing.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {connections.map((conn) => (
            <div key={conn.id} className="border border-white/10 bg-gradient-to-b from-white/5 to-transparent rounded-xl p-5 backdrop-blur-xl relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/5 rounded-full blur-2xl transform translate-x-16 -translate-y-16 group-hover:bg-indigo-500/10 transition-colors" />
              
              <div className="flex items-start justify-between relative z-10">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-white/5 rounded-lg border border-white/10">
                    {conn.provider === 'github' ? <GitBranch className="w-5 h-5 text-white" /> : <GitBranch className="w-5 h-5 text-orange-500" />}
                  </div>
                  <div>
                    <h3 className="text-gray-200 font-medium capitalize">{conn.provider}</h3>
                    <p className="text-xs text-gray-500 truncate max-w-[200px]">{conn.connection_identity}</p>
                  </div>
                </div>
                
                <span className={`px-2.5 py-1 rounded-full text-[10px] font-medium tracking-wider uppercase border ${
                  conn.status === 'CONNECTED' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                  conn.status === 'REVOKED' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                  'bg-gray-500/10 text-gray-400 border-gray-500/20'
                }`}>
                  {conn.status}
                </span>
              </div>

              <div className="mt-6 flex items-center justify-between relative z-10">
                <div className="text-xs text-gray-500">
                  Added {new Date(conn.created_at).toLocaleDateString()}
                </div>
                {conn.status === 'CONNECTED' && (
                  <button 
                    onClick={() => handleDisconnect(conn.id)}
                    className="text-xs font-medium text-red-400 hover:text-red-300 transition-colors bg-red-400/10 hover:bg-red-400/20 px-3 py-1.5 rounded-lg"
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
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-gray-900 border border-white/10 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl">
            <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between">
              <h3 className="text-lg font-medium text-white flex items-center gap-2">
                {selectedProvider === 'github' ? <GitBranch className="w-5 h-5" /> : <GitBranch className="w-5 h-5" />}
                Connect {selectedProvider === 'github' ? 'GitHub' : 'GitLab'}
              </h3>
              <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-white transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <form onSubmit={handleConnect} className="p-6 space-y-5">
              {/* Provider Selection */}
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setSelectedProvider('github')}
                  className={`flex-1 flex flex-col items-center gap-2 py-4 rounded-xl border transition-all ${
                    selectedProvider === 'github' 
                      ? 'bg-indigo-500/10 border-indigo-500 text-white' 
                      : 'bg-white/5 border-white/10 text-gray-400 hover:bg-white/10'
                  }`}
                >
                  <GitBranch className="w-6 h-6" />
                  <span className="text-sm font-medium">GitHub</span>
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedProvider('gitlab')}
                  className={`flex-1 flex flex-col items-center gap-2 py-4 rounded-xl border transition-all ${
                    selectedProvider === 'gitlab' 
                      ? 'bg-indigo-500/10 border-indigo-500 text-white' 
                      : 'bg-white/5 border-white/10 text-gray-400 hover:bg-white/10'
                  }`}
                >
                  <GitBranch className="w-6 h-6" />
                  <span className="text-sm font-medium">GitLab</span>
                </button>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1.5">Repository URL</label>
                <input
                  type="url"
                  required
                  placeholder={`https://${selectedProvider}.com/owner/repo`}
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all placeholder:text-gray-600"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1.5 flex items-center gap-2">
                  Access Token
                  <Shield className="w-3.5 h-3.5 text-emerald-400" />
                </label>
                <div className="relative">
                  <Key className="w-4 h-4 text-gray-500 absolute left-3.5 top-3" />
                  <input
                    type="password"
                    required
                    placeholder="Enter Personal Access Token"
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    className="w-full bg-black/40 border border-white/10 rounded-lg pl-10 pr-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all placeholder:text-gray-600"
                  />
                </div>
                <p className="text-[11px] text-gray-500 mt-2 flex items-start gap-1.5">
                  <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                  Tokens are encrypted at rest with authenticated encryption and never exposed in the UI or sandbox execution.
                </p>
              </div>

              {error && (
                <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-xs px-4 py-3 rounded-lg flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={isConnecting}
                className="w-full bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50 disabled:hover:bg-indigo-500 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/20 border border-indigo-400/30 mt-4"
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
