import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

# Import clients conditionally to avoid hard dependencies if not used
try:
    from anthropic import AsyncAnthropic
except ImportError:
    AsyncAnthropic = None

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

from backend.config import Settings

logger = logging.getLogger(__name__)

class LLMEngine:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.templates_dir = settings.templates.directory

        # Ensure templates dir exists
        if not self.templates_dir.exists():
            logger.warning(f"Templates directory not found: {self.templates_dir}")
            self.env = None
        else:
            self.env = Environment(loader=FileSystemLoader(self.templates_dir))

        self.anthropic_client = None
        self.openai_client = None
        self.ollama_client = None

    def _get_anthropic_client(self):
        if not AsyncAnthropic:
            raise ImportError("anthropic package not installed")
        if not self.anthropic_client:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            self.anthropic_client = AsyncAnthropic(api_key=api_key)
        return self.anthropic_client

    def _get_openai_client(self):
        if not AsyncOpenAI:
            raise ImportError("openai package not installed")
        if not self.openai_client:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self.openai_client = AsyncOpenAI(api_key=api_key)
        return self.openai_client

    def _get_ollama_client(self):
        # Ollama typically uses OpenAI compatible API or raw HTTP
        # For simplicity, we'll use OpenAI client pointing to Ollama base_url
        if not AsyncOpenAI:
            raise ImportError("openai package not installed (required for Ollama wrapper)")
        if not self.ollama_client:
            base_url = self.settings.llm.ollama.base_url
            self.ollama_client = AsyncOpenAI(
                base_url=f"{base_url}/v1",
                api_key="ollama" # required but ignored
            )
        return self.ollama_client

    def render_template(self, template_name: str, **kwargs) -> str:
        if not self.env:
            raise FileNotFoundError("Templates directory not configured or missing")

        # Add .j2 extension if missing
        if not template_name.endswith(".j2"):
            template_name += ".j2"

        try:
            template = self.env.get_template(template_name)
            return template.render(**kwargs)
        except TemplateNotFound:
            raise FileNotFoundError(f"Template '{template_name}' not found in {self.templates_dir}")

    async def refine_text(self, text: str, template_name: str, provider: Optional[str] = None) -> str:
        """
        Refine text using an LLM and a prompt template.
        """
        # Render prompt
        prompt = self.render_template(template_name, text=text)

        # Determine provider
        if not provider:
            provider = self.settings.llm.default_provider

        logger.info(f"Refining text with template '{template_name}' using provider '{provider}'")

        if provider == "anthropic":
            client = self._get_anthropic_client()
            model = self.settings.llm.anthropic.model
            max_tokens = self.settings.llm.anthropic.max_tokens

            response = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text

        elif provider == "openai":
            client = self._get_openai_client()
            model = self.settings.llm.openai.model
            max_tokens = self.settings.llm.openai.max_tokens

            response = await client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content

        elif provider == "ollama":
            client = self._get_ollama_client()
            model = self.settings.llm.ollama.model
            # Ollama might ignore max_tokens or use options

            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content

        else:
            raise ValueError(f"Unknown provider: {provider}")
