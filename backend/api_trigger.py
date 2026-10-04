import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # First get workspaces
        resp = await client.get("http://127.0.0.1:8000/api/v1/workspaces/")
        print("Workspaces:", resp.status_code, resp.text)
        if "items" not in resp.json():
            print("No items in workspaces response. Are we authenticated?")
            return
        ws = resp.json()["items"][0]["id"]
        
        # Get repos
        resp = await client.get(f"http://127.0.0.1:8000/api/v1/orchestration/repositories?workspace_id={ws}")
        repos = resp.json()["items"]
        if not repos:
            print("No repos")
            return
        repo_id = repos[0]["id"]
        print("Repo:", repo_id)
        
        # Trigger analysis
        resp = await client.post(
            f"http://127.0.0.1:8000/api/v1/orchestration/analyze",
            json={"repository_id": repo_id, "revision": "main"}
        )
        data = resp.json()
        print("Triggered:", data)
        
        analysis_id = data["analysis_id"]
        print(f"Waiting for {analysis_id}...")
        
        # Poll
        for _ in range(10):
            await asyncio.sleep(2)
            resp = await client.get(f"http://127.0.0.1:8000/api/v1/orchestration/analyses/{analysis_id}")
            st = resp.json()
            print(st["status"], st.get("error_message"))
            if st["status"] in ["COMPLETED", "FAILED"]:
                break

if __name__ == "__main__":
    asyncio.run(main())
