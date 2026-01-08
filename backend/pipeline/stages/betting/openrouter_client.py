"""
OpenRouter API Client

Wrapper for OpenRouter multi-model LLM API.

Supports all 8 agent models:
- GPT-4o, Claude 3.5, Grok-2, Gemini Pro
- Llama 3.1, Mistral Large, DeepSeek V2, Qwen Max

Methods:
- generate_decision(model_slug, prompt): Get betting decision
- parse_json_response(response): Extract structured decision
"""
