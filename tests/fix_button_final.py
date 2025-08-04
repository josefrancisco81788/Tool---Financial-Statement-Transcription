#!/usr/bin/env python3
"""
Script to fix the button logic issue in app.py
"""

def fix_button_logic():
    # Read the current app.py
    with open('app.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the problematic section and fix it
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Look for the problematic pattern
        if 'st.error("❌ Failed to extract data from the document. Please try with a clearer image or different document.")' in line:
            # Add this line
            fixed_lines.append(line)
            i += 1
            
            # Skip any problematic else clause that follows
            while i < len(lines) and lines[i].strip() != 'else:':
                if lines[i].strip() and not lines[i].startswith('    # Footer'):
                    fixed_lines.append(lines[i])
                i += 1
            
            # Add the correct else clause
            if i < len(lines) and lines[i].strip() == 'else:':
                fixed_lines.append('        \n')
                fixed_lines.append('else:\n')
                fixed_lines.append('    # Only show message when no approach is selected for PDFs\n')
                fixed_lines.append('    if uploaded_file.type == "application/pdf":\n')
                fixed_lines.append('        st.info("👆 Please select a processing approach above to continue.")\n')
                fixed_lines.append('    else:\n')
                fixed_lines.append('        st.error("❌ Unexpected state: Non-PDF file should always show button")\n')
                fixed_lines.append('\n')
                
                # Skip the old problematic section
                i += 1
                while i < len(lines) and not lines[i].startswith('    # Footer'):
                    i += 1
            
        else:
            fixed_lines.append(line)
            i += 1
    
    # Write the fixed content
    with open('app.py', 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print("Fixed the button logic issue!")

if __name__ == "__main__":
    fix_button_logic() 