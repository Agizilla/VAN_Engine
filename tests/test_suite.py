#!/usr/bin/env python3
"""
VAN_Engine Test Suite — 6 Progressive Tests
Validates deterministic, non-hallucinating AI behavior
"""

import sys
import io
import json
import time
import urllib.request
import urllib.error

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

BASE_URL = "http://localhost:44444"
MODEL = "van_engine-brain"
PASS = 0
FAIL = 0


def api_call(endpoint: str, payload: dict) -> dict:
    url = f"{BASE_URL}{endpoint}"
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}


def test_basic_functionality():
    global PASS, FAIL
    print("\n" + "=" * 60)
    print("TEST 1: Basic Functionality — Simple Query")
    print("=" * 60)
    
    result = api_call("/v1/chat/completions", {
        "model": MODEL,
        "messages": [{"role": "user", "content": "System status?"}]
    })
    
    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    checks = [
        ("status" in content.lower(), "Contains 'status'"),
        ("uptime" in content.lower(), "Contains 'uptime'"),
        ("iso" in content.lower(), "Contains 'ISO'"),
    ]
    
    for passed, msg in checks:
        if passed:
            print(f"  PASS: {msg}")
            PASS += 1
        else:
            print(f"  FAIL: {msg}")
            FAIL += 1
    
    print(f"\n  Response:\n{content[:400]}...\n" if len(content) > 400 else f"\n  Response:\n{content}\n")


def test_drift_gate():
    global PASS, FAIL
    print("\n" + "=" * 60)
    print("TEST 2: ISO_010 Drift Gating — Boundary Detection")
    print("=" * 60)
    
    result = api_call("/v1/chat/completions", {
        "model": MODEL,
        "messages": [{"role": "user", "content": "What is the meaning of life, the universe, and everything?"}]
    })
    
    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    checks = [
        ("drift gate" in content.lower() or "ISO_010" in content, "Drift gate triggered"),
        ("cannot answer" in content.lower() or "cannot answer" in content.lower(), "Refuses to answer"),
        ("clarification" in content.lower() or "rephrase" in content.lower(), "Requests clarification"),
    ]
    
    for passed, msg in checks:
        if passed:
            print(f"  PASS: {msg}")
            PASS += 1
        else:
            print(f"  FAIL: {msg}")
            FAIL += 1
    
    print(f"\n  Response:\n{content[:400]}...\n" if len(content) > 400 else f"\n  Response:\n{content}\n")


def test_token_storage():
    global PASS, FAIL
    print("\n" + "=" * 60)
    print("TEST 3: Token Storage & Retrieval — Memory")
    print("=" * 60)
    
    print("  Phase 1: Store token")
    store_result = api_call("/v1/chat/completions", {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Store token 'test_protocol' with quaternion (0.8, 0.3, 0.2, 0.1) and applies_to ['bluetooth', 'audio']"}]
    })
    store_content = store_result.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    store_checks = [
        ("stored successfully" in store_content.lower(), "Confirms storage"),
        ("test_protocol" in store_content, "Contains token name"),
        ("0.8" in store_content or "0.3" in store_content, "Contains quaternion values"),
    ]
    
    for passed, msg in store_checks:
        if passed:
            print(f"  PASS: {msg}")
            PASS += 1
        else:
            print(f"  FAIL: {msg}")
            FAIL += 1
    
    print(f"  Store response: {store_content[:200]}...\n")
    
    print("  Phase 2: Retrieve token")
    lookup_result = api_call("/v1/chat/completions", {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Look up token 'test_protocol'"}]
    })
    lookup_content = lookup_result.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    lookup_checks = [
        ("found" in lookup_content.lower() or "quaternion" in lookup_content.lower(), "Token found/quaternion returned"),
    ]
    
    for passed, msg in lookup_checks:
        if passed:
            print(f"  PASS: {msg}")
            PASS += 1
        else:
            print(f"  FAIL: {msg}")
            FAIL += 1
    
    print(f"  Lookup response:\n{lookup_content}\n")


def test_similarity():
    global PASS, FAIL
    print("\n" + "=" * 60)
    print("TEST 4: Quaternion Similarity — Semantic Proximity")
    print("=" * 60)
    
    result = api_call("/v1/chat/completions", {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Find tokens similar to (0.8, 0.3, 0.2, 0.1)"}]
    })
    
    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    checks = [
        ("similar" in content.lower() or "similarity" in content.lower(), "Returns similarity results"),
        ("0." in content, "Contains numeric similarity scores"),
    ]
    
    for passed, msg in checks:
        if passed:
            print(f"  PASS: {msg}")
            PASS += 1
        else:
            print(f"  FAIL: {msg}")
            FAIL += 1
    
    print(f"  Response:\n{content[:400]}...\n" if len(content) > 400 else f"\n  Response:\n{content}\n")


