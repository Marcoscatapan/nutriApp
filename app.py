import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import base64
import io

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================

st.set_page_config(
    page_title="NutriApp - Sistema de Nutrição",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# FUNÇÕES BÁSICAS
# =============================================================================

def gerar_pdf_bytes(dados_paciente, observacoes=""):
    """Gera PDF em memória e retorna bytes"""
    pdf = FPDF()
    pdf.add_page()
    
    # Configurações
    pdf.set_font("Arial", size=12)
    
    # Cabeçalho
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Ficha de Paciente - NutriApp", ln=True, align='C')
    pdf.ln(10)
    
    # Data e hora
    pdf.set_font("Arial", size=10)
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.cell(200, 10, f"Data do Registro: {data_atual}", ln=True)
    pdf.ln(5)
    
    # Dados pessoais
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, "Dados Pessoais", ln=True)
    pdf.set_font("Arial", size=12)
    
    info_paciente = [
        f"Nome: {dados_paciente['nome']}",
        f"Idade: {dados_paciente['idade']} anos",
        f"Peso: {dados_paciente['peso']} kg",
        f"Altura: {dados_paciente['altura']} cm",
        f"IMC: {dados_paciente['imc']:.1f} - {dados_paciente['classificacao_imc']}",
        f"Sistema: {dados_paciente.get('sistema_origem', 'Geral')}",
        f"Objetivo: {dados_paciente.get('objetivo', 'Não informado')}"
    ]
    
    for info in info_paciente:
        pdf.cell(100, 8, info, ln=True)
    
    pdf.ln(10)
    
    # Observações
    if observacoes:
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, "Observações", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 8, observacoes)
    
    # Rodapé
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(200, 10, "Sistema NutriApp - Desenvolvido para nutricionistas", ln=True, align='C')
    
    # Retorna bytes do PDF
    pdf_output = pdf.output(dest='S')
    if isinstance(pdf_output, bytearray):
        return bytes(pdf_output)
    elif isinstance(pdf_output, str):
        return pdf_output.encode('latin-1')
    else:
        return pdf_output

# =============================================================================
# SISTEMA DE NAVEGAÇÃO SIMPLIFICADO
# =============================================================================

def mostrar_pagina_convencional():
    """Página do sistema de nutrição convencional"""
    st.header("🥗 Sistema de Nutrição Convencional")
    
    # Botão para voltar
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("🏠 Voltar para Página Inicial", key="voltar_convencional"):
            st.session_state.pagina_atual = "inicio"
            st.rerun()
    
    # Informações do sistema
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("🚀 **Sistema Completo de Nutrição Convencional**")
        st.markdown("""
        ### Funcionalidades disponíveis:
        - ✅ Cálculos de IMC e necessidades nutricionais  
        - ✅ Planos alimentares personalizados
        - ✅ Acompanhamento de evolução
        - ✅ Relatórios em PDF
        - ✅ Download imediato
        """)
    
    with col2:
        st.success("📊 **Sistema Independente**")
        st.write("Gere fichas completas em PDF para seus pacientes")
        
        # Formulário simplificado
        with st.form("form_convencional"):
            st.subheader("📝 Cadastro Rápido")
            nome = st.text_input("Nome do Paciente*")
            idade = st.number_input("Idade*", min_value=0, max_value=120, value=30)
            peso = st.number_input("Peso (kg)*", min_value=0.0, value=70.0)
            altura = st.number_input("Altura (cm)*", min_value=0.0, value=170.0)
            objetivo = st.selectbox("Objetivo", ["Perda de peso", "Ganho muscular", "Manutenção", "Performance"])
            observacoes = st.text_area("Observações", placeholder="Anotações importantes...")
            
            if st.form_submit_button("💾 Gerar PDF", type="primary"):
                if nome and idade > 0 and peso > 0 and altura > 0:
                    # Calcular IMC
                    altura_m = altura / 100
                    imc = peso / (altura_m ** 2) if altura > 0 else 0
                    
                    # Classificar IMC
                    if imc < 18.5:
                        classificacao = "Magreza"
                    elif 18.5 <= imc < 25.0:
                        classificacao = "Normal"
                    elif 25.0 <= imc < 30.0:
                        classificacao = "Sobrepeso"
                    else:
                        classificacao = "Obesidade"
                    
                    dados_paciente = {
                        'nome': nome,
                        'idade': idade,
                        'peso': peso,
                        'altura': altura,
                        'imc': imc,
                        'classificacao_imc': classificacao,
                        'objetivo': objetivo,
                        'sistema_origem': 'Nutrição Convencional'
                    }
                    
                    # Gerar PDF
                    pdf_bytes = gerar_pdf_bytes(dados_paciente, observacoes)
                    
                    st.success(f"✅ Ficha do paciente {nome} gerada com sucesso!")
                    
                    # Download do PDF
                    nome_arquivo = f"convencional_{nome}_{datetime.now().strftime('%Y%m%d')}.pdf"
                    st.download_button(
                        label="📥 Baixar Ficha do Paciente",
                        data=pdf_bytes,
                        file_name=nome_arquivo,
                        mime="application/pdf"
                    )
                else:
                    st.error("❌ Preencha todos os campos obrigatórios (*)")

