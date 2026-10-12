"""
Solução 3: Implement log sampling
Recomenda estratégias de amostragem para reduzir volume de logs mantendo insights.
"""

from typing import List, Dict, Any
import json
from collections import defaultdict


class SamplingRecommender:
    """
    Recomenda estratégias de amostragem de logs baseado em:
    - Volume de logs por serviço
    - Taxa de logs por minuto
    - Padrões repetitivos
    - Distribuição de níveis
    """

    # Thresholds para recomendação de sampling
    THRESHOLDS = {
        'high_volume_per_minute': 100,  # logs/min que indica necessidade de sampling
        'very_high_volume_per_minute': 500,  # logs/min que indica necessidade urgente
        'repetition_threshold': 50,  # repetições que indicam necessidade de sampling
    }

    # Estratégias de sampling
    SAMPLING_STRATEGIES = {
        'rate_based': {
            'name': 'Rate-based Sampling',
            'description': 'Amostra 1 a cada N logs',
            'use_case': 'Alto volume de logs similares'
        },
        'time_based': {
            'name': 'Time-based Sampling',
            'description': 'Amostra 1 log por intervalo de tempo',
            'use_case': 'Logs muito frequentes do mesmo tipo'
        },
        'adaptive': {
            'name': 'Adaptive Sampling',
            'description': 'Ajusta taxa de amostragem dinamicamente baseado em volume',
            'use_case': 'Tráfego variável ao longo do dia'
        },
        'priority_based': {
            'name': 'Priority-based Sampling',
            'description': 'Sempre loga ERRORs, amostra INFOs',
            'use_case': 'Preservar logs críticos enquanto reduz ruído'
        },
        'head_based': {
            'name': 'Head-based Sampling',
            'description': 'Decisão de amostragem no início da transação',
            'use_case': 'Rastreamento distribuído (traces)'
        }
    }

    def __init__(self, llm_client=None):
        """
        Inicializa o recomendador.

        Args:
            llm_client: Cliente LLM para análise avançada (opcional)
        """
        self.llm_client = llm_client
        self.recommendations = []

    def analyze(self, logs: List[Dict[str, Any]],
                log_rate: Dict[str, Any],
                service_dist: Dict[str, int],
                duplicates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analisa necessidade de sampling e recomenda estratégias.

        Args:
            logs: Lista de logs
            log_rate: Taxa de logs (do LogProcessor)
            service_dist: Distribuição por serviço
            duplicates: Padrões duplicados

        Returns:
            Relatório de análise
        """
        self.recommendations = []

        # MODO COM IA: Recomendações personalizadas de sampling
        if self.llm_client:
            return self._analyze_with_ai(logs, log_rate, service_dist, duplicates)

        # MODO STANDARD: Recomendações baseadas em regras fixas
        # 1. Analisa volume geral
        volume_analysis = self._analyze_volume(log_rate)

        # 2. Analisa por serviço
        service_analysis = self._analyze_per_service(logs, service_dist)

        # 3. Analisa padrões repetitivos
        repetition_analysis = self._analyze_repetitive_patterns(duplicates)

        # 4. Gera recomendações de estratégias
        strategies = self._recommend_strategies(
            volume_analysis, service_analysis, repetition_analysis
        )

        # Calcula redução estimada
        estimated_reduction = self._calculate_estimated_reduction(strategies)

        return {
            'analysis_type': 'Log Sampling Recommendations',
            'current_state': {
                'total_logs': len(logs),
                'rate_per_minute': log_rate.get('rate_per_minute', 0),
                'rate_per_second': log_rate.get('rate_per_second', 0),
                'duration_minutes': log_rate.get('duration_minutes', 0)
            },
            'volume_analysis': volume_analysis,
            'service_analysis': service_analysis,
            'repetition_analysis': repetition_analysis,
            'recommended_strategies': strategies,
            'estimated_reduction': estimated_reduction,
            'recommendations': self.recommendations,
            'llm_insights': None,
            'severity': self._calculate_severity(log_rate)
        }

    def _analyze_volume(self, log_rate: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa volume geral de logs."""
        rate_per_min = log_rate.get('rate_per_minute', 0)
        needs_sampling = False
        urgency = 'none'

        if rate_per_min > self.THRESHOLDS['very_high_volume_per_minute']:
            needs_sampling = True
            urgency = 'critical'
            self.recommendations.append({
                'type': 'urgent_sampling_needed',
                'priority': 'critical',
                'description': f"Volume crítico: {rate_per_min:.1f} logs/min",
                'action': 'Implementar sampling imediatamente para reduzir custos e overhead'
            })
        elif rate_per_min > self.THRESHOLDS['high_volume_per_minute']:
            needs_sampling = True
            urgency = 'high'
            self.recommendations.append({
                'type': 'sampling_recommended',
                'priority': 'high',
                'description': f"Volume alto: {rate_per_min:.1f} logs/min",
                'action': 'Considerar implementação de sampling para otimizar recursos'
            })

        return {
            'rate_per_minute': rate_per_min,
            'needs_sampling': needs_sampling,
            'urgency': urgency,
            'assessment': self._get_volume_assessment(rate_per_min)
        }

    def _analyze_per_service(self, logs: List[Dict[str, Any]],
                            service_dist: Dict[str, int]) -> List[Dict[str, Any]]:
        """Analisa volume por serviço."""
        total_logs = len(logs)
        service_analysis = []

        for service, count in sorted(service_dist.items(),
                                     key=lambda x: x[1], reverse=True):
            percentage = (count / total_logs) * 100 if total_logs > 0 else 0

            analysis = {
                'service': service,
                'log_count': count,
                'percentage': round(percentage, 2),
                'needs_sampling': False,
                'recommended_rate': None
            }

            # Serviços que representam mais de 20% do total podem precisar sampling
            if percentage > 20:
                analysis['needs_sampling'] = True
                # Recomenda sampling mais agressivo para volumes maiores
                if percentage > 40:
                    analysis['recommended_rate'] = '1:10'  # 1 em cada 10
                elif percentage > 30:
                    analysis['recommended_rate'] = '1:5'   # 1 em cada 5
                else:
                    analysis['recommended_rate'] = '1:3'   # 1 em cada 3

                self.recommendations.append({
                    'type': 'service_sampling',
                    'service': service,
                    'priority': 'high' if percentage > 30 else 'medium',
                    'description': f"Serviço '{service}' gera {percentage:.1f}% dos logs",
                    'action': f"Implementar sampling rate {analysis['recommended_rate']} "
                             f"para este serviço"
                })

            service_analysis.append(analysis)

        return service_analysis

    def _analyze_repetitive_patterns(self,
                                    duplicates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analisa padrões repetitivos que precisam de sampling."""
        high_repetition = []

        for dup in duplicates:
            if dup['count'] > self.THRESHOLDS['repetition_threshold']:
                high_repetition.append({
                    'pattern': dup['pattern'],
                    'count': dup['count'],
                    'recommended_strategy': 'time_based',
                    'suggested_interval': '1 per minute'
                })

                self.recommendations.append({
                    'type': 'pattern_sampling',
                    'priority': 'high',
                    'pattern': dup['pattern']['message'][:100],
                    'count': dup['count'],
                    'action': 'Implementar sampling temporal: logar apenas 1 vez por minuto'
                })

        return {
            'high_repetition_patterns': len(high_repetition),
            'patterns': high_repetition[:10],
            'total_logs_affected': sum(p['count'] for p in high_repetition)
        }

    def _recommend_strategies(self, volume_analysis: Dict[str, Any],
                             service_analysis: List[Dict[str, Any]],
                             repetition_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Recomenda estratégias específicas de sampling."""
        strategies = []

        # Priority-based sampling (sempre recomendado)
        strategies.append({
            'strategy': 'priority_based',
            'details': self.SAMPLING_STRATEGIES['priority_based'],
            'priority': 'high',
            'implementation': {
                'description': 'Preservar todos ERROR/FATAL, amostrar INFO/DEBUG',
                'rules': [
                    'ERROR, FATAL, WARN: 100% (sempre logar)',
                    'INFO: Amostragem de 10-20% para operações bem-sucedidas',
                    'DEBUG: Desabilitar em produção ou amostrar 1%'
                ],
                'expected_reduction': '40-60%'
            }
        })

        # Rate-based para alto volume
        if volume_analysis['needs_sampling']:
            strategies.append({
                'strategy': 'rate_based',
                'details': self.SAMPLING_STRATEGIES['rate_based'],
                'priority': 'high' if volume_analysis['urgency'] == 'critical' else 'medium',
                'implementation': {
                    'description': 'Amostragem baseada em taxa fixa',
                    'recommended_rate': '1:5' if volume_analysis['urgency'] == 'critical' else '1:3',
                    'apply_to': ['INFO logs de operações bem-sucedidas'],
                    'expected_reduction': '80%' if volume_analysis['urgency'] == 'critical' else '66%'
                }
            })

        # Time-based para padrões repetitivos
        if repetition_analysis['high_repetition_patterns'] > 0:
            strategies.append({
                'strategy': 'time_based',
                'details': self.SAMPLING_STRATEGIES['time_based'],
                'priority': 'high',
                'implementation': {
                    'description': 'Amostragem temporal para eventos repetitivos',
                    'recommended_interval': '1 log per minute',
                    'apply_to': [
                        'Logs idênticos que se repetem mais de 50 vezes',
                        'Health checks',
                        'Heartbeats'
                    ],
                    'affected_patterns': repetition_analysis['high_repetition_patterns'],
                    'expected_reduction': f"{repetition_analysis.get('total_logs_affected', 0)} logs"
                }
            })

        # Adaptive sampling para serviços com alto volume
        high_volume_services = [s for s in service_analysis if s['needs_sampling']]
        if high_volume_services:
            strategies.append({
                'strategy': 'adaptive',
                'details': self.SAMPLING_STRATEGIES['adaptive'],
                'priority': 'medium',
                'implementation': {
                    'description': 'Ajusta sampling dinamicamente baseado em carga',
                    'apply_to_services': [s['service'] for s in high_volume_services[:3]],
                    'rules': [
                        'Tráfego normal (< 100 logs/min): 100% dos logs',
                        'Tráfego alto (100-500 logs/min): 20% dos logs INFO',
                        'Tráfego muito alto (> 500 logs/min): 5% dos logs INFO'
                    ],
                    'expected_reduction': '30-70% durante picos'
                }
            })

        return strategies

    def _calculate_estimated_reduction(self,
                                      strategies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcula redução estimada com as estratégias recomendadas."""
        # Estimativa conservadora: melhor estratégia pode reduzir 40-60%
        min_reduction = 40
        max_reduction = 60

        if any(s['priority'] == 'high' for s in strategies):
            max_reduction = 70

        return {
            'estimated_percentage': f"{min_reduction}-{max_reduction}%",
            'confidence': 'medium',
            'note': 'Redução real depende da implementação específica e mix de logs'
        }

    def _get_volume_assessment(self, rate_per_min: float) -> str:
        """Retorna avaliação textual do volume."""
        if rate_per_min > 1000:
            return 'Crítico - Volume extremamente alto'
        elif rate_per_min > 500:
            return 'Muito alto - Sampling urgente recomendado'
        elif rate_per_min > 100:
            return 'Alto - Sampling recomendado'
        elif rate_per_min > 50:
            return 'Moderado - Monitorar crescimento'
        else:
            return 'Normal - Sem ação imediata necessária'

    def _analyze_with_ai(self, logs: List[Dict[str, Any]],
                        log_rate: Dict[str, Any],
                        service_dist: Dict[str, int],
                        duplicates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Análise inteligente usando LLM para recomendar estratégias de sampling."""
        print(f"      🤖 IA criando estratégias personalizadas de sampling...")

        # Prepara contexto rico
        top_services = dict(sorted(service_dist.items(), key=lambda x: x[1], reverse=True)[:10])

        # Agrupa logs por padrão
        pattern_stats = []
        for dup in duplicates[:20]:
            pattern_stats.append({
                'message_pattern': dup['pattern']['message'][:100],
                'count': dup['count'],
                'service': dup['pattern'].get('service')
            })

        # Amostras de logs por serviço
        service_samples = defaultdict(list)
        for log in logs[:50]:
            service = log.get('service', 'unknown')
            if len(service_samples[service]) < 3:
                service_samples[service].append({
                    'level': log.get('level'),
                    'message': log.get('message', '')[:100]
                })

        system_prompt = """Você é um especialista em observabilidade e log sampling.
Analise o volume e padrões de logs e CRIE estratégias personalizadas de sampling.

Avalie:
1. Qual a taxa de logs atual e se necessita sampling
2. Quais serviços/padrões mais geram logs
3. Qual severidade do problema (ok, low, medium, high, critical)
4. Estratégias específicas de sampling recomendadas

IMPORTANTE: Responda SEMPRE em português brasileiro. Todos os campos de texto devem estar em português.

Responda APENAS com JSON válido:
{
  "severity": "ok|low|medium|high|critical",
  "needs_sampling": true|false,
  "recommended_strategies": [
    {
      "strategy_name": "nome da estratégia em português",
      "priority": "low|medium|high|critical",
      "description": "descrição detalhada em português",
      "apply_to": ["onde aplicar em português"],
      "expected_reduction_percentage": 50,
      "implementation_notes": "como implementar em português"
    }
  ],
  "estimated_total_reduction": {
    "min_percentage": 30,
    "max_percentage": 60
  },
  "summary": "resumo da análise em português"
}"""

        user_prompt = f"""Analise este cenário de logs:

VOLUME:
- Total de logs: {len(logs)}
- Taxa: {log_rate.get('rate_per_minute', 0):.1f} logs/min
- Duração: {log_rate.get('duration_minutes', 0):.1f} min

TOP SERVIÇOS (por volume):
{json.dumps(top_services, indent=2, ensure_ascii=False)}

PADRÕES MAIS REPETITIVOS:
{json.dumps(pattern_stats, indent=2, ensure_ascii=False)}

AMOSTRAS DE LOGS POR SERVIÇO:
{json.dumps(dict(service_samples), indent=2, ensure_ascii=False)}

Crie estratégias personalizadas de sampling para este cenário."""

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

            strategies = ai_result.get('recommended_strategies', [])

            # Converte para formato esperado
            formatted_strategies = []
            for strat in strategies:
                formatted_strategies.append({
                    'strategy': strat.get('strategy_name'),
                    'details': {
                        'name': strat.get('strategy_name'),
                        'description': strat.get('description')
                    },
                    'priority': strat.get('priority', 'medium'),
                    'implementation': {
                        'description': strat.get('description'),
                        'apply_to': strat.get('apply_to', []),
                        'expected_reduction': f"{strat.get('expected_reduction_percentage', 0)}%",
                        'notes': strat.get('implementation_notes')
                    },
                    'ai_generated': True
                })

            # Cria recomendações
            self.recommendations = []
            for strat in strategies:
                self.recommendations.append({
                    'type': 'ai_sampling_strategy',
                    'priority': strat.get('priority'),
                    'strategy': strat.get('strategy_name'),
                    'action': strat.get('description'),
                    'ai_generated': True
                })

            severity = ai_result.get('severity', 'medium')
            reduction = ai_result.get('estimated_total_reduction', {})

            print(f"      ✓ IA recomendou {len(strategies)} estratégias (severidade: {severity})")
            print(f"      ✓ Redução estimada: {reduction.get('min_percentage', 0)}-{reduction.get('max_percentage', 0)}%")

            return {
                'analysis_type': 'Log Sampling Recommendations (AI-Powered)',
                'current_state': {
                    'total_logs': len(logs),
                    'rate_per_minute': log_rate.get('rate_per_minute', 0),
                    'rate_per_second': log_rate.get('rate_per_second', 0),
                    'duration_minutes': log_rate.get('duration_minutes', 0)
                },
                'volume_analysis': {},
                'service_analysis': [],
                'repetition_analysis': {},
                'recommended_strategies': formatted_strategies,
                'estimated_reduction': {
                    'estimated_percentage': f"{reduction.get('min_percentage', 0)}-{reduction.get('max_percentage', 0)}%",
                    'confidence': 'high',
                    'ai_generated': True
                },
                'ai_analysis': {
                    'needs_sampling': ai_result.get('needs_sampling'),
                    'summary': ai_result.get('summary'),
                    'severity': severity
                },
                'recommendations': self.recommendations,
                'llm_insights': ai_result.get('summary'),
                'severity': severity
            }

        except Exception as e:
            print(f"      ⚠️  Erro na análise com IA: {e}")
            print(f"      → Caindo de volta para análise baseada em regras")
            # Fallback
            volume_analysis = self._analyze_volume(log_rate)
            service_analysis = self._analyze_per_service(logs, service_dist)
            repetition_analysis = self._analyze_repetitive_patterns(duplicates)
            strategies = self._recommend_strategies(
                volume_analysis, service_analysis, repetition_analysis
            )
            estimated_reduction = self._calculate_estimated_reduction(strategies)

            return {
                'analysis_type': 'Log Sampling Recommendations',
                'current_state': {
                    'total_logs': len(logs),
                    'rate_per_minute': log_rate.get('rate_per_minute', 0),
                    'rate_per_second': log_rate.get('rate_per_second', 0),
                    'duration_minutes': log_rate.get('duration_minutes', 0)
                },
                'volume_analysis': volume_analysis,
                'service_analysis': service_analysis,
                'repetition_analysis': repetition_analysis,
                'recommended_strategies': strategies,
                'estimated_reduction': estimated_reduction,
                'recommendations': self.recommendations,
                'llm_insights': f"Erro na análise IA: {e}",
                'severity': self._calculate_severity(log_rate)
            }

    def _calculate_severity(self, log_rate: Dict[str, Any]) -> str:
        """Calcula severidade baseado na taxa de logs."""
        rate = log_rate.get('rate_per_minute', 0)

        if rate > self.THRESHOLDS['very_high_volume_per_minute']:
            return 'critical'
        elif rate > self.THRESHOLDS['high_volume_per_minute']:
            return 'high'
        elif rate > 50:
            return 'medium'
        elif rate > 0:
            return 'low'
        return 'ok'
