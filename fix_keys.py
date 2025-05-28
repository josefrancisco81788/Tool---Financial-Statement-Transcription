#!/usr/bin/env python3
"""
Fix the duplicate message issue in app.py
"""

def fix_duplicate_message():
    # Read the file
    with open('app.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find and remove the problematic line 3042
    # Look for the pattern where the message appears inside the show_button block
    fixed_lines = []
    i = 0
    inside_show_button_block = False
    
    while i < len(lines):
        line = lines[i]
        
        # Track if we're inside the show_button block
        if 'if show_button:' in line:
            inside_show_button_block = True
            fixed_lines.append(line)
        elif line.strip().startswith('else:') and inside_show_button_block:
            # This is the end of the show_button block
            inside_show_button_block = False
            fixed_lines.append(line)
        elif inside_show_button_block and 'st.info("👆 Please select a processing approach above to continue.")' in line:
            # Skip this line - it's the problematic one inside the show_button block
            print(f"Removing problematic line {i+1}: {line.strip()}")
            # Also skip the preceding if statement
            if i > 0 and 'if uploaded_file.type == "application/pdf":' in lines[i-1]:
                # Remove the previous line too
                fixed_lines.pop()
                print(f"Also removing line {i}: {lines[i-1].strip()}")
        else:
            fixed_lines.append(line)
        
        i += 1
    
    # Write the fixed file
    with open('app.py', 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print("Fixed the duplicate message issue!")

if __name__ == "__main__":
    fix_duplicate_message() 