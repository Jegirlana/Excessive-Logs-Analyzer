"""
Cliente para integração com LLM APIs (Claude, ChatGPT, Groq, Google Gemini e Puter).
Utiliza prompt caching para otimizar custos em análises repetitivas.
"""

import os
from typing import Optional

# Anthropic (Claude)
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    Anthropic = None

# OpenAI (ChatGPT)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

# Groq
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    Groq = None

# Google Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

# Puter (via HTTP bridge)
try:
    from src.utils.puter_client import PuterClient
    PUTER_AVAILABLE = True
except ImportError:
    PUTER_AVAILABLE = False
    PuterClient = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class LLMClient:
    """Cliente para realizar análises usando diferentes APIs de LLM."""

    def __init__(self, provider: str = "claude", model: str = None):
        """
        Inicializa o cliente LLM.

        Args:
            provider: Provedor de LLM ("claude", "chatgpt", "groq", "gemini", "puter")
            model: Nome do modelo específico (opcional)
        """
        self.provider = provider.lower()

        if self.provider == "claude":
            self._init_claude(model)
        elif self.provider == "chatgpt":
            self._init_chatgpt(model)
        elif self.provider == "groq":
            self._init_groq(model)
        elif self.provider == "gemini":
            self._init_gemini(model)
        elif self.provider == "puter":
            self._init_puter(model)
        else:
            raise ValueError(f"Provedor desconhecido: {provider}. Use 'claude', 'chatgpt', 'groq', 'gemini' ou 'puter'")

    def _init_claude(self, model: Optional[str] = None):
        """
        Inicializa cliente Claude.
        Tenta na ordem: Anthropic API direta → OpenRouter (gratuito).
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("Módulo 'openai' não está instalado. "
                            "Execute: pip install openai")

        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        openrouter_key = os.getenv("OPENROUTER_API_KEY")

        if anthropic_key and ANTHROPIC_AVAILABLE:
            # API oficial paga
            self.client = Anthropic(api_key=anthropic_key)
            self.model = model or os.getenv("CLAUDE_MODEL_NAME", "claude-3-5-sonnet-20241022")
            self._claude_backend = "anthropic"
        elif openrouter_key:
            # OpenRouter: proxy gratuito, usa interface OpenAI SDK
            self.client = OpenAI(
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers={"HTTP-Referer": "https://github.com/Jegirlana/Excessive-Logs-Analyzer"},
            )
            self.model = model or os.getenv("CLAUDE_MODEL_NAME", "anthropic/claude-3.5-haiku")
            self._claude_backend = "openrouter"
        else:
            raise ValueError(
                "Nenhuma chave configurada para Claude. "
                "Configure ANTHROPIC_API_KEY (pago) ou OPENROUTER_API_KEY (gratuito) no arquivo .env"
            )

    def _init_chatgpt(self, model: Optional[str] = None):
        """
        Inicializa cliente ChatGPT.
        Tenta na ordem: OpenAI API direta → GitHub Models (gratuito).
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("Módulo 'openai' não está instalado. "
                            "Execute: pip install openai")

        openai_key = os.getenv("OPENAI_API_KEY")
        github_token = os.getenv("GITHUB_TOKEN")

        if openai_key:
            # API oficial paga
            self.client = OpenAI(api_key=openai_key)
            self.model = model or os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
        elif github_token:
            # GitHub Models: tier gratuito com gpt-4o-mini
            self.client = OpenAI(
                api_key=github_token,
                base_url="https://models.inference.ai.azure.com",
            )
            self.model = model or os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
        else:
            raise ValueError(
                "Nenhuma chave configurada para ChatGPT. "
                "Configure OPENAI_API_KEY (pago) ou GITHUB_TOKEN (gratuito) no arquivo .env"
            )

    def _init_groq(self, model: Optional[str] = None):
        """Inicializa cliente Groq."""
        if not GROQ_AVAILABLE:
            raise ImportError("Módulo 'groq' não está instalado. "
                            "Execute: pip install groq")

        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY não encontrada. Configure no arquivo .env")

        self.client = Groq(api_key=self.api_key)
        self.model = model or os.getenv("GROQ_MODEL_NAME", "openai/gpt-oss-20b")

    def _init_gemini(self, model: Optional[str] = None):
        """Inicializa cliente Google Gemini."""
        if not GEMINI_AVAILABLE:
            raise ImportError("Módulo 'google-generativeai' não está instalado. "
                            "Execute: pip install google-generativeai")

        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY não encontrada. Configure no arquivo .env")

        genai.configure(api_key=self.api_key)
        self.model = model or os.getenv("GEMINI_MODEL_NAME", "gemini-flash-latest")
        self.client = genai.GenerativeModel(self.model)

    def _init_puter(self, model: Optional[str] = None):
        """Inicializa cliente Puter (via HTTP bridge)."""
        if not PUTER_AVAILABLE:
            raise ImportError("Módulo 'puter_client' não está disponível. "
                            "Verifique se o arquivo src/utils/puter_client.py existe")

        # Puter usa HTTP bridge, não precisa de API key aqui
        # A autenticação é feita no servidor Node.js
        bridge_url = os.getenv("PUTER_BRIDGE_URL", "http://localhost:3000")

        try:
            self.client = PuterClient(base_url=bridge_url)
            self.model = model or os.getenv("PUTER_MODEL_NAME", "gpt-5.4-nano")
        except ConnectionError as e:
            raise ConnectionError(
                f"Não foi possível conectar ao Puter Bridge em {bridge_url}. "
                f"Certifique-se de que o servidor está rodando (cd puter-bridge && npm start). "
                f"Erro: {e}"
            )

    def analyze_with_caching(self, system_prompt: str, user_prompt: str,
                            cached_content: str = None) -> str:
        """
        Realiza análise usando prompt caching para otimização.

        Args:
            system_prompt: Prompt do sistema com instruções
            user_prompt: Prompt do usuário com dados a analisar
            cached_content: Conteúdo a ser cacheado (ex: documentação, contexto grande)

        Returns:
            Resposta do modelo em formato texto
        """
        if self.provider == "claude":
            return self._analyze_claude_with_caching(system_prompt, user_prompt, cached_content)
        elif self.provider == "chatgpt":
            return self._analyze_chatgpt(system_prompt, user_prompt, cached_content)
        elif self.provider == "groq":
            return self._analyze_groq(system_prompt, user_prompt, cached_content)
        elif self.provider == "gemini":
            return self._analyze_gemini(system_prompt, user_prompt, cached_content)
        elif self.provider == "puter":
            return self._analyze_puter(system_prompt, user_prompt, cached_content)

    def _analyze_claude_with_caching(self, system_prompt: str, user_prompt: str,
                                    cached_content: str = None) -> str:
        """Análise com Claude — Anthropic SDK (com caching) ou OpenRouter (interface OpenAI)."""
        if getattr(self, "_claude_backend", "anthropic") == "anthropic":
            messages = [{"role": "user", "content": user_prompt}]
            if cached_content:
                system = [
                    {"type": "text", "text": system_prompt},
                    {"type": "text", "text": cached_content, "cache_control": {"type": "ephemeral"}},
                ]
            else:
                system = system_prompt
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system,
                messages=messages,
            )
            return response.content[0].text
        else:
            # OpenRouter usa interface OpenAI
            full_system = system_prompt
            if cached_content:
                full_system = f"{system_prompt}\n\nContexto adicional:\n{cached_content}"
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": full_system},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=4096,
                temperature=0.7,
            )
            return response.choices[0].message.content

    def _analyze_chatgpt(self, system_prompt: str, user_prompt: str,
                        cached_content: str = None) -> str:
        """Análise com ChatGPT/OpenAI."""
        # Combina system prompt com cached content se fornecido
        full_system = system_prompt
        if cached_content:
            full_system = f"{system_prompt}\n\nContexto adicional:\n{cached_content}"

        messages = [
            {"role": "system", "content": full_system},
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=4096,
            temperature=0.7
        )

        return response.choices[0].message.content

    def _analyze_groq(self, system_prompt: str, user_prompt: str,
                     cached_content: str = None) -> str:
        """Análise com Groq (API compatível com OpenAI)."""
        # Combina system prompt com cached content se fornecido
        full_system = system_prompt
        if cached_content:
            full_system = f"{system_prompt}\n\nContexto adicional:\n{cached_content}"

        messages = [
            {"role": "system", "content": full_system},
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=4096,
            temperature=0.7
        )

        return response.choices[0].message.content

    def _analyze_gemini(self, system_prompt: str, user_prompt: str,
                       cached_content: str = None) -> str:
        """Análise com Google Gemini."""
        # Gemini combina system e user prompt em um único texto
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        if cached_content:
            full_prompt = f"{system_prompt}\n\nContexto adicional:\n{cached_content}\n\n{user_prompt}"

        response = self.client.generate_content(
            full_prompt,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 4096,
            }
        )

        return response.text

    def _analyze_puter(self, system_prompt: str, user_prompt: str,
                      cached_content: str = None) -> str:
        """Análise com Puter (via HTTP bridge)."""
        # Usa o método analyze_with_caching do PuterClient
        return self.client.analyze_with_caching(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            cached_content=cached_content or "",
            model=self.model
        )

    def analyze_simple(self, prompt: str) -> str:
        """
        Análise simples sem caching.

        Args:
            prompt: Prompt completo para análise

        Returns:
            Resposta do modelo
        """
        if self.provider == "claude":
            if getattr(self, "_claude_backend", "anthropic") == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.content[0].text
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=4096,
                    temperature=0.7,
                )
                return response.choices[0].message.content

        elif self.provider == "chatgpt":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096,
                temperature=0.7
            )
            return response.choices[0].message.content

        elif self.provider == "groq":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096,
                temperature=0.7
            )
            return response.choices[0].message.content

        elif self.provider == "gemini":
            response = self.client.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 4096,
                }
            )
            return response.text

        elif self.provider == "puter":
            response = self.client.chat(
                prompt=prompt,
                model=self.model,
                temperature=0.7,
                max_tokens=4096
            )
            return self.client._extract_text_from_response(response)
