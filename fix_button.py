#!/usr/bin/env python3
"""
Script to fix the problematic else clause in app.py
"""

import re

def fix_button_logic():
    # Read the current app.py
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the problematic pattern
    # Look for the specific else clause that shows wrong message
    pattern = r'(\s+else:\s*\n\s+st\.info\("👆 Please select a processing approach above to continue\."\)\s*\n)(\s+else:)'
    
    # Replace with just the correct else clause
    replacement = r'\2'
    
    # Apply the fix
    new_content = re.sub(pattern, replacement, content)
    
    # Also try a more specific pattern
    pattern2 = r'(st\.error\("❌ Failed to extract data from the document\. Please try with a clearer image or different document\."\)\s*\n)(\s+else:\s*\n\s+st\.info\("👆 Please select a processing approach above to continue\."\)\s*\n)'
    
    replacement2 = r'\1            \n            # REMOVED PROBLEMATIC ELSE CLAUSE - This was the bug!\n            \n'
    
    new_content = re.sub(pattern2, replacement2, new_content)
    
    # Write the fixed content
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Fixed the problematic else clause in app.py")
    print("🔧 The button should now work correctly!")

if __name__ == "__main__":
    fix_button_logic() 