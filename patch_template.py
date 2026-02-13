
path = r"d:\TEAMSUFFER\templates\home_fixed.html"
try:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    old_str = "{% if selected_game_id==g.id %}"
    new_str = "{% if selected_game_id == g.id %}"
    
    if old_str in content:
        print("Found bad string, replacing...")
        content = content.replace(old_str, new_str)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("File updated successfully.")
    elif new_str in content:
        print("File already has the correct string.")
    else:
        print("Could not find the target string to replace.")
        # Debug: print that line
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if "selected_game_id" in line:
                print(f"Line {i+1}: {line.strip()}")

except Exception as e:
    print(f"Error: {e}")
