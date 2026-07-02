import streamlit as st
import pandas as pd
import numpy as np
import json
from sklearn.ensemble import RandomForestRegressor
import statsmodels.api as sm
from statsmodels.sandbox.regression.predstd import wls_prediction_std
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io
import matplotlib.pyplot as plt

st.set_page_config(page_title="Plataforma AVM SaaS - Engenharia", page_icon="🏢", layout="wide")

# =====================================================================
# BASE DE DADOS COMPACTA PARA CÁLCULOS REGRESSIVOS RIGOROSOS
# =====================================================================
@st.cache_data
def carregar_base_casas_goiania():
    dados = [
        (450000, 6000, 75,  200, 1200, "CASA"), (480000, 6153, 78,  220, 1250, "CASA"), 
        (430000, 5972, 72,  200, 1150, "CASA"), (510000, 6375, 80,  250, 1300, "CASA"), 
        (460000, 6133, 75,  210, 1220, "CASA"), (390000, 5571, 70,  180, 950,  "CASA"),
        (750000, 8823, 85,  360, 3200, "CASA"), (820000, 8913, 92,  400, 3300, "CASA"), 
        (790000, 8777, 90,  380, 3100, "CASA"), (1200000, 12000, 100, 450, 4800, "CASA"), 
        (250000, 2500, 100, 200, 400,  "CASA")
    ]
    return pd.DataFrame(dados, columns=['valor_total_declarado', 'valor_unitario_m2', 'area_privativa', 'area_terreno', 'indice_fiscal', 'tipologia'])

# =====================================================================
# GERADOR DE GRÁFICO IMOBILIÁRIO (Matplotlib para PDF)
# =====================================================================
def gerar_grafico_mercado(df_saneado, area_alvo, valor_estimado_m2):
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.scatter(df_saneado['area_privativa'], df_saneado['valor_unitario_m2'], color='#2B6CB0', alpha=0.7, label='Amostras Homologadas')
    ax.scatter(area_alvo, valor_estimado_m2, color='#E53E3E', marker='*', s=150, label='Imóvel Avaliado')
    ax.set_title('Dispersão do Mercado (Área vs Preço m²)', fontsize=10, fontweight='bold', color='#1A365D')
    ax.set_xlabel('Área Construída Privativa (m²)', fontsize=8)
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
def gerar_laudo_cientifico_pdf(tenant, area, terreno, fiscal, valores, model_stats, status_jur, score_jur, num_amostras, grafico_buf):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=35, leftMargin=35, topMargin=35, bottomMargin=35)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('T1', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor("#1A365D"), spaceAfter=12)
    subtitle_style = ParagraphStyle('T2', parent=styles['Heading2'], fontSize=11, textColor=colors.HexColor("#2B6CB0"), spaceAfter=6)
    text_style = ParagraphStyle('T3', parent=styles['Normal'], fontSize=8.5, leading=12, spaceAfter=5)
    
    story.append(Paragraph("LAUDO TÉCNICO DE ENGENHARIA DE AVALIAÇÕES", title_style))
    story.append(Paragraph(f"<b>Instituição Solicitante:</b> {tenant} | <b>Normativa:</b> ABNT NBR 14653-2 e Resoluções CMN", text_style))
    story.append(Spacer(1, 10))
    
    # Seção 1: Dados do Imóvel
    story.append(Paragraph("1. Identificação da Garantia Alvo", subtitle_style))
    t1 = Table([
        ["Área Construída", f"{area} m²", "Área do Terreno", f"{terreno} m²"],
        ["Índice Fiscal", f"{fiscal:.2f}", "Tipologia Imóvel", "Casa Horizontal"]
    ], colWidths=)
    t1.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")), ('PADDING', (0,0), (-1,-1), 4)]))
    story.append(t1)
    story.append(Spacer(1, 10))
    
    # Seção 2: Resultados do AVM
    story.append(Paragraph("2. Avaliação Econômica e Intervalo de Predição (Confiança 95%)", subtitle_style))
    t2 = Table([
        ["Métrica de Cobertura do Risco", "Valor do m² Construído", "Valor Total Admissível"],
        ["Limite Inferior Admissível (LTV)", f"R$ {valores['v_min']/area:,.2f}", f"R$ {valores['v_min']:,.2f}"],
        ["Valor Médio Estimado de Mercado", f"R$ {valores['v_medio']/area:,.2f}", f"R$ {valores['v_medio']:,.2f}"],
        ["Limite Superior Admissível", f"R$ {valores['v_max']/area:,.2f}", f"R$ {valores['v_max']:,.2f}"]
    ], colWidths=)
    t2.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")), ('PADDING', (0,0), (-1,-1), 5), ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#EBF8FF"))]))
    story.append(t2)
    story.append(Spacer(1, 10))
    
    # Seção 3: Equação e Gráfico (Mágica Visual no PDF)
    story.append(Paragraph("3. Diagnóstico do Modelo de Inferência Estatística", subtitle_style))
    story.append(Paragraph(f"<b>Equação de Regressão Gerada:</b> {model_stats['equacao']}", text_style))
    story.append(Spacer(1, 5))
    
    # Insere o gráfico gerado dinamicamente
    story.append(Image(grafico_buf, width=320, height=160))
    story.append(Spacer(1, 10))
    
    # Seção 4: Enquadramento de Graus da NBR 14653-2
    story.append(Paragraph("4. Enquadramento de Graus de Rigor (ABNT NBR 14653-2)", subtitle_style))
    t_grau = Table([
        ["Critério Avaliado", "Métrica do Modelo", "Grau Enquadrado"],
        ["Quantidade Mínima de Amostras", f"{num_amostras} Imóveis", model_stats['grau_amostras']],
        ["Coeficiente de Determinação (R²)", f"{model_stats['r2']}", model_stats['grau_r2']],
        ["Amplitude do Intervalo (Precisão)", f"{model_stats['amplitude']}%", model_stats['grau_precisao']]
    ], colWidths=)
    t_grau.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4A5568")), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")), ('PADDING', (0,0), (-1,-1), 4)]))
    story.append(t_grau)
    story.append(Spacer(1, 10))
    
    # Seção 5: Compliance Jurídico
    story.append(Paragraph("5. Homologação da Esteira de Risco Legal", subtitle_style))
    t3 = Table([["Status Documental", "APROVADO PARA GARANTIA" if status_jur else "REPROVADO / BLOQUEADO"], ["Grau de Risco Matricial", score_jur]], colWidths=)
    t3.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")), ('PADDING', (0,0), (-1,-1), 5), ('TEXTCOLOR', (1,0), (1,0), colors.HexColor("#38A169") if status_jur else colors.HexColor("#E53E3E"))]))
    story.append(t3)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# =====================================================================
