import streamlit as st
import pandas as pd
import json
import statsmodels.api as sm
from statsmodels.sandbox.regression.predstd import wls_prediction_std
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

st.set_page_config(page_title="Plataforma AVM SaaS - Casas", page_icon="🏢", layout="wide")

@st.cache_data
def base_dados_padrao():
    # Base padrão de casas simulada com Índice Fiscal
    # Colunas: total, unitario, area_construida, quartos, padrao, area_terreno, indice_fiscal
    dados = [
        (450000, 6000, 75,  2, 2, 200, 1), (480000, 6153, 78,  2, 2, 220, 1), (430000, 5972, 72,  2, 2, 200, 1),
        (510000, 6375, 80,  2, 2, 250, 1), (460000, 6133, 75,  2, 2, 210, 1), (390000, 5571, 70,  2, 2, 180, 2),
        (750000, 8823, 85,  3, 3, 360, 2), (820000, 8913, 92,  3, 3, 400, 2), (790000, 8777, 90,  3, 3, 380, 2),
        (1200000, 12000, 100, 3, 3, 450, 3), (250000, 2500, 100, 2, 1, 200, 4)
    ]
    return pd.DataFrame(dados, columns=['valor_total_declarado', 'valor_unitario_m2', 'area_privativa', 'qtd_quartos', 'padrao_construtivo_id', 'area_terreno', 'indice_fiscal'])

