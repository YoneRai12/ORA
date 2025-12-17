import torch
import sys

print(f"PyTorch Version: {torch.__version__}")
print(f"CUDA Version: {torch.version.cuda}")
print(f"CUDA Available: {torch.cuda.is_available()}")

if not torch.cuda.is_available():
    print("CUDA not available. Exiting.")
    sys.exit(1)

try:
    print(f"Device Name: {torch.cuda.get_device_name(0)}")
    print(f"Capability: {torch.cuda.get_device_capability(0)}")

    print("Testing basic tensor move to CUDA...")
    x = torch.randn(10, 10).cuda()
    print("Success.")

    print("Testing float32 matmul...")
    y = torch.matmul(x, x)
    print("Success.")

    print("Testing bfloat16 matmul...")
    x_bf16 = x.to(torch.bfloat16)
    y_bf16 = torch.matmul(x_bf16, x_bf16)
    print("Success.")
    
    print("ALL CHECKS PASSED.")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)
