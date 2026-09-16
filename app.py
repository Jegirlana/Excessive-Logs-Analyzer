"""
Interface gráfica para o Excessive Logs Analyzer.
Execute com: streamlit run app.py
"""

import json
import os
import sys
import tempfile
import threading
from datetime import datetime
from typing import Dict, Any, Optional

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()


# ─── Configuração da página ───────────────────────────────────────────────────

st.set_page_config(
    page_title="Analisador de Logs Excessivos",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Report a bug": None,
        "Get help": None,
        "About": "**Analisador de Logs Excessivos** — Identifica e mitiga o antipadrão Excessive Logs usando análise estatística e IA.",
    },
)

st.markdown("""
<style>
    .metric-card {
        background: #f0f2f6;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    .severity-ok       { color: #28a745; font-weight: bold; }
    .severity-low      { color: #6c757d; font-weight: bold; }
    .severity-medium   { color: #fd7e14; font-weight: bold; }
    .severity-high     { color: #dc3545; font-weight: bold; }
    .severity-critical { color: #721c24; font-weight: bold; }
    .issue-row { border-left: 3px solid #ff4b4b; padding-left: 8px; margin: 4px 0; }
    .rec-row   { border-left: 3px solid #0068c9; padding-left: 8px; margin: 4px 0; }

    /* Oculta o botão de Deploy do Streamlit */
    [data-testid="stAppDeployButton"] { display: none !important; }

    /* Traduz itens do menu de 3 pontinhos (tipo action — têm stMainMenuItemLabel) */
    [data-testid="stMainMenuItem-rerun"] [data-testid="stMainMenuItemLabel"],
    [data-testid="stMainMenuItem-clearCache"] [data-testid="stMainMenuItemLabel"],
    [data-testid="stMainMenuItem-print"] [data-testid="stMainMenuItemLabel"],
    [data-testid="stMainMenuItem-recordScreencast"] [data-testid="stMainMenuItemLabel"],
    [data-testid="stMainMenuItem-about"] [data-testid="stMainMenuItemLabel"],
    [data-testid="stMainMenuItem-changeTheme"] [data-testid="stMainMenuItemLabel"],
    [data-testid="stMainMenuItem-theme-System"] [data-testid="stMainMenuItemLabel"],
    [data-testid="stMainMenuItem-theme-Light"] [data-testid="stMainMenuItemLabel"],
    [data-testid="stMainMenuItem-theme-Dark"] [data-testid="stMainMenuItemLabel"]
        { font-size: 0 !important; }

    [data-testid="stMainMenuItem-rerun"] [data-testid="stMainMenuItemLabel"]::before
        { content: "Reexecutar"; font-size: 14px; }
    [data-testid="stMainMenuItem-clearCache"] [data-testid="stMainMenuItemLabel"]::before
        { content: "Limpar cache"; font-size: 14px; }
    [data-testid="stMainMenuItem-print"] [data-testid="stMainMenuItemLabel"]::before
        { content: "Imprimir"; font-size: 14px; }
    [data-testid="stMainMenuItem-recordScreencast"] [data-testid="stMainMenuItemLabel"]::before
        { content: "Gravar tela"; font-size: 14px; }
    [data-testid="stMainMenuItem-about"] [data-testid="stMainMenuItemLabel"]::before
        { content: "Sobre"; font-size: 14px; }
    [data-testid="stMainMenuItem-changeTheme"] [data-testid="stMainMenuItemLabel"]::before
        { content: "Tema"; font-size: 14px; }
    [data-testid="stMainMenuItem-theme-System"] [data-testid="stMainMenuItemLabel"]::before
        { content: "Padrão do sistema"; font-size: 14px; }
    [data-testid="stMainMenuItem-theme-Light"] [data-testid="stMainMenuItemLabel"]::before
        { content: "Claro"; font-size: 14px; }
    [data-testid="stMainMenuItem-theme-Dark"] [data-testid="stMainMenuItemLabel"]::before
        { content: "Escuro"; font-size: 14px; }

    /* autoRerun é tipo toggle — o texto fica direto no botão, sem stMainMenuItemLabel */
    [data-testid="stMainMenuItem-autoRerun"] { font-size: 0 !important; }
    [data-testid="stMainMenuItem-autoRerun"]::before
        { content: "Reexecução automática"; font-size: 14px; }

    /* Oculta textos internos do file_uploader gerados pelo Streamlit em inglês */
    [data-testid="stFileUploaderDropzoneInstructions"] > div > span { display: none; }
    [data-testid="stFileUploaderDropzoneInstructions"] > div::before {
        content: "Arraste e solte o arquivo aqui";
        font-size: 14px;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] > div > small { display: none; }
    [data-testid="stFileUploaderDropzoneInstructions"] > div::after {
        content: "Limite: 200 MB por arquivo • JSON";
        font-size: 12px;
        color: #888;
        display: block;
    }
    [data-testid="stFileUploaderDropzone"] button[data-testid="baseButton-secondary"] span { display: none; }
    [data-testid="stFileUploaderDropzone"] button[data-testid="baseButton-secondary"]::before {
        content: "Procurar arquivo";
    }
</style>
""", unsafe_allow_html=True)


