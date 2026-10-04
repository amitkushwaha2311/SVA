with open('tests/test_execution.py', 'r') as file:
    content = file.read()
content = content.replace('result.sandbox_backend == "SAFE_FALLBACK"', 'result.sandbox_identity.backend_name == "SAFE_FALLBACK"')
with open('tests/test_execution.py', 'w') as file:
    file.write(content)
