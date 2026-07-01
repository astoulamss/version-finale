import sys
import os

# Ensure ydays is in path
sys.path.insert(0, "/app")

from ai.utils.llm_client import call_llm

try:
    print("Calling Mistral...")
    res = call_llm("System", "Hello")
    print("Result:")
    print(res)
except Exception as e:
    import traceback
    traceback.print_exc()
