import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# Load env vars
load_dotenv(".env.local")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("debug_mcp")
logger.setLevel(logging.DEBUG)

# Silence noisy loggers
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

from credentialwatch_agent.mcp_client import mcp_client

async def debug_mcp():
    logger.info("Starting MCP debug script...")
    
    # Check environment variables
    logger.info(f"NPI_MCP_URL: {os.getenv('NPI_MCP_URL')}")
    logger.info(f"CRED_DB_MCP_URL: {os.getenv('CRED_DB_MCP_URL')}")
    logger.info(f"ALERT_MCP_URL: {os.getenv('ALERT_MCP_URL')}")

    try:
        logger.info("Connecting to MCP servers...")
        await mcp_client.connect()
        logger.info("Connected to MCP servers.")
    except Exception as e:
        logger.error(f"Failed to connect to MCP servers: {e}", exc_info=True)
        return

    # Test NPI Tool
    logger.info("\n--- Testing NPI Tool: search_providers ---")
    try:
        result = await mcp_client.call_tool("npi", "search_providers", {"query": "cardiology"})
        logger.info(f"NPI Tool Result: {result}")
    except Exception as e:
        logger.error(f"NPI Tool Call Failed: {e}", exc_info=True)

    # Test Cred DB Tool
    logger.info("\n--- Testing Cred DB Tool: list_expiring_credentials ---")
    try:
        result = await mcp_client.call_tool("cred_db", "list_expiring_credentials", {"window_days": 90})
        logger.info(f"Cred DB Tool Result: {result}")
    except Exception as e:
        logger.error(f"Cred DB Tool Call Failed: {e}", exc_info=True)

    logger.info("\nClosing connections...")
    await mcp_client.close()
    logger.info("Done.")

if __name__ == "__main__":
    asyncio.run(debug_mcp())
