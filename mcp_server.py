# mcp_server.py
import anyio
import click
import mcp.types as types
from mcp.server.lowlevel import Server
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--port", default=8000, help="Port to listen on for SSE")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport type",
)
def main(port: int, transport: str) -> int:
    # 创建一个 MCP 服务器
    logger.info("Creating MCP server instance")
    app = Server("MetaGPTIntegration")

    # 统一的工具处理器
    @app.call_tool()
    async def tool_handler(
        name: str, arguments: dict
    ) -> list[types.TextContent]:
        logger.info(f"Processing tool request: {name}")
        
        if name == "add_numbers":
            if "a" not in arguments or "b" not in arguments:
                raise ValueError("Missing required arguments 'a' and 'b'")
            a = arguments["a"]
            b = arguments["b"]
            logger.info(f"Adding numbers: {a} + {b}")
            result = a + b
            return [types.TextContent(type="text", text=str(result))]
            
        elif name == "greeting":
            if "name" not in arguments:
                raise ValueError("Missing required argument 'name'")
            user_name = arguments["name"]
            logger.info(f"Getting greeting for {user_name}")
            greeting = f"Hello, {user_name}!"
            return [types.TextContent(type="text", text=greeting)]
            
        else:
            raise ValueError(f"Unknown tool: {name}")

    # 列出可用工具
    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="add_numbers",
                description="Add two numbers",
                inputSchema={
                    "type": "object",
                    "required": ["a", "b"],
                    "properties": {
                        "a": {
                            "type": "integer",
                            "description": "First number",
                        },
                        "b": {
                            "type": "integer",
                            "description": "Second number",
                        }
                    },
                },
            ),
            types.Tool(
                name="greeting",
                description="Get a personalized greeting",
                inputSchema={
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name to greet",
                        }
                    },
                },
            )
        ]

    logger.info("Starting MCP server")
    if transport == "sse":
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )

        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        import uvicorn

        uvicorn.run(starlette_app, host="0.0.0.0", port=port)
    else:
        from mcp.server.stdio import stdio_server

        async def arun():
            async with stdio_server() as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )

        anyio.run(arun)

    return 0

if __name__ == "__main__":
    main()