# ─── Helpers ──────────────────────────────────────────────────────────────────

SEVERITY_EMOJI = {
    "ok": "✅",
    "low": "🟡",
    "medium": "🟠",
    "high": "🔴",
    "critical": "💀",
}

PROVIDER_LABELS = {
    "groq":     "Groq (Llama 3.3 70B) — Gratuito",
    "gemini":   "Gemini Flash — Gratuito",
    "claude":   "Claude (Haiku via OpenRouter) — Gratuito",
    "chatgpt":  "ChatGPT (GPT-4o Mini via GitHub) — Gratuito",
    "standard": "Standard (sem IA) — Gratuito",
}

PROVIDER_HELP = {
    "groq":     "Requer GROQ_API_KEY no arquivo .env",
    "gemini":   "Requer GOOGLE_API_KEY no arquivo .env",
    "claude":   "Requer OPENROUTER_API_KEY (gratuito em openrouter.ai) ou ANTHROPIC_API_KEY",
    "chatgpt":  "Requer GITHUB_TOKEN (gratuito em github.com/settings/tokens) ou OPENAI_API_KEY",
    "standard": "Sempre disponível — análise baseada em regras",
}


def _check_provider_availability() -> Dict[str, bool]:
    """Verifica quais provedores estão disponíveis com base nas variáveis de ambiente."""
    available = {}
    available["groq"] = bool(os.getenv("GROQ_API_KEY"))
    available["gemini"] = bool(os.getenv("GOOGLE_API_KEY"))
    available["standard"] = True
    available["claude"] = bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENROUTER_API_KEY"))
    available["chatgpt"] = bool(os.getenv("OPENAI_API_KEY") or os.getenv("GITHUB_TOKEN"))
    return available


def _severity_badge(severity: str) -> str:
    emoji = SEVERITY_EMOJI.get(severity, "❓")
    css_class = f"severity-{severity}"
    return f'<span class="{css_class}">{emoji} {severity.upper()}</span>'


def _health_color(score: int) -> str:
    if score >= 80:
        return "normal"
    if score >= 60:
        return "off"
    return "inverse"


# ─── Execução da análise ──────────────────────────────────────────────────────

