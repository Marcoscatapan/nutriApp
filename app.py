import streamlit as st

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
# CSS PERSONALIZADO - CORRIGIDO
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
    
    /* CARDS PRINCIPAIS - MESMO TAMANHO */
    .main-card {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white;
        padding: 3rem 2rem;
        border-radius: 20px;
        margin: 1rem 0;
        text-align: center;
        height: 380px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        border: none;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .main-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    .main-card-triatlo {
        background: linear-gradient(135deg, #2196F3 0%, #21CBF3 100%);
    }
    .card-icon {
        font-size: 4rem;
        margin-bottom: 1.5rem;
    }
    .card-title {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .card-description {
        font-size: 1.1rem;
        opacity: 0.9;
        line-height: 1.5;
    }
    
    /* CARDS DE CARACTERÍSTICAS - ALINHADOS */
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
        justify-content: flex-start;
        margin: 0 0.5rem 1rem 0.5rem;
    }
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
        color: #2E86AB;
        height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .feature-title {
        font-size: 1.3rem;
        font-weight: bold;
        margin-bottom: 1rem;
        color: #333;
        height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .feature-description {
        color: #666;
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
    
    /* REMOVENDO O CSS QUE ESCONDE A SIDEBAR */
    /* Mantemos apenas o estilo personalizado sem interferir na funcionalidade */
</style>
""", unsafe_allow_html=True)



# =============================================================================
# PÁGINA INICIAL
# =============================================================================
def main():
    """
    Página principal do NutriApp - Sistema de Nutrição
    """
    
    # Header principal
    st.markdown('<div class="main-header">🥗 NutriApp</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Sistema Completo de Nutrição Clínica e Esportiva</div>', unsafe_allow_html=True)
    
    # Informação sobre navegação
    st.success("🎯 **Use o menu lateral para acessar os sistemas especializados**")
    
    # Divisão em colunas para as opções principais - CARDS NO MESMO TAMANHO
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="main-card">
            <div class="card-icon">🥗</div>
            <div class="card-title">Nutrição Convencional</div>
            <div class="card-description">
                Sistema completo para pacientes em geral<br>
                • Cálculos de IMC e necessidades<br>
                • Planos alimentares personalizados<br>
                • Relatórios profissionais em PDF<br>
                • Download imediato
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="main-card main-card-triatlo">
            <div class="card-icon">🏊‍♂️🚴‍♂️🏃‍♂️</div>
            <div class="card-title">Nutrição para Triatletas</div>
            <div class="card-description">
                Sistema especializado para atletas<br>
                • Cálculos para endurance<br>
                • Hidratação e suplementação<br>
                • Gestão de performance<br>
                • Relatórios especializados em PDF<br>
                • Download imediato
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Seção de características do sistema - ICONES E TEXTOS ALINHADOS
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
                Cálculos baseados em TMB, TGE e NAF utilizando tabelas TACO e TBCA como referência nutricional.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
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
            <div class="feature-icon">📋</div>
            <div class="feature-title">Relatórios em PDF</div>
            <div class="feature-description">
                Geração automática de PDFs profissionais com dados completos dos pacientes.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
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
            <div class="feature-icon">🎯</div>
            <div class="feature-title">Personalização</div>
            <div class="feature-description">
                Adaptação total às metas, restrições e objetivos de cada paciente.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📱</div>
            <div class="feature-title">Interface Intuitiva</div>
            <div class="feature-description">
                Design moderno e responsivo para melhor experiência do usuário.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Instruções de uso
    st.markdown("---")
    st.markdown("## 📖 Como Usar")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style='background: #f8f9fa; padding: 2rem; border-radius: 10px; border-left: 4px solid #4CAF50;'>
            <h3 style='color: #2E86AB; margin-bottom: 1rem;'>🥗 Nutrição Convencional</h3>
            <ul style='color: #666; line-height: 1.8;'>
                <li>Ideal para pacientes em geral</li>
                <li>Controle de peso e saúde</li>
                <li>Planos alimentares balanceados</li>
                <li>Acompanhamento nutricional completo</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background: #f8f9fa; padding: 2rem; border-radius: 10px; border-left: 4px solid #2196F3;'>
            <h3 style='color: #2E86AB; margin-bottom: 1rem;'>🏊‍♂️ Triatlo</h3>
            <ul style='color: #666; line-height: 1.8;'>
                <li>Especializado para atletas</li>
                <li>Nutrição para endurance</li>
                <li>Timing nutricional</li>
                <li>Suplementação esportiva</li>
            </ul>
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
# EXECUÇÃO
# =============================================================================
if __name__ == "__main__":
    main()
#streamlit run app.py