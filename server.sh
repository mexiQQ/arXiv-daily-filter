# pip install --upgrade vllm
# pip install --upgrade mistral_common

vllm serve mistralai/Mistral-Small-24B-Instruct-2501 --tokenizer_mode mistral --config_format mistral --load_format mistral --tool-call-parser mistral --enable-auto-tool-choice --max-model-len 8192 --tensor-parallel-size 2 --gpu-memory-utilization 0.85