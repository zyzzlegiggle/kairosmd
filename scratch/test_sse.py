from mcp.server.fastmcp import FastMCP
import os

mcp = FastMCP("Test")

@mcp.tool()
def hello():
    return "world"

if __name__ == "__main__":
    print("Attempting to run with transport='sse'...")
    try:
        mcp.run(transport="sse")
    except Exception as e:
        print(f"Failed: {e}")