def _run_analysis(log_file_path: str, selected_providers: list, status_placeholder) -> Dict[str, Any]:
    """
    Executa a análise nos provedores selecionados.
    Retorna o dicionário de resultados com a mesma estrutura de ExcessiveLogsAnalyzer.
    """
    # Importações aqui para evitar overhead na inicialização da página
    from src.utils.log_processor import LogProcessor
    from src.analyzers.log_level_analyzer import LogLevelAnalyzer
    from src.analyzers.unnecessary_logs_detector import UnnecessaryLogsDetector
    from src.analyzers.sampling_recommender import SamplingRecommender
    from src.utils.llm_client import LLMClient

    processor = LogProcessor()

    with status_placeholder.status("Carregando logs...", expanded=True) as status:
        st.write("📂 Carregando arquivo de logs...")
        logs = processor.load_logs(log_file_path)
        st.write(f"✓ {len(logs)} logs carregados")

        st.write("📊 Calculando estatísticas...")
        level_dist      = processor.get_level_distribution(logs)
        service_dist    = processor.get_service_distribution(logs)
        service_levels  = processor.group_by_service_and_level(logs)
        duplicates      = processor.find_duplicate_logs(logs)
        log_rate        = processor.calculate_log_rate(logs)
        error_types     = processor.get_error_types(logs)
        http_status_dist = processor.get_http_status_distribution(logs)
        tags_dist       = processor.get_tags_distribution(logs)
        st.write("✓ Estatísticas processadas")

        all_results: Dict[str, Any] = {}

        for provider in selected_providers:
            st.write(f"🤖 Analisando com **{provider.upper()}**...")

            llm_client = None
            if provider != "standard":
                try:
                    llm_client = LLMClient(provider=provider)
                except Exception as e:
                    st.warning(f"⚠️ Não foi possível inicializar {provider}: {e}")
                    continue

            level_analyzer     = LogLevelAnalyzer(llm_client)
            unnecessary_detect = UnnecessaryLogsDetector(llm_client)
            sampling_recomm    = SamplingRecommender(llm_client)

            try:
                level_analysis      = level_analyzer.analyze(logs, service_levels)
                unnecessary_analysis = unnecessary_detect.analyze(logs, duplicates)
                sampling_analysis   = sampling_recomm.analyze(logs, log_rate, service_dist, duplicates)
            except Exception as e:
                st.warning(f"⚠️ Erro na análise com {provider}: {e}")
                continue

            overall = _calculate_assessment(level_analysis, unnecessary_analysis, sampling_analysis)

            all_results[provider] = {
                "metadata": {
                    "analysis_timestamp": datetime.now().isoformat(),
                    "log_file": log_file_path,
                    "analysis_mode": provider,
                    "llm_provider": llm_client.provider if llm_client else None,
                    "model": llm_client.model if llm_client else None,
                },
                "analyses": {
                    "log_levels": level_analysis,
                    "unnecessary_logs": unnecessary_analysis,
                    "sampling_recommendations": sampling_analysis,
                },
                "overall_assessment": overall,
            }
            st.write(f"✓ {provider.upper()} concluído — Pontuação de Saúde: {overall['health_score']}/100")

        status.update(label="✅ Análise concluída!", state="complete", expanded=False)

    return {
        "metadata": {
            "analysis_timestamp": datetime.now().isoformat(),
            "log_file": log_file_path,
            "analysis_mode": "all",
            "modes_executed": list(all_results.keys()),
        },
        "summary": {
            "total_logs": len(logs),
            "level_distribution": level_dist,
            "service_distribution": service_dist,
            "log_rate": log_rate,
            "error_types": error_types,
            "http_status_distribution": http_status_dist,
            "tags_distribution": tags_dist,
            "duplicate_patterns": len(duplicates),
        },
        "results_by_mode": all_results,
    }