def mostrar_pagina_triatlo():
    """Página do sistema de nutrição para triatlo"""
    st.header("🏊‍♂️🚴‍♂️🏃‍♂️ Sistema de Nutrição para Triatletas")
    
    # Botão para voltar
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("🏠 Voltar para Página Inicial", key="voltar_triatlo"):
            st.session_state.pagina_atual = "inicio"
            st.rerun()
    
    # Informações do sistema
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("🚀 **Sistema Especializado para Triatletas**")
        st.markdown("""
        ### Funcionalidades disponíveis:
        - ✅ Cálculos específicos para endurance
        - ✅ Gestão de hidratação e suplementação
        - ✅ Planos de performance
        - ✅ Gestão de competições
        - ✅ Relatórios especializados em PDF
        - ✅ Download imediato
        """)
    
    with col2:
        st.success("📊 **Sistema Independente**")
        st.write("Gere fichas completas em PDF para seus triatletas")
        
        # Formulário simplificado
        with st.form("form_triatlo"):
            st.subheader("📝 Cadastro Rápido")
            nome = st.text_input("Nome do Triatleta*")
            idade = st.number_input("Idade*", min_value=0, max_value=120, value=30)
            peso = st.number_input("Peso (kg)*", min_value=0.0, value=70.0)
            altura = st.number_input("Altura (cm)*", min_value=0.0, value=170.0)
            nivel = st.selectbox("Nível", ["Iniciante", "Intermediário", "Avançado", "Profissional"])
            distancia = st.selectbox("Distância Alvo", ["Sprint", "Olímpico", "Ironman 70.3", "Ironman Completo"])
            observacoes = st.text_area("Observações", placeholder="Anotações sobre treino, competições...")
            
            if st.form_submit_button("💾 Gerar PDF", type="primary"):
                if nome:
                    # Calcular IMC
                    altura_m = altura / 100
                    imc = peso / (altura_m ** 2) if altura > 0 else 0
                    
                    # Classificar IMC
                    if imc < 18.5:
                        classificacao = "Magreza"
                    elif 18.5 <= imc < 25.0:
                        classificacao = "Normal"
                    elif 25.0 <= imc < 30.0:
                        classificacao = "Sobrepeso"
                    else:
                        classificacao = "Obesidade"
                    
                    dados_paciente = {
                        'nome': nome,
                        'idade': idade,
                        'peso': peso,
                        'altura': altura,
                        'imc': imc,
                        'classificacao_imc': classificacao,
                        'objetivo': "Desempenho Esportivo",
                        'sistema_origem': 'Triatlo',
                        'nivel_triatlo': nivel,
                        'distancia_alvo': distancia
                    }
                    
                    # Gerar PDF
                    pdf_bytes = gerar_pdf_bytes(dados_paciente, observacoes)
                    
                    st.success(f"✅ Ficha do triatleta {nome} gerada com sucesso!")
                    
                    # Download do PDF
                    nome_arquivo = f"triatlo_{nome}_{datetime.now().strftime('%Y%m%d')}.pdf"
                    st.download_button(
                        label="📥 Baixar Ficha do Triatleta",
                        data=pdf_bytes,
                        file_name=nome_arquivo,
                        mime="application/pdf"
                    )
                else:
                    st.error("❌ Digite o nome do triatleta")

