import sys
import os

# Add src to path so we can import the package
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from credentialwatch_agent.main import demo

if __name__ == "__main__":
    demo.launch(ssr_mode=False)
