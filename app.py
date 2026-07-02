import streamlit as st
import pandas as pd
import numpy as np
import json
from sklearn.ensemble import RandomForestRegressor
import io
import matplotlib.pyplot as plt

st.set_page_config(page_title="Plataforma AVM SaaS - Multi-Tipologia", page_icon="🏢", layout="wide")

# =====================================================================
# BASE DE DADOS COMPACTA PARA CÁLCULOS RIGOROSOS DE IA
# =====================================================================
@st.cache_data
def carregar_base_multitipologia_padrao():
    dados = [
        # CASAS (total, unitario, area_construida, indice_fiscal, area_terreno, vagas, andar, pe_direito, tipologia)
        (450000, 6000, 120, 1200, 200, 2, 0, 3.0, "CASA"),
        (480000, 6153, 125, 1250, 220, 2, 0, 3.0, "CASA"),
        (510000, 6375, 130, 1300, 250, 2, 0, 3.2, "CASA"),
        (750000, 8823, 185, 3200, 360, 3, 0, 3.5, "CASA"),
        (820000, 8913, 192, 3300, 400, 3, 0, 3.5, "CASA"),
        # APARTAMENTOS
        (350000, 5833, 60, 1500, 0, 1, 3, 2.7, "APARTAMENTO"),
        (380000, 6129, 62, 1600, 0, 1, 5, 2.7, "APARTAMENTO"),
        (420000, 6461, 65, 1800, 0, 2, 8, 2.8, "APARTAMENTO"),
        (650000, 8666, 75, 3400, 0, 2, 12, 2.9, "APARTAMENTO"),
        (720000, 9000, 80, 3600, 0, 2, 15, 3.0, "APARTAMENTO"),
        # LOTES / TERRENOS
        (150000, 428, 350, 800, 350, 0, 0, 0, "LOTE"),
        (165000, 458, 360, 850, 360, 0, 0, 0, "LOTE"),
        (210000, 525, 400, 1100, 400, 0, 0, 0, "LOTE"),
        (450000, 900, 500, 2800, 500, 0, 0, 0, "LOTE"),
        # GALPÕES COMERCIAIS
        (1200000, 2400, 500, 900, 800, 0, 0, 6.0, "GALPAO"),
        (1500000, 2500, 600, 950, 900, 0, 0, 7.0, "GALPAO"),
        (2100000, 2625, 800, 1100, 1200, 0, 0, 8.0, "GALPAO")
    ]
    df_res = pd.DataFrame(dados, columns=['valor_total_declarado', 'valor_unitario_m2', 'area_privativa', 'indice_fiscal', 'area_terreno', 'vagas_garagem', 'andar', 'pe_direito', 'tipologia'])
    return df_res

# =====================================================================
# GERADOR DE GRÁFICO IMOBILIÁRIO (Matplotlib)
# =====================================================================
def gerar_grafico_mercado(df_saneado, area_alvo, valor_estimado_m2):
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.scatter(df_saneado['area_privativa'], df_saneado['valor_unitario_m2'], color='#2B6CB0', alpha=0.7, label='Amostras Homologadas')
    ax.scatter(area_alvo, valor_estimado_m2, color='#E53E3E', marker='*', s=150, label='Imóvel Avaliado')
    ax.set_title('Dispersão do Mercado (Área vs Preço m²)', fontsize=10, fontweight='bold', color='#1A365D')
    ax.set_xlabel('Área (m²)', fontsize=8)
    ax.set_ylabel('Preço Unitário (R$/m²)', fontsize=8)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(fontsize=7, loc='best')
    plt.tight_layout()
    
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', dpi=200)
    img_buf.seek(0)
    plt.close(fig)
    return img_buf

# =====================================================================
# INTERFACE PRINCIPAL DO PAINEL SAAS
# =====================================================================
st.title("🏢 Painel Avançado de Engenharia Imobiliária SaaS")
st.markdown("Gestão automatizada de risco imobiliário por Inteligência Artificial (Random Forest).")
st.divider()

