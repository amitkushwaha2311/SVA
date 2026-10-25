"""
SVA API Trigger & Inspection Script
====================================

Connects to the local SVA backend server (default: http://127.0.0.1:8000),
authenticates (if needed), triggers an analysis job, polls until completion,
and displays domain results (Intent, Contracts, Evidence, Verification).
"""

import asyncio
import os
import sys
import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = os.environ.get("SVA_API_URL", "http://127.0.0.1:8000")
USER_EMAIL = os.environ.get("SVA_USER_EMAIL", "test@example.com")
USER_PASSWORD = os.environ.get("SVA_USER_PASSWORD", "testpassword123")


async def main():
    print(f"Connecting to SVA backend at: {BASE_URL}")

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # Check health
        try:
            health = await client.get("/health")
            print(f"Server health check: {health.status_code}")
        except httpx.ConnectError:
            print(f"ERROR: Cannot connect to {BASE_URL}. Ensure the backend server is running:")
            print("  uvicorn app.api.main:app --host 127.0.0.1 --port 8000")
            return

        # Attempt authentication if required
        auth_resp = await client.post("/auth/login", json={"email": USER_EMAIL, "password": USER_PASSWORD})
        if auth_resp.status_code == 200:
            print(f"Authenticated as: {USER_EMAIL}")
        else:
            print(f"Auth note ({auth_resp.status_code}): Proceeding without session login (or user already authenticated via cookies).")

        # 1. Get workspaces
        resp = await client.get("/api/v1/workspaces")
        if resp.status_code != 200:
            print(f"Failed to fetch workspaces: {resp.status_code} {resp.text}")
            return

        workspaces_data = resp.json()
        workspaces = workspaces_data if isinstance(workspaces_data, list) else workspaces_data.get("items", [])
        if not workspaces:
            print("No workspaces found. Create a workspace first.")
            return

        ws = workspaces[0]
        ws_id = ws["id"]
        print(f"Active Workspace: {ws.get('name', 'unnamed')} ({ws_id})")

        # 2. Get repositories
        resp = await client.get(f"/api/v1/orchestration/repositories?workspace_id={ws_id}")
        if resp.status_code != 200:
            print(f"Failed to fetch repositories: {resp.status_code} {resp.text}")
            return

        repos = resp.json().get("items", [])
        if not repos:
            print("No repositories registered in this workspace.")
            return

        repo = repos[0]
        repo_id = repo["id"]
        print(f"Target Repository: {repo.get('name')} ({repo.get('repository_identifier')}) [ID: {repo_id}]")

        # 3. Trigger analysis via POST /api/v1/orchestration/repositories/{repository_id}/analyses
        print(f"Triggering analysis for repo {repo_id} (revision: main)...")
        resp = await client.post(
            f"/api/v1/orchestration/repositories/{repo_id}/analyses",
            json={"revision": "main"},
        )
        if resp.status_code not in (200, 201, 202):
            print(f"Failed to trigger analysis: {resp.status_code} {resp.text}")
            return

        data = resp.json()
        analysis_id = data.get("id") or data.get("analysis_id")
        print(f"Analysis triggered successfully. ID: {analysis_id} (Status: {data.get('status')})")

        # 4. Poll status via GET /api/v1/orchestration/analyses/{analysis_id}/status
        print(f"Polling status for analysis {analysis_id}...")
        for i in range(30):
            await asyncio.sleep(2)
            resp = await client.get(f"/api/v1/orchestration/analyses/{analysis_id}/status")
            if resp.status_code != 200:
                print(f"Poll check returned {resp.status_code}: {resp.text}")
                continue

            st = resp.json()
            status = st.get("status")
            print(f"  [{i+1}/30] Status: {status}" + (f" | Error: {st.get('error_message')}" if st.get('error_message') else ""))
            if status in ["COMPLETED", "FAILED", "CANCELLED"]:
                break

        # 5. Fetch domain results if completed
        if status == "COMPLETED":
            print("\n=== Analysis Domain Results ===")
            for domain in ["intent", "contracts", "evidence", "verification"]:
                res = await client.get(f"/api/v1/analyses/{analysis_id}/{domain}")
                if res.status_code == 200:
                    data = res.json()
                    count = len(data) if isinstance(data, list) else len(data.get("items", []))
                    print(f"  {domain.capitalize()}: {count} item(s)")
                else:
                    print(f"  {domain.capitalize()}: {res.status_code}")


if __name__ == "__main__":
    asyncio.run(main())

