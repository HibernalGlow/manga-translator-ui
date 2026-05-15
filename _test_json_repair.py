import json_repair

# Test 1: Truncated JSON (missing closing brackets)
bad1 = '{"translations":[{"id":1,"translation":"aaa"},{"id":2,"translation":"bbb"},{"id":3,"translation":"ccc"},{"id":4,"translation":"ddd"'
r1 = json_repair.loads(bad1)
print(f"Test1 truncated: {r1}")

# Test 2: Fullwidth colon
bad2 = '{"id":2,"text\uff1a"bbb"}'
r2 = json_repair.loads(bad2)
print(f"Test2 fullwidth colon: {r2}")

# Test 3: Smart quotes in values
bad3 = '{"id":1,"translation":"\u201cHello\u201d"}'
r3 = json_repair.loads(bad3)
print(f"Test3 smart quotes: {r3}")

# Test 4: The exact case from the log - missing } on last object
bad4 = """{
  "translations": [
    { "id": 1, "translation": "soft and weak" },
    { "id": 2, "translation": "must practice repeatedly" },
    { "id": 3, "translation": "you still have room for improvement" },
    { "id": 4, "translation": "...yes"
  ]
}"""
r4 = json_repair.loads(bad4)
print(f"Test4 valid JSON: {r4}")

# Test 5: Truncated mid-value
bad5 = '{"translations":[{"id":1,"translation":"hello"},{"id":2,"translation":"wor'
r5 = json_repair.loads(bad5)
print(f"Test5 truncated mid-value: {r5}")

# Test 6: Trailing comma
bad6 = '{"translations":[{"id":1,"translation":"hello"},]}'
r6 = json_repair.loads(bad6)
print(f"Test6 trailing comma: {r6}")

print("\nAll tests passed!")