st.sidebar.header("🔑 Assinatura e Faturamento")
tenant_selecionado = st.sidebar.selectbox("Cliente Institucional", ["001 - Banco Alfa S.A.", "002 - Imobiliária Local Ltda"])
plano_assinatura = "ENTERPRISE" if "Alfa" in tenant_selecionado else "STANDARD"

st.sidebar.markdown(f"**Plano Contratado:** {'🟢 ENTERPRISE' if plano_assinatura == 'ENTERPRISE' else '🟡 STANDARD'}")

aba_avm, aba_juridico = st.tabs(["📊 1. Avaliação Estatística por IA (AVM)", "📜 2. Análise Jurídica"])

# Inicialização segura de todas as chaves de estado de memória na sessão
if 'status_juridico_global' not in st.session_state: st.session_state.status_juridico_global = True
if 'score_juridico_global' not in st.session_state: st.session_state.score_juridico_global = "PENDENTE"
if 'resultado_ia_guardado' not in st.session_state: st.session_state.resultado_ia_guardado = None

with aba_avm:
    st.subheader("Configuração da Base e Modelagem")
    arquivo_planilha = st.file_uploader("Arraste aqui a planilha consolidada de imóveis do banco (.xlsx ou .csv)", type=["xlsx", "csv"])
    
    if arquivo_planilha is not None:
        try:
            if arquivo_planilha.name.endswith('.csv'):
                df_global = pd.read_csv(arquivo_planilha)
            else:
                df_global = pd.read_excel(arquivo_planilha)
            st.success(f"🟩 Base do banco '{arquivo_planilha.name}' carregada com sucesso!")
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")
            df_global = carregar_base_multitipologia_padrao()
    else:
        st.info("💡 Modo de Demonstração: Utilizando a base de dados sintética de múltiplas tipologias.")
        df_global = carregar_base_multitipologia_padrao()

    st.write("---")
    st.markdown("#### 🎯 Selecione a Tipologia do Imóvel Alvo para o Teste de Cenário")
    
    sub_casa, sub_apto, sub_lote, sub_galpao = st.tabs(["🏡 Casas", "🏢 Apartamentos", "📐 Lotes / Terrenos", "🏭 Galpões Comerciais"])
    
    # Processador de clique centralizado
    tipologia_sel = "CASA"
    area_alvo = 120.0
    indice_alvo = 1200.0
    atributos = {"area_terreno": 200.0, "vagas_garagem": 2, "andar": 0, "pe_direito": 3.0}
    gatilho_disparado = False

    with sub_casa:
        st.markdown("##### Parâmetros para Imóveis Horizontais")
        c1, c2 = st.columns(2)
        area_casa = c1.number_input("Área Construída Privativa (m²)", min_value=10.0, value=120.0, key="c_a")
        terreno_casa = c1.number_input("Área Total do Terreno (m²)", min_value=10.0, value=200.0, key="c_t")
        indice_casa = c2.number_input("Índice Fiscal da Quadra (1 a 5000)", min_value=0.0, value=1200.0, key="c_i")
        quartos_casa = c2.slider("Quantidade de Quartos", 1, 6, 3, key="c_q")
        if st.button("🚀 Calcular AVM de Casa"):
            tipologia_sel = "CASA"
            area_alvo = area_casa
            indice_alvo = indice_casa
            atributos = {"area_terreno": terreno_casa, "vagas_garagem": quartos_casa, "andar": 0, "pe_direito": 3.0}
            gatilho_disparado = True

    with sub_apto:
        st.markdown("##### Parâmetros para Edificações Verticais")
        a1, a2 = st.columns(2)
        area_apto = a1.number_input("Área Privativa do Apartamento (m²)", min_value=10.0, value=75.0, key="ap_a")
        andar_apto = a1.number_input("Número do Andar / Pavimento", min_value=0, value=5, key="ap_an")
        vagas_apto = a2.slider("Vagas de Garagem no Subsolo", 0, 4, 1, key="ap_v")
        indice_apto = a2.number_input("Índice Fiscal da Quadra (1 a 5000)", min_value=0.0, value=2800.0, key="ap_i")
        if st.button("🚀 Calcular AVM de Apartamento"):
            tipologia_sel = "APARTAMENTO"
            area_alvo = area_apto
            indice_alvo = indice_apto
            atributos = {"area_terreno": 0, "vagas_garagem": vagas_apto, "andar": andar_apto, "pe_direito": 2.8}
            gatilho_disparado = True

    with sub_lote:
        st.markdown("##### Parâmetros para Solos Nus / Lotes")
        l1, l2 = st.columns(2)
        area_lote = l1.number_input("Área Total do Lote (m²)", min_value=10.0, value=450.0, key="lo_a")
        indice_lote = l2.number_input("Índice Fiscal do Zoneamento (1 a 5000)", min_value=0.0, value=900.0, key="lo_i")
        if st.button("🚀 Calcular AVM de Lote"):
            tipologia_sel = "LOTE"
            area_alvo = area_lote
            indice_alvo = indice_lote
            atributos = {"area_terreno": area_lote, "vagas_garagem": 0, "andar": 0, "pe_direito": 0}
            gatilho_disparado = True

    with sub_galpao:
        st.markdown("##### Parâmetros para Imóveis Logísticos / Industriais")
        g1, g2 = st.columns(2)
        area_galpao = g1.number_input("Área Útil do Galpão (m²)", min_value=50.0, value=600.0, key="ga_a")
        pe_galpao = g1.number_input("Pé-direito Livre (Metros)", min_value=3.0, value=7.5, key="ga_pe")
        indice_galpao = g2.number_input("Índice Fiscal Industrial (1 a 5000)", min_value=0.0, value=1100.0, key="ga_i")
        if st.button("🚀 Calcular AVM de Galpão"):
            tipologia_sel = "GALPAO"
            area_alvo = area_galpao
            indice_alvo = indice_galpao
            atributos = {"area_terreno": area_galpao * 1.5, "vagas_garagem": 0, "andar": 0, "pe_direito": pe_galpao}
            gatilho_disparado = True

    # EXECUÇÃO DO MOTOR MATEMÁTICO REAL
    if gatilho_disparado:
        # Padroniza nomes de texto vindos do Excel externo
        if 'tipologia' in df_global.columns:
            df_global['tipologia'] = df_global['tipologia'].astype(str).str.upper().str.strip()
        else:
            df_global['tipologia'] = "CASA"
            
        df_tipo = df_global[df_global['tipologia'] == tipologia_sel].copy()
        
        if len(df_tipo) < 3:
            st.error(f"Amostras insuficientes de {tipologia_sel} na planilha enviada.")
        else:
            # Blindagem contra falta de colunas secundárias
            for col_nome in ['area_terreno', 'vagas_garagem', 'andar', 'pe_direito']:
                if col_nome not in df_tipo.columns: df_tipo[col_nome] = 0.0
                
            q1 = df_tipo['valor_unitario_m2'].quantile(0.25)
            q3 = df_tipo['valor_unitario_m2'].quantile(0.75)
            iqr = q3 - q1
            df_saneado = df_tipo[(df_tipo['valor_unitario_m2'] >= q1 - 1.5*iqr) & (df_tipo['valor_unitario_m2'] <= q3 + 1.5*iqr)].copy()
            
            X = df_saneado[['area_privativa', 'indice_fiscal', 'area_terreno', 'vagas_garagem', 'andar', 'pe_direito']]
            Y = df_saneado['valor_unitario_m2']
            
            # Treinamento da IA por Árvores de Decisão
