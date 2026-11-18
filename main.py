import re
import time
import pandas as pd
import plotly.express as px
import streamlit as st
from src.filtro_service import FiltroMaterialService

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA & ESTÉTICA CLEAN (SAAS)
# ==============================================================================
st.set_page_config(
    page_title="MatSelect Pro | Seleção de Materiais Industriais",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {background-color: rgba(0,0,0,0);}
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# 2. CAMADA DE CACHE (VELOCIDADE INSTANTÂNEA)
# ==============================================================================
@st.cache_resource
def obter_servico():
    return FiltroMaterialService()


@st.cache_data
def executar_selecao(temperatura, esforco, quimico, aplicacao):
    servico = obter_servico()
    condicoes = {
        "temperatura_C": temperatura,
        "esforco_mecanico": esforco.lower(),
        "contato_quimico": quimico,
        "aplicacao": aplicacao,
    }
    return servico.selecionar(condicoes)


def _extrair_num(val):
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        nums = [float(n) for n in re.findall(r"[-+]?\d*\.\d+|\d+", val.replace(",", "."))]
        if nums:
            return sum(nums) / len(nums)
    return None


@st.cache_data
def obter_dataframe_catalogo():
    servico = obter_servico()
    linhas = []
    for m in servico.materiais:
        prop = m.get("propriedades_tecnicas", {})
        tracao = _extrair_num(prop.get("resistencia_tracao_MPa") or prop.get("limite_escoamento_MPa"))
        densidade = _extrair_num(prop.get("densidade_g_cm3"))
        temp_max = servico._obter_limite_temperatura(m)
        linhas.append(
            {
                "ID": m.get("id", ""),
                "Material": m.get("nome", ""),
                "Categoria": m.get("categoria", ""),
                "Tipo": m.get("tipo", ""),
                "Tração / Escoamento (MPa)": tracao,
                "Densidade (g/cm³)": densidade,
                "Temp. Máx. Serviço (°C)": temp_max,
                "Aplicações Principais": ", ".join(m.get("aplicacoes_tipicas", [])[:3]),
            }
        )
    return pd.DataFrame(linhas)


# ==============================================================================
# 3. COMPONENTE: ESTATÍSTICAS PARA NERDS (TELEMETRIA DE ENGENHARIA)
# ==============================================================================
def renderizar_stats_for_nerds(item, mat_raw, temp_req, temp_max, latencia_ms):
    # Monta a equação matemática do Score
    partes_eq = ["Base(50)"]
    for d in item.get("detalhamento", []):
        partes_eq.append(f"{d['Pontos']} ({d['Critério']})")
    equacao_str = " ".join(partes_eq) + f" = {item['pontuacao']} pts"

    # Calcula margem térmica
    folga_termica = temp_max - temp_req
    uso_termico_pct = max(0.0, (temp_req / temp_max) * 100) if temp_max > 0 else 0.0

    # Formata propriedades técnicas brutas
    props = mat_raw.get("propriedades_tecnicas", {})
    props_formatadas = " | ".join(
        [f"{k.replace('_', ' ')}: {v}" for k, v in props.items()]
    ) or "N/D"

    aplicacoes_str = ", ".join(mat_raw.get("aplicacoes_tipicas", [])) or "N/D"

    html_box = (
        '<div style="background-color:#161616; color:#E5E7EB; font-family:\'Courier New\', monospace; '
        'font-size:12px; padding:14px 16px; border-radius:8px; border-left:4px solid #0F62FE; '
        'margin-top:10px; line-height:1.55;">'
        '<div style="color:#60A5FA; font-weight:bold; margin-bottom:6px; letter-spacing:0.5px;">'
        '🤓 ESTATÍSTICAS PARA NERDS // TELEMETRIA DE ENGENHARIA'
        '</div>'
        f'<div><span style="color:#9CA3AF;">Material ID / Classe:</span> {item["id"]} • {mat_raw.get("tipo", "-")}</div>'
        f'<div><span style="color:#9CA3AF;">Equação do Score:</span> <span style="color:#34D399;">{equacao_str}</span></div>'
        f'<div><span style="color:#9CA3AF;">Regime Térmico:</span> {temp_req} °C / {temp_max} °C máx '
        f'(Uso: {uso_termico_pct:.1f}% | Folga: +{folga_termica} °C)</div>'
        f'<div><span style="color:#9CA3AF;">Datasheet Bruto:</span> {props_formatadas}</div>'
        f'<div><span style="color:#9CA3AF;">Aplicações Base:</span> {aplicacoes_str}</div>'
        f'<div style="color:#9CA3AF; margin-top:4px; font-size:11px;">'
        f'Latência de Inferência: {latencia_ms:.2f} ms | Motor: FiltroMaterialService v2.1'
        f'</div>'
        '</div>'
    )
    st.markdown(html_box, unsafe_allow_html=True)


# ==============================================================================
# 4. GERENCIAMENTO DE ESTADO & CENÁRIOS RÁPIDOS (1 CLIQUE)
# ==============================================================================
CENARIOS = {
    "Uso Geral": {"temp": 25, "esforco": "Moderado", "quimico": False, "kw": ""},
    "⚙️ Eixo / Engrenagem": {"temp": 80, "esforco": "Alto", "quimico": False, "kw": "engrenagem"},
    "🧪 Meio Corrosivo": {"temp": 60, "esforco": "Moderado", "quimico": True, "kw": ""},
    "❄️ Criogenia (-50°C)": {"temp": -50, "esforco": "Alto", "quimico": False, "kw": ""},
    "🔥 Alta Temp. (300°C)": {"temp": 300, "esforco": "Alto", "quimico": False, "kw": ""},
}

if "temp" not in st.session_state:
    st.session_state.temp = 25
if "esforco" not in st.session_state:
    st.session_state.esforco = "Moderado"
if "quimico" not in st.session_state:
    st.session_state.quimico = False
if "kw" not in st.session_state:
    st.session_state.kw = ""


def aplicar_cenario():
    escolha = st.session_state.get("cenario_selecionado")
    if escolha and escolha in CENARIOS:
        cfg = CENARIOS[escolha]
        st.session_state.temp = cfg["temp"]
        st.session_state.esforco = cfg["esforco"]
        st.session_state.quimico = cfg["quimico"]
        st.session_state.kw = cfg["kw"]


def resetar_filtros():
    st.session_state.temp = 25
    st.session_state.esforco = "Moderado"
    st.session_state.quimico = False
    st.session_state.kw = ""
    st.session_state.cenario_selecionado = None


# ==============================================================================
# 5. BARRA LATERAL (CONTROLES INTUITIVOS + MODO NERD)
# ==============================================================================
with st.sidebar:
    st.markdown("### ⚙️ Parâmetros de Projeto")
    st.caption("Configure as condições operacionais ou teste um cenário rápido.")

    st.pills(
        "Cenários Rápidos",
        options=list(CENARIOS.keys()),
        key="cenario_selecionado",
        on_change=aplicar_cenario,
        help="Preenche automaticamente os filtros com casos típicos da indústria.",
    )

    st.divider()

    temp_req = st.slider(
        "Temperatura de Operação (°C)",
        min_value=-100,
        max_value=750,
        step=5,
        key="temp",
        help="Elimina materiais que deformam, fundem ou oxidam acima desta temperatura.",
    )

    esforco_req = st.segmented_control(
        "Esforço Mecânico",
        options=["Baixo", "Moderado", "Alto"],
        key="esforco",
        selection_mode="single",
        help="Define a exigência de resistência à tração e penaliza materiais sujeitos à fluência (creep).",
    )
    if not esforco_req:
        esforco_req = "Moderado"

    quimico_req = st.toggle(
        "Ambiente Químico / Corrosivo",
        key="quimico",
        help="Prioriza materiais inertes a ácidos, bases, solventes ou maresia.",
    )

    kw_req = st.text_input(
        "Aplicação ou Componente (opcional)",
        placeholder="Ex: tubulação, bucha, aeronáutica...",
        key="kw",
        help="Busca palavras-chave nas aplicações industriais consolidadas de cada material.",
    )

    st.divider()

    modo_nerd = st.toggle(
        "🤓 Estatísticas para Nerds",
        value=False,
        help="Exibe telemetria técnica completa, fórmula de pontuação, folga térmica e ficha bruta em cada resultado.",
    )

    st.button("↺ Limpar Filtros", on_click=resetar_filtros, use_container_width=True)


# ==============================================================================
# 6. EXECUÇÃO DO MOTOR & CABEÇALHO (KPIs)
# ==============================================================================
servico = obter_servico()
mapa_materiais = {m["id"]: m for m in servico.materiais}
total_base = len(servico.materiais)

t_inicio = time.perf_counter()
resultados = executar_selecao(temp_req, esforco_req, quimico_req, kw_req)
latencia_ms = (time.perf_counter() - t_inicio) * 1000

st.title("Seletor Inteligente de Materiais")
st.caption("Sistema de apoio à decisão para engenharia mecânica, química e manufatura.")

col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
with col_kpi1:
    with st.container(border=True):
        st.metric("Materiais Compatíveis", f"{len(resultados)} de {total_base}")
with col_kpi2:
    with st.container(border=True):
        top_nome = resultados[0]["material"] if resultados else "Nenhum"
        top_pts = f"{resultados[0]['pontuacao']} pts" if resultados else "Ajuste os filtros"
        st.metric("Recomendação #1", top_nome, delta=top_pts)
with col_kpi3:
    with st.container(border=True):
        regime = f"{temp_req} °C • Esforço {esforco_req}"
        tag_quim = "Corrosivo" if quimico_req else "Sem ataque químico"
        st.metric("Condição Analisada", regime, delta=tag_quim, delta_color="off")

st.write("")


# ==============================================================================
# 7. NAVEGAÇÃO PRINCIPAL (4 ABAS LIMPAS)
# ==============================================================================
tab_rec, tab_cat, tab_graf, tab_ficha = st.tabs(
    [
        "🎯 Recomendador",
        "📋 Catálogo Completo",
        "📊 Comparador Gráfico",
        "🔍 Ficha Técnica",
    ]
)

# ------------------------------------------------------------------------------
# ABA 1: RECOMENDADOR (TOP 3 EM DESTAQUE + EXPANDER PARA O RESTANTE)
# ------------------------------------------------------------------------------
with tab_rec:
    if not resultados:
        st.warning(
            "Nenhum material da base suporta essa combinação extrema de parâmetros. "
            "Tente reduzir a temperatura de operação ou clicar em **Limpar Filtros**."
        )
    else:
        st.subheader("Melhores Opções para o Projeto")
        medalhas = ["🥇 1º Lugar", "🥈 2º Lugar", "🥉 3º Lugar"]
        top_3 = resultados[:3]
        restante = resultados[3:]

        for idx, item in enumerate(top_3):
            mat_raw = mapa_materiais.get(item["id"], {})
            temp_max = servico._obter_limite_temperatura(mat_raw)

            with st.container(border=True):
                c1, c2, c3 = st.columns([4.5, 1.3, 1.5], vertical_alignment="center")
                with c1:
                    st.markdown(f"**{medalhas[idx]} — {item['material']}** &nbsp; `{item['categoria']}`")
                    resumo = item["justificativas"][0] if item["justificativas"] else "Compatível com os parâmetros."
                    st.caption(resumo)
                    if item["limitacoes"]:
                        alertas_criticos = [a for a in item["limitacoes"] if "ALERTA" in a or "próximo" in a.lower()]
                        if alertas_criticos:
                            st.caption(f"⚠️ {alertas_criticos[0]}")

                with c2:
                    st.metric("Score", f"{item['pontuacao']} pts")

                with c3:
                    with st.popover("Ver Análise", use_container_width=True):
                        st.markdown(f"#### {item['material']}")
                        st.markdown("**Por que foi recomendado:**")
                        for j in item["justificativas"]:
                            st.markdown(f"- ✅ {j}")

                        if item["limitacoes"]:
                            st.markdown("**Pontos de Atenção / Limitações:**")
                            for lim in item["limitacoes"]:
                                st.markdown(f"- ⚠️ {lim}")

                        if item["detalhamento"]:
                            st.markdown("**Composição da Nota:**")
                            st.dataframe(
                                pd.DataFrame(item["detalhamento"]),
                                hide_index=True,
                                use_container_width=True,
                            )

                # Exibe o painel estilo YouTube se "Estatísticas para Nerds" estiver ativo
                if modo_nerd:
                    renderizar_stats_for_nerds(item, mat_raw, temp_req, temp_max, latencia_ms)

        if restante:
            st.write("")
            with st.expander(f"Ver outras {len(restante)} opções compatíveis (4º ao {len(resultados)}º lugar)"):
                for pos, item in enumerate(restante, start=4):
                    mat_raw = mapa_materiais.get(item["id"], {})
                    temp_max = servico._obter_limite_temperatura(mat_raw)

                    col_a, col_b, col_c = st.columns([4.5, 1.3, 1.5], vertical_alignment="center")
                    with col_a:
                        st.markdown(f"**#{pos} {item['material']}** `{item['categoria']}`")
                    with col_b:
                        st.write(f"**{item['pontuacao']} pts**")
                    with col_c:
                        with st.popover("Detalhes", use_container_width=True):
                            for j in item["justificativas"]:
                                st.markdown(f"- ✅ {j}")
                            for lim in item["limitacoes"]:
                                st.markdown(f"- ⚠️ {lim}")

                    if modo_nerd:
                        renderizar_stats_for_nerds(item, mat_raw, temp_req, temp_max, latencia_ms)

                    st.divider()

# ------------------------------------------------------------------------------
# ABA 2: CATÁLOGO COMPLETO
# ------------------------------------------------------------------------------
with tab_cat:
    df_cat = obter_dataframe_catalogo()
    categorias_disponiveis = ["Todos"] + sorted(df_cat["Categoria"].unique().tolist())
    cat_filtro = st.pills("Filtrar por Categoria", options=categorias_disponiveis, default="Todos")

    if cat_filtro and cat_filtro != "Todos":
        df_exibir = df_cat[df_cat["Categoria"] == cat_filtro]
    else:
        df_exibir = df_cat

    st.dataframe(
        df_exibir,
        hide_index=True,
        use_container_width=True,
        height=480,
    )

# ------------------------------------------------------------------------------
# ABA 3: COMPARADOR GRÁFICO (PLOTLY LEVE)
# ------------------------------------------------------------------------------
with tab_graf:
    df_graf = obter_dataframe_catalogo().dropna(subset=["Tração / Escoamento (MPa)", "Densidade (g/cm³)"])

    st.subheader("Mapa de Ashby Simplificado: Resistência vs. Densidade")
    st.caption("Ideal para identificar materiais leves e resistentes (canto superior esquerdo).")

    fig = px.scatter(
        df_graf,
        x="Densidade (g/cm³)",
        y="Tração / Escoamento (MPa)",
        color="Categoria",
        text="ID",
        hover_name="Material",
        hover_data=["Tipo", "Temp. Máx. Serviço (°C)"],
        color_discrete_map={
            "Metal": "#0F62FE",
            "Polímero": "#198038",
            "Compósito": "#8A3FFC",
        },
    )
    fig.update_traces(textposition="top center", marker=dict(size=11, opacity=0.88))
    fig.update_layout(
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        height=500,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(showgrid=True, gridcolor="#EAECEF"),
        yaxis=dict(showgrid=True, gridcolor="#EAECEF"),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ------------------------------------------------------------------------------
# ABA 4: FICHA TÉCNICA INDIVIDUAL
# ------------------------------------------------------------------------------
with tab_ficha:
    nomes_materiais = [m["nome"] for m in servico.materiais]
    escolhido = st.selectbox("Selecione um material para consultar especificações completas:", nomes_materiais)

    mat_obj = next((m for m in servico.materiais if m["nome"] == escolhido), None)

    if mat_obj:
        with st.container(border=True):
            st.markdown(f"### {mat_obj['nome']}")
            st.caption(f"**Categoria:** {mat_obj.get('categoria', '-')} &nbsp;|&nbsp; **Classe:** {mat_obj.get('tipo', '-')}")

            col_esq, col_dir = st.columns(2, gap="large")

            with col_esq:
                st.markdown("#### Propriedades Técnicas")
                props = mat_obj.get("propriedades_tecnicas", {})
                if props:
                    tabela_props = [
                        {"Propriedade": k.replace("_", " ").capitalize(), "Valor": str(v)}
                        for k, v in props.items()
                    ]
                    st.dataframe(pd.DataFrame(tabela_props), hide_index=True, use_container_width=True)

            with col_dir:
                st.markdown("#### Aplicações Típicas")
                for app in mat_obj.get("aplicacoes_tipicas", []):
                    st.markdown(f"- {app}")

                st.markdown("#### Características Relevantes")
                for car in mat_obj.get("caracteristicas_relevantes", []):
                    st.markdown(f"- {car}")

                if mat_obj.get("limitacoes_cuidados"):
                    st.markdown("#### Limitações e Cuidados")
                    for lim in mat_obj["limitacoes_cuidados"]:
                        st.warning(lim)