"""
Cliente para integração com LLM APIs (Claude, ChatGPT, Groq, Google Gemini e Puter).
Utiliza prompt caching para otimizar custos em análises repetitivas.
"""

import os
import time
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


# Preço por 1 000 tokens (USD). Atualizar conforme tabelas oficiais dos provedores.
_MODEL_PRICING = {
    # Anthropic (direto)
    "claude-3-5-sonnet-20241022":      {"input": 0.003,   "output": 0.015},
    # OpenRouter — gratuito = sem custo, mas registra tokens
    "anthropic/claude-haiku-4.5":      {"input": 0.0,     "output": 0.0},
    "anthropic/claude-haiku-5.5":      {"input": 0.0,     "output": 0.0},
    "anthropic/claude-sonnet-4.5":     {"input": 0.0,     "output": 0.0},
    "anthropic/claude-3.5-haiku:free": {"input": 0.0,     "output": 0.0},
    # OpenAI direto
    "gpt-4o-mini":                     {"input": 0.00015, "output": 0.0006},
    # GitHub Models — gratuito local
    "openai/gpt-4o-mini":              {"input": 0.0,     "output": 0.0},
    # Groq — gratuito (free tier)
    "llama-3.3-70b-versatile":         {"input": 0.0,     "output": 0.0},
    # Gemini — gratuito (free tier)
    "models/gemini-2.5-flash":         {"input": 0.0,     "output": 0.0},
    "gemini-2.5-flash":                {"input": 0.0,     "output": 0.0},
    "models/gemini-flash-latest":      {"input": 0.0,     "output": 0.0},
}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = _MODEL_PRICING.get(model, {"input": 0.0, "output": 0.0})
    return round(
        (input_tokens / 1000) * pricing["input"] +
        (output_tokens / 1000) * pricing["output"],
        6,
    )


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
        # Acumulador de recursos: preenchido a cada chamada à API
        self.resource_usage = {
            "calls":          0,
            "retries":        0,
            "input_tokens":   0,
            "output_tokens":  0,
            "total_tokens":   0,
            "estimated_cost_usd": 0.0,
            "last_status":    None,   # "ok" | "error" | "fallback"
            "errors":         [],
        }

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

    def _record_usage(self, input_tokens: int, output_tokens: int, status: str = "ok", error: str = None):
        """Acumula tokens, custo e status de uma chamada."""
        self.resource_usage["calls"] += 1
        self.resource_usage["input_tokens"] += input_tokens
        self.resource_usage["output_tokens"] += output_tokens
        self.resource_usage["total_tokens"] += input_tokens + output_tokens
        self.resource_usage["estimated_cost_usd"] = round(
            self.resource_usage["estimated_cost_usd"] +
            _estimate_cost(self.model, input_tokens, output_tokens),
            6,
        )
        self.resource_usage["last_status"] = status
        if error:
            self.resource_usage["errors"].append(error)

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
            # OpenRouter via interface OpenAI SDK
            self.client = OpenAI(
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers={"HTTP-Referer": "https://github.com/Jegirlana/Excessive-Logs-Analyzer"},
            )
            self.model = model or os.getenv("CLAUDE_MODEL_NAME", "anthropic/claude-haiku-4.5")
            self._claude_backend = "openrouter"
            # Modelos de fallback em ordem crescente de custo
            self._openrouter_fallbacks = [
                "anthropic/claude-haiku-4.5",
                "anthropic/claude-haiku-5.5",
                "anthropic/claude-sonnet-4.5",
            ]
        else:
            raise ValueError(
                "Nenhuma chave configurada para Claude. "
                "Configure ANTHROPIC_API_KEY (pago) ou OPENROUTER_API_KEY (gratuito) no arquivo .env"
            )

    def _init_chatgpt(self, model: Optional[str] = None):
        """
        Inicializa cliente ChatGPT.
        Ordem: OPENAI_API_KEY (pago) → GitHub Models via gh auth (gratuito, só local).
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("Módulo 'openai' não está instalado. "
                            "Execute: pip install openai")

        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.client = OpenAI(api_key=openai_key)
            self.model = model or os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
            self._chatgpt_backend = "openai"
            return

        # Tenta token do gh CLI (funciona localmente após 'gh auth login')
        github_token = self._get_gh_cli_token()
        if github_token:
            self.client = OpenAI(
                base_url="https://models.github.ai/inference",
                api_key=github_token,
            )
            self.model = model or os.getenv("OPENAI_MODEL_NAME", "openai/gpt-4o-mini")
            self._chatgpt_backend = "github"
            return

        raise ValueError(
            "Nenhuma chave configurada para ChatGPT. "
            "Execute 'gh auth login' para usar GitHub Models gratuitamente (local), "
            "ou configure OPENAI_API_KEY no arquivo .env"
        )

    @staticmethod
    def _get_gh_cli_token() -> Optional[str]:
        """Lê o token OAuth do gh CLI em ~/.config/gh/hosts.yml."""
        import subprocess
        try:
            result = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True, text=True, timeout=5,
            )
            token = result.stdout.strip()
            if token and not result.returncode:
                return token
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return None

    def _init_groq(self, model: Optional[str] = None):
        """Inicializa cliente Groq."""
        if not GROQ_AVAILABLE:
            raise ImportError("Módulo 'groq' não está instalado. "
                            "Execute: pip install groq")

        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY não encontrada. Configure no arquivo .env")

        self.client = Groq(api_key=self.api_key)
        self.model = model or os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")

    def _init_gemini(self, model: Optional[str] = None):
        """Inicializa cliente Google Gemini."""
        if not GEMINI_AVAILABLE:
            raise ImportError("Módulo 'google-generativeai' não está instalado. "
                            "Execute: pip install google-generativeai")

        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY não encontrada. Configure no arquivo .env")

        genai.configure(api_key=self.api_key)
        self.model = model or os.getenv("GEMINI_MODEL_NAME", "models/gemini-2.5-flash")
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

    def _openrouter_call(self, messages: list) -> str:
        """Chama OpenRouter com fallback sequencial de modelos em caso de 404/503."""
        models_to_try = [self.model] + [
            m for m in getattr(self, "_openrouter_fallbacks", []) if m != self.model
        ]
        last_error = None
        first = True
        for model_name in models_to_try:
            if not first:
                self.resource_usage["retries"] += 1
            first = False
            try:
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=4096,
                    temperature=0.7,
                    timeout=90,
                )
                usage = response.usage
                status = "fallback" if model_name != self.model else "ok"
                self._record_usage(
                    getattr(usage, "prompt_tokens", 0),
                    getattr(usage, "completion_tokens", 0),
                    status=status,
                )
                return response.choices[0].message.content
            except Exception as e:
                last_error = e
                err_str = str(e)
                if "404" in err_str or "No endpoints" in err_str or "503" in err_str:
                    self.resource_usage["retries"] += 1
                    self._record_usage(0, 0, status="error", error=err_str[:120])
                    continue
                self._record_usage(0, 0, status="error", error=str(e)[:120])
                raise
        raise last_error

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
                timeout=60,
            )
            self._record_usage(
                response.usage.input_tokens,
                response.usage.output_tokens,
            )
            return response.content[0].text
        else:
            # OpenRouter usa interface OpenAI
            full_system = system_prompt
            if cached_content:
                full_system = f"{system_prompt}\n\nContexto adicional:\n{cached_content}"
            messages = [
                {"role": "system", "content": full_system},
                {"role": "user", "content": user_prompt},
            ]
            return self._openrouter_call(messages)

    def _chatgpt_call(self, messages: list) -> str:
        """Chama ChatGPT via OpenAI API ou GitHub Models (local)."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=4096,
            temperature=0.7,
            timeout=90,
        )
        if isinstance(response, str):
            self._record_usage(0, 0, status="error",
                               error="GitHub Models retornou resposta inválida")
            raise ValueError(
                "GitHub Models retornou resposta inválida. "
                "Execute 'gh auth login' no terminal e tente novamente."
            )
        usage = response.usage
        self._record_usage(
            getattr(usage, "prompt_tokens", 0),
            getattr(usage, "completion_tokens", 0),
        )
        return response.choices[0].message.content

    def _analyze_chatgpt(self, system_prompt: str, user_prompt: str,
                        cached_content: str = None) -> str:
        """Análise com ChatGPT/OpenAI."""
        full_system = system_prompt
        if cached_content:
            full_system = f"{system_prompt}\n\nContexto adicional:\n{cached_content}"

        messages = [
            {"role": "system", "content": full_system},
            {"role": "user", "content": user_prompt}
        ]

        return self._chatgpt_call(messages)

    def _analyze_groq(self, system_prompt: str, user_prompt: str,
                     cached_content: str = None) -> str:
        """Análise com Groq (API compatível com OpenAI)."""
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
            temperature=0.7,
            timeout=60,
        )
        usage = response.usage
        self._record_usage(
            getattr(usage, "prompt_tokens", 0),
            getattr(usage, "completion_tokens", 0),
        )
        return response.choices[0].message.content

    def _gemini_generate(self, prompt: str) -> str:
        """Chama Gemini com retry automático em caso de 503 e fallback de modelo."""
        try:
            request_options = genai.types.RequestOptions(timeout=120)
        except AttributeError:
            request_options = {"timeout": 120}

        generation_config = {"temperature": 0.7, "max_output_tokens": 4096}
        fallback_models = ["models/gemini-2.5-flash", "models/gemini-flash-latest", "models/gemini-pro-latest"]
        models_to_try = [self.model] + [m for m in fallback_models if m != self.model]

        last_error = None
        first_model = True
        for model_name in models_to_try:
            if not first_model:
                self.resource_usage["retries"] += 1
            first_model = False
            client = genai.GenerativeModel(model_name)
            for attempt in range(3):
                if attempt > 0:
                    self.resource_usage["retries"] += 1
                try:
                    response = client.generate_content(
                        prompt,
                        generation_config=generation_config,
                        request_options=request_options,
                    )
                    # usage_metadata disponível no SDK >= 0.5
                    um = getattr(response, "usage_metadata", None)
                    inp = getattr(um, "prompt_token_count", 0) or 0
                    out = getattr(um, "candidates_token_count", 0) or 0
                    status = "fallback" if model_name != self.model else "ok"
                    self._record_usage(inp, out, status=status)
                    return response.text
                except Exception as e:
                    last_error = e
                    err_str = str(e)
                    if "503" in err_str or "high demand" in err_str or "overloaded" in err_str.lower():
                        self._record_usage(0, 0, status="error", error=err_str[:120])
                        wait = 10 * (attempt + 1)
                        time.sleep(wait)
                        continue
                    self._record_usage(0, 0, status="error", error=err_str[:120])
                    break

        raise last_error

    def _analyze_gemini(self, system_prompt: str, user_prompt: str,
                       cached_content: str = None) -> str:
        """Análise com Google Gemini."""
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        if cached_content:
            full_prompt = f"{system_prompt}\n\nContexto adicional:\n{cached_content}\n\n{user_prompt}"

        return self._gemini_generate(full_prompt)

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
                    timeout=60,
                )
                self._record_usage(
                    response.usage.input_tokens,
                    response.usage.output_tokens,
                )
                return response.content[0].text
            else:
                return self._openrouter_call([{"role": "user", "content": prompt}])

        elif self.provider == "chatgpt":
            return self._chatgpt_call([{"role": "user", "content": prompt}])

        elif self.provider == "groq":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096,
                temperature=0.7,
                timeout=60,
            )
            usage = response.usage
            self._record_usage(
                getattr(usage, "prompt_tokens", 0),
                getattr(usage, "completion_tokens", 0),
            )
            return response.choices[0].message.content

        elif self.provider == "gemini":
            return self._gemini_generate(prompt)

        elif self.provider == "puter":
            response = self.client.chat(
                prompt=prompt,
                model=self.model,
                temperature=0.7,
                max_tokens=4096
            )
            return self.client._extract_text_from_response(response)
