import urllib.request
import json

# Login
login_data = json.dumps({"email": "devuser@gmail.com", "password": "devpassword123"}).encode()
req = urllib.request.Request(
    "http://127.0.0.1:8000/auth/login",
    data=login_data,
    headers={"Content-Type": "application/json"},
    method="POST"
)

with urllib.request.urlopen(req) as resp:
    print("Login status:", resp.status)
    body = json.loads(resp.read())
    print("Login body:", body)
    
    # Extract session cookie
    cookies = resp.headers.get_all("Set-Cookie") or []
    print("Set-Cookie headers:", cookies)
    
    session_cookie = None
    for c in cookies:
        if c.startswith("session="):
            session_cookie = c.split(";")[0].strip()
            break

print("Session cookie:", session_cookie)
print()

if session_cookie:
    # Test /auth/me
    req2 = urllib.request.Request(
        "http://127.0.0.1:8000/auth/me",
        headers={"Cookie": session_cookie},
        method="GET"
    )
    try:
        with urllib.request.urlopen(req2) as resp2:
            print("/auth/me status:", resp2.status)
            print("/auth/me body:", json.loads(resp2.read()))
    except Exception as e:
        print("/auth/me FAILED:", e)
    
    print()
    
    # Test /api/v1/workspaces/
    req3 = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/workspaces/",
        headers={"Cookie": session_cookie},
        method="GET"
    )
    try:
        with urllib.request.urlopen(req3) as resp3:
            print("/api/v1/workspaces/ status:", resp3.status)
            print("/api/v1/workspaces/ body:", json.loads(resp3.read()))
    except Exception as e:
        print("/api/v1/workspaces/ FAILED:", e)