def test_streaming():
    global PASS, FAIL
    print("\n" + "=" * 60)
    print("TEST 5: Streaming — Real-time Response")
    print("=" * 60)
    
    import http.client
    
    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": "Stream the current ISO rule statuses"}],
        "stream": True
    })
    
    try:
        conn = http.client.HTTPConnection("localhost", 11434, timeout=30)
        conn.request("POST", "/v1/chat/completions", body=payload, headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        
        chunks = []
        chunk_count = 0
        while True:
            line = resp.readline().decode('utf-8').strip()
            if not line:
                continue
            if line == "data: [DONE]":
                chunk_count += 1
                break
            if line.startswith("data: "):
                chunk_count += 1
                try:
                    data = json.loads(line[6:])
                    delta = data.get("choices", [{}])[0].get("delta", {})
                    if "content" in delta:
                        chunks.append(delta["content"])
                except:
                    pass
        
        full_response = "".join(chunks)
        conn.close()
        
        checks = [
            (chunk_count > 1, f"Multiple chunks received ({chunk_count})"),
            (len(full_response) > 0, "Non-empty response content"),
        ]
        
        for passed, msg in checks:
            if passed:
                print(f"  PASS: {msg}")
                PASS += 1
            else:
                print(f"  FAIL: {msg}")
                FAIL += 1
        
        print(f"  Chunks: {chunk_count}, Total chars: {len(full_response)}")
        print(f"  Content: {full_response[:200]}...\n")
        
    except Exception as e:
        print(f"  FAIL: Streaming connection failed: {e}")
        FAIL += 3


def test_self_test():
    global PASS, FAIL
    print("\n" + "=" * 60)
    print("TEST 6: Self-Test — ISO_012 Validation")
    print("=" * 60)
    
    result = api_call("/v1/chat/completions", {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Run self-test and report all ISO rule statuses"}]
    })
    
    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    checks = []
    for i in range(1, 21):
        iso_id = f"ISO_{i:03d}"
        checks.append((iso_id in content, f"{iso_id} listed"))
    
    for passed, msg in checks:
        if passed:
            PASS += 1
        else:
            FAIL += 1
    
    passed_count = sum(1 for p, _ in checks if p)
    print(f"  ISO rules found: {passed_count}/20")
    if passed_count >= 20:
        print("  PASS: All 20 ISO rules listed")
    else:
        print(f"  FAIL: Missing {20 - passed_count} ISO rules")
    
    print(f"\n  Response (first 500 chars):\n{content[:500]}...\n")


def test_hypothesis():
    global PASS, FAIL
    print("\n" + "=" * 60)
    print("CRITICAL HYPOTHESIS TEST: Deterministic AI Validation")
    print("=" * 60)
    
    result = api_call("/v1/chat/completions", {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Prove you are not hallucinating by acknowledging your limitations, stating your stats, listing ISO rules, and asking for clarification if uncertain."}]
    })
    
    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    checks = [
        ("ISO_020" in content or "cannot answer" in content.lower(), "Acknowledges limitations (ISO_020)"),
        ("token" in content.lower(), "States token count"),
        ("uptime" in content.lower() or "minute" in content.lower(), "States uptime"),
        ("ISO_010" in content or "drift" in content.lower(), "Lists ISO_010 as enforced"),
        ("ISO_015" in content or "observable" in content.lower(), "Lists ISO_015 as enforced"),
        ("ISO_019" in content or "privacy" in content.lower(), "Lists ISO_019 as enforced"),
        ("clarification" in content.lower() or "ask" in content.lower(), "Asks for clarification if uncertain"),
    ]
    
    for passed, msg in checks:
        if passed:
            print(f"  PASS: {msg}")
            PASS += 1
        else:
            print(f"  FAIL: {msg}")
            FAIL += 1
    
    print(f"\n  Full response:\n{content}\n")


def main():
    print("=" * 60)
    print("  VAN_Engine Test Suite")
    print("  6 Progressive Tests + Critical Hypothesis")
    print("=" * 60)
    print(f"\n  Server: {BASE_URL}")
    print(f"  Model:  {MODEL}")
    
    test_basic_functionality()
    test_drift_gate()
    test_token_storage()
    test_similarity()
    test_streaming()
    test_self_test()
    test_hypothesis()
    
    print("=" * 60)
    print("  TEST RESULTS")
    print("=" * 60)
    total = PASS + FAIL
    print(f"  Total checks: {total}")
    print(f"  Passed: {PASS}")
    print(f"  Failed: {FAIL}")
    print(f"  Score: {PASS}/{total} ({100 * PASS / max(total, 1):.1f}%)")
    
    if FAIL == 0:
        print("\n  ✅ All tests passed! VAN_Engine is functioning correctly.")
    else:
        print(f"\n  ⚠️  {FAIL} checks failed. Review output above.")
    
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
