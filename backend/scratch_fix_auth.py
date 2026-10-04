import os
import re

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # We need to replace:
    # me_resp = await client.get("/auth/me", cookies=login_resp.cookies)
    # with:
    # client.cookies = login_resp.cookies
    # me_resp = await client.get("/auth/me")
    
    # Simple regex for the specific cases
    content = re.sub(
        r'(\w+)\s*=\s*await client\.(get|post)\(([^,]+),\s*cookies=([^\)]+)\)',
        r'client.cookies = \4\n        \1 = await client.\2(\3)',
        content
    )

    with open(filepath, 'w') as f:
        f.write(content)

fix_file('tests/test_auth.py')
fix_file('tests/test_auth_security.py')
