"""Quick test of essential packages"""
print("Testing essential packages...")

essentials = [
    "langchain_core",
    "langgraph", 
    "langchain",
    "langchain_openai",
    "langchain_anthropic",
    "langchain_google_genai",
    "fastapi",
    "pydantic"
]

for package in essentials:
    try:
        __import__(package)
        print(f"✓ {package}")
    except ImportError:
        print(f"✗ {package}")

print("\nTesting imports...")
try:
    from langgraph.graph import StateGraph
    from langchain_core.messages import BaseMessage
    from fastapi import FastAPI
    from pydantic import BaseModel
    print("✓ Core imports work!")
except Exception as e:
    print(f"✗ Import error: {e}")