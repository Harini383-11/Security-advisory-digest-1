#!/usr/bin/env python3
import inspect
from src.modules import dedup, rag, llm_service, agent

for m, name in [(dedup, 'dedup'), (rag, 'rag'), (llm_service, 'llm_service'), (agent, 'agent')]:
    classes = [x for x in dir(m) if inspect.isclass(getattr(m, x)) and not x.startswith('_')]
    print(f"{name}: {classes}")
