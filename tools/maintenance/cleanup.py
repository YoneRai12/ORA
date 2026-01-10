
lines_to_delete_start = 703
lines_to_delete_end = 915
file_path = r"c:\Users\YoneRai12\Desktop\ORADiscordBOT-main3\src\cogs\memory.py"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Adjust for 0-index
# We want to keep lines[:702] and lines[915:]
# Line 703 is index 702.
# Line 915 is index 914.
# So slice: lines[:702] + lines[915:]
new_lines = lines[:lines_to_delete_start-1] + lines[lines_to_delete_end:]

print(f"Original line count: {len(lines)}")
print(f"New line count: {len(new_lines)}")

with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)
