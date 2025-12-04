import asyncio
import logging
from credentialwatch_agent.main import run_chat_turn

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO)

async def main():
    print("Running verification for refactored interactive query...")
    
    # Test query
    query = "Find a cardiologist in NY"
    history = []
    
    try:
        response = await run_chat_turn(query, history)
        print("\n--- Response ---")
        print(response)
        print("----------------")
        print("Verification SUCCESS: run_chat_turn executed without errors.")
    except Exception as e:
        print(f"\nVerification FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
