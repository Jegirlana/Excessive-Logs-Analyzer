"""
Solução 1: Use log levels effectively
Analisa o uso de níveis de log e identifica configurações inadequadas.
"""

from typing import List, Dict, Any
from collections import defaultdict
import json
import random


class LogLevelAnalyzer:
    """
    Analisa a efetividade do uso de níveis de log.
    Detecta quando há excesso de logs em níveis inadequados.
    """

    # Thresholds baseados em boas práticas
    THRESHOLDS = {
        'info_percentage_max': 70,  # INFO não deve passar de 70%
        'debug_percentage_max': 5,   # DEBUG deve ser < 5% em produção
        'error_percentage_min': 1,   # Pelo menos 1% de erro é esperado
        'warn_percentage_min': 5,    # Pelo menos 5% de warnings
    }

    def __init__(self, llm_client=None):
        """
        Inicializa o analisador.

        Args:
            llm_client: Cliente LLM para análise avançada (opcional)
        """
        self.llm_client = llm_client
        self.issues = []
        self.recommendations = []

    def analyze(self, logs: List[Dict[str, Any]],
                service_levels: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
        """
        Analisa distribuição de níveis de log.

        Args:
            logs: Lista de logs
            service_levels: Distribuição de níveis por serviço

        Returns:
            Relatório de análise
        """
        self.issues = []
        self.recommendations = []

        total_logs = len(logs)
        level_dist = self._calculate_level_distribution(logs)

        # MODO COM IA: Análise contextual dos níveis de log
        if self.llm_client:
            return self._analyze_with_ai(logs, level_dist, service_levels)

        # MODO STANDARD: Análise baseada em thresholds fixos
        # Análise geral
        self._analyze_overall_distribution(level_dist, total_logs)

        # Análise por serviço
        self._analyze_per_service(service_levels)

        return {
            'analysis_type': 'Log Level Effectiveness',
            'total_logs': total_logs,
            'level_distribution': level_dist,
            'level_percentages': self._calculate_percentages(level_dist, total_logs),
            'service_distribution': service_levels,
            'issues': self.issues,
            'recommendations': self.recommendations,
            'llm_insights': None,
            'severity': self._calculate_severity()
        }

    def _calculate_level_distribution(self, logs: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calcula distribuição de níveis."""
        dist = {'INFO': 0, 'WARN': 0, 'ERROR': 0, 'DEBUG': 0, 'FATAL': 0}
        for log in logs:
            level = log.get('level', 'UNKNOWN')
            if level in dist:
                dist[level] += 1
        return dist

    def _calculate_percentages(self, dist: Dict[str, int], total: int) -> Dict[str, float]:
        """Calcula percentuais."""
        if total == 0:
            return {k: 0.0 for k in dist}
        return {k: round((v / total) * 100, 2) for k, v in dist.items()}

    def _analyze_overall_distribution(self, level_dist: Dict[str, int], total: int):
        """Analisa distribuição geral de níveis."""
        percentages = self._calculate_percentages(level_dist, total)

        # Verifica excesso de INFO
        if percentages['INFO'] > self.THRESHOLDS['info_percentage_max']:
            self.issues.append({
                'type': 'excessive_info_logs',
                'severity': 'high',
                'description': f"Logs INFO representam {percentages['INFO']:.1f}% do total "
                              f"(acima do limite de {self.THRESHOLDS['info_percentage_max']}%)",
                'impact': 'Ruído excessivo que dificulta identificação de problemas reais',
                'count': level_dist['INFO']
            })
            self.recommendations.append({
                'issue': 'excessive_info_logs',
                'recommendation': 'Revisar logs INFO e converter logs triviais para DEBUG ou remover',
                'priority': 'high',
                'examples': [
                    'Remover logs de requisições bem-sucedidas de assets estáticos',
                    'Converter logs de operações rotineiras para DEBUG',
                    'Implementar amostragem para operações de alto volume'
                ]
            })

        # Verifica presença de DEBUG em produção
        if percentages['DEBUG'] > self.THRESHOLDS['debug_percentage_max']:
            self.issues.append({
                'type': 'debug_in_production',
                'severity': 'critical',
                'description': f"Logs DEBUG representam {percentages['DEBUG']:.1f}% "
                              f"(acima do limite de {self.THRESHOLDS['debug_percentage_max']}%)",
                'impact': 'Logs de debug em produção causam overhead e expõem informações sensíveis',
                'count': level_dist['DEBUG']
            })
            self.recommendations.append({
                'issue': 'debug_in_production',
                'recommendation': 'Desabilitar nível DEBUG em produção imediatamente',
                'priority': 'critical',
                'examples': [
                    'Configurar log level para INFO ou superior em produção',
                    'Usar variáveis de ambiente para controlar níveis por ambiente',
                    'Implementar flag feature para habilitar DEBUG apenas quando necessário'
                ]
            })

        # Verifica falta de logs de erro/warning
        if percentages['ERROR'] < self.THRESHOLDS['error_percentage_min']:
            self.issues.append({
                'type': 'insufficient_error_logs',
                'severity': 'medium',
                'description': f"Logs ERROR representam apenas {percentages['ERROR']:.1f}% do total",
                'impact': 'Possível subnotificação de erros ou tratamento inadequado',
                'count': level_dist['ERROR']
            })

        if percentages['WARN'] < self.THRESHOLDS['warn_percentage_min']:
            self.issues.append({
                'type': 'insufficient_warn_logs',
                'severity': 'low',
                'description': f"Logs WARN representam apenas {percentages['WARN']:.1f}% do total",
                'impact': 'Possível falta de monitoramento de condições anormais',
                'count': level_dist['WARN']
            })

    def _analyze_per_service(self, service_levels: Dict[str, Dict[str, int]]):
        """Analisa níveis por serviço."""
        for service, levels in service_levels.items():
            total = sum(levels.values())
            if total == 0:
                continue

            percentages = self._calculate_percentages(levels, total)

            # Identifica serviços com distribuição problemática
            if percentages.get('INFO', 0) > 80:
                self.issues.append({
                    'type': 'service_excessive_info',
                    'severity': 'medium',
                    'service': service,
                    'description': f"Serviço '{service}' tem {percentages['INFO']:.1f}% de logs INFO",
                    'impact': 'Serviço específico gerando ruído excessivo',
                    'count': levels.get('INFO', 0)
                })

            if percentages.get('DEBUG', 0) > 0:
                self.issues.append({
                    'type': 'service_debug_enabled',
                    'severity': 'high',
                    'service': service,
                    'description': f"Serviço '{service}' tem logs DEBUG habilitados "
                                  f"({percentages['DEBUG']:.1f}%)",
                    'impact': 'Debug habilitado em produção para este serviço',
                    'count': levels.get('DEBUG', 0)
                })

    def _analyze_with_ai(self, logs: List[Dict[str, Any]],
                        level_dist: Dict[str, int],
                        service_levels: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
        """Análise inteligente usando LLM para avaliar uso de níveis de log."""
        print(f"      🤖 IA avaliando uso de níveis de log...")

        total_logs = len(logs)
        percentages = self._calculate_percentages(level_dist, total_logs)

        # Prepara contexto rico para IA
        sample_logs_by_level = defaultdict(list)
        sample = random.sample(logs, min(100, len(logs)))
        for log in sample:
            level = log.get('level', 'UNKNOWN')
            if len(sample_logs_by_level[level]) < 5:
                sample_logs_by_level[level].append({
                    'message': log.get('message', '')[:150],
                    'service': log.get('service'),
                    'http': log.get('http', {}).get('status_code') if log.get('http') else None
                })

        system_prompt = """Você é um especialista em observabilidade.
Analise o uso de níveis de log (INFO, WARN, ERROR, DEBUG) e determine se estão sendo usados apropriadamente.

Critérios:
- INFO: deve ser < 70% do total. Operações relevantes, não triviais.
- DEBUG: deve ser < 5% em produção (idealmente 0%). Apenas para desenvolvimento.
- WARN: esperado 5-15%. Condições anormais que não são erros.
- ERROR: esperado 1-10%. Falhas reais que precisam atenção.

Avalie cada nível e identifique:
1. Níveis usados inadequadamente (ex: INFO para logs triviais)
2. Logs que deveriam estar em nível diferente
3. Severidade do problema (ok, low, medium, high, critical)

IMPORTANTE: Responda SEMPRE em português brasileiro. Todos os campos de texto devem estar em português.

Responda APENAS com JSON válido:
{
  "severity": "ok|low|medium|high|critical",
  "issues": [
    {
      "type": "issue_type",
      "level_affected": "INFO|WARN|ERROR|DEBUG",
      "description": "descrição do problema em português",
      "severity": "low|medium|high|critical",
      "recommendation": "o que fazer em português"
    }
  ],
  "summary": "breve resumo da análise em português"
}"""

        user_prompt = f"""Analise esta distribuição de níveis de log:

DISTRIBUIÇÃO GERAL:
{json.dumps(percentages, indent=2)}

DISTRIBUIÇÃO POR SERVIÇO:
{json.dumps(service_levels, indent=2, ensure_ascii=False)}

AMOSTRAS POR NÍVEL:
{json.dumps(dict(sample_logs_by_level), indent=2, ensure_ascii=False)}

Avalie se os níveis estão sendo usados corretamente."""

        try:
            response = self.llm_client.analyze_simple(
                f"{system_prompt}\n\n{user_prompt}"
            )

            # Parse JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                ai_result = json.loads(json_match.group())
            else:
                raise ValueError("Resposta não contém JSON válido")

            # Converte issues da IA para formato esperado
            self.issues = []
            for issue in ai_result.get('issues', []):
                self.issues.append({
                    'type': issue.get('type', 'ai_identified_issue'),
                    'severity': issue.get('severity', 'medium'),
                    'description': issue.get('description'),
                    'impact': issue.get('recommendation'),
                    'level_affected': issue.get('level_affected'),
                    'ai_generated': True
                })

                self.recommendations.append({
                    'issue': issue.get('type'),
                    'recommendation': issue.get('recommendation'),
                    'priority': issue.get('severity'),
                    'ai_generated': True
                })

            severity = ai_result.get('severity', 'medium')
            print(f"      ✓ IA detectou {len(self.issues)} issues (severidade: {severity})")

            return {
                'analysis_type': 'Log Level Effectiveness (AI-Powered)',
                'total_logs': total_logs,
                'level_distribution': level_dist,
                'level_percentages': percentages,
                'service_distribution': service_levels,
                'issues': self.issues,
                'recommendations': self.recommendations,
                'ai_analysis': {
                    'summary': ai_result.get('summary'),
                    'severity': severity
                },
                'llm_insights': ai_result.get('summary'),
                'severity': severity
            }

        except Exception as e:
            print(f"      ⚠️  Erro na análise com IA: {e}")
            print(f"      → Caindo de volta para análise baseada em regras")
            # Fallback para análise com regras
            self._analyze_overall_distribution(level_dist, total_logs)
            self._analyze_per_service(service_levels)
            return {
                'analysis_type': 'Log Level Effectiveness',
                'total_logs': total_logs,
                'level_distribution': level_dist,
                'level_percentages': percentages,
                'service_distribution': service_levels,
                'issues': self.issues,
                'recommendations': self.recommendations,
                'llm_insights': f"Erro na análise IA: {e}",
                'severity': self._calculate_severity()
            }

    def _calculate_severity(self) -> str:
        """Calcula severidade geral baseado nos issues encontrados."""
        if not self.issues:
            return 'ok'

        severities = [issue['severity'] for issue in self.issues]
        if 'critical' in severities:
            return 'critical'
        elif 'high' in severities:
            return 'high'
        elif 'medium' in severities:
            return 'medium'
        return 'low'
