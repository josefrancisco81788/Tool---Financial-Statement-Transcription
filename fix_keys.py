#!/usr/bin/env python3

# Fix duplicate widget keys in app.py
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the duplicate widget keys
content = content.replace(
    'key="download_detailed_csv"', 
    'key=f"download_detailed_csv_{abs(hash(str(data))) % 10000}"'
)
content = content.replace(
    'key="download_summary_csv"', 
    'key=f"download_summary_csv_{abs(hash(str(data))) % 10000}"'
)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ Fixed duplicate widget keys!')
print('🔧 Replaced hardcoded keys with unique hash-based keys') 