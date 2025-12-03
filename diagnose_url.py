import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv(".env.local")

async def diagnose():
    url = os.getenv("NPI_MCP_URL")
    print(f"Testing URL: {url}")
    
    if not url:
        print("URL not found in env vars.")
        return

    try:
        async with httpx.AsyncClient() as client:
            print("Sending GET request...")
            response = await client.get(url, timeout=10.0)
            print(f"Status Code: {response.status_code}")
            print("Headers:")
            for k, v in response.headers.items():
                print(f"  {k}: {v}")
            print(f"Content (first 200 chars): {response.text[:200]}")
    except httpx.TimeoutException:
        print("Request timed out.")
    except Exception as e:
        print(f"Error: {e}")

    # Try with SSE headers and streaming
    try:
        async with httpx.AsyncClient() as client:
            print("\nSending GET request with Accept: text/event-stream (streaming)...")
            headers = {"Accept": "text/event-stream"}
            async with client.stream("GET", url, headers=headers, timeout=10.0) as response:
                print(f"Status Code: {response.status_code}")
                print("Headers:")
                for k, v in response.headers.items():
                    print(f"  {k}: {v}")
                
                print("\nReading stream...")
                count = 0
                async for line in response.aiter_lines():
                    if line:
                        print(f"Received: {line}")
                    count += 1
                    if count >= 20:
                        print("Reached limit of 20 lines. Stopping.")
                        break
    except httpx.TimeoutException:
        print("Request timed out (SSE stream).")
    except Exception as e:
        print(f"Error (SSE): {e}")

if __name__ == "__main__":
    asyncio.run(diagnose())
