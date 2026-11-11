import streamlit as st
import pandas as pd
import json
import os
import re
import plotly.express as px
import plotly.graph_objects as go

from src.filtro_service import FiltroMaterialService

# 1. Configuração da Página
st.set_page_config(
    page_title="Seletor de Materiais Industriais",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Injeção de CSS Customizado (Visual Moderno e Alto Contraste)
st.markdown("""
    <style>
    /* Estilo dos Cards de Materiais */
    .material-card {
        background-color: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .material-card:hover {
        border-color: #4DA6FF;
        transform: translateY(-2px);
    }
    
    /* Badges de Categoria */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-left: 8px;
    }
    .badge-metal { background-color: #2E4057; color: #E0E6ED; border: 1px solid #4A6572; }
    .badge-polimero { background-color: #1B4965; color: #BEE9E8; border: 1px solid #62B6CB; }
    .badge-composito { background-color: #4A154B; color: #F1D302; border: 1px solid #9D4EDD; }

    /* Estilização das Métricas da Barra Superior */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700;
        color: #4DA6FF;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Leitura dos Dados do JSON
@st.cache_data
def carregar_json_materiais():
    base_dir = os.path.dirname(__file__)
    json_path = os.path.join(base_dir, 'data', 'materiais.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    return dados['materiais']

def extrair_valor_numerico(val):
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        numeros = [float(n) for n in re.findall(r"[-+]?\d*\.\d+|\d+", val.replace(',', '.'))]
        if numeros:
            return sum(numeros) / len(numeros)
    return None

def obter_badge_html(categoria):
    cat_lower = categoria.lower()
    if 'metal' in cat_lower:
        return f'<span class="badge badge-metal">🔩 {categoria}</span>'
    elif 'polímero' in cat_lower or 'polimero' in cat_lower:
        return f'<span class="badge badge-polimero">🧪 {categoria}</span>'
    elif 'compósito' in cat_lower or 'composito' in cat_lower:
        return f'<span class="badge badge-composito">💎 {categoria}</span>'
    return f'<span class="badge">{categoria}</span>'

lista_materiais = carregar_json_materiais()
filtro_service = FiltroMaterialService()

# 4. Barra Lateral (Filtros Acessíveis com Tooltips)
st.sidebar.header("⚙️ Parâmetros do Projeto")
st.sidebar.caption("Selecione as condições de trabalho para filtrar os materiais adequados:")

faixas_temperatura = {
    "-50 °C a -20 °C (Frio extremo / Criogênico)": -20,
    "-19 °C a 0 °C (Refrigeração / Baixa temp.)": 0,
    "0 °C a 50 °C (Ambiente / Processos padrão)": 50,
    "51 °C a 80 °C (Aquecimento moderado)": 80,
    "81 °C a 120 °C (Temperatura intermediária)": 120,
    "121 °C a 250 °C (Temperatura elevada)": 250,
    "251 °C a 400 °C (Alta temperatura / Térmico severo)": 400
}

opcao_temp = st.sidebar.selectbox(
    "Faixa de Temperatura de Operação:",
    options=list(faixas_temperatura.keys()),
    index=2,
    help="Define a temperatura máxima contínua suportada pelo material no processo."
)

temp_operacao = faixas_temperatura[opcao_temp]

aplicacao_busca = st.sidebar.text_input(
    "Aplicação Desejada (Palavra-chave):",
    placeholder="Ex: tubulação, engrenagem, bucha, eixos...",
    help="Filtra materiais com histórico de uso na aplicação informada."
)

contato_quimico = st.sidebar.checkbox(
    "Exige Alta Resistência Química",
    help="Marque se a peça trabalhará em contato direto com ácidos, bases, solventes ou névoa salina."
)

esforco_mecanico = st.sidebar.radio(
    "Nível de Esforço Mecânico:",
    options=["baixo", "moderado", "alto"],
    format_func=lambda x: {
        "baixo": "🟢 Baixo (Cargas leves / Sem exigência estrutural)",
        "moderado": "🟡 Moderado (Uso geral / Cargas normais)",
        "alto": "🔴 Alto (Cargas severas / Fadiga / Impacto)"
    }[x],
    help="Define a solicitação de carga e riscos de falha por impacto ou fadiga."
)

condicoes_usuario = {
    'temperatura_C': temp_operacao,
    'aplicacao': aplicacao_busca,
    'contato_quimico': contato_quimico,
    'esforco_mecanico': esforco_mecanico
}

# 5. Painel Principal
st.title("⚙️ Seletor de Materiais Industriais")
st.markdown("Plataforma de Engenharia para Seleção, Comparação e Auditoria Técnica de Materiais.")

# KPI Summary Bar
recomendacoes = filtro_service.selecionar(condicoes_usuario)
col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
col_kpi1.metric("Total no Catálogo", len(lista_materiais))
col_kpi2.metric("Materiais Compatíveis", len(recomendacoes))
if recomendacoes:
    col_kpi3.metric("Top Material Recomendado", recomendacoes[0]['material'])
else:
    col_kpi3.metric("Top Material Recomendado", "Nenhum")

st.divider()

# Abas Principais
tab_recomendador, tab_catalogo, tab_graficos, tab_ficha = st.tabs([
    "🎯 Recomendador Inteligente", 
    "📋 Catálogo Completo", 
    "📊 Comparador Gráfico", 
    "🔍 Ficha Técnica"
])

# --- ABA 1: RECOMENDADOR INTELIGENTE ---
with tab_recomendador:
    st.subheader("Resultados da Análise")
    
    if not recomendacoes:
        st.warning("⚠️ **Nenhum material atendeu integralmente a todos os critérios definidos.** Tente reduzir a temperatura exigida ou alterar o nível de esforço.")
    else:
        st.success(f"Encontrados **{len(recomendacoes)}** materiais apropriados para o perfil operacional.")
        
        for idx, rec in enumerate(recomendacoes, start=1):
            badge_html = obter_badge_html(rec['categoria'])
            
            # Card com HTML/CSS estilizado
            st.markdown(f"""
                <div class="material-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3 style="margin: 0; padding: 0;">#{idx} {rec['material']} {badge_html}</h3>
                        <span style="font-size: 1.2rem; font-weight: bold; color: #4DA6FF;">{rec['pontuacao']} pts</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            c_info, c_score = st.columns([7, 3])
            
            with c_info:
                st.markdown("**Justificativas de Seleção:**")
                for just in rec['justificativas']:
                    st.markdown(f"- ✅ {just}")
                    
                if rec.get('limitacoes'):
                    with st.expander("⚠️ Cuidados e Limitações do Material"):
                        for lim in rec['limitacoes']:
                            st.markdown(f"- {lim}")

                if rec.get('detalhamento'):
                    with st.expander("🔬 Ver Auditoria e Memória de Cálculo"):
                        st.table(rec['detalhamento'])
            
            with c_score:
                # Barra visual de indicador de pontuação (0 a 150 pts max)
                progresso = min(rec['pontuacao'] / 150.0, 1.0)
                st.caption("Aproveitamento do Score:")
                st.progress(progresso)
            
            st.markdown("<br>", unsafe_allow_html=True)

# --- ABA 2: CATÁLOGO COMPLETO ---
with tab_catalogo:
    st.subheader("Base de Dados Completa")
    
    dados_tabela = []
    for m in lista_materiais:
        prop = m.get("propriedades_tecnicas", {})
        tracao = prop.get("resistencia_tracao_MPa") or prop.get("limite_escoamento_MPa", "N/A")
        
        dados_tabela.append({
            "ID": m["id"],
            "Material": m["nome"],
            "Categoria": m["categoria"],
            "Tipo": m["tipo"],
            "Densidade (g/cm³)": prop.get("densidade_g_cm3", "N/A"),
            "Resistência (MPa)": tracao,
            "Módulo Young (GPa)": prop.get("modulo_elasticidade_GPa", "N/A")
        })
    
    df_catalogo = pd.DataFrame(dados_tabela)
    st.dataframe(
        df_catalogo,
        use_container_width=True,
        hide_index=True
    )

# --- ABA 3: COMPARADOR GRÁFICO ---
with tab_graficos:
    st.subheader("Análise Comparativa Métrica")
    
    nomes_materiais = [m["nome"] for m in lista_materiais]
    selecionados = st.multiselect(
        "Selecione materiais para comparar visualmente:",
        options=nomes_materiais,
        default=nomes_materiais[:5]
    )
    
    if selecionados:
        dados_grafico = []
        for m in lista_materiais:
            if m["nome"] in selecionados:
                prop = m.get("propriedades_tecnicas", {})
                dens = extrair_valor_numerico(prop.get("densidade_g_cm3"))
                trac = extrair_valor_numerico(prop.get("resistencia_tracao_MPa") or prop.get("limite_escoamento_MPa"))
                mod = extrair_valor_numerico(prop.get("modulo_elasticidade_GPa"))
                
                dados_grafico.append({
                    "Material": m["nome"],
                    "Categoria": m["categoria"],
                    "Densidade (g/cm³)": dens,
                    "Resistência Mecânica (MPa)": trac,
                    "Módulo Elasticidade (GPa)": mod
                })
        
        df_g = pd.DataFrame(dados_grafico)
        
        g_col1, g_col2 = st.columns(2)
        
        with g_col1:
            fig_trac = px.bar(
                df_g, x="Material", y="Resistência Mecânica (MPa)",
                color="Categoria", title="Resistência Mecânica (MPa)",
                text_auto=True, template="plotly_dark"
            )
            st.plotly_chart(fig_trac, use_container_width=True)
            
        with g_col2:
            fig_dens = px.bar(
                df_g, x="Material", y="Densidade (g/cm³)",
                color="Categoria", title="Densidade (g/cm³)",
                text_auto=True, template="plotly_dark"
            )
            st.plotly_chart(fig_dens, use_container_width=True)
    else:
        st.info("Selecione materiais acima para gerar os gráficos.")

# --- ABA 4: FICHA TÉCNICA DETALHADA ---
with tab_ficha:
    st.subheader("Ficha Técnica Individual")
    
    mat_selecionado = st.selectbox(
        "Escolha o material para visualizar:",
        options=[m["nome"] for m in lista_materiais]
    )
    
    mat_obj = next(m for m in lista_materiais if m["nome"] == mat_selecionado)
    
    st.markdown(f"## **{mat_obj['nome']}** {obter_badge_html(mat_obj['categoria'])}", unsafe_allow_html=True)
    st.markdown(f"**Tipo:** {mat_obj['tipo']}")
    
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        st.markdown("### 🧪 Propriedades Técnicas")
        for k, v in mat_obj.get("propriedades_tecnicas", {}).items():
            chave_formatada = k.replace("_", " ").title()
            st.markdown(f"- **{chave_formatada}:** {v}")
            
        st.markdown("### 🎯 Lógica do Programa")
        st.info(mat_obj.get("logica_selecao_programa", "Não informada."))

    with col_f2:
        st.markdown("### ⚙️ Aplicações Típicas")
        for app in mat_obj.get("aplicacoes_tipicas", []):
            st.markdown(f"- {app}")
            
        st.markdown("### ✨ Características Relevantes")
        for carac in mat_obj.get("caracteristicas_relevantes", []):
            st.markdown(f"- {carac}")

    if mat_obj.get("limitacoes_cuidados"):
        st.warning("### ⚠️ Limitações e Cuidados")
        for lim in mat_obj["limitacoes_cuidados"]:
            st.markdown(f"- {lim}")