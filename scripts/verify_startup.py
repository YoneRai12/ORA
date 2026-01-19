
import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

print("Attempting to import src.bot...")
try:
    from src import bot  # noqa: F401
    print("SUCCESS: Imported src.bot")
except Exception as e:
    print(f"FAILED: Could not import src.bot: {e}")

print("Attempting to import src.views.music_dashboard...")
try:
    from src.views import music_dashboard  # noqa: F401
    print("SUCCESS: Imported src.views.music_dashboard")
except Exception as e:
    print(f"FAILED: Could not import src.views.music_dashboard: {e}")

print("Attempting to import src.cogs.ora...")
try:
    from src.cogs import ora  # noqa: F401
    print("SUCCESS: Imported src.cogs.ora")
except Exception as e:
    print(f"FAILED: Could not import src.cogs.ora: {e}")
