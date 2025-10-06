"""
Example script demonstrating how to use the LLM integration with EmailMCP

This script shows:
1. How to call the LLM inference endpoint
2. How to execute actions suggested by the LLM
3. How to integrate LLM with EmailMCP workflows
"""

import httpx
import asyncio
import json

# Configuration
BASE_URL = "http://localhost:8080"
LLM_API_KEY = "your-llm-api-key"
MCP_API_KEY = "emailmcp-oWyFsIqTUhnoOZQDaEPBfMKOQV2ElAtw"

async def llm_inference_example():
    """Example: Use LLM to understand user intent and suggest actions"""
    async with httpx.AsyncClient() as client:
        # Call LLM inference
        response = await client.post(
            f"{BASE_URL}/llm/inference",
            headers={
                "X-API-Key": LLM_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "prompt": "I need to check my email analytics for the last month",
                "user_id": "user123",
                "max_tokens": 500,
                "temperature": 0.7
            }
        )
        
        result = response.json()
        print("LLM Inference Result:")
        print(json.dumps(result, indent=2))
        print("\n")
        
        return result

async def execute_llm_action_example():
    """Example: Execute an action suggested by the LLM"""
    async with httpx.AsyncClient() as client:
        # Execute an action (e.g., check system status)
        response = await client.post(
            f"{BASE_URL}/llm/execute-action",
            headers={
                "X-API-Key": LLM_API_KEY,
                "X-MCP-API-Key": MCP_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "action_type": "check_status",
                "user_id": "user123",
                "parameters": {}
            }
        )
        
        result = response.json()
        print("Action Execution Result:")
        print(json.dumps(result, indent=2))
        print("\n")
        
        return result

async def send_email_via_llm_example():
    """Example: Use LLM to compose and send an email"""
    async with httpx.AsyncClient() as client:
        # First, get LLM suggestion
        inference_response = await client.post(
            f"{BASE_URL}/llm/inference",
            headers={
                "X-API-Key": LLM_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "prompt": "Send an email to test@example.com about our new feature launch",
                "user_id": "user123",
                "max_tokens": 500,
                "temperature": 0.7
            }
        )
        
        inference_result = inference_response.json()
        print("LLM Suggestion:")
        print(json.dumps(inference_result, indent=2))
        
        # If LLM suggests sending email, execute it
        if inference_result.get("action") == "send_email":
            print("\nExecuting email send action...")
            
            # Note: This requires a valid user with Gmail connected
            # For demo purposes, this shows the structure
            try:
                execute_response = await client.post(
                    f"{BASE_URL}/llm/execute-action",
                    headers={
                        "X-API-Key": LLM_API_KEY,
                        "X-MCP-API-Key": MCP_API_KEY,
                        "Content-Type": "application/json"
                    },
                    json={
                        "action_type": "send_email",
                        "user_id": "user123",
                        "parameters": {
                            "to": ["test@example.com"],
                            "subject": "New Feature Launch",
                            "body": "We're excited to announce our new feature!",
                            "body_type": "text"
                        }
                    }
                )
                
                execute_result = execute_response.json()
                print("Email Send Result:")
                print(json.dumps(execute_result, indent=2))
            except Exception as e:
                print(f"Note: Email sending requires a configured user: {e}")

async def check_llm_capabilities():
    """Example: Check available LLM capabilities"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/llm/capabilities")
        result = response.json()
        print("LLM Capabilities:")
        print(json.dumps(result, indent=2))
        print("\n")
        return result

async def main():
    """Run all examples"""
    print("=" * 60)
    print("EmailMCP + LLM Integration Examples")
    print("=" * 60)
    print("\n")
    
    # 1. Check capabilities
    print("1. Checking LLM Capabilities...")
    print("-" * 60)
    await check_llm_capabilities()
    
    # 2. LLM Inference
    print("2. LLM Inference Example...")
    print("-" * 60)
    await llm_inference_example()
    
    # 3. Execute Action
    print("3. Execute Action Example...")
    print("-" * 60)
    await execute_llm_action_example()
    
    # 4. Send Email (full workflow)
    print("4. Send Email via LLM Example...")
    print("-" * 60)
    await send_email_via_llm_example()
    
    print("\n")
    print("=" * 60)
    print("Examples Complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
