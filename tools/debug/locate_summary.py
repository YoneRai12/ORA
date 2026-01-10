
path = r"c:\Users\YoneRai12\Desktop\ORADiscordBOT-main3\src\cogs\ora.py"
with open(path, "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        if "summarize_chat" in line:
            print(f"Found at {i}: {line.strip()}")
