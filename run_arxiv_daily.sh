#!/bin/bash

cd "$(dirname "$0")" || exit 1

/home/jli265/miniconda3/envs/llm_factory/bin/python alignment_daily.py

/home/jli265/miniconda3/envs/llm_factory/bin/python backdoor_daily.py