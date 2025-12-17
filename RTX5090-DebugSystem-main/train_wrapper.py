#!/usr/bin/env python3
import os
import sys
import subprocess
import shlex

def main():
    """
    Wrapper for training commands.
    Allows easy switching between python, accelerate, deepspeed, etc.
    via environment variables or arguments.
    """
    # Default to python train.py if no args provided
    cmd = sys.argv[1:]
    if not cmd:
        cmd = ["python", "train.py"]
    
    # If the first arg is a known launcher alias, expand it
    # This allows PHOENIX_TRAIN_CMD="accelerate launch train.py" to work easily
    # even if passed as a single string in some contexts (though phoenix splits it).
    
    print(f"[train_wrapper] Launching: {' '.join(cmd)}")
    
    # Ensure stdout/stderr are flushed
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    
    try:
        # Replace current process with the training process
        # On Windows, os.execvp behaves slightly differently but is generally fine for this.
        # However, subprocess.run is safer if we want to do post-processing later.
        # For now, we want to be a transparent wrapper.
        if os.name == 'nt':
            # Windows doesn't support true execvp replacement in the same way, 
            # so we run and wait.
            proc = subprocess.run(cmd, env=env)
            sys.exit(proc.returncode)
        else:
            os.execvpe(cmd[0], cmd, env)
    except Exception as e:
        print(f"[train_wrapper] Failed to launch: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
