
with open(r"c:\Users\YoneRai12\Desktop\ORADiscordBOT-main3\src\cogs\ora.py", "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        if "def _build_history" in line:
            print(f"Found at {i}: {line.strip()}")