def gerar_laudo_pdf(tenant, area, quartos, padrao, terreno, indice_fiscal, v_estimado, v_min, v_max, r2, n_amostras, status_juridico, score_juridico):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('T1', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor("#1A365D"), spaceAfter=15)
    subtitle_style = ParagraphStyle('T2', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor("#2B6CB0"), spaceAfter=8)
    text_style = ParagraphStyle('T3', parent=styles['Normal'], fontSize=9, leading=13, spaceAfter=6)
    
    story.append(Paragraph("LAUDO TÉCNICO E LEGAL DE GARANTIA IMOBILIÁRIA (AVM - CASAS)", title_style))
    story.append(Paragraph(f"<b>Instituição Solicitante:</b> {tenant}", text_style))
    story.append(Paragraph("<b>Normativos:</b> Resoluções CMN nº 4.676/2018 e nº 4.925/2021 (Bacen) | ABNT NBR 14653-2", text_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("1. Dados do Imóvel Horizontal Solicitado", subtitle_style))
    dados_imovel = [
        ["Área Construída", f"{area} m²", "Quantidade de Quartos", f"{quartos}"],
        ["Área do Terreno", f"{terreno} m²", "Índice Fiscal (Zonamento)", f"Zona {indice_fiscal}"],
        ["Padrão Construtivo", f"{padrao}", "Tipologia do Bem", "Casa / Imóvel Horizontal"]
    ]
    t1 = Table(dados_imovel, colWidths=[130, 130, 130, 130])
    t1.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")), ('PADDING', (0,0), (-1,-1), 4)]))
    story.append(t1)
    
    story.append(Paragraph("2. Avaliação Estatística e Intervalos de Confiança (95%)", subtitle_style))
    t2 = Table([
        ["Métrica de Garantia", "Valor Total Admissível"],
        ["Limite Mínimo Admissível (Margem LTV)", f"R$ {v_min:,.2f}"],
        ["Valor Médio Estimado de Mercado", f"R$ {v_estimado:,.2f}"],
        ["Limite Máximo Admissível", f"R$ {v_max:,.2f}"]
    ], colWidths=[260, 260])
    t2.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")), ('PADDING', (0,0), (-1,-1), 5)]))
    story.append(t2)
    
    story.append(Paragraph("3. Status da Esteira de Risco Jurídico", subtitle_style))
    t3 = Table([
        ["Validação Cadastral", "APROVADO" if status_juridico else "REPROVADO / BLOQUEADO"],
        ["Classificação de Risco Legal", score_juridico]
    ], colWidths=[260, 260])
    t3.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")), ('PADDING', (0,0), (-1,-1), 5), ('TEXTCOLOR', (1,0), (1,0), colors.HexColor("#38A169") if status_juridico else colors.HexColor("#E53E3E"))]))
    story.append(t3)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

st.title("🏢 Painel de Crédito e Controle Multi-Tenant - Módulo Casas")
st.markdown("Gestão de risco imobiliário horizontal e barramento de faturamento SaaS por assinatura.")
st.divider()

st.sidebar.header("🔑 Assinatura e Faturamento")
tenant_selecionado = st.sidebar.selectbox("Cliente Institucional", ["001 - Banco Alfa S.A.", "002 - Imobiliária Local Ltda"])

if "Alfa" in tenant_selecionado:
    plano_assinatura = "ENTERPRISE"
    limite_consultas = "Ilimitado"
    cor_plano = "🟢"
else:
    plano_assinatura = "STANDARD (Apenas AVM)"
    limite_consultas = "Restam 4 consultas no mês"
    cor_plano = "🟡"

st.sidebar.markdown(f"**Plano Contratado:** {cor_plano} {plano_assinatura}")
st.sidebar.markdown(f"**Limitação de Uso:** {limite_consultas}")

aba_avm, aba_juridico = st.tabs(["📊 1. Avaliação Estatística (AVM)", "📜 2. Análise Jurídica da Matrícula"])

if 'status_juridico_global' not in st.session_state:
    st.session_state.status_juridico_global = True
if 'score_juridico_global' not in st.session_state:
    st.session_state.score_juridico_global = "PENDENTE"

with aba_avm:
    st.subheader("Simulador de Garantia Imobiliária para Imóveis Horizontais")
    st.markdown("### 💾 Upload da Base de Dados de Casas")
    arquivo_planilha = st.file_uploader("Arraste e solte aqui a planilha de mercado de casas contendo as colunas 'area_terreno' e 'indice_fiscal'.", type=["xlsx", "csv"])
    
    if arquivo_planilha is not None:
        try:
            if arquivo_planilha.name.endswith('.csv'):
                df_mercado = pd.read_csv(arquivo_planilha)
            else:
                df_mercado = pd.read_excel(arquivo_planilha)
            st.success(f"🟩 Planilha de casas '{arquivo_planilha.name}' carregada com sucesso!")
        except Exception as e:
            st.error(f"Erro ao ler o arquivo: {e}")
            df_mercado = base_dados_padrao()
    else:
        st.info("💡 Modo de Demonstração: Utilizando a base padrão de casas embutida.")
        df_mercado = base_dados_padrao()
        
    st.write("---")
    st.markdown("#### Características da Casa Alvo")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        area_alvo = st.number_input("Área Construída Privativa (m²)", min_value=10.0, max_value=1000.0, value=75.0, step=1.0)
        area_terreno_alvo = st.number_input("Área Total do Terreno (m²)", min_value=50.0, max_value=5000.0, value=200.0, step=10.0)
    with col2:
        quartos = st.slider("Quantidade de Quartos", 1, 6, 2)
        # RECURSO DE IMPACTO: Campo numérico de entrada direta do Índice Fiscal exigido por Goiânia
        indice_fiscal_alvo = st.number_input("Índice Fiscal da Prefeitura (Zona 1 a 4)", min_value=1, max_value=4, value=1, step=1)
    with col3:
        padrao = st.selectbox("Padrão Construtivo da Casa", ["Baixo (ID: 1)", "Normal (ID: 2)", "Alto (ID: 3)"], index=1)

    if st.button("🚀 Calcular Avaliação da Casa"):
        q1 = df_mercado['valor_unitario_m2'].quantile(0.25)
        q3 = df_mercado['valor_unitario_m2'].quantile(0.75)
        iqr = q3 - q1
        df_saneado = df_mercado[(df_mercado['valor_unitario_m2'] >= q1 - 1.5*iqr) & (df_mercado['valor_unitario_m2'] <= q3 + 1.5*iqr)]
        
        Y = df_saneado['valor_unitario_m2']
        # ENTRADA DE VARIÁVEL COMPLIANCE: O modelo agora processa o 'indice_fiscal' de Goiânia como vetor contínuo
        X = df_saneado[['area_privativa', 'area_terreno', 'indice_fiscal']]
        X = sm.add_constant(X)
        modelo = sm.OLS(Y, X).fit()
        
        vetor_alvo = [1, area_alvo, area_terreno_alvo, float(indice_fiscal_alvo)]
        prstd, iv_l, iv_u = wls_prediction_std(modelo, exog=[vetor_alvo], alpha=0.05)
        
        preco_m2_calc = float(modelo.predict([vetor_alvo]))
        valor_final_calc = preco_m2_calc * area_alvo
        v_min_calc = float(iv_l) * area_alvo
        v_max_calc = float(iv_u) * area_alvo
        r2_calc = f"{modelo.rsquared:.4f}"
        n_amostras_calc = len(df_saneado)
        
        st.success("🎯 Cálculos Realizados com Sucesso para o Mercado de Casas!")
        c_v1, c_v2, c_v3 = st.columns(3)
        c_v1.metric(label="Valor Estimado de Mercado", value=f"R$ {valor_final_calc:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        c_v2.metric(label="Mínimo Admissível (Margem LTV)", value=f"R$ {v_min_calc:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        c_v3.metric(label="Máximo Admissível", value=f"R$ {v_max_calc:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        st.markdown("### 📈 Indicadores de Governança do Modelo (NBR 14653)")
        m1, m2, m3 = st.columns(3)
        m1.metric("Precisão do Modelo (R²)", r2_calc)
        m2.metric("Amostras Brutas Lidas", f"{len(df_mercado)} casas")
        m3.metric("Amostras Homologadas (Pós-IQR)", f"{n_amostras_calc} casas")
        
        st.markdown("### 📥 Emissão de Relatório Certificado")
        pdf_data = gerar_laudo_pdf(
            tenant_selecionado, area_alvo, quartos, padrao, area_terreno_alvo, indice_fiscal_alvo,
            valor_final_calc, v_min_calc, v_max_calc,
            r2_calc, n_amostras_calc,
            status_juridico=st.session_state.status_juridico_global, 
            score_juridico=st.session_state.score_juridico_global
        )
        st.download_button(
            label="📄 Baixar Laudo de Avaliação Consolidado (PDF)",
            data=pdf_data,
            file_name="laudo_casas_oficial.pdf",
            mime="application/pdf"
        )

with aba_juridico:
    st.subheader("Esteira de Análise de Risco Documental")
    if "STANDARD" in plano_assinatura:
        st.error("🔒 Recurso Bloqueado para o Plano Atual")
