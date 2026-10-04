import asyncio
import httpx

async def trigger_via_api():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        # 1. Login
        login = await client.post("/auth/login", json={
            "email": "devuser@gmail.com",
            "password": "devpassword123"
        })
        if login.status_code != 200:
            print("Login failed:", login.status_code, login.text)
            return
            
        print("Logged in successfully.")
        
        # 2. Get workspaces
        ws_res = await client.get("/api/v1/workspaces/")
        if ws_res.status_code != 200 or not ws_res.json():
            print("No workspaces found:", ws_res.status_code, ws_res.text)
            return
        
        ws_id = ws_res.json()[0]["id"]
        print("Workspace:", ws_id)
        
        # 3. Get repository
        repo_res = await client.get(f"/api/v1/workspaces/{ws_id}/repositories")
        if repo_res.status_code != 200 or not repo_res.json():
            print("No repositories found:", repo_res.status_code, repo_res.text)
            return
            
        repo_id = repo_res.json()[0]["id"]
        print("Repository:", repo_id)
        
        # 4. Trigger analysis
        analysis_res = await client.post(f"/api/v1/analyses", json={
            "repository_id": repo_id,
            "revision": "HEAD"
        })
        if analysis_res.status_code != 202:
            print("Failed to trigger analysis:", analysis_res.status_code, analysis_res.text)
            return
            
        analysis_id = analysis_res.json()["analysis_id"]
        print("Triggered analysis:", analysis_id)

asyncio.run(trigger_via_api())
