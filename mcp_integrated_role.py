# metagpt_integration.py
import asyncio
from metagpt.roles import Role
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPIntegratedRole(Role):
    def __init__(self, name, profile, goal, constraints):
        # 使用关键字参数初始化父类
        super().__init__(name=name, profile=profile, goal=goal, constraints=constraints)
        self._server_params = StdioServerParameters(
            command="python",
            args=["scripts/mcp_server.py"]
        )

    async def list_tools(self, session):
        """列出所有可用的工具"""
        try:
            tools = await session.list_tools()
            logger.info("Available tools:")
            for tool in tools.tools:
                logger.info(f"- {tool.name}: {tool.description}")
            return tools
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            return None

    async def call_add_numbers(self, session, a: int, b: int):
        """调用加法工具"""
        try:
            result = await session.call_tool("add_numbers", {"a": a, "b": b})
            logger.info(f"Result of add_numbers: {result.content[0].text}")
            return result
        except Exception as e:
            logger.error(f"Error calling add_numbers: {e}")
            return None

    async def call_greeting(self, session, name: str):
        """调用问候工具"""
        try:
            result = await session.call_tool("greeting", {"name": name})
            logger.info(f"Result of greeting: {result.content[0].text}")
            return result
        except Exception as e:
            logger.error(f"Error calling greeting: {e}")
            return None

    async def run(self, *args, **kwargs):
        """运行角色的主要逻辑"""
        logger.info("Starting MCP integrated role...")
        
        try:
            async with stdio_client(self._server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    logger.info("Connected to MCP server")

                    # 列出可用工具
                    await self.list_tools(session)

                    # 测试加法工具
                    await self.call_add_numbers(session, 2, 3)

                    # 测试问候工具
                    await self.call_greeting(session, "Alice")

        except Exception as e:
            logger.error(f"Error in MCP integration: {e}")
            raise

async def main():
    try:
        role = MCPIntegratedRole(
            name="MCPAgent",
            profile="MCP Integrated Agent",
            goal="Use MCP tools",
            constraints=""
        )
        await role.run()
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())