# INTERFACE DO STREAMLIT
# =====================================================================
st.title("🏢 Painel Avançado de Engenharia Imobiliária SaaS")
st.markdown("Cálculos científicos por Inferência Estatística em conformidade estrita com a NBR 14653-2.")
st.hr()

st.sidebar.header("🔑 Acesso Multi-Tenant")
tenant_selecionado = st.sidebar.selectbox("Cliente", ["001 - Banco Alfa S.A.", "002 - Imobiliária Local Ltda"])
plano_assinatura = "ENTERPRISE" if "Alfa" in tenant_selecionado else "STANDARD"

aba_avm, aba_juridico = st.tabs(["📊 1. Avaliação Normatizada", "📜 2. Análise Jurídica"])

if 'status_juridico_global' not in st.session_state:
    st.session_state.status_juridico_global = True
if 'score_juridico_global' not in st.session_state:
    st.session_state.score_juridico_global = "PENDENTE"

with aba_avm:
    st.subheader("Base de Dados de Casas (Goiânia)")
    arquivo_planilha = st.file_uploader("Suba a planilha com as colunas 'area_terreno' e 'indice_fiscal'", type=["xlsx", "csv"])
    df_mercado = carregar_base_casas_goiania() if arquivo_planilha is None else (pd.read_csv(arquivo_planilha) if arquivo_planilha.name.endswith('.csv') else pd.read_excel(arquivo_planilha))
    
    st.write("---")
    st.markdown("#### Atributos do Imóvel Avaliado")
    col1, col2 = st.columns(2)
    area_alvo = col1.number_input("Área Construída Privativa (m²)", min_value=10.0, value=75.0)
    area_terreno_alvo = col1.number_input("Área Total do Terreno (m²)", min_value=10.0, value=200.0)
    indice_fiscal_alvo = col2.number_input("Índice Fiscal da Quadra", min_value=0.0, value=1200.0)
    padrao = col2.selectbox("Padrão Construtivo", ["Baixo", "Normal", "Alto"], index=1)

    if st.button("🚀 Calcular Avaliação Científica NBR"):
        # Saneamento IQR
        q1 = df_mercado['valor_unitario_m2'].quantile(0.25)
        q3 = df_mercado['valor_unitario_m2'].quantile(0.75)
        iqr = q3 - q1
        df_saneado = df_mercado[(df_mercado['valor_unitario_m2'] >= q1 - 1.5*iqr) & (df_mercado['valor_unitario_m2'] <= q3 + 1.5*iqr)].copy()
        
        # Regressão Linear Múltipla Científica (Mínimos Quadrados)
        Y = df_saneado['valor_unitario_m2']
        X = df_saneado[['area_privativa', 'area_terreno', 'indice_fiscal']]
        X = sm.add_constant(X)
        modelo = sm.OLS(Y, X).fit()
        
        # Predição e Intervalos com 95% de Confiança (NBR 14653)
        vetor_alvo = [1, area_alvo, area_terreno_alvo, float(indice_fiscal_alvo)]
        prstd, iv_l, iv_u = wls_prediction_std(modelo, exog=[vetor_alvo], alpha=0.05)
        
        preco_m2 = float(modelo.predict([vetor_alvo]))
        v_estimado = preco_m2 * area_alvo
        v_min = float(iv_l) * area_alvo
        v_max = float(iv_u) * area_alvo
        
