"""LLM client factory for Microsoft Agent Framework — Azure OpenAI provider.

Uses agent_framework.openai.OpenAIChatClient with Azure-specific parameters:
    azure_endpoint  — your Azure OpenAI resource URL
    api_key         — Azure resource key
    model           — deployment name (e.g. gpt-4.1)
    api_version     — Azure API version (e.g. 2024-08-01-preview)

To switch provider in future, update only the four AZURE_OPENAI_* env vars
in .env — zero code changes required.  The same OpenAIChatClient supports
plain OpenAI too (omit azure_endpoint / api_version, set api_key + base_url).
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class LLMFactory:
    """Factory that creates a configured Azure OpenAI chat client.

    All MARA agents obtain their LLM client through this factory so that
    provider credentials and model selection are centralised in one place.

    Client creation is deferred (lazy) — the application boots cleanly even
    when credentials are not yet configured, which is safe for local
    development and integration tests that do not exercise the Copilot.
    """

    @staticmethod
    def create_client() -> Any:
        """Create and return an Azure-OpenAI-backed OpenAIChatClient.

        Reads all credentials from application settings at call time so
        that pydantic-settings has fully loaded .env before we touch them.

        Returns:
            OpenAIChatClient configured for Azure OpenAI.

        Raises:
            ValueError: If AZURE_OPENAI_API_KEY or AZURE_OPENAI_ENDPOINT
                        are not set in the environment.
        """
        # Late import — prevents the openai SDK from validating credentials
        # at module load time, which would crash startup if the key is absent.
        from agent_framework.openai import OpenAIChatClient
        from app.core.config import settings

        if not settings.AZURE_OPENAI_API_KEY:
            raise ValueError(
                "AZURE_OPENAI_API_KEY is not set. "
                "Add it to your .env file before using the Planning Copilot. "
                "All other planning API endpoints remain available without it."
            )
        if not settings.AZURE_OPENAI_ENDPOINT:
            raise ValueError(
                "AZURE_OPENAI_ENDPOINT is not set. "
                "Example: https://maqopenai.openai.azure.com/"
            )

        logger.info(
            "Creating Azure OpenAI client | deployment=%s endpoint=%s api_version=%s",
            settings.AZURE_OPENAI_DEPLOYMENT,
            settings.AZURE_OPENAI_ENDPOINT,
            settings.AZURE_OPENAI_API_VERSION,
        )

        from openai import AsyncAzureOpenAI

        async_client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            max_retries=5,
        )

        return OpenAIChatClient(
            model=settings.AZURE_OPENAI_DEPLOYMENT,
            async_client=async_client,
        )
