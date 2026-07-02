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

st.set_page_config(page_title="Plataforma AVM SaaS - Engenharia", page_icon="🏢", layout="wide")

# =====================================================================
# BASE DE DADOS COMPACTA PARA CÁLCULOS RIGOROSOS DE IA
# =====================================================================
@st.cache_data
def carregar_base_multitipologia_padrao():
    dados = [
        (450000, 6000, 120, 1200, 200, 2, 0, 3.0, "CASA"),
        (480000, 6153, 125, 1250, 220, 2, 0, 3.0, "CASA"),
        (510000, 6375, 130, 1300, 250, 2, 0, 3.2, "CASA"),
        (750000, 8823, 185, 3200, 360, 3, 0, 3.5, "CASA"),
        (820000, 8913, 192, 3300, 400, 3, 0, 3.5, "CASA"),
        (350000, 5833, 60, 1500, 0, 1, 3, 2.7, "APARTAMENTO"),
        (380000, 6129, 62, 1600, 0, 1, 5, 2.7, "APARTAMENTO"),
        (420000, 6461, 65, 1800, 0, 2, 8, 2.8, "APARTAMENTO"),
        (1200000, 2400, 500, 900, 800, 0, 0, 6.0, "GALPAO")
    ]
    return pd.DataFrame(dados, columns=['valor_total_declarado', 'valor_unitario_m2', 'area_privativa', 'indice_fiscal', 'area_terreno', 'vagas_garagem', 'andar', 'pe_direito', 'tipologia'])

# =====================================================================
# GERADOR DE GRÁFICO IMOBILIÁRIO (Matplotlib para PDF)
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
def gerar_laudo_cientifico_pdf(tenant, tipologia, area, valores, model_stats, status_jur, score_jur, num_amostras, grafico_buf):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=35, leftMargin=35, topMargin=35, bottomMargin=35)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('T1', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor("#1A365D"), spaceAfter=12)
    subtitle_style = ParagraphStyle('T2', parent=styles['Heading2'], fontSize=11, textColor=colors.HexColor("#2B6CB0"), spaceAfter=6)
    text_style = ParagraphStyle('T3', parent=styles['Normal'], fontSize=8.5, leading=12, spaceAfter=5)
    
    story.append(Paragraph("LAUDO TÉCNICO DE ENGENHARIA DE AVALIAÇÕES POR IA", title_style))
    story.append(Paragraph(f"<b>Instituição Solicitante:</b> {tenant} | <b>Normativa:</b> ABNT NBR 14653-2", text_style))
    story.append(Spacer(1, 10))
    
    # Seção 1: Dados do Imóvel
    story.append(Paragraph("1. Identificação da Garantia Alvo", subtitle_style))
    t1 = Table([["Tipologia do Bem", tipologia, "Dimensão Privativa", f"{area} m²"]], colWidths=[130, 130, 130, 130])
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
    ], colWidths=[200, 160, 160])
    t2.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")), ('PADDING', (0,0), (-1,-1), 5), ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#EBF8FF"))]))
    story.append(t2)
    story.append(Spacer(1, 10))
    
    # Seção 3: Equação e Gráfico
    story.append(Paragraph("3. Diagnóstico e Comportamento de Mercado", subtitle_style))
    story.append(Paragraph(f"<b>Equação de Tendência Estimada pelas Árvores:</b> {model_stats['equacao']}", text_style))
    story.append(Spacer(1, 5))
    story.append(Image(grafico_buf, width=320, height=160))
    story.append(Spacer(1, 10))
    
    # Seção 4: Enquadramento de Graus
    story.append(Paragraph("4. Enquadramento de Graus de Rigor (ABNT NBR 14653-2)", subtitle_style))
    t_grau = Table([
        ["Critério Avaliado", "Métrica do Modelo", "Grau Enquadrado"],
        ["Quantidade Mínima de Amostras", f"{num_amostras} Imóveis", model_stats['grau_amostras']],
        ["Coeficiente de Determinação (R²)", f"{model_stats['r2']}", model_stats['grau_r2']],
        ["Amplitude do Intervalo (Precisão)", f"{model_stats['amplitude']}%", model_stats['grau_precisao']]
    ], colWidths=[200, 160, 160])
    t_grau.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4A5568")), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")), ('PADDING', (0,0), (-1,-1), 4)]))
    story.append(t_grau)
    story.append(Spacer(1, 10))
    
    # Seção 5: Compliance Jurídico
    story.append(Paragraph("5. Homologação da Esteira de Risco Legal", subtitle_style))
    t3 = Table([["Status Documental", "APROVADO PARA GARANTIA" if status_jur else "REPROVADO / BLOQUEADO"], ["Grau de Risco Matricial", score_jur]], colWidths=[200, 320])
    t3.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")), ('PADDING', (0,0), (-1,-1), 5), ('TEXTCOLOR', (1,0), (1,0), colors.HexColor("#38A169") if status_jur else colors.HexColor("#E53E3E"))]))
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
plano_assinatura = "ENTERPRISE" if "Alfa" in tenant_selecionado else "STANDARD"

st.sidebar.markdown(f"**Plano Contratado:** {'🟢 ENTERPRISE' if plano_assinatura == 'ENTERPRISE' else '🟡 STANDARD'}")

aba_avm, aba_juridico = st.tabs(["📊 1. Avaliação Estatística por IA (AVM)", "📜 2. Análise Jurídica"])

if 'status_juridico_global' not in st.session_state: st.session_state.status_juridico_global = True
if 'score_juridico_global' not in st.session_state: st.session_state.score_juridico_global = "PENDENTE"

with aba_avm:
    st.subheader("Configuração da Base e Modelagem")
    arquivo_planilha = st.file_uploader("Arraste aqui a planilha consolidada de imóveis do banco (.xlsx ou .csv)", type=["xlsx", "csv"])
    df_global = carregar_base_multitipologia_padrao() if arquivo_planilha is None else (pd.read_csv(arquivo_planilha) if arquivo_planilha.name.endswith('.csv') else pd.read_excel(arquivo_planilha))
    
    st.write("---")
    tipologia_sel = st.selectbox("🎯 Selecione a Tipologia do Imóvel Alvo:", ["🏡 CASA", "🏢 APARTAMENTO", "📐 LOTE", "🏭 GALPAO"])
    
    st.write("---")
    st.markdown("#### Atributos do Imóvel Avaliado")
    col1, col2 = st.columns(2)
    area_alvo = col1.number_input("Dimensão/Área Principal (m²)", min_value=10.0, value=120.0)
    indice_alvo = col2.number_input("Índice Fiscal da Quadra", min_value=0.0, value=1200.0)
    
    area_terreno_valor, vagas_valor, andar_valor, pe_direito_valor = 0.0, 0, 0, 3.0
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

    st.write("---")
    if st.button("🚀 Calcular Avaliação por Inteligência Artificial"):
        tipologia_limpa = tipologia_sel.replace("🏡 ", "").replace("🏢 ", "").replace("📐 ", "").replace("🏭 ", "").strip()
        
        if 'tipologia' in df_global.columns:
            df_global['tipologia'] = df_global['tipologia'].astype(str).str.upper().str.strip()
        else:
