
import os

file_path = r'd:\TEAMSUFFER\templates\home_fixed.html'

print(f"Checking {file_path}")

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        print(f"Line 41 BEFORE: {lines[40].strip()}")
except Exception as e:
    print(f"Read error: {e}")

# The specific content we want
new_line_41 = '                    <option value="{{ g.id }}" {% if selected_game_id == g.id %}selected{% endif %}>{{ g.name }}</option>\n'

# We will modify the lines list
if 'selected_game_id==g.id' in lines[40]:
    print("Found error line, fixing...")
    lines[40] = new_line_41
else:
    print("Line 41 doesn't match expected error pattern, checking if it's already fixed...")
    if 'selected_game_id == g.id' in lines[40]:
        print("Line is ALREADY FIXED.")
    else:
        print(f"Line 41 content is unexpected: {lines[40]}")
        # Force overwrite anyway
        lines[40] = new_line_41

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    print(f"Line 41 AFTER: {lines[40].strip()}")

# Fix home.html too
file_path_home = r'd:\TEAMSUFFER\templates\home.html'
print(f"\nChecking {file_path_home}")
try:
    with open(file_path_home, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        # Line 48 in home.html (approximate, based on view_file earlier it was 48)
        # Let's find the line with the error dynamically
        target_index = -1
        for i, line in enumerate(lines):
            if 'selected_game_id' in line and '<option' in line:
                target_index = i
                print(f"Found target at line {i+1}: {line.strip()}")
                break
        
        if target_index != -1:
            if 'selected_game_id==g.id' in lines[target_index]:
                print("Found error, fixing...")
                lines[target_index] = lines[target_index].replace('selected_game_id==g.id', 'selected_game_id == g.id')
                with open(file_path_home, 'w', encoding='utf-8') as f_out:
                    f_out.writelines(lines)
                print("Fixed home.html")
            elif 'selected_game_id == g.id' in lines[target_index]:
                 print("home.html is already correct.")
            else:
                 print("Could not match exact error pattern in home.html")
        else:
            print("Could not find target line in home.html")

except Exception as e:
    print(f"Error processing home.html: {e}")
