@echo off
echo Installing PyTorch with CUDA support...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
echo Installing Training Libraries...
pip install transformers peft bitsandbytes trl datasets accelerate scipy
echo Installation Complete.
pause
