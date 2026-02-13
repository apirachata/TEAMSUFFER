
import os
import re

files_to_fix = [
    r"d:\TEAMSUFFER\templates\home_fixed.html",
    r"d:\TEAMSUFFER\templates\home.html"
]

for file_path in files_to_fix:
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        continue
        
    print(f"Processing {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        # EXPERIMENTAL FIX 1: Add spaces around ==
        # Pattern: space or no space, ==, space or no space
        # We want to normalize to: space == space
        content = re.sub(r'(\S)==(\S)', r'\1 == \2', content)
        
        # EXPERIMENTAL FIX 2: Join split tags
        # Pattern: {% ... %} split across lines
        # Django tags regex: \{%\s*.*?\s*%\}
        # But specifically looking for {% endif \n %}
        
        # Fix split endif specifically as seen in logs
        # "{% endif\n%}" or similar
        content = re.sub(r'{%\s*endif\s*\n\s*%}', '{% endif %}', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed errors in {file_path}")
        else:
            print(f"No errors found in {file_path}")
            
    except Exception as e:
        print(f"Failed to process {file_path}: {e}")
