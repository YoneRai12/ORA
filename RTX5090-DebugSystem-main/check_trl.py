from trl import SFTTrainer
import inspect

print("Inspecting SFTTrainer arguments:")
sig = inspect.signature(SFTTrainer.__init__)
for name in sig.parameters:
    print(f"  Arg: {name}")
