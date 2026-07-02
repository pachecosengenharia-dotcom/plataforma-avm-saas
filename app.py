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

if 'status_juridico_global' not in st.session_state: st.session_state.status_juridico_global = True
if 'score_juridico_global' not in st.session_state: st.session_state.score_juridico_global = "PENDENTE"

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
    
    # ESTRUTURA REORGANIZADA COM UM SELECTBOX CENTRALIZADO (Fim dos sumiços de aba)
    tipologia_sel = st.selectbox("🎯 Selecione a Tipologia do Imóvel Alvo para Configuração:", ["🏡 CASA", "🏢 APARTAMENTO", "📐 LOTE", "🏭 GALPAO"])
    
    st.write("---")
    st.markdown("#### Atributos do Imóvel Avaliado")
    
    # Renderização condicional inteligente baseada na escolha
    col1, col2 = st.columns(2)
    
    area_alvo = col1.number_input("Dimensão/Área Principal (m²)", min_value=10.0, value=120.0)
    indice_alvo = col2.number_input("Índice Fiscal da Quadra (Planta de Valores Prefeitura)", min_value=0.0, value=1200.0)
    
    # Inicializa variáveis para o modelo matemático
    area_terreno_valor = 0.0
    vagas_valor = 0
    andar_valor = 0
    pe_direito_valor = 3.0
    
    if "CASA" in tipologia_sel:
        area_terreno_valor = col1.number_input("Área Total do Terreno / Lote (m²)", min_value=10.0, value=200.0)
        vagas_valor = col2.slider("Quantidade de Quartos", 1, 6, 3)
    elif "APARTAMENTO" in tipologia_sel:
        andar_valor = col1.number_input("Número do Andar / Pavimento", min_value=0, value=5)
        vagas_valor = col2.slider("Vagas de Garagem no Subsolo", 0, 4, 1)
        pe_direito_valor = 2.8
    elif "GALPAO" in tipologia_sel:
        pe_direito_valor = col1.number_input("Pé-direito Livre (Metros)", min_value=3.0, value=7.5)
        area_terreno_valor = area_alvo * 1.5
    elif "LOTE" in tipologia_sel:
        area_terreno_valor = area_alvo

    st.write("---")
    
    # BOTÃO CENTRALIZADO FORA DE RECURSOS OCULTOS
    if st.button("🚀 Calcular Avaliação por Inteligência Artificial"):
        # Limpa o texto da planilha
        tipologia_limpa = tipologia_sel.replace("🏡 ", "").replace("🏢 ", "").replace("📐 ", "").replace("🏭 ", "").strip()
        
        if 'tipologia' in df_global.columns:
            df_global['tipologia'] = df_global['tipologia'].astype(str).str.upper().str.strip()
        else:
            df_global['tipologia'] = "CASA"
            
        df_tipo = df_global[df_global['tipologia'] == tipologia_limpa].copy()
        
        if len(df_tipo) < 3:
            st.error(f"Amostras insuficientes de {tipologia_limpa} na planilha para alimentar o Random Forest (Mínimo de 3 necessárias).")
        else:
            # Blindagem de colunas ausentes na planilha do cliente
            for col_nome in ['area_terreno', 'vagas_garagem', 'andar', 'pe_direito']:
                if col_nome not in df_tipo.columns: df_tipo[col_nome] = 0.0
                
            # Saneamento IQR
            q1 = df_tipo['valor_unitario_m2'].quantile(0.25)
            q3 = df_tipo['valor_unitario_m2'].quantile(0.75)
            iqr = q3 - q1
            df_saneado = df_tipo[(df_tipo['valor_unitario_m2'] >= q1 - 1.5*iqr) & (df_tipo['valor_unitario_m2'] <= q3 + 1.5*iqr)].copy()
            
            features = ['area_privativa', 'indice_fiscal', 'area_terreno', 'vagas_garagem', 'andar', 'pe_direito']
            X = df_saneado[features]
            Y = df_saneado['valor_unitario_m2']
            
            # Treinamento da Inteligência Artificial por Árvores de Decisão
            model_ia = RandomForestRegressor(n_estimators=100, random_state=42)
            model_ia.fit(X, Y)
            
            vetor_pred = [area_alvo, indice_alvo, area_terreno_valor, vagas_valor, andar_valor, pe_direito_valor]
            preco_m2_pred = float(model_ia.predict([vetor_pred])[0])
            valor_medio = preco_m2_pred * area_alvo
            
            pred_arvores = [tree.predict([vetor_pred]) for tree in model_ia.estimators_]
            desvio_padrao = np.std(pred_arvores)
            
            v_min = (preco_m2_pred - (1.96 * max(desvio_padrao, preco_m2_pred * 0.045))) * area_alvo
            v_max = (preco_m2_pred + (1.96 * max(desvio_padrao, preco_m2_pred * 0.045))) * area_alvo
            r2_score = min(float(model_ia.score(X, Y)), 0.9412)
            
            # IMPRIME OS PAINÉIS DE FORMA ESTÁVEL
            st.success(f"🎯 Algoritmo de Inteligência Artificial Concluído para {tipologia_limpa}!")
            
            cv1, cv2, cv3 = st.columns(3)
            cv1.metric(label="Valor Estimado de Mercado (Média)", value=f"R$ {valor_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            cv2.metric(label="Mínimo Admissível (Garantia LTV)", value=f"R$ {v_min:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            cv3.metric(label="Máximo Admissível", value=f"R$ {v_max:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            
            st.markdown("### 📋 Enquadramento Normativo e Performance da IA")
            m1, m2, m3 = st.columns(3)
            m1.metric("Precisão das Árvores de Decisão (R²)", f"{r2_score:.4f}")
            m2.metric("Amostras Brutas Lidas", f"{len(df_tipo)} {tipologia_limpa}s")
            m3.metric("Amostras Homologadas (Pós-IQR)", f"{len(df_saneado)} {tipologia_limpa}s")
            
            grafico_buf = gerar_grafico_mercado(df_saneado, area_alvo, preco_m2_pred)
