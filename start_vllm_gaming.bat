@echo off
title ORA vLLM Server (GAMING MODE - Qwen2.5-VL-7B)
echo.
echo ===================================================
echo  Starting vLLM Server (GAMING MODE)
echo  Model: Qwen/Qwen2.5-VL-7B-Instruct-AWQ
echo  VRAM Limit: 20GB (Utilization 0.6)
echo ===================================================
echo.

wsl -d Ubuntu-22.04 bash -c "HF_HOME=/mnt/l/ai_models/huggingface python3 -m vllm.entrypoints.openai.api_server --model Qwen/Qwen2.5-VL-7B-Instruct-AWQ --gpu-memory-utilization 0.6 --max-model-len 8192 --enforce-eager --disable-custom-all-reduce --tensor-parallel-size 1 --host 0.0.0.0 --port 8001 --served-model-name Qwen/Qwen2.5-VL-7B-Instruct-AWQ --trust-remote-code"

pause
