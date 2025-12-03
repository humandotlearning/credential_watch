import logging
import sys
import os

# Add src to path so we can import credentialwatch_agent
sys.path.append(os.path.join(os.getcwd(), "src"))

from credentialwatch_agent.mcp_client import mcp_client

# Configure root logger as main.py does
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Log something via mcp_client
print("--- START LOG TEST ---")
mcp_client.logger.info("This should appear exactly ONCE.")
print("--- END LOG TEST ---")
