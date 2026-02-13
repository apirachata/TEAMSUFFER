
path = r"d:\TEAMSUFFER\templates\home_fixed.html"
try:
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    skip = False
    for i in range(len(lines)):
        if skip:
            skip = False
            continue
            
        line = lines[i]
        # Check for the specific broken split tag
        if "{% endif" in line and not "%}" in line:
            # Check next line
            if i + 1 < len(lines) and "%}" in lines[i+1]:
                # Join them
                print(f"Fixing lines {i+1} and {i+2}")
                combined = line.strip() + " %}\n"
                new_lines.append(combined)
                skip = True
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
            
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("File patched.")

except Exception as e:
    print(f"Error: {e}")
