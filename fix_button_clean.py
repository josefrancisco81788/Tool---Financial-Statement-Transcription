#!/usr/bin/env python3
"""
Clean fix for the button logic issue in app.py
"""

def fix_button_logic():
    # Read the current app.py
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the problematic section and replace it
    # Look for the pattern after the st.error line
    old_pattern = '''st.error("❌ Failed to extract data from the document. Please try with a clearer image or different document.")
            # For PDFs, show message to select approach; for other cases, this shouldn't happen
            if uploaded_file.type == "application/pdf":
                st.info("👆 Please select a processing approach above to continue.")
        
else:
    # Only show message when no approach is selected for PDFs
    if uploaded_file.type == "application/pdf":
        st.info("👆 Please select a processing approach above to continue.")
    else:
        st.error("❌ Unexpected state: Non-PDF file should always show button")'''
    
    new_pattern = '''st.error("❌ Failed to extract data from the document. Please try with a clearer image or different document.")
        
        else:
            # Only show message when no approach is selected for PDFs
            if uploaded_file.type == "application/pdf":
                st.info("👆 Please select a processing approach above to continue.")
            else:
                st.error("❌ Unexpected state: Non-PDF file should always show button")'''
    
    # Replace the problematic section
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        print("Found and fixed the problematic pattern!")
    else:
        print("Pattern not found, trying alternative approach...")
        # Alternative approach - remove duplicate lines
        lines = content.split('\n')
        fixed_lines = []
        skip_next = False
        
        for i, line in enumerate(lines):
            if skip_next:
                skip_next = False
                continue
                
            # Remove duplicate message lines
            if 'Please select a processing approach above to continue' in line:
                # Check if this is a duplicate
                if i > 0 and 'Please select a processing approach above to continue' in lines[i-1]:
                    continue  # Skip this duplicate
                elif i < len(lines) - 1 and 'Please select a processing approach above to continue' in lines[i+1]:
                    # Keep this one, skip the next
                    fixed_lines.append(line)
                    skip_next = True
                    continue
            
            fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
    
    # Write the fixed content
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Fixed the button logic issue!")

if __name__ == "__main__":
    fix_button_logic() 