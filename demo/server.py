from mcp.server.fastmcp import FastMCP
from eval import grade_answer

server = FastMCP("Support answer grading")
server.tool()(grade_answer)

if __name__ == "__main__":
    server.run(transport="stdio")
