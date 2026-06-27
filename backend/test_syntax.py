"""Test syntax of Python files"""
import ast

files = ['app/main.py', 'scrape_rgukt.py']
for f in files:
    with open(f, 'r', encoding='utf-8') as fh:
        ast.parse(fh.read(), filename=f)
    print(f"OK: {f}")
print("All files syntax OK")
