import os
from dotenv import load_dotenv

load_dotenv(".env.local")

print(f"NPI_MCP_URL={os.getenv('NPI_MCP_URL')}")
print(f"CRED_DB_MCP_URL={os.getenv('CRED_DB_MCP_URL')}")
print(f"ALERT_MCP_URL={os.getenv('ALERT_MCP_URL')}")
