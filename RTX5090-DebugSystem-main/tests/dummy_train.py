import time
import sys
import os

def main():
    print("Dummy training started...")
    mode = os.environ.get("DUMMY_MODE", "normal")
    
    if mode == "hang":
        print("Simulating hang...")
        time.sleep(3600)
    elif mode == "crash":
        print("Simulating crash...")
        sys.exit(1)
    elif mode == "oom":
        print("CUDA out of memory", file=sys.stderr)
        sys.exit(1)
    else:
        print("Training finished successfully.")

if __name__ == "__main__":
    main()
