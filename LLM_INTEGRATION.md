# LLM Integration Guide for EmailMCP

## Overview

EmailMCP now includes LLM inference capabilities that allow Large Language Models to interact with the email service. The LLM can understand user intents, suggest actions, and execute operations on the EmailMCP service.

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   LLM API   │─────▶│  temp.py     │─────▶│  EmailMCP   │
│   Client    │      │  (Inference) │      │  Service    │
└─────────────┘      └──────────────┘      └─────────────┘
```

The LLM integration consists of:
1. **temp.py**: Contains the LLM inference logic and router
2. **main.py**: Integrates the LLM router into the FastAPI application
3. **API Endpoints**: Three main endpoints for LLM interaction

## Getting Started

### 1. Server Setup

The LLM integration is automatically included when you start the EmailMCP server:

```bash
# Start the server
uvicorn src.mcp.main:app --host 0.0.0.0 --port 8080

# Or using Docker
docker-compose up
```

### 2. API Endpoints

#### Check LLM Capabilities

Get information about available LLM capabilities:

```bash
curl http://localhost:8080/llm/capabilities
```

Response:
```json
{
  "capabilities": ["send_email", "get_analytics", "check_status"],
  "description": "LLM inference server integrated with EmailMCP",
  "version": "1.0.0",
  "endpoints": [...]
}
```

#### LLM Inference

Send a prompt to the LLM for processing:

```bash
curl -X POST http://localhost:8080/llm/inference \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-llm-api-key" \
  -d '{
    "prompt": "Send an email to user about monthly report",
    "user_id": "user123",
    "max_tokens": 500,
    "temperature": 0.7
  }'
```

Response:
```json
{
  "response": "LLM response...",
  "action": "send_email",
  "parameters": {
    "suggested_subject": "Monthly Report",
    "suggested_body": "..."
  },
  "timestamp": "2025-10-06T12:00:00"
}
```

#### Execute LLM Action

Execute an action suggested by the LLM:

```bash
curl -X POST http://localhost:8080/llm/execute-action \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-llm-api-key" \
  -H "X-MCP-API-Key: your-mcp-api-key" \
  -d '{
    "action_type": "send_email",
    "user_id": "user123",
    "parameters": {
      "to": ["recipient@example.com"],
      "subject": "Test Email",
      "body": "Hello from LLM",
      "body_type": "text"
    }
  }'
```

## Supported Actions

### 1. Send Email

Execute email sending through EmailMCP:

```json
{
  "action_type": "send_email",
  "user_id": "user123",
  "parameters": {
    "to": ["recipient@example.com"],
    "subject": "Email Subject",
    "body": "Email body content",
    "body_type": "text",
    "cc": ["cc@example.com"],
    "bcc": ["bcc@example.com"]
  }
}
```

### 2. Get Analytics

Retrieve email analytics for a user:

```json
{
  "action_type": "get_analytics",
  "user_id": "user123",
  "parameters": {}
}
```

### 3. Check Status

Check the health status of the EmailMCP service:

```json
{
  "action_type": "check_status",
  "user_id": "user123",
  "parameters": {}
}
```

## Integration Examples

### Python Example

See `examples/llm_integration_example.py` for a complete working example:

```python
import httpx
import asyncio

async def llm_inference():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8080/llm/inference",
            headers={
                "X-API-Key": "your-api-key",
                "Content-Type": "application/json"
            },
            json={
                "prompt": "Check email analytics",
                "user_id": "user123"
            }
        )
        return response.json()

asyncio.run(llm_inference())
```

### JavaScript Example

```javascript
const response = await fetch('http://localhost:8080/llm/inference', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'your-api-key'
  },
  body: JSON.stringify({
    prompt: 'Send an email to user about updates',
    user_id: 'user123',
    max_tokens: 500
  })
});

const result = await response.json();
console.log(result);
```

### cURL Example

```bash
# Inference
curl -X POST http://localhost:8080/llm/inference \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key" \
  -d '{"prompt": "What are my email statistics?", "user_id": "user123"}'

# Execute Action
curl -X POST http://localhost:8080/llm/execute-action \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key" \
  -H "X-MCP-API-Key: mcp-key" \
  -d '{
    "action_type": "check_status",
    "user_id": "user123",
    "parameters": {}
  }'
```

## Authentication

The LLM endpoints require two API keys:

1. **X-API-Key**: For authenticating LLM requests
2. **X-MCP-API-Key**: For authenticating actions on EmailMCP service

Configure these in your `.env` file:

```env
LLM_API_KEY=your-secure-llm-api-key
MCP_API_KEY=emailmcp-oWyFsIqTUhnoOZQDaEPBfMKOQV2ElAtw
```

## Customizing the LLM

The current implementation in `temp.py` uses a mock LLM. To integrate with a real LLM service:

### OpenAI Integration

```python
import openai

async def llm_inference(prompt: str, context: Optional[Dict] = None, 
                       max_tokens: int = 500, temperature: float = 0.7):
    response = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an email assistant..."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens,
        temperature=temperature
    )
    
    return {
        "response": response.choices[0].message.content,
        "action": parse_action(response.choices[0].message.content),
        "parameters": extract_parameters(response.choices[0].message.content)
    }
```

### Anthropic Claude Integration

```python
import anthropic

async def llm_inference(prompt: str, context: Optional[Dict] = None,
                       max_tokens: int = 500, temperature: float = 0.7):
    client = anthropic.Anthropic(api_key="your-api-key")
    
    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return {
        "response": message.content[0].text,
        "action": parse_action(message.content[0].text),
        "parameters": extract_parameters(message.content[0].text)
    }
```

### Local Model Integration

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("your-model")
tokenizer = AutoTokenizer.from_pretrained("your-model")

async def llm_inference(prompt: str, context: Optional[Dict] = None,
                       max_tokens: int = 500, temperature: float = 0.7):
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_length=max_tokens)
    response = tokenizer.decode(outputs[0])
    
    return {
        "response": response,
        "action": parse_action(response),
        "parameters": extract_parameters(response)
    }
```

## API Documentation

Once the server is running, you can access:

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **OpenAPI JSON**: http://localhost:8080/openapi.json

## Testing

Run the example script to test the integration:

```bash
python3 examples/llm_integration_example.py
```

## Troubleshooting

### Server won't start
- Check that port 8080 is not already in use
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check the logs for import errors

### LLM endpoints return 401
- Verify you're including the `X-API-Key` header
- Check that the API key is valid

### Actions fail to execute
- Verify the `X-MCP-API-Key` is correct
- Ensure the user has proper Gmail OAuth setup
- Check the EmailMCP service logs

## Production Considerations

1. **Replace Mock LLM**: Integrate with a real LLM service (OpenAI, Claude, etc.)
2. **API Key Management**: Use environment variables or secrets manager
3. **Rate Limiting**: Add rate limiting for LLM endpoints
4. **Logging**: Add comprehensive logging for debugging
5. **Monitoring**: Monitor LLM API costs and usage
6. **Caching**: Cache common LLM responses to reduce costs
7. **Error Handling**: Add retry logic for LLM API failures

## Next Steps

1. Review the code in `temp.py` to understand the implementation
2. Run the example script to see it in action
3. Customize the LLM integration for your use case
4. Add more action types as needed
5. Integrate with your preferred LLM service

## Support

For issues or questions:
- Check the API documentation at `/docs`
- Review the example code in `examples/llm_integration_example.py`
- See the main README.md for general EmailMCP documentation