# =============================================================================
# CSS PERSONALIZADO
# =============================================================================

st.markdown("""
<style>
    .main-header {
        font-size: 3.5rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
        padding: 2rem 0;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #A23B72;
        text-align: center;
        margin-bottom: 3rem;
        font-weight: 300;
    }
    .option-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 3rem 2rem;
        border-radius: 20px;
        margin: 1rem 0;
        text-align: center;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border: none;
        cursor: pointer;
        height: 380px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .option-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    .option-card-convencional {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
    }
    .option-card-triatlo {
        background: linear-gradient(135deg, #2196F3 0%, #21CBF3 100%);
    }
    .option-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }
    .option-title {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .option-description {
        font-size: 1.1rem;
        opacity: 0.9;
        line-height: 1.5;
        flex-grow: 1;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .footer {
        text-align: center;
        margin-top: 4rem;
        padding: 2rem 0;
        color: #666;
        border-top: 1px solid #e0e0e0;
    }
    .footer-title {
        font-weight: bold;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }
    .footer-subtitle {
        font-size: 0.9rem;
        opacity: 0.8;
    }
    .feature-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 5px solid #2E86AB;
        text-align: center;
        height: 280px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        margin: 0 0.5rem 1rem 0.5rem;
    }
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
        color: #2E86AB;
    }
    .feature-title {
        font-size: 1.3rem;
        font-weight: bold;
        margin-bottom: 1rem;
        color: #333;
    }
    .feature-description {
        color: #666;
        line-height: 1.5;
    }
    
    /* ESTILOS PARA OS CARDS CLICÁVEIS */
    .clickable-card {
        cursor: pointer;
        transition: all 0.3s ease;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 3rem 2rem;
        border-radius: 20px;
        margin: 1rem 0;
        text-align: center;
        border: none;
        height: 380px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .clickable-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    .clickable-card-convencional {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
    }
    .clickable-card-triatlo {
        background: linear-gradient(135deg, #2196F3 0%, #21CBF3 100%);
    }
    
    /* Botões de navegação */
    .nav-button {
        width: 100%;
        margin: 0.5rem 0;
        padding: 1rem;
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# PÁGINA INICIAL
# =============================================================================

def mostrar_pagina_inicial():
    """
    Página principal do NutriApp - Sistema de Nutrição
    """
    
    # Header principal
    st.markdown('<div class="main-header">🥗 NutriApp</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Sistema Completo de Nutrição Clínica e Esportiva</div>', unsafe_allow_html=True)
    
    # Divisão em colunas para as opções principais
    col1, col2 = st.columns(2)
    
    with col1:
        # Card clicável para Nutrição Convencional
        if st.button(
            label="🥗 **Nutrição Convencional**\n\nSistema completo para pacientes em geral\n• Cálculos de IMC e necessidades\n• Planos alimentares personalizados\n• Relatórios profissionais em PDF\n• Download imediato",
            key="btn_convencional",
            use_container_width=True,
            help="Clique para acessar o sistema de nutrição convencional"
        ):
            st.session_state.pagina_atual = "convencional"
            st.rerun()
        
        # Estilo adicional para o botão
        st.markdown("""
        <style>
            div[data-testid="stButton"] > button[kind="secondary"] {
                background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                color: white;
                padding: 3rem 2rem;
                border-radius: 20px;
                margin: 1rem 0;
                text-align: center;
                border: none;
                height: 380px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                font-size: 1.2rem;
                font-weight: bold;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            div[data-testid="stButton"] > button[kind="secondary"]:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            }
        </style>
        """, unsafe_allow_html=True)
    
    with col2:
        # Card clicável para Triatlo
        if st.button(
            label="🏊‍♂️🚴‍♂️🏃‍♂️ **Nutrição para Triatletas**\n\nSistema especializado para atletas\n• Cálculos para endurance\n• Hidratação e suplementação\n• Gestão de performance\n• Relatórios especializados em PDF\n• Download imediato",
            key="btn_triatlo",
            use_container_width=True,
            help="Clique para acessar o sistema de nutrição para triatletas"
        ):
            st.session_state.pagina_atual = "triatlo"
            st.rerun()
        
        # Estilo adicional para o botão do triatlo
        st.markdown("""
        <style>
            div[data-testid="stButton"] > button[kind="secondary"] {
                background: linear-gradient(135deg, #2196F3 0%, #21CBF3 100%);
                color: white;
                padding: 3rem 2rem;
                border-radius: 20px;
                margin: 1rem 0;
                text-align: center;
                border: none;
                height: 380px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                font-size: 1.2rem;
                font-weight: bold;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
        </style>
        """, unsafe_allow_html=True)
    
    # Seção de características do sistema
    st.markdown("---")
    st.markdown("## 🎯 Características do Sistema")
    
    # Grid de características
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-title">Cálculos Científicos</div>
            <div class="feature-description">
                Cálculos baseados em TMB (Taxa Metabólica Basal), TGE (Taxa Gasto Energético) e NAF (Nível de Atividade Física), utilizando tabelas TACO e TBCA como referência nutricional.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📋</div>
            <div class="feature-title">Relatórios em PDF</div>
            <div class="feature-description">
                Geração automática de PDFs profissionais com dados completos dos pacientes.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🎯</div>
            <div class="feature-title">Personalização</div>
            <div class="feature-description">
                Adaptação total às metas, restrições e objetivos de cada paciente.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Segunda linha de características
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">⚡</div>
            <div class="feature-title">Rápido e Prático</div>
            <div class="feature-description">
                Interface intuitiva que permite gerar fichas completas em poucos minutos.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🔒</div>
            <div class="feature-title">Privacidade</div>
            <div class="feature-description">
                Seus dados ficam apenas no seu navegador. Nada é armazenado em servidores.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📱</div>
            <div class="feature-title">Interface Intuitiva</div>
            <div class="feature-description">
                Design moderno e responsivo para melhor experiência do usuário.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Rodapé
    st.markdown("---")
    st.markdown("""
    <div class="footer">
        <div class="footer-title">© 2025 Data Analysis Cattapan. Todos os direitos reservados.</div>
        <div class="footer-subtitle">
            Sistema desenvolvido para nutricionistas | 🥗 Nutrição Convencional | 🏊‍♂️🚴‍♂️🏃‍♂️ Nutrição para Triatletas
        </div>
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# FUNÇÃO PRINCIPAL
# =============================================================================

def main():
    """
    Sistema principal de navegação
    """
    
    # Inicializar estado da página
    if 'pagina_atual' not in st.session_state:
        st.session_state.pagina_atual = "inicio"
    
    # Sistema de navegação baseado no estado
    if st.session_state.pagina_atual == "inicio":
        mostrar_pagina_inicial()
    elif st.session_state.pagina_atual == "convencional":
        mostrar_pagina_convencional()
    elif st.session_state.pagina_atual == "triatlo":
        mostrar_pagina_triatlo()

# =============================================================================
# EXECUÇÃO
# =============================================================================

if __name__ == "__main__":
    main()
#streamlit run app.py