def _calculate_assessment(level_analysis, unnecessary_analysis, sampling_analysis) -> Dict[str, Any]:
    severities = [
        level_analysis["severity"],
        unnecessary_analysis["severity"],
        sampling_analysis["severity"],
    ]
    order = ["ok", "low", "medium", "high", "critical"]
    max_severity = max(severities, key=lambda s: order.index(s) if s in order else 0)

    total_issues = (
        len(level_analysis.get("issues", []))
        + len(unnecessary_analysis.get("issues", []))
        + len(sampling_analysis.get("recommended_strategies", []))
    )

    score_map = {"critical": 20, "high": 40, "medium": 60, "low": 80}
    health_score = score_map.get(max_severity, 100)

    priority_actions = []
    if level_analysis["severity"] in ("critical", "high"):
        priority_actions.append({"priority": 1, "action": "Ajustar níveis de log",
                                  "reason": "Configuração inadequada detectada"})
    if unnecessary_analysis.get("reduction_potential_percentage", 0) > 30:
        priority_actions.append({"priority": 2, "action": "Remover logs desnecessários",
                                  "reason": f"Potencial de redução: {unnecessary_analysis['reduction_potential_percentage']:.1f}%"})
    if sampling_analysis["severity"] in ("critical", "high"):
        priority_actions.append({"priority": 3, "action": "Implementar amostragem",
                                  "reason": "Volume de logs requer amostragem"})

    return {
        "overall_severity": max_severity,
        "health_score": health_score,
        "total_issues": total_issues,
        "priority_actions": priority_actions,
        "summary": f"{total_issues} problema(s) detectado(s) — severidade {max_severity.upper()}",
    }


# ─── Componentes de visualização ──────────────────────────────────────────────

def _show_summary_metrics(summary: Dict[str, Any]):
    """Métricas globais do arquivo de logs."""
    log_rate = summary.get("log_rate", {})
    cols = st.columns(4)
    cols[0].metric("Total de Logs", f"{summary['total_logs']:,}")
    cols[1].metric("Taxa (logs/min)", f"{log_rate.get('rate_per_minute', 0):.1f}")
    cols[2].metric("Duração", f"{log_rate.get('duration_minutes', 0):.1f} min")
    cols[3].metric("Padrões Duplicados", summary.get("duplicate_patterns", 0))


def _show_level_chart(level_dist: Dict[str, int]):
    import pandas as pd
    if not level_dist:
        return
    df = pd.DataFrame(
        {"Nível": list(level_dist.keys()), "Quantidade": list(level_dist.values())}
    ).sort_values("Quantidade", ascending=False)
    st.bar_chart(df.set_index("Nível"))


def _show_service_chart(service_dist: Dict[str, int]):
    import pandas as pd
    if not service_dist:
        return
    top = dict(sorted(service_dist.items(), key=lambda x: x[1], reverse=True)[:10])
    df = pd.DataFrame({"Serviço": list(top.keys()), "Logs": list(top.values())})
    st.bar_chart(df.set_index("Serviço"))


