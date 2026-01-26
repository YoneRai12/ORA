@echo off
title ORA-vLLM-Server
echo [INFO] Starting vLLM (Ministral-3-14B-Reasoning)...
L:\ORADiscordBOT_Env\Scripts\python.exe -m vllm.entrypoints.openai.api_server --model mistralai/ministral-3-14b-reasoning --quantization awq --dtype half --gpu-memory-utilization 0.90 --max-model-len 2048 --enforce-eager --disable-custom-all-reduce --tensor-parallel-size 1 --port 8008 --trust-remote-code
pause
