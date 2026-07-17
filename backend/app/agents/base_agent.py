"""Base MARA Agent — wraps Microsoft Agent Framework's Agent class.

All MARA specialised agents inherit from BaseMARAAgent.

Design rules:
    ✅ LLM client is always provided by LLMFactory (provider-swappable).
    ✅ All data access goes through MCPPlanningClient.
    ✅ Tool functions are plain async Python callables — no class boilerplate.
    ✅ LLM client is created lazily — app starts even without OPENAI_API_KEY.
    ❌ Subclasses must never import Planning Services.
    ❌ Subclasses must never perform numerical calculations.
"""

import logging
from typing import Any, Callable

from app.mcp.client import MCPPlanningClient

logger = logging.getLogger(__name__)


class BaseMARAAgent:
    """Thin wrapper around agent_framework.Agent with MCP client wiring.

    Every specialised MARA agent creates one instance of this class,
    passing its own tools (functions that call mcp_client.call_tool).

    The underlying agent_framework.Agent is created lazily on the first
    call to run(), so the application boots cleanly even when no API key
    is configured.

    Args:
        name:        Unique agent name shown in logs and agent traces.
        instructions: System prompt that defines the agent's role and behaviour.
        mcp_client:  Shared MCPPlanningClient instance (injected, not created here).
        tools:       List of plain async callables the agent can invoke.
    """

    def __init__(
        self,
        name: str,
        instructions: str,
        mcp_client: MCPPlanningClient,
        tools: list[Callable],
    ) -> None:
        self.name = name
        self.mcp_client = mcp_client
        self._instructions = instructions
        self._tools = tools
        self._agent: Any = None  # created lazily in run()

        logger.debug("Registered agent: %s with %d tool(s)", name, len(tools))

    def _get_agent(self) -> Any:
        """Return the agent_framework.Agent, creating it on first call."""
        if self._agent is None:
            from agent_framework import Agent
            from app.core.llm_factory import LLMFactory

            self._agent = Agent(
                name=self.name,
                client=LLMFactory.create_client(),
                instructions=self._instructions,
                tools=self._tools,
            )
            logger.debug("Created Agent instance for: %s", self.name)
        return self._agent

    async def run(self, message: str, **kwargs: Any) -> Any:
        """Process a message and return the agent's response object.

        The agent will:
          1. Read the message.
          2. Decide which tool(s) to call (via the LLM).
          3. Call those tools through MCPPlanningClient.
          4. Synthesise the tool results into a natural language response.

        Args:
            message: User question or task description.
            **kwargs: Additional context passed to agent_framework.Agent.run().

        Returns:
            AgentResponse object.
        """
        logger.info("Agent %s processing: %.120s", self.name, message)
        result = await self._get_agent().run(message, **kwargs)
        if result.usage_details:
            logger.info(
                "Agent %s usage: prompt_tokens=%s, completion_tokens=%s, total_tokens=%s",
                self.name,
                result.usage_details.get("input_token_count"),
                result.usage_details.get("output_token_count"),
                result.usage_details.get("total_token_count"),
            )
        logger.debug("Agent %s result: %.200s", self.name, result.text)
        return result
