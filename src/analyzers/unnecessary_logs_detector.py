"""
Solução 2: Log only what's necessary
Detecta logs desnecessários que não agregam valor para análise ou troubleshooting.
"""

from typing import List, Dict, Any
from collections import defaultdict
import json
import random
import re


class UnnecessaryLogsDetector:
    """
    Detecta padrões de logs que não agregam valor:
    - Logs duplicados ou muito repetitivos
    - Logs de assets estáticos
    - Logs de operações triviais bem-sucedidas
    - Logs com informações redundantes
    """

    # Padrões de paths que geralmente não precisam de log
    STATIC_ASSET_PATTERNS = [
        r'\.js$', r'\.css$', r'\.png$', r'\.jpg$', r'\.jpeg$',
        r'\.gif$', r'\.svg$', r'\.ico$', r'\.woff$', r'\.ttf$',
        r'/static/', r'/assets/', r'/images/', r'/fonts/'
    ]

    # Status codes que geralmente não precisam log INFO
    SUCCESS_CODES = [200, 201, 204, 304]

    def __init__(self, llm_client=None):
        """
        Inicializa o detector.

        Args:
            llm_client: Cliente LLM para análise avançada (opcional)
        """
        self.llm_client = llm_client
        self.issues = []
        self.recommendations = []

    def analyze(self, logs: List[Dict[str, Any]],
                duplicates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detecta logs desnecessários.

        Args:
            logs: Lista de logs
            duplicates: Lista de logs duplicados (do LogProcessor)

        Returns:
            Relatório de análise
        """
        self.issues = []
        self.recommendations = []

        # MODO COM IA: Análise inteligente usando LLM
        if self.llm_client:
            return self._analyze_with_ai(logs, duplicates)

        # MODO STANDARD: Análise baseada em regras fixas
        return self._analyze_with_rules(logs, duplicates)

    def _analyze_with_rules(self, logs: List[Dict[str, Any]],
                           duplicates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Análise baseada em regras fixas (modo Standard)."""
        # 1. Analisa logs de assets estáticos
        static_logs = self._detect_static_asset_logs(logs)

        # 2. Analisa logs de sucesso triviais
        trivial_success = self._detect_trivial_success_logs(logs)

        # 3. Analisa duplicatas excessivas
        excessive_duplicates = self._analyze_duplicates(duplicates)

        # 4. Analisa logs com baixo conteúdo informativo
        low_info_logs = self._detect_low_information_logs(logs)

        # Calcula potencial de redução (cap em total de logs para evitar dupla contagem)
        unnecessary_count = min(
            len(static_logs) +
            len(trivial_success) +
            sum(d['count'] - 1 for d in excessive_duplicates),
            len(logs)
        )

        reduction_percentage = round((unnecessary_count / len(logs)) * 100, 2) if logs else 0

        return {
            'analysis_type': 'Unnecessary Logs Detection',
            'total_logs': len(logs),
            'unnecessary_logs_count': unnecessary_count,
            'reduction_potential_percentage': reduction_percentage,
            'static_asset_logs': {
                'count': len(static_logs),
                'percentage': round((len(static_logs) / len(logs)) * 100, 2) if logs else 0,
                'samples': static_logs[:5]
            },
            'trivial_success_logs': {
                'count': len(trivial_success),
                'percentage': round((len(trivial_success) / len(logs)) * 100, 2) if logs else 0,
                'samples': trivial_success[:5]
            },
            'excessive_duplicates': {
                'patterns_count': len(excessive_duplicates),
                'total_duplicate_logs': sum(d['count'] for d in excessive_duplicates),
                'top_patterns': excessive_duplicates[:10]
            },
            'low_information_logs': {
                'count': len(low_info_logs),
                'samples': low_info_logs[:5]
            },
            'issues': self.issues,
            'recommendations': self.recommendations,
            'llm_insights': None,
            'severity': self._calculate_severity(reduction_percentage)
        }

    def _detect_static_asset_logs(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detecta logs de assets estáticos."""
        static_logs = []

        for log in logs:
            http = log.get('http', {})
            if not isinstance(http, dict):
                continue

            path = http.get('path', '')
            status_code = http.get('status_code')

            # Verifica se é asset estático
            for pattern in self.STATIC_ASSET_PATTERNS:
                if re.search(pattern, path):
                    static_logs.append(log)
                    break

        if static_logs:
            self.issues.append({
                'type': 'static_asset_logging',
                'severity': 'high',
                'description': f"Encontrados {len(static_logs)} logs de assets estáticos",
                'impact': 'Logs de assets estáticos raramente agregam valor e geram ruído',
                'count': len(static_logs),
                'percentage': round((len(static_logs) / len(logs)) * 100, 2) if logs else 0
            })

            self.recommendations.append({
                'issue': 'static_asset_logging',
                'recommendation': 'Desabilitar logging para assets estáticos',
                'priority': 'high',
                'examples': [
                    'Adicionar filtro no middleware de logging para excluir requests de assets',
                    'Usar configuração específica no servidor web (nginx, apache) para não logar assets',
                    'Implementar lista de exclusão de paths estáticos'
                ],
                'estimated_reduction': f"{len(static_logs)} logs ({round((len(static_logs) / len(logs)) * 100, 1)}%)"
            })

        return static_logs

    def _detect_trivial_success_logs(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detecta logs de sucesso triviais."""
        trivial_logs = []

        for log in logs:
            level = log.get('level')
            http = log.get('http', {})

            if level == 'INFO' and isinstance(http, dict):
                status_code = http.get('status_code')
                method = http.get('method')

                # Logs INFO de GET bem-sucedidos geralmente são desnecessários
                if method == 'GET' and status_code in self.SUCCESS_CODES:
                    trivial_logs.append(log)

        if trivial_logs:
            self.issues.append({
                'type': 'trivial_success_logs',
                'severity': 'medium',
                'description': f"Encontrados {len(trivial_logs)} logs INFO de operações GET bem-sucedidas",
                'impact': 'Logs de operações triviais bem-sucedidas geram ruído desnecessário',
                'count': len(trivial_logs)
            })

            self.recommendations.append({
                'issue': 'trivial_success_logs',
                'recommendation': 'Remover ou reduzir logs de operações triviais bem-sucedidas',
                'priority': 'medium',
                'examples': [
                    'Não logar GET requests bem-sucedidos em nível INFO',
                    'Usar amostragem para operações de leitura de alto volume',
                    'Logar apenas operações de escrita (POST, PUT, DELETE) ou com erros'
                ],
                'estimated_reduction': f"{len(trivial_logs)} logs"
            })

        return trivial_logs

    def _analyze_duplicates(self, duplicates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analisa duplicatas excessivas."""
        excessive = []

        for dup in duplicates:
            count = dup['count']
            # Considera excessivo quando há mais de 10 logs idênticos
            if count > 10:
                excessive.append(dup)

        if excessive:
            total_excessive = sum(d['count'] for d in excessive)
            self.issues.append({
                'type': 'excessive_duplicate_logs',
                'severity': 'high',
                'description': f"Encontrados {len(excessive)} padrões de logs excessivamente repetidos",
                'impact': 'Logs duplicados indicam falta de deduplicação ou rate limiting',
                'patterns_count': len(excessive),
                'total_logs': total_excessive
            })

            self.recommendations.append({
                'issue': 'excessive_duplicate_logs',
                'recommendation': 'Implementar deduplicação e rate limiting de logs',
                'priority': 'high',
                'examples': [
                    'Implementar debouncing para logs similares (ex: logar apenas 1 vez a cada minuto)',
                    'Adicionar contador de ocorrências ao invés de logar cada evento',
                    'Usar aggregação para eventos repetitivos',
                    'Implementar rate limiting por tipo de log'
                ],
                'top_offenders': [
                    {
                        'pattern': d['pattern']['message'][:100],
                        'count': d['count']
                    }
                    for d in excessive[:5]
                ]
            })

        return excessive

    def _detect_low_information_logs(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detecta logs com baixo conteúdo informativo."""
        low_info = []

        for log in logs:
            message = log.get('message', '')

            # Mensagens muito curtas ou genéricas
            if len(message) < 10 or message == '':
                low_info.append(log)
                continue

            # Mensagens muito genéricas
            generic_patterns = [
                r'^ok$', r'^success$', r'^done$', r'^complete$',
                r'^processing$', r'^started$', r'^finished$'
            ]

            for pattern in generic_patterns:
                if re.match(pattern, message.lower()):
                    low_info.append(log)
                    break

        if low_info:
            self.issues.append({
                'type': 'low_information_content',
                'severity': 'low',
                'description': f"Encontrados {len(low_info)} logs com baixo conteúdo informativo",
                'impact': 'Logs sem contexto suficiente dificultam troubleshooting',
                'count': len(low_info)
            })

        return low_info

    def _analyze_with_ai(self, logs: List[Dict[str, Any]],
                        duplicates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Análise inteligente usando LLM para classificar logs como necessários/desnecessários."""
        print(f"      🤖 IA analisando {len(logs)} logs individualmente...")

        # Amostra aleatória reduzida para respeitar limites de tokens por minuto
        sample_size = min(40, len(logs))
        sample_logs = random.sample(logs, sample_size)

        # Prepara prompt para classificação em batch
        system_prompt = """Especialista em observabilidade. Classifique logs como NECESSÁRIO ou DESNECESSÁRIO.
DESNECESSÁRIO: asset estático, health check GET 200, mensagem genérica, repetitivo sem valor.
NECESSÁRIO: erro/falha, escrita (POST/PUT/DELETE), contexto de debug, evento significativo.
Responda APENAS com JSON:
{"unnecessary_logs":[0,2,5],"reasoning":"explicação","severity":"low|medium|high|critical","top_issues":["issue1"]}"""

        logs_data = []
        for i, log in enumerate(sample_logs):
            logs_data.append({
                'index': i,
                'level': log.get('level'),
                'message': log.get('message', '')[:80],
                'service': log.get('service'),
                'http': {
                    'method': log.get('http', {}).get('method'),
                    'path': log.get('http', {}).get('path', '')[:60],
                    'status_code': log.get('http', {}).get('status_code')
                } if log.get('http') else None
            })

        user_prompt = f"""Analise estes {len(logs_data)} logs e identifique quais são desnecessários:

{json.dumps(logs_data, indent=2, ensure_ascii=False)}

Classifique cada log e retorne o JSON solicitado."""

        try:
            response = self.llm_client.analyze_simple(
                f"{system_prompt}\n\n{user_prompt}"
            )

            # Parse resposta JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                ai_result = json.loads(json_match.group())
            else:
                raise ValueError("Resposta da IA não contém JSON válido")

            unnecessary_indices = ai_result.get('unnecessary_logs', [])
            unnecessary_logs = [sample_logs[i] for i in unnecessary_indices if i < len(sample_logs)]

            # Extrapola para o dataset completo
            extrapolation_factor = len(logs) / sample_size
            estimated_unnecessary = int(len(unnecessary_logs) * extrapolation_factor)
            reduction_percentage = round((estimated_unnecessary / len(logs)) * 100, 2)

            print(f"      ✓ IA identificou {len(unnecessary_logs)}/{sample_size} logs desnecessários na amostra")
            print(f"      ✓ Estimativa total: {estimated_unnecessary}/{len(logs)} ({reduction_percentage}%)")

            # Cria issues baseado na análise da IA
            self.issues = []
            for issue_desc in ai_result.get('top_issues', [])[:3]:
                self.issues.append({
                    'type': 'ai_identified_issue',
                    'severity': ai_result.get('severity', 'medium'),
                    'description': issue_desc,
                    'impact': 'Identificado por análise de IA',
                    'count': estimated_unnecessary
                })

            # Recomendações da IA
            self.recommendations = [{
                'issue': 'ai_analysis',
                'recommendation': ai_result.get('reasoning', 'Revisar logs identificados como desnecessários'),
                'priority': ai_result.get('severity', 'medium'),
                'ai_generated': True
            }]

            return {
                'analysis_type': 'Unnecessary Logs Detection (AI-Powered)',
                'total_logs': len(logs),
                'unnecessary_logs_count': estimated_unnecessary,
                'reduction_potential_percentage': reduction_percentage,
                'static_asset_logs': {
                    'count': 0,
                    'percentage': 0,
                    'samples': []
                },
                'trivial_success_logs': {
                    'count': 0,
                    'percentage': 0,
                    'samples': []
                },
                'excessive_duplicates': {
                    'patterns_count': 0,
                    'total_duplicate_logs': 0,
                    'top_patterns': []
                },
                'low_information_logs': {
                    'count': 0,
                    'samples': []
                },
                'ai_analysis': {
                    'sample_size': sample_size,
                    'unnecessary_in_sample': len(unnecessary_logs),
                    'samples': unnecessary_logs[:5],
                    'reasoning': ai_result.get('reasoning'),
                    'severity': ai_result.get('severity')
                },
                'issues': self.issues,
                'recommendations': self.recommendations,
                'llm_insights': ai_result.get('reasoning'),
                'severity': ai_result.get('severity', 'medium')
            }

        except Exception as e:
            print(f"      ⚠️  Erro na análise com IA: {e}")
            print(f"      → Caindo de volta para análise baseada em regras")
            return self._analyze_with_rules(logs, duplicates)

    def _calculate_severity(self, reduction_percentage: float) -> str:
        """Calcula severidade baseado no potencial de redução."""
        if reduction_percentage >= 50:
            return 'critical'
        elif reduction_percentage >= 30:
            return 'high'
        elif reduction_percentage >= 15:
            return 'medium'
        elif reduction_percentage > 0:
            return 'low'
        return 'ok'