def _show_provider_results(provider: str, data: Dict[str, Any], summary: Dict[str, Any]):
    """Exibe os resultados de um provedor em seções."""
    assessment = data["overall_assessment"]
    analyses   = data["analyses"]
    metadata   = data["metadata"]

    # Cabeçalho com métricas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Pontuação de Saúde", f"{assessment['health_score']}/100",
                delta=None,
                help="0 = crítico, 100 = perfeito")
    col2.metric("Severidade", assessment["overall_severity"].upper())
    col3.metric("Problemas", assessment["total_issues"])
    col4.metric("Modelo", metadata.get("model") or "regras")

    if assessment.get("priority_actions"):
        st.subheader("🎯 Ações Prioritárias")
        for action in assessment["priority_actions"]:
            st.info(f"**{action['priority']}. {action['action']}** — {action['reason']}")

    # Distribuição de níveis
    st.subheader("📊 Distribuição de Níveis de Log")
    col_lv, col_svc = st.columns(2)
    with col_lv:
        st.caption("Por nível")
        _show_level_chart(summary.get("level_distribution", {}))
    with col_svc:
        st.caption("Por serviço (top 10)")
        _show_service_chart(summary.get("service_distribution", {}))

    # Análise 1 — Níveis de log
    with st.expander("📋 Análise 1: Efetividade dos Níveis de Log", expanded=True):
        ll = analyses["log_levels"]
        pct = ll.get("level_percentages", {})
        if pct:
            import pandas as pd
            df_pct = pd.DataFrame({"Nível": list(pct.keys()), "%": list(pct.values())}).set_index("Nível")
            st.dataframe(df_pct, use_container_width=True)
        if ll.get("llm_insights"):
            st.info(f"💡 **Observação da IA:** {ll['llm_insights']}")
        issues = ll.get("issues", [])
        if issues:
            st.markdown(f"**{len(issues)} problema(s) encontrado(s):**")
            for issue in issues:
                sev = issue.get("severity", "")
                st.markdown(
                    f'<div class="issue-row">🔸 <b>{issue.get("type","")}</b> '
                    f'<span class="severity-{sev}">({sev})</span><br>'
                    f'{issue.get("description","")}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.success("Nenhum problema encontrado nesta análise.")

    # Análise 2 — Logs desnecessários
    with st.expander("🔎 Análise 2: Detecção de Logs Desnecessários", expanded=True):
        ul = analyses["unnecessary_logs"]
        col_a, col_b = st.columns(2)
        col_a.metric("Logs desnecessários", ul.get("unnecessary_logs_count", 0))
        col_b.metric("Potencial de redução", f"{ul.get('reduction_potential_percentage', 0):.1f}%")
        if ul.get("llm_insights"):
            st.info(f"💡 **Observação da IA:** {ul['llm_insights']}")
        issues = ul.get("issues", [])
        if issues:
            st.markdown(f"**{len(issues)} problema(s) encontrado(s):**")
            for issue in issues:
                sev = issue.get("severity", "")
                st.markdown(
                    f'<div class="issue-row">🔸 <b>{issue.get("type","")}</b> '
                    f'<span class="severity-{sev}">({sev})</span><br>'
                    f'{issue.get("description","")}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.success("Nenhum problema encontrado nesta análise.")

    # Análise 3 — Sampling
    with st.expander("📈 Análise 3: Recomendações de Amostragem", expanded=True):
        sr = analyses["sampling_recommendations"]
        current = sr.get("current_state", {})
        col_r, col_e = st.columns(2)
        col_r.metric("Taxa atual", f"{current.get('rate_per_minute', 0):.1f} logs/min")
        col_e.metric("Redução estimada", sr.get("estimated_reduction", {}).get("estimated_percentage", "—"))
        if sr.get("llm_insights"):
            st.info(f"💡 **Observação da IA:** {sr['llm_insights']}")
        strategies = sr.get("recommended_strategies", [])
        if strategies:
            st.markdown(f"**{len(strategies)} estratégia(s) recomendada(s):**")
            for strat in strategies:
                name = strat.get("strategy") or strat.get("details", {}).get("name", "?")
                impl = strat.get("implementation", {})
                st.markdown(
                    f'<div class="rec-row">🔹 <b>{name}</b> — '
                    f'{impl.get("description", strat.get("details", {}).get("description",""))}'
                    f'<br>Redução esperada: {impl.get("expected_reduction","?")}</div>',
                    unsafe_allow_html=True,
                )


def _show_comparative_tab(results_by_mode: Dict[str, Any]):
    """Tabela comparativa entre todos os modos."""
    import pandas as pd

    rows = []
    for mode, data in results_by_mode.items():
        assessment = data["overall_assessment"]
        analyses   = data["analyses"]
        rows.append({
            "Provedor": mode.upper(),
            "Pontuação de Saúde": assessment["health_score"],
            "Severidade": assessment["overall_severity"].upper(),
            "Problemas": assessment["total_issues"],
            "Redução potencial": f"{analyses['unnecessary_logs'].get('reduction_potential_percentage',0):.1f}%",
            "Estratégias de amostragem": len(analyses["sampling_recommendations"].get("recommended_strategies", [])),
            "Modelo": data["metadata"].get("model") or "regras",
        })

    if rows:
        df = pd.DataFrame(rows).set_index("Provedor")
        st.dataframe(df, use_container_width=True)


def _build_individual_report(provider: str, data: Dict[str, Any], summary: Dict[str, Any]) -> Dict:
    return {
        "metadata": data["metadata"],
        "summary": summary,
        "analyses": data["analyses"],
        "overall_assessment": data["overall_assessment"],
    }


# ─── Interface principal ──────────────────────────────────────────────────────

def main():
    # Cabeçalho
    st.title("🔍 Analisador de Logs Excessivos")
    st.markdown(
        "Identifica e mitiga o antipadrão **Excessive Logs** usando análise estatística e IA. "
        "Configure os provedores na barra lateral e clique em **Executar Análise**."
    )
    st.divider()

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("⚙️ Configuração")

        # Upload de arquivo
        st.caption("Passo 1 — Escolha o arquivo de logs")
        st.subheader("📂 Arquivo de Logs")
        uploaded = st.file_uploader(
            "Selecione um arquivo JSON de logs",
            type=["json"],
            help="Formato esperado: lista de objetos JSON com campos data/hora, nível, serviço e mensagem.",
        )

        use_default = st.checkbox(
            "Usar dataset padrão (synthetic_logs.json)",
            value=uploaded is None,
            disabled=uploaded is not None,
        )

        st.divider()

        # Provedores
        st.caption("Passo 2 — Escolha um provedor de IA")
        st.subheader("🤖 Provedores de IA")
        availability = _check_provider_availability()

        claude_status = "🟢 Disponível" if availability["claude"] else "🔴 Chave não configurada"
        chatgpt_status = "🟢 Disponível" if availability["chatgpt"] else "🔴 Chave não configurada"
        st.caption(f"Claude: {claude_status} · ChatGPT: {chatgpt_status}")

        selected: Dict[str, bool] = {}
        for provider in ["groq", "gemini", "claude", "chatgpt", "standard"]:
            avail = availability[provider]
            label = PROVIDER_LABELS[provider]
            help_text = PROVIDER_HELP[provider]
            if avail:
                selected[provider] = st.checkbox(label, value=True, help=help_text)
            else:
                st.checkbox(label, value=False, disabled=True,
                            help=f"❌ Indisponível — {help_text}")
                selected[provider] = False

        active_providers = [p for p, v in selected.items() if v]

        st.divider()

        # Relatório de saída
        st.caption("Passo 3 — Defina o nome do relatório")
        st.subheader("📁 Saída")
        output_name = st.text_input(
            "Nome base dos relatórios",
            value="synthetic_logs",
            help="Os relatórios serão salvos em reports/{nome}_{provedor}.json",
        )

        st.divider()

        # Botão de execução
        st.caption("Passo 4 — Execute a análise")
        run_btn = st.button(
            "▶ Executar Análise",
            type="primary",
            disabled=len(active_providers) == 0,
            use_container_width=True,
        )

        if len(active_providers) == 0:
            st.warning("Selecione pelo menos um provedor.")

        # Dica de configuração de Claude/ChatGPT
        if not availability["claude"] or not availability["chatgpt"]:
            with st.expander("Como ativar Claude e ChatGPT?"):
                st.markdown(
                    "**Claude** — obtenha uma chave gratuita em [openrouter.ai](https://openrouter.ai) "
                    "e defina `OPENROUTER_API_KEY` no `.env`.\n\n"
                    "**ChatGPT** — gere um token em "
                    "[github.com/settings/tokens](https://github.com/settings/tokens) "
                    "e defina `GITHUB_TOKEN` no `.env`."
                )

    # ── Área principal ────────────────────────────────────────────────────────

    # Preview do arquivo antes da análise
    if not run_btn:
        log_path_preview = None
        if uploaded:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
            tmp.write(uploaded.getvalue())
            tmp.flush()
            log_path_preview = tmp.name
        elif use_default:
            default_path = os.path.join(os.path.dirname(__file__), "dataset", "synthetic_logs.json")
            if os.path.exists(default_path):
                log_path_preview = default_path

        if log_path_preview:
            try:
                with open(log_path_preview, encoding="utf-8") as f:
                    preview_logs = json.load(f)
                st.subheader(f"📋 Pré-visualização — {len(preview_logs)} logs carregados")
                import pandas as pd
                preview_rows = []
                for log in preview_logs[:10]:
                    preview_rows.append({
                        "Data/Hora": log.get("timestamp", ""),
                        "Nível": log.get("level", ""),
                        "Serviço": log.get("service", ""),
                        "Mensagem": log.get("message", "")[:80],
                    })
                st.dataframe(pd.DataFrame(preview_rows), use_container_width=True)
                st.caption("Exibindo os 10 primeiros logs.")
            except Exception:
                pass

        if not log_path_preview:
            st.info("📂 Carregue um arquivo de logs ou use o dataset padrão para começar.")

        return

    # ── Execução ──────────────────────────────────────────────────────────────
    log_file_path: Optional[str] = None

    if uploaded:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        tmp.write(uploaded.getvalue())
        tmp.flush()
        log_file_path = tmp.name
    elif use_default:
        log_file_path = os.path.join(os.path.dirname(__file__), "dataset", "synthetic_logs.json")

    if not log_file_path or not os.path.exists(log_file_path):
        st.error("❌ Arquivo de logs não encontrado. Faça upload ou use o dataset padrão.")
        return

    status_placeholder = st.empty()

    try:
        result = _run_analysis(log_file_path, active_providers, status_placeholder)
    except Exception as e:
        st.error(f"❌ Erro durante a análise: {e}")
        with st.expander("Detalhes do erro"):
            import traceback
            st.code(traceback.format_exc())
        return

    results_by_mode = result.get("results_by_mode", {})
    summary = result["summary"]

    if not results_by_mode:
        st.warning("Nenhum resultado disponível. Verifique as configurações dos provedores.")
        return

    # Salva relatórios em reports/
    reports_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(reports_dir, exist_ok=True)

    mode_label_map = {
        "groq": "groq", "gemini": "gemini", "claude": "claude_ai",
        "chatgpt": "chatgpt", "standard": "sem_ia",
    }
    report_paths: Dict[str, str] = {}

    for mode, data in results_by_mode.items():
        label = mode_label_map.get(mode, mode)
        filepath = os.path.join(reports_dir, f"{output_name}_{label}.json")
        report_content = _build_individual_report(mode, data, summary)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report_content, f, indent=2, ensure_ascii=False)
        report_paths[mode] = filepath

    comp_path = os.path.join(reports_dir, f"{output_name}_comparativo.json")
    with open(comp_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Métricas gerais
    st.subheader("📊 Visão Geral do Dataset")
    _show_summary_metrics(summary)
    st.divider()

    # Abas por provedor + comparativo
    tab_labels = [f"🤖 {PROVIDER_LABELS.get(p, p.upper()).split(' —')[0]}" for p in results_by_mode] + ["📊 Comparativo"]
    tabs = st.tabs(tab_labels)

    for i, (provider, data) in enumerate(results_by_mode.items()):
        with tabs[i]:
            st.subheader(f"Análise com {PROVIDER_LABELS.get(provider, provider)}")
            _show_provider_results(provider, data, summary)

            # Download do relatório individual
            label = mode_label_map.get(provider, provider)
            filepath = report_paths.get(provider)
            if filepath and os.path.exists(filepath):
                with open(filepath, encoding="utf-8") as f:
                    report_json = f.read()
                st.download_button(
                    label=f"⬇ Baixar relatório {label}.json",
                    data=report_json,
                    file_name=f"{output_name}_{label}.json",
                    mime="application/json",
                    key=f"download_{provider}",
                )

    with tabs[-1]:
        st.subheader("Comparativo entre Provedores")
        _show_comparative_tab(results_by_mode)

        if os.path.exists(comp_path):
            with open(comp_path, encoding="utf-8") as f:
                comp_json = f.read()
            st.download_button(
                label="⬇ Baixar relatório comparativo",
                data=comp_json,
                file_name=f"{output_name}_comparativo.json",
                mime="application/json",
                key="download_comparativo",
            )

    st.success(f"✅ Relatórios salvos em `reports/`")


if __name__ == "__main__":
    main()
