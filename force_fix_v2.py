
import os

file_path = r'd:\TEAMSUFFER\templates\home_fixed_v2.html'
target_line_content = '{% if selected_game_id==g.id %}'
replacement_content = '{% if selected_game_id == g.id %}'

print(f"Processing {file_path}...")

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    found = False
    for i, line in enumerate(lines):
        if 'selected_game_id==g.id' in line:
            print(f"Found bad syntax on line {i+1}: {line.strip()}")
            lines[i] = line.replace('selected_game_id==g.id', 'selected_game_id == g.id')
            found = True
        elif 'selected_game_id == g.id' in line:
             print(f"Line {i+1} appears correct: {line.strip()}")
             
    if found:
        print("Writing changes...")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        # Verify
        with open(file_path, 'r', encoding='utf-8') as f:
            check_lines = f.readlines()
            for i, line in enumerate(check_lines):
                 if 'selected_game_id' in line and '<option' in line:
                     print(f"VERIFICATION Line {i+1}: {line.strip()}")
    else:
        print("No bad syntax found to fix (or file was already correct).")

except Exception as e:
    print(f"Error: {e}")
