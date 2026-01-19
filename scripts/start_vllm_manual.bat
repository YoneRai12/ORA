@echo off
echo Starting vLLM in WSL...
wsl -d Ubuntu-22.04 nohup python3 -m vllm.entrypoints.openai.api_server --model Qwen/Qwen2.5-VL-32B-Instruct-AWQ --quantization awq --dtype half --gpu-memory-utilization 0.90 --max-model-len 2048 --enforce-eager --disable-custom-all-reduce --tensor-parallel-size 1 --port 8001 --trust-remote-code > vllm.log 2>&1 &
echo vLLM started on port 8001. Check vllm.log for details.
pause
