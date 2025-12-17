@echo off
title ORA vLLM Server (GAMING MODE - Ministral)
echo.
echo ===================================================
echo  Starting vLLM Server (GAMING MODE)
echo  Model: mistralai/Ministral-3-14B-Instruct-2512
echo  VRAM Limit: 25GB (Utilization 0.78)
echo ===================================================
echo.

wsl -d Ubuntu-22.04 bash -c "HF_HOME=/mnt/l/ai_models/huggingface python3 -m vllm.entrypoints.openai.api_server --model mistralai/Ministral-3-14B-Instruct-2512 --gpu-memory-utilization 0.78 --max-model-len 8192 --enforce-eager --disable-custom-all-reduce --tensor-parallel-size 1 --host 0.0.0.0 --port 8001 --served-model-name mistralai/Ministral-3-14B-Instruct-2512 --trust-remote-code"

pause
