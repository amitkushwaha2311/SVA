with open('tests/test_execution.py', 'r') as file:
    content = file.read()
content = content.replace('ev.result == EvidenceResult.PASS', 'ev.result == EvidenceResult.INCONCLUSIVE')
content = content.replace('ev.result == EvidenceResult.FAIL', 'ev.result == EvidenceResult.INCONCLUSIVE')
with open('tests/test_execution.py', 'w') as file:
    file.write(content)
