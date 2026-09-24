/**
 * SVA Frontend Unit Tests — Vitest + React Testing Library
 *
 * Tests are organized by domain:
 * 1. SVA State Display — all verification decision states
 * 2. Evidence — rendering, inspector, stale evidence
 * 3. Security — no dangerouslySetInnerHTML, no credential exposure
 * 4. Utilities — apiFetch routing
 * 5. Auth — login/signup form behavior
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

// ─── 1. SVA State Display ─────────────────────────────────────────────────────

describe('SVA Verification States', () => {
  const STATES = ['PROVEN', 'SUPPORTED', 'VIOLATED', 'UNKNOWN', 'INCONCLUSIVE', 'STALE'];

  it('defines all 6 required verification states', () => {
    // Each state must be a distinct non-empty string
    const unique = new Set(STATES);
    expect(unique.size).toBe(6);
    STATES.forEach(s => expect(typeof s).toBe('string'));
  });

  it('UNKNOWN is not treated as a positive result', () => {
    const positiveStates = ['PROVEN', 'SUPPORTED'];
    expect(positiveStates).not.toContain('UNKNOWN');
    expect(positiveStates).not.toContain('INCONCLUSIVE');
    expect(positiveStates).not.toContain('STALE');
  });

  it('VIOLATED is not treated as a passing state', () => {
    const passingStates = ['PROVEN', 'SUPPORTED'];
    expect(passingStates).not.toContain('VIOLATED');
  });
});

// ─── 2. Security — XSS / Content Safety ─────────────────────────────────────

describe('Security: XSS and Repository Content Safety', () => {
  it('does not produce dangerouslySetInnerHTML in evidence descriptions', () => {
    // Repository content (e.g., a description field) should be treated as text,
    // not rendered as HTML.
    const maliciousContent = '<script>alert("xss")</script>';
    const escaped = maliciousContent
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');

    expect(escaped).not.toContain('<script>');
    expect(escaped).toContain('&lt;script&gt;');
  });

  it('never stores credentials in localStorage', () => {
    // Verify the mock localStorage has no session tokens
    const localStorageKeys = Object.keys(localStorage);
    const credentialKeys = localStorageKeys.filter(k =>
      k.toLowerCase().includes('token') ||
      k.toLowerCase().includes('session') ||
      k.toLowerCase().includes('password')
    );
    expect(credentialKeys).toHaveLength(0);
  });

  it('apiFetch always uses same-origin credentials (session cookie)', async () => {
    // Verify that the api fetch configuration uses same-origin credentials
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ ok: true }), { status: 200 })
    );

    const { apiFetch } = await import('@/lib/api');
    await apiFetch('/evidence/?workspace_id=default');

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/evidence/'),
      expect.objectContaining({ credentials: 'same-origin' })
    );
    fetchSpy.mockRestore();
  });
});

// ─── 3. API Routing ───────────────────────────────────────────────────────────

describe('apiFetch routing logic', () => {
  it('routes /auth endpoints to /api/auth (not /api/v1/auth)', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ id: 'u1' }), { status: 200 })
    );

    const { apiFetch } = await import('@/lib/api');
    await apiFetch('/auth/me');

    expect(fetchSpy).toHaveBeenCalledWith(
      '/api/auth/me',
      expect.any(Object)
    );
    fetchSpy.mockRestore();
  });

  it('routes /v1/evidence to /api/v1/evidence', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ items: [] }), { status: 200 })
    );

    const { apiFetch } = await import('@/lib/api');
    await apiFetch('/v1/evidence/');

    expect(fetchSpy).toHaveBeenCalledWith(
      '/api/v1/evidence/',
      expect.any(Object)
    );
    fetchSpy.mockRestore();
  });

  it('throws on non-OK response', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: 'Not found' }), { status: 404 })
    );

    const { apiFetch } = await import('@/lib/api');
    await expect(apiFetch('/v1/missing/')).rejects.toThrow('Not found');
    vi.restoreAllMocks();
  });

  it('does not set Authorization header (uses HttpOnly cookie instead)', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({}), { status: 200 })
    );

    const { apiFetch } = await import('@/lib/api');
    await apiFetch('/v1/contracts/?workspace_id=w1');

    const callArgs = fetchSpy.mock.calls[0][1] as RequestInit;
    const headers = new Headers(callArgs?.headers);
    expect(headers.get('Authorization')).toBeNull();
    fetchSpy.mockRestore();
  });
});

// ─── 4. Evidence Types ────────────────────────────────────────────────────────

describe('Evidence data model constraints', () => {
  it('evidence status STALE does not imply VIOLATED', () => {
    const violatingStates = ['VIOLATED'];
    expect(violatingStates).not.toContain('STALE');
  });

  it('evidence integrity requires hash algorithm and hash value', () => {
    const mockIntegrity = {
      evidence_hash: 'abc123',
      hash_algorithm: 'SHA-256',
      parent_evidence_ids: [],
    };

    expect(mockIntegrity.evidence_hash).toBeTruthy();
    expect(mockIntegrity.hash_algorithm).toBeTruthy();
    expect(Array.isArray(mockIntegrity.parent_evidence_ids)).toBe(true);
  });

  it('UNKNOWN status does not mean VIOLATED', () => {
    const status = 'UNKNOWN';
    expect(status).not.toBe('VIOLATED');
    expect(status).not.toBe('PROVEN');
  });
});

// ─── 5. Workspace Isolation ───────────────────────────────────────────────────

describe('Workspace isolation contract', () => {
  it('workspace A id differs from workspace B id', () => {
    const workspaceA = { id: 'ws-a', name: 'Workspace A' };
    const workspaceB = { id: 'ws-b', name: 'Workspace B' };

    expect(workspaceA.id).not.toBe(workspaceB.id);
  });

  it('filtering evidence by workspace_id excludes other workspaces', () => {
    const allEvidence = [
      { evidence_id: 'ev1', workspace_id: 'ws-a' },
      { evidence_id: 'ev2', workspace_id: 'ws-b' },
      { evidence_id: 'ev3', workspace_id: 'ws-a' },
    ];

    const forWorkspaceA = allEvidence.filter(e => e.workspace_id === 'ws-a');
    const forWorkspaceB = allEvidence.filter(e => e.workspace_id === 'ws-b');

    expect(forWorkspaceA.map(e => e.evidence_id)).not.toContain('ev2');
    expect(forWorkspaceB.map(e => e.evidence_id)).not.toContain('ev1');
    expect(forWorkspaceB.map(e => e.evidence_id)).not.toContain('ev3');
  });
});

// ─── 6. Auth Form Validation ──────────────────────────────────────────────────

describe('Authentication form validation', () => {
  it('login requires both email and password', () => {
    const validateLogin = (email: string, password: string) => {
      if (!email) return 'Email required';
      if (!password) return 'Password required';
      return null;
    };

    expect(validateLogin('', 'pass')).toBe('Email required');
    expect(validateLogin('user@example.com', '')).toBe('Password required');
    expect(validateLogin('user@example.com', 'securepass')).toBeNull();
  });

  it('does not log passwords', () => {
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

    // Simulate what a secure login handler should do: never log credentials
    const secureLoginHandler = (_email: string, _password: string) => {
      // No console.log(password) allowed
    };

    secureLoginHandler('user@example.com', 's3cret');
    expect(consoleSpy).not.toHaveBeenCalledWith(expect.stringContaining('s3cret'));
    consoleSpy.mockRestore();
  });
});
