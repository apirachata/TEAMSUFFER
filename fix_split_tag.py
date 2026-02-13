
import os
import re

files_to_fix = [
    r'd:\TEAMSUFFER\templates\home_fixed.html',
    r'd:\TEAMSUFFER\templates\home.html'
]

def fix_file(file_path):
    print(f"Checking {file_path}")
    if not os.path.exists(file_path):
        print("File not found.")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to find split endif tags: {% endif followed by whitespace/newlines and then %}
    pattern = r'\{%\s*endif\s*[\r\n]+\s*%\}'
    
    # Check if pattern exists
    if re.search(pattern, content):
        print("Found split endif tag. Fixing...")
        # Replace with single line {% endif %}
        new_content = re.sub(pattern, '{% endif %}', content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Fixed.")
    else:
        print("No split endif tags found.")

for fp in files_to_fix:
    fix_file(fp)
