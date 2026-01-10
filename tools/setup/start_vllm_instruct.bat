@echo off
title ORA vLLM Server (INSTRUCT - Default)
echo.
echo ===================================================
echo ===================================================
echo  Starting Ministral-3-14B-Instruct-2512 (Local Optimal)
echo  Features: High Reasoning, Fluent Japanese, Tools
echo ===================================================
echo.

wsl -d Ubuntu-22.04 bash -c "HF_HOME=/mnt/l/ai_models/huggingface python3 -m vllm.entrypoints.openai.api_server --model mistralai/Ministral-3-14B-Instruct-2512 --gpu-memory-utilization 0.60 --max-model-len 16384 --enforce-eager --disable-custom-all-reduce --tensor-parallel-size 1 --host 0.0.0.0 --port 8001 --served-model-name mistralai/Ministral-3-14B-Instruct-2512 --trust-remote-code"


echo.
pause
