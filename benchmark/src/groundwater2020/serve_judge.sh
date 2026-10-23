#!/usr/bin/env bash
# Start the local Qwen3.8-27B judge for grade_local.py on GPUs 0,1 (change GPUS if they are busy).
# Then: python grade_local.py answers_<model>.md   (use the vllm conda env's python for `openai`)
GPUS=${GPUS:-0,1}
V=/data/local/home/xizhan/miniconda3/envs/vllm/bin
VLLM_USE_FLASHINFER_SAMPLER=0 CUDA_VISIBLE_DEVICES=$GPUS HF_HUB_CACHE=/data/huggingface/hub HF_HUB_OFFLINE=1 \
exec $V/vllm serve Qwen/Qwen3.8-27B --served-model-name qwen3.8-27b --tensor-parallel-size 2 \
  --language-model-only --reasoning-parser qwen3 --max-model-len 32768 --gpu-memory-utilization 0.9 \
  --host 127.0.0.1 --port 8137
