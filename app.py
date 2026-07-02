import streamlit as st
import pandas as pd
import numpy as np
import json
from sklearn.ensemble import RandomForestRegressor
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
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
# LAUDO CERTIFICADO COMPLETO (ABNT NBR 14653)
# =====================================================================
def gerar_laudo_pdf_ia(tenant, tipologia, area, valores, model_stats, status_juridico, score_juridico, grafico_buf):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('T1', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor("#1A365D"), spaceAfter=15)
    subtitle_style = ParagraphStyle('T2', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor("#2B6CB0"), spaceAfter=8)
    text_style = ParagraphStyle('T3', parent=styles['Normal'], fontSize=9, leading=13, spaceAfter=6)
    
    story.append(Paragraph(f"LAUDO TÉCNICO CORE AVM - INTELIGÊNCIA ARTIFICIAL ({tipologia})", title_style))
    story.append(Paragraph(f"<b>Instituição Solicitante:</b> {tenant}", text_style))
    story.append(Paragraph("<b>Metodologia Core:</b> Algoritmo de Árvores de Decisão (Random Forest) | NBR 14653", text_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("1. Escopo de Avaliação Imobiliária", subtitle_style))
    t1 = Table([["Tipologia do Bem", tipologia, "Dimensão Principal", f"{area} m²"]], colWidths=[130, 130, 130, 130])
    t1.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")), ('PADDING', (0,0), (-1,-1), 5)]))
    story.append(t1)
    
    story.append(Paragraph("2. Resultados do Motor de Machine Learning", subtitle_style))
    t2 = Table([
        ["Métrica de Cobertura do Risco", "Valor Comercial Admissível"],
        ["Margem Mínima de Segurança (Garantia)", f"R$ {valores['v_min']:,.2f}"],
        ["Valor de Face Estimado (Média)", f"R$ {valores['v_medio']:,.2f}"],
        ["Limite de Mercado Máximo", f"R$ {valores['v_max']:,.2f}"]
    ], colWidths=[260, 260])
    t2.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")), ('PADDING', (0,0), (-1,-1), 5)]))
    story.append(t2)
    story.append(Spacer(1, 5))
    story.append(Paragraph(f"<b>Métricas de Redes de Decisão:</b> Precisão de Ajuste R² = {model_stats['r2']} | Amostras Saneadas = {model_stats['saneadas']}.", text_style))
    
    story.append(Spacer(1, 5))
    story.append(Image(grafico_buf, width=320, height=160))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("3. Status da Esteira de Risco Jurídico", subtitle_style))
    t3 = Table([["Status Documental", "APROVADO PARA GARANTIA" if status_juridico else "REPROVADO"], ["Grau de Risco Legal", score_juridico]], colWidths=[260, 260])
    t3.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")), ('PADDING', (0,0), (-1,-1), 5), ('TEXTCOLOR', (1,0), (1,0), colors.HexColor("#38A169") if status_juridico else colors.HexColor("#E53E3E"))]))
    story.append(t3)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# =====================================================================
# INTERFACE PRINCIPAL DO PAINEL SAAS
# =====================================================================
st.title("🏢 Painel Avançado de Engenharia Imobiliária SaaS")
st.markdown("Gestão automatizada de risco imobiliário por Inteligência Artificial (Random Forest).")
st.divider()

st.sidebar.header("🔑 Assinatura e Faturamento")
tenant_selecionado = st.sidebar.selectbox("Cliente Institucional", ["001 - Banco Alfa S.A.", "002 - Imobiliária Local Ltda"])
st.sidebar.markdown("**Plano Contratado:** 🟢 ENTERPRISE (Acesso Total Liberado)")

aba_avm, aba_juridico = st.tabs(["📊 1. Avaliação Estatística por IA (AVM)", "📜 2. Análise Jurídica"])

if 'status_juridico_global' not in st.session_state: st.session_state.status_juridico_global = True
if 'score_juridico_global' not in st.session_state: st.session_state.score_juridico_global = "PENDENTE"
if 'memorizar_calculo' not in st.session_state: st.session_state.memorizar_calculo = None

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
    
    tipologia_sel = st.selectbox("🎯 Selecione a Tipologia do Imóvel Alvo para Configuração:", ["🏡 CASA", "🏢 APARTAMENTO", "📐 LOTE", "🏭 GALPAO"])
    
    st.write("---")
    st.markdown("#### Atributos do Imóvel Avaliado")
    
    col1, col2 = st.columns(2)
    area_alvo = col1.number_input("Dimensão/Área Principal (m²)", min_value=10.0, value=120.0)
    indice_alvo = col2.number_input("Índice Fiscal da Quadra (Planta de Valores Prefeitura)", min_value=0.0, value=1200.0)
    
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
    
    if st.button("🚀 Calcular Avaliação por Inteligência Artificial"):
        tipologia_limpa = tipologia_sel.replace("🏡 ", "").replace("🏢 ", "").replace("📐 ", "").replace("🏭 ", "").strip()
        df_local_processamento = df_global.copy()
        
        if 'tipologia' in df_local_processamento.columns:
