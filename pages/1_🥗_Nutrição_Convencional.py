# nutricao_convencional.py - SISTEMA DE NUTRIÇÃO CONVENCIONAL CORRIGIDO
import streamlit as st
import pandas as pd
from pulp import *
import io
import requests
import numpy as np
from datetime import datetime, timedelta
import base64
import random
import tempfile
import os
from xhtml2pdf import pisa
from io import BytesIO
from fpdf import FPDF
# === PRIMEIRO: set_page_config DEVE SER A PRIMEIRA LINHA ===
st.set_page_config(
    page_title="🥗 Nutrição Convencional", 
    page_icon="🥗",
    layout="wide"
)

# === SEGUNDO: CSS para ocultar TODOS os elementos do header ===
st.markdown("""
<style>
    /* Oculta o menu hamburguer e header completo do Streamlit */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Remove o menu superior DIREITO (Share, Deploy, 3 pontinhos) */
    .stDeployButton {display:none;}
    #stDecoration {display:none;}
    
    /* Remove os botões de ação do header */
    [data-testid="stActionButton"] {display:none;}
    [data-testid="baseButton-header"] {display:none;}
    
    /* Remove elementos específicos do header direito */
    .stApp > header {display: none;}
    .stApp [data-testid="stHeader"] {display: none;}
    .stApp [data-testid="stToolbar"] {display: none;}
    
    /* Remove qualquer elemento restante do header */
    .stApp > div:first-child {display: none;}
    
    /* Remove o padding extra do topo */
    .css-18e3th9 {
        padding-top: 0rem;
        padding-bottom: 0rem;
    }
    
    /* Ajusta o conteúdo principal para ocupar o espaço */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Remove qualquer margem residual */
    .main .block-container {
        padding-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURAÇÃO E CONSTANTES ---

# URLs do Google Drive CORRETAS
RECEITAS_URL = "https://drive.google.com/file/d/1VN4aGOjqsX0fdhN2HxOAVBL21jIjJy4V/view?usp=sharing"
ALIMENTOS_URL = "https://drive.google.com/file/d/1NKptsdF_dFGV9i4j6VGCYGTP9PkrJIZV/view?usp=sharing"

DIAS_SEMANA = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]

# --- SISTEMA DE REFEIÇÕES ORGANIZADO ---
REFEICOES_ORGANIZADAS = [
    {"tipo": "Café da Manhã", "horario": "07:00"},
    {"tipo": "Intervalo", "horario": "09:30"},
    {"tipo": "Almoço", "horario": "12:00"},
    {"tipo": "Intervalo", "horario": "15:00"},
    {"tipo": "Lanche", "horario": "17:00"},
    {"tipo": "Intervalo", "horario": "19:00"},
    {"tipo": "Jantar", "horario": "20:00"},
    {"tipo": "Ceia", "horario": "22:00"}
]

# --- OPÇÕES ---
SEXO_OPCOES = ['- Selecione -', 'Masculino', 'Feminino']

NAF_OPCOES = {
    '- Selecione -': 0.0, 
    'Sedentário': 1.2,
    'Moderado': 1.55,
    'Ativo': 1.725,
    'Atleta': 1.9
}

META_OPCOES = [
    '- Selecione -',
    'Controle de peso', 
    'Perda de Peso', 
    'Ganho de Massa',
    'Desempenho Esportivo'
]

# --- TIPOS DE DIETA ---
TIPOS_DIETA = {
    'Equilibrada': {'carbs': 50, 'proteinas': 25, 'gorduras': 25},
    'Low Carb': {'carbs': 20, 'proteinas': 40, 'gorduras': 40},
    'Cetogênica': {'carbs': 5, 'proteinas': 25, 'gorduras': 70},
    'High Carb': {'carbs': 60, 'proteinas': 20, 'gorduras': 20},
    'Mediterrânea': {'carbs': 45, 'proteinas': 20, 'gorduras': 35},
    'Hiperproteica': {'carbs': 30, 'proteinas': 45, 'gorduras': 25},
    'Plant-based': {'carbs': 55, 'proteinas': 20, 'gorduras': 25},
    'DASH': {'carbs': 50, 'proteinas': 25, 'gorduras': 25}
}

FAIXAS_ETARIAS = {
    'Criança (0-11 anos)': {'idade_min': 0, 'idade_max': 11},
    'Adolescente (12-17 anos)': {'idade_min': 12, 'idade_max': 17},
    'Adulto (18-59 anos)': {'idade_min': 18, 'idade_max': 59},
    'Idoso (60+ anos)': {'idade_min': 60, 'idade_max': 120}
}

# --- SISTEMA DE REFEIÇÕES AUTOMÁTICO ---
TIPOS_REFEICAO = [refeicao["tipo"] for refeicao in REFEICOES_ORGANIZADAS]

class SistemaCardapioAutomatico:
    def __init__(self, df_receitas):
        self.df_receitas = df_receitas
        self.receitas_por_tipo = self._organizar_receitas_por_tipo()
    
    def _organizar_receitas_por_tipo(self):
        """Organiza receitas por tipo de refeição adequado"""
        receitas_por_tipo = {refeicao["tipo"]: [] for refeicao in REFEICOES_ORGANIZADAS}
        
        for _, receita in self.df_receitas.iterrows():
            tipo_receita = str(receita.get('Tipo_Refeicao', 'Almoço')).strip()
            
            if tipo_receita == 'nan' or not tipo_receita:
                tipo_receita = 'Almoço'
            
            if 'Café' in tipo_receita or 'Cafe' in tipo_receita:
                receitas_por_tipo['Café da Manhã'].append(receita)
            elif 'Lanche' in tipo_receita or 'Intervalo' in tipo_receita:
                if len(receitas_por_tipo['Lanche']) < len(receitas_por_tipo['Intervalo']):
                    receitas_por_tipo['Lanche'].append(receita)
                else:
                    receitas_por_tipo['Intervalo'].append(receita)
            elif 'Almoço' in tipo_receita or 'Almoco' in tipo_receita:
                receitas_por_tipo['Almoço'].append(receita)
            elif 'Jantar' in tipo_receita:
                receitas_por_tipo['Jantar'].append(receita)
            elif 'Ceia' in tipo_receita:
                receitas_por_tipo['Ceia'].append(receita)
            else:
                receitas_por_tipo['Almoço'].append(receita)
                receitas_por_tipo['Jantar'].append(receita)
        
        return receitas_por_tipo
    
    def gerar_cardapio_semanal_sem_repeticao(self, tipo_dieta='Equilibrada', perfil=[]):
        """Gera cardápio semanal sem repetições de refeições"""
        cardapio_semanal = {}
        receitas_utilizadas_semana = set()
        
        for dia in DIAS_SEMANA:
            cardapio_dia = {}
            receitas_utilizadas_dia = set()
            
            for refeicao_info in REFEICOES_ORGANIZADAS:
                tipo_refeicao = refeicao_info["tipo"]
                horario = refeicao_info["horario"]
                
                receitas_disponiveis = [
                    receita for receita in self.receitas_por_tipo[tipo_refeicao]
                    if receita.name not in receitas_utilizadas_dia 
                    and receita.name not in receitas_utilizadas_semana
                ]
                
                if not receitas_disponiveis:
                    receitas_disponiveis = [
                        receita for receita in self.receitas_por_tipo[tipo_refeicao]
                        if receita.name not in receitas_utilizadas_dia
                    ]
                
                if receitas_disponiveis:
                    if 'Celíaco' in perfil:
                        receitas_disponiveis = [r for r in receitas_disponiveis if r.get('Apta_Celiaco', 'Sim') == 'Sim']
                    if 'Lactose' in perfil:
                        receitas_disponiveis = [r for r in receitas_disponiveis if r.get('Sem_Lactose', 'Sim') == 'Sim']
                    if 'Alérgico a Leite' in perfil:
                        receitas_disponiveis = [r for r in receitas_disponiveis if r.get('Sem_Lactose', 'Sim') == 'Sim']
                    if 'Alérgico a Ovo' in perfil:
                        receitas_disponiveis = [r for r in receitas_disponiveis if r.get('Sem_Ovo', 'Sim') == 'Sim']
                    if 'Alérgico a Oleaginosas' in perfil:
                        receitas_disponiveis = [r for r in receitas_disponiveis if r.get('Sem_Oleaginosas', 'Sim') == 'Sim']
                    if 'Vegano' in perfil:
                        receitas_disponiveis = [r for r in receitas_disponiveis if r.get('Vegano', 'Nao') == 'Sim']
                    elif 'Vegetariano' in perfil:
                        receitas_disponiveis = [r for r in receitas_disponiveis if r.get('Vegetariano', 'Nao') == 'Sim']
                    elif 'Ovo-Lacto Vegetariano' in perfil:
                        receitas_disponiveis = [r for r in receitas_disponiveis if r.get('Vegetariano', 'Nao') == 'Sim']
                    elif 'Pesco-Vegetariano' in perfil:
                        receitas_disponiveis = [r for r in receitas_disponiveis if r.get('Vegetariano', 'Nao') == 'Sim']
                
                if receitas_disponiveis:
                    receita_escolhida = random.choice(receitas_disponiveis)
                    cardapio_dia[tipo_refeicao] = {
                        'receita': receita_escolhida,
                        'horario': horario
                    }
                    receitas_utilizadas_dia.add(receita_escolhida.name)
                    receitas_utilizadas_semana.add(receita_escolhida.name)
                else:
                    receitas_fallback = self.receitas_por_tipo[tipo_refeicao]
                    if receitas_fallback:
                        receita_escolhida = random.choice(receitas_fallback)
                        cardapio_dia[tipo_refeicao] = {
                            'receita': receita_escolhida,
                            'horario': horario
                        }
            
            cardapio_semanal[dia] = cardapio_dia
        
        return cardapio_semanal

# --- FUNÇÕES PARA CARREGAR DADOS ---
@st.cache_data(ttl=3600)
def carregar_csv_google_drive(url):
    """Carrega dados do Google Drive com tratamento robusto"""
    try:
        file_id = url.split('/d/')[1].split('/')[0]
        download_url = f'https://drive.google.com/uc?id={file_id}&export=download'
        
        response = requests.get(download_url)
        response.raise_for_status()
        
        for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
            try:
                df = pd.read_csv(io.StringIO(response.text), encoding=encoding)
                if not df.empty and len(df.columns) > 1:
                    return df
            except:
                continue
                
        return None
        
    except Exception as e:
        return None

@st.cache_data
def carregar_dados_completos():
    """Carrega todos os dados do Google Drive"""
    df_receitas = carregar_csv_google_drive(RECEITAS_URL)
    if df_receitas is None or df_receitas.empty:
        df_receitas = carregar_dados_fallback_receitas()
    else:
        df_receitas = calcular_calorias_receitas(df_receitas)
    
    df_alimentos = carregar_csv_google_drive(ALIMENTOS_URL)
    if df_alimentos is None or df_alimentos.empty:
        df_alimentos = carregar_dados_fallback_alimentos()
    
    return df_alimentos, df_receitas

def calcular_calorias_receitas(df_receitas):
    """Calcula calorias totais baseadas nos macronutrientes"""
    if 'Tipo_Refeicao' in df_receitas.columns:
        df_receitas['Tipo_Refeicao'] = df_receitas['Tipo_Refeicao'].astype(str)
    
    if 'Total_Calorias' not in df_receitas.columns:
        carb_col = 'Carboidratos' if 'Carboidratos' in df_receitas.columns else 'Macro_Carboidratos'
        prot_col = 'Proteinas' if 'Proteinas' in df_receitas.columns else 'Macro_Proteinas'
        lip_col = 'Lipideos' if 'Lipideos' in df_receitas.columns else 'Macro_Lipidios'
        
        df_receitas['Total_Calorias'] = (
            df_receitas[carb_col] * 4 + 
            df_receitas[prot_col] * 4 + 
            df_receitas[lip_col] * 9
        )
    
    if 'Tipo_Refeicao' not in df_receitas.columns and 'Periodo' in df_receitas.columns:
        df_receitas['Tipo_Refeicao'] = df_receitas['Periodo'].astype(str)
    
    if 'Macro_Carboidratos' not in df_receitas.columns and 'Carboidratos' in df_receitas.columns:
        df_receitas['Macro_Carboidratos'] = df_receitas['Carboidratos']
    
    if 'Macro_Proteinas' not in df_receitas.columns and 'Proteinas' in df_receitas.columns:
        df_receitas['Macro_Proteinas'] = df.receitas['Proteinas']
    
    if 'Macro_Lipidios' not in df_receitas.columns and 'Lipideos' in df_receitas.columns:
        df_receitas['Macro_Lipidios'] = df_receitas['Lipideos']
    
    if 'Sem_Ovo' not in df_receitas.columns:
        df_receitas['Sem_Ovo'] = 'Sim'
    if 'Sem_Oleaginosas' not in df_receitas.columns:
        df_receitas['Sem_Oleaginosas'] = 'Sim'
    
    return df_receitas

def carregar_dados_fallback_receitas():
    """Dados de fallback para receitas"""
    receitas_data = {
        'Nome_Receita': [
            'Aveia com Whey e Frutas', 'Omelete de Claras com Abacate', 'Tapioca com Queijo Branco',
            'Panqueca de Aveia com Mel', 'Iogurte Grego com Granola e Mel', 'Pão Integral com Ovo',
            'Vitamina de Banana com Aveia', 'Creme de Abacate', 'Mix de Castanhas', 'Fruta com Pasta de Amendoim',
            'Iogurte com Sementes', 'Barra de Cereal Caseira', 'Cookies de Aveia', 'Shake Proteico',
            'Biscoito Integral', 'Frutas Secas', 'Arroz Integral com Frango Grelhado', 'Quinoa com Salmão e Legumes',
            'Batata Doce com Carne Moída', 'Massa Integral com Atum', 'Feijão com Arroz e Bife',
            'Lentilha com Legumes e Ovo', 'Risoto de Cogumelos', 'Sanduíche Natural', 'Wrap de Frango',
            'Salada de Frutas', 'Smoothie Verde', 'Torrada com Abacate', 'Iogurte com Granola',
            'Sopa de Legumes com Frango', 'Omelete de Vegetais', 'Peixe Assado com Batata',
            'Frango à Parmegiana Light', 'Carne Moída com Abóbora', 'Salada de Grãos com Atum',
            'Chá com Biscoito Integral', 'Leite Morno com Mel', 'Iogurte Natural', 'Pera Cozida',
            'Gelatina Diet', 'Banana com Canela'
        ],
        'Tipo_Refeicao': [
            'Café da Manhã', 'Café da Manhã', 'Café da Manhã', 'Café da Manhã', 'Café da Manhã',
            'Café da Manhã', 'Café da Manhã', 'Café da Manhã', 'Intervalo', 'Intervalo', 'Intervalo',
            'Intervalo', 'Intervalo', 'Intervalo', 'Intervalo', 'Intervalo', 'Almoço', 'Almoço',
            'Almoço', 'Almoço', 'Almoço', 'Almoço', 'Almoço', 'Lanche', 'Lanche', 'Lanche', 'Lanche',
            'Lanche', 'Lanche', 'Jantar', 'Jantar', 'Jantar', 'Jantar', 'Jantar', 'Jantar', 'Ceia',
            'Ceia', 'Ceia', 'Ceia', 'Ceia', 'Ceia'
        ],
        'Total_Calorias': [
            350, 280, 220, 320, 300, 250, 280, 200, 150, 180, 120, 200, 220, 250, 100, 150,
            450, 400, 420, 380, 500, 350, 320, 300, 280, 200, 180, 250, 220, 300, 280, 350,
            400, 320, 280, 100, 120, 80, 90, 60, 110
        ],
        'Macro_Carboidratos': [
            45, 15, 30, 50, 45, 25, 40, 10, 10, 20, 15, 25, 30, 20, 15, 25, 60, 45, 55, 50,
            65, 40, 55, 35, 25, 40, 30, 20, 35, 35, 15, 40, 30, 25, 20, 20, 25, 10, 20, 12, 25
        ],
        'Macro_Proteinas': [
            25, 20, 15, 15, 20, 18, 15, 8, 5, 8, 10, 5, 8, 25, 3, 5, 35, 30, 30, 25, 35, 20,
            12, 20, 25, 5, 8, 15, 12, 25, 20, 30, 35, 25, 20, 3, 5, 8, 2, 10, 1
        ],
        'Macro_Lipidios': [
            8, 15, 5, 8, 8, 12, 5, 15, 12, 8, 5, 8, 8, 8, 4, 6, 10, 12, 10, 8, 12, 8, 6, 8,
            10, 2, 3, 12, 8, 8, 18, 12, 15, 10, 15, 1, 2, 2, 1, 0, 1
        ],
        'Apta_Celiaco': ['Sim'] * 41,
        'Sem_Lactose': ['Nao', 'Sim', 'Nao', 'Sim', 'Nao', 'Sim', 'Sim', 'Sim'] + ['Sim'] * 33,
        'Sem_Ovo': ['Sim', 'Sim', 'Nao', 'Sim', 'Sim', 'Nao', 'Sim', 'Sim'] + ['Sim'] * 33,
        'Sem_Oleaginosas': ['Sim'] * 41,
        'Vegetariano': ['Nao', 'Sim', 'Nao', 'Sim', 'Nao', 'Sim', 'Sim', 'Sim'] + ['Sim'] * 16 + ['Nao'] * 11 + ['Sim'] * 6,
        'Vegano': ['Nao', 'Nao', 'Nao', 'Nao', 'Nao', 'Nao', 'Sim', 'Sim'] + ['Sim'] * 16 + ['Nao'] * 17
    }
    
    df = pd.DataFrame(receitas_data)
    df.index.name = 'id'
    
    df['Tipo_Refeicao'] = df['Tipo_Refeicao'].astype(str)
    df['Apta_Celiaco'] = df['Apta_Celiaco'].astype(str)
    df['Sem_Lactose'] = df['Sem_Lactose'].astype(str)
    df['Sem_Ovo'] = df['Sem_Ovo'].astype(str)
    df['Sem_Oleaginosas'] = df['Sem_Oleaginosas'].astype(str)
    df['Vegetariano'] = df['Vegetariano'].astype(str)
    df['Vegano'] = df['Vegano'].astype(str)
    
    return df.reset_index()

def carregar_dados_fallback_alimentos():
    """Dados de fallback para alimentos"""
    return pd.DataFrame({
        'Nome': ['Banana', 'Aveia', 'Batata Doce', 'Frango', 'Whey Protein', 'Salmão', 
                'Quinoa', 'Arroz Integral', 'Ovo', 'Abacate', 'Tapioca', 'Pão Integral',
                'Iogurte Grego', 'Castanhas', 'Mel'],
        'Calorias': [89, 389, 86, 165, 120, 208, 120, 130, 155, 160, 160, 250, 59, 600, 304],
        'Carboidratos': [23, 66, 20, 0, 4, 0, 21, 28, 1, 9, 40, 45, 4, 20, 82],
        'Proteinas': [1.1, 17, 1.6, 31, 24, 20, 4, 2.7, 13, 2, 1, 10, 10, 15, 0.3],
        'Lipidios': [0.3, 7, 0.1, 3.6, 1, 13, 2, 0.3, 11, 15, 0, 3, 1, 50, 0]
    })

def obter_faixa_etaria(idade):
    """Determina a faixa etária baseada na idade"""
    for faixa, limites in FAIXAS_ETARIAS.items():
        if limites['idade_min'] <= idade <= limites['idade_max']:
            return faixa
    return 'Adulto (18-59 anos)'

# --- FUNÇÃO DE HIDRATAÇÃO SIMPLIFICADA ---
def calcular_hidratacao_basica(peso_kg):
    """Calcula hidratação básica"""
    return peso_kg * 35

# --- FUNÇÕES PARA INTERAÇÃO DAS ABAS ---
def obter_suplementos_recomendados(meta, tipo_dieta):
    """Retorna suplementos recomendados baseados no perfil do paciente"""
    suplementos_recomendados = set()
    
    base_suplementos = {
        'Whey Protein', 'Multivitamínico', 'Ômega-3', 'Vitamina D', 'Magnésio'
    }
    
    suplementos_recomendados.update(base_suplementos)
    
    if meta == 'Desempenho Esportivo':
        suplementos_recomendados.update(['BCAA', 'Creatina', 'Glutamina'])
    elif meta == 'Ganho de Massa':
        suplementos_recomendados.update(['Creatina', 'BCAA', 'Glutamina'])
    elif meta == 'Perda de Peso':
        suplementos_recomendados.update(['Cafeína', 'BCAA'])
    
    if tipo_dieta == 'Cetogênica':
        suplementos_recomendados.update(['Eletrólitos', 'Óleo MCT'])
    
    return suplementos_recomendados

def obter_lista_compras_recomendada(cardapio_semanal, tipo_dieta, meta):
    """Gera lista de compras recomendada baseada no cardápio e perfil"""
    alimentos_recomendados = set()
    
    alimentos_base = {
        'Banana', 'Aveia', 'Batata Doce', 'Ovo', 'Abacate', 
        'Pão Integral', 'Iogurte Grego', 'Castanhas', 'Mel'
    }
    
    alimentos_recomendados.update(alimentos_base)
    
    if tipo_dieta in ['High Carb', 'Equilibrada']:
        alimentos_recomendados.update(['Arroz Integral', 'Massa Integral', 'Quinoa', 'Tapioca'])
    elif tipo_dieta in ['Low Carb', 'Cetogênica']:
        alimentos_recomendados.update(['Abacate', 'Castanhas', 'Azeite de Oliva', 'Sementes (chia, linhaça)'])
        alimentos_recomendados.discard('Arroz Integral')
        alimentos_recomendados.discard('Massa Integral')
        alimentos_recomendados.discard('Tapioca')
    elif tipo_dieta == 'Hiperproteica':
        alimentos_recomendados.update(['Frango', 'Peixe', 'Whey Protein', 'Queijo Cottage', 'Salmão'])
    elif tipo_dieta == 'Plant-based':
        alimentos_recomendados.update(['Leguminosas', 'Quinoa', 'Nozes', 'Sementes', 'Tofu'])
        alimentos_recomendados.discard('Frango')
        alimentos_recomendados.discard('Peixe')
        alimentos_recomendados.discard('Ovo')
    
    if meta == 'Desempenho Esportivo':
        alimentos_recomendados.update(['Bebidas Esportivas'])
    elif meta == 'Perda de Peso':
        alimentos_recomendados.update(['Vegetais variados', 'Proteínas magras'])
    
    return alimentos_recomendados

# --- FUNÇÕES ESPECÍFICAS PARA TIPOS DE DIETA ---
def calcular_macros_por_dieta(tge, tipo_dieta):
    """Calcula macros baseado no tipo de dieta selecionado"""
    if tipo_dieta not in TIPOS_DIETA:
        tipo_dieta = 'Equilibrada'
    
    macros_percent = TIPOS_DIETA[tipo_dieta]
    
    cho_g = (tge * macros_percent['carbs'] / 100) / 4
    ptn_g = (tge * macros_percent['proteinas'] / 100) / 4
    lip_g = (tge * macros_percent['gorduras'] / 100) / 9
    
    return macros_percent['carbs'], macros_percent['proteinas'], macros_percent['gorduras'], cho_g, ptn_g, lip_g

def obter_recomendacoes_dieta(tipo_dieta):
    """Retorna recomendações específicas para cada tipo de dieta"""
    recomendacoes = {
        'Equilibrada': {
            'descricao': 'Dieta balanceada com distribuição equilibrada de macronutrientes',
            'alimentos_recomendados': ['Frutas variadas', 'Vegetais coloridos', 'Grãos integrais', 'Proteínas magras'],
            'alimentos_evitar': ['Alimentos ultraprocessados', 'Açúcares refinados', 'Gorduras trans'],
            'dicas': ['Mantenha hidratação adequada', 'Varie as cores no prato', 'Coma a cada 3-4 horas']
        },
        'Low Carb': {
            'descricao': 'Dieta com redução de carboidratos para controle glicêmico e perda de peso',
            'alimentos_recomendados': ['Vegetais folhosos', 'Carnes magras', 'Ovos', 'Abacate', 'Castanhas'],
            'alimentos_evitar': ['Açúcares', 'Grãos refinados', 'Frutas muito doces', 'Amidos'],
            'dicas': ['Aumente ingestão de gorduras boas', 'Mantenha proteínas adequadas', 'Monitorar cetose']
        },
        'Cetogênica': {
            'descricao': 'Dieta muito baixa em carboidratos para induzir cetose nutricional',
            'alimentos_recomendados': ['Carnes gordas', 'Abacate', 'Ovos', 'Queijos', 'Azeite', 'Castanhas'],
            'alimentos_evitar': ['Todos os grãos', 'Frutas doces', 'Açúcares', 'Leguminosas'],
            'dicas': ['Mantenha carboidratos abaixo de 30g/dia', 'Suplemente eletrólitos', 'Monitorar corpos cetônicos']
        },
        'High Carb': {
            'descricao': 'Dieta rica em carboidratos para atletas de endurance',
            'alimentos_recomendados': ['Batata doce', 'Arroz integral', 'Massas integrais', 'Frutas', 'Aveia'],
            'alimentos_evitar': ['Gorduras em excesso', 'Alimentos muito processados'],
            'dicas': ['Focar em carboidratos complexos', 'Timing correto de refeições', 'Hidratação adequada']
        },
        'Mediterrânea': {
            'descricao': 'Baseada na dieta tradicional dos países mediterrâneos',
            'alimentos_recomendados': ['Azeite de oliva', 'Peixes', 'Frutas frescas', 'Vegetais', 'Grãos integrais'],
            'alimentos_evitar': ['Carnes processadas', 'Açúcares refinados', 'Gorduras saturadas'],
            'dicas': ['Use azeite como principal gordura', 'Consuma peixes 2-3x/semana', 'Vinho tinto com moderação']
        },
        'Hiperproteica': {
            'descricao': 'Dieta com ênfase em proteínas para ganho muscular',
            'alimentos_recomendados': ['Carnes magras', 'Ovos', 'Peixes', 'Whey protein', 'Queijo cottage'],
            'alimentos_evitar': ['Carboidratos simples', 'Gorduras em excesso'],
            'dicas': ['Distribua proteínas ao longo do dia', 'Mantenha hidratação', 'Combine com treino de força']
        },
        'Plant-based': {
            'descricao': 'Dieta baseada em alimentos de origem vegetal',
            'alimentos_recomendados': ['Leguminosas', 'Grãos integrais', 'Nozes', 'Sementes', 'Vegetais variados'],
            'alimentos_evitar': ['Carnes', 'Laticínios', 'Ovos'],
            'dicas': ['Combine fontes proteicas', 'Suplemente B12 se necessário', 'Varie as fontes alimentares']
        },
        'DASH': {
            'descricao': 'Dieta para controle da pressão arterial',
            'alimentos_recomendados': ['Frutas', 'Vegetais', 'Laticínios low-fat', 'Grãos integrais'],
            'alimentos_evitar': ['Sódio', 'Açúcares', 'Carnes vermelhas'],
            'dicas': ['Controle de sódio', 'Rica em potássio', 'Moderação em proteínas animais']
        }
    }
    
    return recomendacoes.get(tipo_dieta, recomendacoes['Equilibrada'])

# --- FUNÇÕES DE CÁLCULO NUTRICIONAL ---
def calcular_imc_e_classificar(peso_kg: float, altura_cm: float):
    """Calcula IMC e classificação"""
    if altura_cm <= 0 or peso_kg <= 0:
        return 0.0, "Não calculado"
    
    altura_m = altura_cm / 100
    imc = peso_kg / (altura_m ** 2)
    
    if imc < 18.5:
        classificacao = "Magreza"
    elif 18.5 <= imc < 25.0:
        classificacao = "Normal"
    elif 25.0 <= imc < 30.0:
        classificacao = "Sobrepeso"
    elif 30.0 <= imc < 35.0:
        classificacao = "Obesidade Grau I"
    elif 35.0 <= imc < 40.0:
        classificacao = "Obesidade Grau II"
    else:
        classificacao = "Obesidade Grau III"
        
    return imc, classificacao

def calcular_tmb(peso, altura, idade, sexo):
    if peso <= 0 or altura <= 0 or idade <= 0 or sexo not in ['Masculino', 'Feminino']:
        return 0.0
    
    if sexo == 'Masculino':
        return (10 * peso) + (6.25 * altura) - (5 * idade) + 5
    else:
        return (10 * peso) + (6.25 * altura) - (5 * idade) - 161

# --- FUNÇÕES DE OTIMIZAÇÃO ---
def otimizar_cardapio(df_receitas, tge_alvo, cho_g_alvo, ptn_g_alvo, perfil, tipo_dieta):
    """Otimização simplificada considerando tipo de dieta"""
    df = df_receitas.copy()
    
    if 'Celíaco' in perfil and 'Apta_Celiaco' in df.columns:
        df = df[df['Apta_Celiaco'] == 'Sim']
    if 'Lactose' in perfil and 'Sem_Lactose' in df.columns:
        df = df[df['Sem_Lactose'] == 'Sim']
    if 'Alérgico a Leite' in perfil and 'Sem_Lactose' in df.columns:
        df = df[df['Sem_Lactose'] == 'Sim']
    if 'Alérgico a Ovo' in perfil and 'Sem_Ovo' in df.columns:
        df = df[df['Sem_Ovo'] == 'Sim']
    if 'Alérgico a Oleaginosas' in perfil and 'Sem_Oleaginosas' in df.columns:
        df = df[df['Sem_Oleaginosas'] == 'Sim']
    if 'Vegano' in perfil and 'Vegano' in df.columns:
        df = df[df['Vegano'] == 'Sim']
    elif 'Vegetariano' in perfil and 'Vegetariano' in df.columns: 
        df = df[df['Vegetariano'] == 'Sim']
    elif 'Ovo-Lacto Vegetariano' in perfil and 'Vegetariano' in df.columns:
        df = df[df['Vegetariano'] == 'Sim']
    elif 'Pesco-Vegetariano' in perfil and 'Vegetariano' in df.columns:
        df = df[df['Vegetariano'] == 'Sim']
    
    if df.empty:
        return None
    
    if tipo_dieta == 'Low Carb':
        df = df[df['Macro_Carboidratos'] <= 30]
    elif tipo_dieta == 'Cetogênica':
        df = df[df['Macro_Carboidratos'] <= 10]
    elif tipo_dieta == 'High Carb':
        df = df[df['Macro_Carboidratos'] >= 40]
    elif tipo_dieta == 'Hiperproteica':
        df = df[df['Macro_Proteinas'] >= 25]
    
    if df.empty:
        return None
    
    cardapio = pd.DataFrame()
    tipos_refeicao = [refeicao["tipo"] for refeicao in REFEICOES_ORGANIZADAS]
    
    for tipo in tipos_refeicao:
        df_tipo = df[df['Tipo_Refeicao'] == tipo]
        if len(df_tipo) > 0:
            receita = df_tipo.sample(1)
            cardapio = pd.concat([cardapio, receita])
    
    return cardapio if not cardapio.empty else None

# --- FUNÇÕES PARA GERAR PDF DA LISTA DE COMPRAS (SIMPLIFICADO) ---
def gerar_html_lista_compras_pdf(lista_compras, dados_paciente, tipo_dieta):
    """Gera HTML para PDF da lista de compras (simplificado)"""
    
    data_emissao = datetime.now().strftime("%d/%m/%Y")
    
    css = """
    <style>
        body {
            font-family: Arial, sans-serif;
            font-size: 12pt;
            line-height: 1.4;
            color: #333;
            margin: 2cm;
        }
        .header {
            text-align: center;
            margin-bottom: 25px;
            border-bottom: 2px solid #333;
            padding-bottom: 15px;
        }
        .section-title {
            font-weight: bold;
            font-size: 14pt;
            margin: 20px 0 10px 0;
            padding-bottom: 5px;
            border-bottom: 1px solid #ccc;
        }
        .paciente-info {
            margin: 15px 0;
            line-height: 1.6;
        }
        .categoria {
            margin: 15px 0;
        }
        .categoria-titulo {
            font-weight: bold;
            font-size: 13pt;
            color: #2c3e50;
            margin-bottom: 8px;
            padding-bottom: 3px;
            border-bottom: 1px solid #3498db;
        }
        .item-lista {
            margin: 5px 0;
            padding-left: 10px;
        }
        .data-emissao {
            text-align: center;
            margin-top: 30px;
            font-size: 11pt;
            color: #666;
        }
    </style>
    """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Lista de Compras - {dados_paciente['nome']}</title>
        {css}
    </head>
    <body>
        <div class="header">
            <h1>LISTA DE COMPRAS NUTRICIONAL</h1>
        </div>
        
        <div class="section-title">DADOS DO PACIENTE</div>
        <div class="paciente-info">
            <p><strong>Nome:</strong> {dados_paciente['nome']}</p>
            <p><strong>Idade:</strong> {dados_paciente['idade']} anos</p>
            <p><strong>Peso:</strong> {dados_paciente['peso']} kg | <strong>Altura:</strong> {dados_paciente['altura']} cm</p>
            <p><strong>IMC:</strong> {dados_paciente['imc']:.1f} - {dados_paciente['classificacao_imc']}</p>
            <p><strong>Tipo de Dieta:</strong> {tipo_dieta}</p>
            <p><strong>Meta:</strong> {dados_paciente['meta']}</p>
        </div>
        
        <div class="section-title">LISTA DE COMPRAS RECOMENDADA</div>
    """
    
    categorias = {
        'Proteínas': [],
        'Carboidratos Complexos': [],
        'Carboidratos Rápidos': [],
        'Gorduras Saudáveis': [],
        'Vegetais': [],
        'Hidratação': [],
        'Suplementos': []
    }
    
    for item in lista_compras:
        item_lower = item.lower()
        if any(proteina in item_lower for proteina in ['frango', 'peixe', 'ovo', 'whey', 'queijo', 'salmão', 'tofu', 'leguminosas', 'carne']):
            categorias['Proteínas'].append(item)
        elif any(carb in item_lower for carb in ['aveia', 'batata doce', 'quinoa', 'arroz integral', 'pão integral', 'massa integral', 'tapioca']):
            categorias['Carboidratos Complexos'].append(item)
        elif any(carb_rapido in item_lower for carb_rapido in ['banana', 'mel', 'frutas secas', 'bebidas esportivas']):
            categorias['Carboidratos Rápidos'].append(item)
        elif any(gordura in item_lower for gordura in ['abacate', 'castanhas', 'azeite', 'sementes', 'nozes', 'óleo mct']):
            categorias['Gorduras Saudáveis'].append(item)
        elif any(vegetal in item_lower for vegetal in ['espinafre', 'brócolis', 'couve', 'pimentão', 'tomate', 'cenoura', 'vegetais']):
            categorias['Vegetais'].append(item)
        elif any(hidra in item_lower for hidra in ['água de coco', 'bebidas esportivas', 'água mineral']):
            categorias['Hidratação'].append(item)
        else:
            categorias['Suplementos'].append(item)
    
    for categoria, itens in categorias.items():
        if itens:
            html += f"""
            <div class="categoria">
                <div class="categoria-titulo">{categoria.upper()}</div>
            """
            for item in sorted(itens):
                html += f'<div class="item-lista">• {item}</div>'
            html += "</div>"
    
    html += f"""
        <div class="data-emissao">
            Data de emissão: {data_emissao}
        </div>
    </body>
    </html>
    """
    
    return html

def gerar_pdf_lista_compras(lista_compras, dados_paciente, tipo_dieta):
    """Gera PDF da lista de compras (simplificado)"""
    try:
        html_content = gerar_html_lista_compras_pdf(lista_compras, dados_paciente, tipo_dieta)
        
        pdf_buffer = BytesIO()
        
        pisa_status = pisa.CreatePDF(
            html_content,
            dest=pdf_buffer,
            encoding='utf-8'
        )
        
        if pisa_status.err:
            st.error(f"Erro ao gerar PDF da lista: {pisa_status.err}")
            return None
        
        pdf_bytes = pdf_buffer.getvalue()
        pdf_buffer.close()
        
        return pdf_bytes
        
    except Exception as e:
        st.error(f"Erro ao gerar PDF da lista: {str(e)}")
        return None

# --- FUNÇÕES PARA GERAR PDF DO PLANO NUTRICIONAL ---
def gerar_html_para_pdf(dados_paciente, cardapio_semanal, nome_nutri, crn, tipo_dieta, meta):
    """Gera HTML formatado para conversão em PDF com xhtml2pdf"""
    
    data_emissao = datetime.now().strftime("%d/%m/%Y")
    hora_emissao = datetime.now().strftime("%H:%M")
    
    css = """
    <style>
        body {
            font-family: Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.0;
            color: #333;
            margin: 2cm;
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
        }
        .section-title {
            font-weight: bold;
            font-size: 13pt;
            margin: 15px 0 8px 0;
            padding-bottom: 3px;
            border-bottom: 1px solid #ccc;
        }
        .paciente-info {
            margin: 12px 0;
            line-height: 1.2;
        }
        .dia-cardapio {
            margin: 12px 0;
            padding: 0;
        }
        .dia-titulo {
            font-size: 12pt;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 8px;
            padding-bottom: 2px;
            border-bottom: 1px solid #3498db;
        }
        .refeicao {
            margin: 4px 0;
            padding: 2px 0;
            line-height: 1.0;
        }
        .refeicao-tipo {
            font-weight: bold;
            color: #555;
        }
        .refeicao-nome {
            margin-left: 5px;
        }
        .totais-dia {
            background-color: #f8f9fa;
            padding: 8px;
            margin: 8px 0 0 0;
            border-radius: 3px;
            font-weight: bold;
            border-left: 3px solid #3498db;
            line-height: 1.0;
        }
        .orientacoes {
            margin: 15px 0;
            padding: 0;
            line-height: 1.0;
        }
        .assinatura-container {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
        }
        .linha-assinatura {
            width: 400px;
            margin: 0 auto;
            border-top: 1px solid #333;
            padding-top: 40px;
        }
        .assinatura-conteudo {
            text-align: center;
            margin-top: 10px;
            line-height: 1.4;
        }
        .assinatura-nome {
            margin: 5px 0;
            font-weight: bold;
            font-size: 13pt;
        }
        .assinatura-crn {
            margin: 5px 0;
            font-size: 11pt;
            color: #666;
        }
        .assinatura-data {
            margin: 5px 0;
            font-size: 11pt;
            color: #666;
        }
    </style>
    """
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Plano Nutricional - {dados_paciente['nome']}</title>
    {css}
</head>
<body>
    <div class="header">
        <h1>PLANO NUTRICIONAL PERSONALIZADO</h1>
    </div>
    
    <div class="section-title">DADOS DO PACIENTE</div>
    <div class="paciente-info">
        <p><strong>Nome:</strong> {dados_paciente['nome']}</p>
        <p><strong>Idade:</strong> {dados_paciente['idade']} anos | <strong>Faixa Etária:</strong> {dados_paciente['faixa_etaria']}</p>
        <p><strong>Peso:</strong> {dados_paciente['peso']} kg | <strong>Altura:</strong> {dados_paciente['altura']} cm</p>
        <p><strong>IMC:</strong> {dados_paciente['imc']:.1f} - {dados_paciente['classificacao_imc']}</p>
        <p><strong>TGE:</strong> {dados_paciente['tge']:.0f} kcal</p>
        <p><strong>Tipo de Dieta:</strong> {tipo_dieta}</p>
        <p><strong>Meta:</strong> {meta}</p>
        <p><strong>Macronutrientes:</strong> C{dados_paciente['cho_p']}% P{dados_paciente['ptn_p']}% G{dados_paciente['lip_p']}%</p>
        <p><strong>Hidratação:</strong> {dados_paciente['hidratacao']:.0f} ml/dia</p>
    </div>
    
    <div class="section-title">CARDÁPIO SEMANAL</div>"""
    
    for dia in DIAS_SEMANA:
        html += f"""<div class="dia-cardapio">
            <div class="dia-titulo">{dia.upper()}</div>"""
        
        if dia in cardapio_semanal and cardapio_semanal[dia]:
            cardapio_dia = cardapio_semanal[dia]
            total_cal = 0
            total_cho = 0
            total_ptn = 0
            total_lip = 0
            
            for refeicao_info in REFEICOES_ORGANIZADAS:
                tipo_refeicao = refeicao_info["tipo"]
                horario = refeicao_info["horario"]
                
                if tipo_refeicao in cardapio_dia:
                    receita_data = cardapio_dia[tipo_refeicao]['receita']
                    
                    html += f"""<div class="refeicao">
                        <span class="refeicao-tipo">{tipo_refeicao} ({horario}):</span>
                        <span class="refeicao-nome">{receita_data['Nome_Receita']}</span>
                    </div>"""
                    
                    total_cal += receita_data['Total_Calorias']
                    total_cho += receita_data['Macro_Carboidratos']
                    total_ptn += receita_data['Macro_Proteinas']
                    total_lip += receita_data['Macro_Lipidios']
            
            html += f"""<div class="totais-dia">
                <strong>TOTAIS DO DIA:</strong><br>
                Calorias: {total_cal:.0f} kcal | Carboidratos: {total_cho:.0f}g | Proteínas: {total_ptn:.0f}g | Gorduras: {total_lip:.0f}g
            </div>"""
        else:
            html += """<div class="refeicao">
                <div class="refeicao-info">Cardápio em ajuste - consulte nutricionista</div>
            </div>"""
        
        html += "</div>"
    
    html += """<div style="page-break-before: always;"></div>
    <div class="section-title">ORIENTAÇÕES GERAIS</div>
    <div class="orientacoes">
        <p>• Plano desenvolvido para suas necessidades específicas</p>
        <p>• Mantenha hidratação adequada durante o dia</p>
        <p>• Ajuste porções conforme fome e necessidades</p>
        <p>• Acompanhamento regular com nutricionista</p>
        <p>• Comunique desconfortos ou dificuldades</p>
        <p>• Combine alimentação com atividade física</p>
        <p>• Respeite os horários das refeições</p>
        <p>• Varie os alimentos dentro das opções permitidas</p>
    </div>
    
    <div class="assinatura-container">
        <div class="linha-assinatura"></div>
        <div class="assinatura-conteudo">
            <div class="assinatura-nome">Clesiane Rossa</div>
            <div class="assinatura-crn">CRN: 15003</div>
            <div class="assinatura-data">Data de emissão: """ + data_emissao + """ às """ + hora_emissao + """</div>
        </div>
    </div>
</body>
</html>"""
    
    return html

def gerar_pdf_com_xhtml2pdf(dados_paciente, cardapio_semanal, nome_nutri, crn, tipo_dieta, meta):
    """Gera PDF usando xhtml2pdf"""
    try:
        html_content = gerar_html_para_pdf(dados_paciente, cardapio_semanal, nome_nutri, crn, tipo_dieta, meta)
        
        pdf_buffer = BytesIO()
        
        pisa_status = pisa.CreatePDF(
            html_content,
            dest=pdf_buffer,
            encoding='utf-8'
        )
        
        if pisa_status.err:
            st.error(f"Erro ao gerar PDF: {pisa_status.err}")
            return None
        
        pdf_bytes = pdf_buffer.getvalue()
        pdf_buffer.close()
        
        return pdf_bytes
        
    except Exception as e:
        st.error(f"Erro ao gerar PDF com xhtml2pdf: {str(e)}")
        return None

# --- FUNÇÃO PARA LIMPAR TODOS OS DADOS ---
def limpar_todos_dados():
    """Limpa todos os dados das seções especificadas"""
    # Dados do paciente
    paciente_keys = ['nome_paciente', 'peso', 'altura', 'idade']
    for key in paciente_keys:
        if key in st.session_state:
            del st.session_state[key]
    
    # Tipo de dieta
    if 'tipo_dieta_input' in st.session_state:
        del st.session_state.tipo_dieta_input
    
    # Restrições alimentares
    restricoes_keys = [
        'celiaca_input', 'lactose_input', 'alergia_leite_input', 
        'alergia_ovo_input', 'alergia_oleaginosas_input', 
        'diabetico_input', 'hipertenso_input'
    ]
    for key in restricoes_keys:
        if key in st.session_state:
            del st.session_state[key]
    
    # Preferências alimentares
    preferencias_keys = [
        'vegetariano_input', 'vegano_input', 'ovo_lacto_input', 'pesco_vegetariano_input'
    ]
    for key in preferencias_keys:
        if key in st.session_state:
            del st.session_state[key]
    
    # Dados profissionais
    profissionais_keys = ['nome_nutri_input', 'crn_input']
    for key in profissionais_keys:
        if key in st.session_state:
            del st.session_state[key]
    
    # Dados da página principal
    principais_keys = [
        'sexo_input', 'atividade_input', 'meta_input',
        'cardapio_semanal', 'cardapio_editavel', 'sistema_cardapio'
    ]
    for key in principais_keys:
        if key in st.session_state:
            del st.session_state[key]
    
    # Limpar também os dados dos editores de cardápio
    for dia in DIAS_SEMANA:
        editor_key = f"editor_{dia}"
        if editor_key in st.session_state:
            del st.session_state[editor_key]
    
    # Limpar dados de PDF e outros
    outros_keys = ['gerar_pdf_lista', 'gerar_pdf']
    for key in outros_keys:
        if key in st.session_state:
            del st.session_state[key]

# --- INTERFACE PRINCIPAL ---
def main():
    # Inicializar session_state
    if 'cardapio_semanal' not in st.session_state:
        st.session_state.cardapio_semanal = {}
    if 'sistema_cardapio' not in st.session_state:
        st.session_state.sistema_cardapio = None
    if 'cardapio_editavel' not in st.session_state:
        st.session_state.cardapio_editavel = {}
    
    # Inicializar dados do paciente se não existirem
    if 'nome_paciente' not in st.session_state:
        st.session_state.nome_paciente = ""
    if 'peso' not in st.session_state:
        st.session_state.peso = 0.0
    if 'altura' not in st.session_state:
        st.session_state.altura = 0.0
    if 'idade' not in st.session_state:
        st.session_state.idade = 0
    
    # Carregar dados
    try:
        df_alimentos, df_receitas = carregar_dados_completos()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        df_alimentos, df_receitas = carregar_dados_fallback_alimentos(), carregar_dados_fallback_receitas()
    
    # Inicializar sistema de cardápio automático
    if st.session_state.sistema_cardapio is None:
        st.session_state.sistema_cardapio = SistemaCardapioAutomatico(df_receitas)
    
    # Sidebar
    with st.sidebar:
        st.header("🎯 Dados do Paciente")
        
        nome_paciente = st.text_input("Nome do Paciente", value=st.session_state.nome_paciente, placeholder="Digite o nome do paciente", key="nome_paciente_input")
        peso = st.number_input("Peso (kg)", min_value=0.0, value=st.session_state.peso, key="peso_input")
        altura = st.number_input("Altura (cm)", min_value=0.0, value=st.session_state.altura, key="altura_input")
        idade = st.number_input("Idade", min_value=0, value=st.session_state.idade, key="idade_input")
        
        # Atualizar session_state
        st.session_state.nome_paciente = nome_paciente
        st.session_state.peso = peso
        st.session_state.altura = altura
        st.session_state.idade = idade
        
        faixa_etaria = obter_faixa_etaria(idade) if idade > 0 else 'Não definida'
        st.info(f"**Faixa Etária:** {faixa_etaria}")
        
        sexo = st.selectbox("Sexo", SEXO_OPCOES, key="sexo_input")
        atividade = st.selectbox("Nível de Atividade", list(NAF_OPCOES.keys()), key="atividade_input")
        meta = st.selectbox("Meta Nutricional", META_OPCOES, key="meta_input")
        
        st.header("🥗 Tipo de Dieta")
        tipo_dieta = st.selectbox("Selecione o Tipo de Dieta", ['- Selecione -'] + list(TIPOS_DIETA.keys()), key="tipo_dieta_input")
        
        if tipo_dieta in TIPOS_DIETA:
            macros = TIPOS_DIETA[tipo_dieta]
            st.info(f"**Distribuição:** C:{macros['carbs']}% P:{macros['proteinas']}% G:{macros['gorduras']}%")
        
        st.header("🚫 Restrições Alimentares")
        celiaca = st.checkbox("Celíaco", value=False, key="celiaca_input")
        lactose = st.checkbox("Intolerante à Lactose", value=False, key="lactose_input")
        alergia_leite = st.checkbox("Alérgico a Leite", value=False, key="alergia_leite_input")
        alergia_ovo = st.checkbox("Alérgico a Ovo", value=False, key="alergia_ovo_input")
        alergia_oleaginosas = st.checkbox("Alérgico a Oleaginosas", value=False, key="alergia_oleaginosas_input")
        diabetico = st.checkbox("Diabético", value=False, key="diabetico_input")
        hipertenso = st.checkbox("Hipertenso", value=False, key="hipertenso_input")
        
        st.header("🥦 Preferências Alimentares")
        vegetariano = st.checkbox("Vegetariano", value=False, key="vegetariano_input")
        vegano = st.checkbox("Vegano", value=False, key="vegano_input")
        ovo_lacto_vegetariano = st.checkbox("Ovo-Lacto Vegetariano", value=False, key="ovo_lacto_input")
        pesco_vegetariano = st.checkbox("Pesco-Vegetariano", value=False, key="pesco_vegetariano_input")
        
        st.header("👩‍⚕️ Dados Profissionais")
        nome_nutri = st.text_input("Nome do Nutricionista", value="", placeholder="Digite o nome do nutricionista", key="nome_nutri_input")
        crn = st.text_input("CRN", value="", placeholder="Digite o CRN", key="crn_input")
        
        # Botão Limpar Todos os Dados
        st.markdown("---")
        if st.button("🔴 Limpar Todos os Dados", type="secondary", key="limpar_dados"):
            limpar_todos_dados()
            st.success("✅ Todos os dados foram limpos!")
            st.rerun()

    # =========================================================================
    # CORREÇÃO DA INTERAÇÃO: USAR session_state DIRETAMENTE NAS ABAS
    # =========================================================================
    
    # Coletar dados do session_state (que são atualizados pela sidebar)
    nome_paciente = st.session_state.nome_paciente
    peso = st.session_state.peso
    altura = st.session_state.altura
    idade = st.session_state.idade
    
    # Coletar dados dos widgets da sidebar
    sexo = st.session_state.sexo_input if 'sexo_input' in st.session_state else '- Selecione -'
    atividade = st.session_state.atividade_input if 'atividade_input' in st.session_state else '- Selecione -'
    meta = st.session_state.meta_input if 'meta_input' in st.session_state else '- Selecione -'
    tipo_dieta = st.session_state.tipo_dieta_input if 'tipo_dieta_input' in st.session_state else '- Selecione -'
    
    # Coletar restrições alimentares
    celiaca = st.session_state.celiaca_input if 'celiaca_input' in st.session_state else False
    lactose = st.session_state.lactose_input if 'lactose_input' in st.session_state else False
    alergia_leite = st.session_state.alergia_leite_input if 'alergia_leite_input' in st.session_state else False
    alergia_ovo = st.session_state.alergia_ovo_input if 'alergia_ovo_input' in st.session_state else False
    alergia_oleaginosas = st.session_state.alergia_oleaginosas_input if 'alergia_oleaginosas_input' in st.session_state else False
    diabetico = st.session_state.diabetico_input if 'diabetico_input' in st.session_state else False
    hipertenso = st.session_state.hipertenso_input if 'hipertenso_input' in st.session_state else False
    
    # Coletar preferências alimentares
    vegetariano = st.session_state.vegetariano_input if 'vegetariano_input' in st.session_state else False
    vegano = st.session_state.vegano_input if 'vegano_input' in st.session_state else False
    ovo_lacto_vegetariano = st.session_state.ovo_lacto_input if 'ovo_lacto_input' in st.session_state else False
    pesco_vegetariano = st.session_state.pesco_vegetariano_input if 'pesco_vegetariano_input' in st.session_state else False
    
    # Cálculos (AGORA usando dados atualizados do session_state)
    perfil = []
    if celiaca: perfil.append('Celíaco')
    if lactose: perfil.append('Lactose')
    if alergia_leite: perfil.append('Alérgico a Leite')
    if alergia_ovo: perfil.append('Alérgico a Ovo')
    if alergia_oleaginosas: perfil.append('Alérgico a Oleaginosas')
    if diabetico: perfil.append('Diabético')
    if hipertenso: perfil.append('Hipertenso')
    if vegetariano: perfil.append('Vegetariano')
    if vegano: perfil.append('Vegano')
    if ovo_lacto_vegetariano: perfil.append('Ovo-Lacto Vegetariano')
    if pesco_vegetariano: perfil.append('Pesco-Vegetariano')
    
    dados_validos = all([
        peso > 0, altura > 0, idade > 0, 
        sexo != '- Selecione -', 
        atividade != '- Selecione -',
        meta != '- Selecione -',
        tipo_dieta != '- Selecione -'
    ])
    
    # Cálculos nutricionais (SEMPRE atualizados)
    if dados_validos:
        imc, classificacao = calcular_imc_e_classificar(peso, altura)
        tmb = calcular_tmb(peso, altura, idade, sexo)
        
        tge = tmb * NAF_OPCOES[atividade]
        if meta == 'Perda de Peso':
            tge = max(tmb * 1.8, tge - 300)
        elif meta == 'Ganho de Massa':
            tge += 500
        elif meta == 'Desempenho Esportivo':
            tge += 400
        
        cho_p, ptn_p, lip_p, cho_g, ptn_g, lip_g = calcular_macros_por_dieta(tge, tipo_dieta)
        
        hidratacao = calcular_hidratacao_basica(peso)
        
        suplementos_recomendados = obter_suplementos_recomendados(meta, tipo_dieta)
        lista_compras_recomendada = obter_lista_compras_recomendada(st.session_state.cardapio_semanal, tipo_dieta, meta)
    else:
        imc = classificacao = tmb = tge = hidratacao = 0
        cho_p = ptn_p = lip_p = cho_g = ptn_g = lip_g = 0
        suplementos_recomendados = set()
        lista_compras_recomendada = set()
    
    # Layout principal (AGORA sempre mostra dados atualizados)
    st.header("📊 Avaliação do Paciente")
    if nome_paciente:
        st.subheader(f"Paciente: {nome_paciente}")
        if idade > 0:
            st.caption(f"Faixa Etária: {faixa_etaria}")
    
    # Métricas (SEMPRE atualizadas)
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("IMC", f"{imc:.1f}", classificacao)
    col2.metric("TGE Diário", f"{tge:.0f} kcal")
    col3.metric("Hidratação", f"{hidratacao:.0f} ml")
    col4.metric("Tipo de Dieta", tipo_dieta)
    col5.metric("Macros", f"C:{cho_p}% P:{ptn_p}% G:{lip_p}%")
    col6.metric("Meta", meta)
    
    # Abas principais (AGORA sempre com dados atualizados)
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🎯 Cardápio Automático", "🥗 Tipos de Dieta", "💪 Plano de Atividade", 
        "💊 Suplementação", "🛒 Lista de Compras", "📊 Relatório PDF"
    ])
    
    with tab1:
        st.header("🍽️ Sistema de Cardápio Automático")
        
        if perfil:
            st.info(f"**Perfil com restrições:** {', '.join(perfil)}")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("📊 Otimizar Cardápio por Meta", type="primary", key="otimizar_cardapio", use_container_width=True):
                if not dados_validos:
                    st.error("❌ Preencha todos os dados primeiro")
                else:
                    with st.spinner("Otimizando cardápio..."):
                        cardapio_otimizado = {}
                        for dia in DIAS_SEMANA:
                            cardapio_dia = otimizar_cardapio(
                                df_receitas, tge, cho_g, ptn_g, perfil, tipo_dieta
                            )
                            if cardapio_dia is not None:
                                cardapio_otimizado[dia] = cardapio_dia
                        
                        if cardapio_otimizado:
                            st.session_state.cardapio_semanal = cardapio_otimizado
                            st.success("✅ Cardápio otimizado gerado com sucesso!")
        
        with col2:
            if st.button("🔄 Gerar Cardápio Semanal Sem Repetições", type="secondary", key="gerar_cardapio", use_container_width=True):
                if not dados_validos:
                    st.error("❌ Preencha todos os dados do paciente primeiro")
                else:
                    with st.spinner("Gerando cardápio sem repetições..."):
                        cardapio_semanal = st.session_state.sistema_cardapio.gerar_cardapio_semanal_sem_repeticao(
                            tipo_dieta, perfil
                        )
                        if cardapio_semanal:
                            st.session_state.cardapio_semanal = cardapio_semanal
                            st.session_state.cardapio_editavel = {}
                            for dia in DIAS_SEMANA:
                                if dia in cardapio_semanal:
                                    st.session_state.cardapio_editavel[dia] = []
                                    for refeicao_info in REFEICOES_ORGANIZADAS:
                                        tipo_refeicao = refeicao_info["tipo"]
                                        horario = refeicao_info["horario"]
                                        if tipo_refeicao in cardapio_semanal[dia]:
                                            receita = cardapio_semanal[dia][tipo_refeicao]['receita']
                                            st.session_state.cardapio_editavel[dia].append({
                                                'tipo_refeicao': tipo_refeicao,
                                                'horario': horario,
                                                'alimento': receita['Nome_Receita'],
                                                'calorias': receita['Total_Calorias'],
                                                'carboidratos': receita['Macro_Carboidratos'],
                                                'proteinas': receita['Macro_Proteinas'],
                                                'gorduras': receita['Macro_Lipidios']
                                            })
                            st.success("✅ Cardápio semanal gerado com sucesso!")
                        else:
                            st.error("❌ Não foi possível gerar cardápio. Tente ajustar as restrições.")
        
        if 'cardapio_editavel' in st.session_state and st.session_state.cardapio_editavel:
            st.subheader("📅 Cardápio Semanal Editável")
            
            for dia in DIAS_SEMANA:
                with st.expander(f"📅 {dia}", expanded=False):
                    if dia in st.session_state.cardapio_editavel:
                        st.write(f"**Cardápio - {dia}**")
                        
                        df_dia = pd.DataFrame(st.session_state.cardapio_editavel[dia])
                        
                        edited_df = st.data_editor(
                            df_dia,
                            key=f"editor_{dia}",
                            num_rows="dynamic",
                            use_container_width=True,
                            column_config={
                                "tipo_refeicao": st.column_config.SelectboxColumn(
                                    "Tipo Refeição",
                                    options=[refeicao["tipo"] for refeicao in REFEICOES_ORGANIZADAS],
                                    required=True
                                ),
                                "horario": st.column_config.TextColumn(
                                    "Horário",
                                    required=True
                                ),
                                "alimento": st.column_config.TextColumn(
                                    "Alimento",
                                    required=True
                                ),
                                "calorias": st.column_config.NumberColumn(
                                    "Calorias",
                                    min_value=0
                                ),
                                "carboidratos": st.column_config.NumberColumn(
                                    "Carboidratos (g)",
                                    min_value=0
                                ),
                                "proteinas": st.column_config.NumberColumn(
                                    "Proteínas (g)",
                                    min_value=0
                                ),
                                "gorduras": st.column_config.NumberColumn(
                                    "Gorduras (g)",
                                    min_value=0
                                )
                            }
                        )
                        
                        col_btn1, col_btn2 = st.columns([1, 1])
                        with col_btn1:
                            if st.button(f"➕ Inserir Linha", key=f"add_{dia}", use_container_width=True):
                                st.session_state.cardapio_editavel[dia].append({
                                    'tipo_refeicao': 'Café da Manhã',
                                    'horario': '07:00',
                                    'alimento': '',
                                    'calorias': 0,
                                    'carboidratos': 0,
                                    'proteinas': 0,
                                    'gorduras': 0
                                })
                                st.rerun()
                        
                        with col_btn2:
                            if st.button(f"➖ Excluir Última Linha", key=f"del_{dia}", use_container_width=True):
                                if st.session_state.cardapio_editavel[dia]:
                                    st.session_state.cardapio_editavel[dia].pop()
                                    st.rerun()
                        
                        st.session_state.cardapio_editavel[dia] = edited_df.to_dict('records')
                        
                        total_cal = sum(item['calorias'] for item in st.session_state.cardapio_editavel[dia])
                        total_cho = sum(item['carboidratos'] for item in st.session_state.cardapio_editavel[dia])
                        total_ptn = sum(item['proteinas'] for item in st.session_state.cardapio_editavel[dia])
                        total_lip = sum(item['gorduras'] for item in st.session_state.cardapio_editavel[dia])
                        
                        st.metric(f"Totais {dia}", f"{total_cal:.0f} kcal", 
                                 f"C: {total_cho:.0f}g | P: {total_ptn:.0f}g | G: {total_lip:.0f}g")
                    else:
                        st.warning("Nenhum cardápio disponível para este dia")
    
    with tab2:
        st.header("🥗 Tipos de Dieta - Informações Detalhadas")
        
        dieta_selecionada = st.selectbox("Selecione uma dieta para ver detalhes", list(TIPOS_DIETA.keys()), key="dieta_detalhes")
        
        if dieta_selecionada:
            recomendacoes = obter_recomendacoes_dieta(dieta_selecionada)
            macros = TIPOS_DIETA[dieta_selecionada]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📋 Informações Gerais")
                st.info(f"**Descrição:** {recomendacoes['descricao']}")
                
                st.subheader("📊 Distribuição de Macros")
                st.metric("Carboidratos", f"{macros['carbs']}%")
                st.metric("Proteínas", f"{macros['proteinas']}%")
                st.metric("Gorduras", f"{macros['gorduras']}%")
            
            with col2:
                st.subheader("✅ Alimentos Recomendados")
                for alimento in recomendacoes['alimentos_recomendados']:
                    st.checkbox(alimento, value=True, key=f"rec_{alimento}")
                
                st.subheader("❌ Alimentos a Evitar")
                for alimento in recomendacoes['alimentos_evitar']:
                    st.checkbox(alimento, value=False, key=f"ev_{alimento}")
            
            st.subheader("💡 Dicas Importantes")
            for dica in recomendacoes['dicas']:
                st.write(f"• {dica}")
    
    with tab3:
        st.header("💪 Plano de Atividade Física")
        
        if dados_validos:
            if meta == 'Desempenho Esportivo':
                st.success("⚽ Plano de Treino para Desempenho")
                st.write("• **Treino específico:** 3-4x por semana")
                st.write("• **Condicionamento:** 2x por semana")
                st.write("• **Mobilidade:** Diária")
                st.write("• **Descanso ativo:** 1-2x por semana")
                
            elif meta == 'Perda de Peso':
                st.success("💪 Plano de Treino para Perda de Peso")
                st.write("• **Cardio:** 4-5x por semana (30-45 min)")
                st.write("• **Musculação:** 3x por semana")
                st.write("• **HIIT:** 2x por semana")
                st.write("• **Caminhada:** Diária (10.000 passos)")
                
            elif meta == 'Ganho de Massa':
                st.success("🏋️‍♂️ Plano de Treino para Hipertrofia")
                st.write("• **Musculação:** 4-5x por semana")
                st.write("• **Descanso:** 48h entre grupos musculares")
                st.write("• **Cardio leve:** 2-3x por semana (20-30 min)")
                st.write("• **Alongamento:** Diário")
                
            else:  # Controle de peso
                st.success("⚖️ Plano de Atividade para Controle de Peso")
                st.write("• **Atividade moderada:** 5x por semana (30 min)")
                st.write("• **Musculação:** 2-3x por semana")
                st.write("• **Alongamento:** Diário")
                st.write("• **Atividades recreativas:** Finais de semana")
        else:
            st.info("Preencha os dados do paciente para ver o plano de atividade")
    
    with tab4:
        st.header("💊 Suplementação Recomendada")
        
        if dados_validos:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("💊 Suplementos por Categoria")
                
                suplementos_categorias = {
                    'Proteínas': ['Whey Protein (30-40g)', 'Proteína Vegetal (30-40g)'],
                    'Aminoácidos': ['BCAA (5-10g)', 'Glutamina (5g)', 'Creatina (5g)'],
                    'Vitaminas e Minerais': ['Multivitamínico', 'Ômega-3 (2-3g)', 'Vitamina D (2000-4000UI)', 'Magnésio (400mg)'],
                    'Energia e Performance': ['Cafeína (3-6mg/kg)', 'Eletrólitos', 'Termogênicos']
                }
                
                for categoria, sups in suplementos_categorias.items():
                    with st.expander(f"{categoria}"):
                        for sup in sups:
                            sup_base = sup.split(' (')[0].lower()
                            is_recomendado = any(sup_base in rec.lower() for rec in suplementos_recomendados)
                            st.checkbox(sup, value=is_recomendado, key=f"sup_{categoria}_{sup}")
            
            with col2:
                st.subheader("🎯 Recomendações Personalizadas")
                st.info(f"**Meta:** {meta}")
                st.info(f"**Tipo de Dieta:** {tipo_dieta}")
                st.info(f"**Nível de Atividade:** {atividade}")
                
                st.subheader("💡 Suplementos Recomendados")
                if suplementos_recomendados:
                    for sup in sorted(suplementos_recomendados):
                        st.write(f"• {sup}")
                else:
                    st.info("Nenhum suplemento específico recomendado para seu perfil")
        else:
            st.info("Preencha os dados do paciente para ver a suplementação")
    
    with tab5:
        st.header("🛒 Lista de Compras Inteligente")
        
        if dados_validos:
            st.success("📋 Lista de compras personalizada para seu plano")
            
            categorias_compras = {
                'Proteínas': ['Frango', 'Peixe', 'Ovos', 'Whey Protein', 'Iogurte Grego', 'Queijo Cottage', 'Salmão', 'Tofu', 'Leguminosas'],
                'Carboidratos Complexos': ['Aveia', 'Batata Doce', 'Quinoa', 'Arroz Integral', 'Pão Integral', 'Massa Integral', 'Tapioca'],
                'Carboidratos Rápidos': ['Banana', 'Mel', 'Frutas Secas', 'Bebidas Esportivas'],
                'Gorduras Saudáveis': ['Abacate', 'Castanhas', 'Azeite de Oliva', 'Sementes (chia, linhaça)', 'Nozes'],
                'Vegetais': ['Espinafre', 'Brócolis', 'Couve', 'Pimentão', 'Tomate', 'Cenoura', 'Vegetais variados'],
                'Hidratação': ['Água de Coco', 'Bebidas Esportivas', 'Água Mineral'],
                'Suplementos': list(suplementos_recomendados) if suplementos_recomendados else ['Whey Protein', 'Creatina', 'BCAA', 'Multivitamínico']
            }
            
            lista_compras_selecionados = []
            
            for categoria, itens in categorias_compras.items():
                with st.expander(f"📋 {categoria}"):
                    for item in itens:
                        is_recomendado = any(item.lower() in rec.lower() for rec in lista_compras_recomendada)
                        if st.checkbox(item, value=is_recomendado, key=f"compra_{categoria}_{item}"):
                            lista_compras_selecionados.append(item)
            
            # BOTÃO PARA GERAR PDF DA LISTA DE COMPRAS (SIMPLIFICADO)
            if lista_compras_selecionados:
                st.markdown("---")
                col1, col2 = st.columns([1, 2])
                with col1:
                    if st.button("📄 Gerar PDF da Lista de Compras", type="primary", key="gerar_pdf_lista"):
                        with st.spinner("Gerando PDF da lista de compras..."):
                            try:
                                dados_paciente_pdf = {
                                    'nome': nome_paciente,
                                    'peso': peso,
                                    'altura': altura,
                                    'idade': idade,
                                    'faixa_etaria': faixa_etaria,
                                    'imc': imc,
                                    'classificacao_imc': classificacao,
                                    'meta': meta
                                }
                                
                                pdf_bytes = gerar_pdf_lista_compras(
                                    lista_compras_selecionados,
                                    dados_paciente_pdf,
                                    tipo_dieta
                                )
                                
                                if pdf_bytes:
                                    pdf_output = f"lista_compras_{nome_paciente.replace(' ', '_')}.pdf"
                                    
                                    st.download_button(
                                        label="📥 Download da Lista de Compras",
                                        data=pdf_bytes,
                                        file_name=pdf_output,
                                        mime="application/pdf",
                                        type="primary"
                                    )
                                    
                                    st.success("✅ PDF da lista de compras gerado com sucesso!")
                                else:
                                    st.error("❌ Falha ao gerar PDF da lista")
                                
                            except Exception as e:
                                st.error(f"❌ Erro ao gerar PDF da lista: {str(e)}")
                with col2:
                    st.info("💡 Clique no botão para gerar um PDF da sua lista de compras.")
            else:
                st.info("💡 Selecione os itens da lista de compras para habilitar a geração do PDF.")
        else:
            st.info("Preencha os dados do paciente para ver a lista de compras")
    
    with tab6:
        st.header("📊 Relatório Completo em PDF")
        
        cardapio_existe = (
            'cardapio_editavel' in st.session_state and 
            st.session_state.cardapio_editavel and
            isinstance(st.session_state.cardapio_editavel, dict) and
            len(st.session_state.cardapio_editavel) > 0
        )
        
        if dados_validos and cardapio_existe:
            if nome_nutri and crn:
                if st.button("📄 Gerar Relatório PDF", type="primary", key="gerar_pdf"):
                    with st.spinner("Gerando relatório PDF..."):
                        try:
                            dados_paciente = {
                                'nome': nome_paciente,
                                'peso': peso,
                                'altura': altura,
                                'idade': idade,
                                'faixa_etaria': faixa_etaria,
                                'imc': imc,
                                'classificacao_imc': classificacao,
                                'tge': tge,
                                'cho_p': cho_p,
                                'ptn_p': ptn_p,
                                'lip_p': lip_p,
                                'hidratacao': hidratacao
                            }
                            
                            cardapio_semanal_pdf = {}
                            for dia in DIAS_SEMANA:
                                if dia in st.session_state.cardapio_semanal:
                                    cardapio_semanal_pdf[dia] = {}
                                    for refeicao_info in REFEICOES_ORGANIZADAS:
                                        tipo_refeicao = refeicao_info["tipo"]
                                        if tipo_refeicao in st.session_state.cardapio_semanal[dia]:
                                            receita_data = st.session_state.cardapio_semanal[dia][tipo_refeicao]['receita']
                                            cardapio_semanal_pdf[dia][tipo_refeicao] = {
                                                'receita': receita_data
                                            }
                            
                            pdf_bytes = gerar_pdf_com_xhtml2pdf(
                                dados_paciente, 
                                cardapio_semanal_pdf,
                                nome_nutri,
                                crn,
                                tipo_dieta,
                                meta
                            )
                            
                            if pdf_bytes:
                                pdf_output = f"plano_nutricional_{nome_paciente.replace(' ', '_')}.pdf"
                                
                                st.download_button(
                                    label="📥 Download do Relatório Completo",
                                    data=pdf_bytes,
                                    file_name=pdf_output,
                                    mime="application/pdf",
                                    type="primary"
                                )
                                
                                st.success("✅ PDF gerado com sucesso! Clique no botão acima para fazer o download.")
                            else:
                                st.error("❌ Falha ao gerar PDF")
                            
                        except Exception as e:
                            st.error(f"❌ Erro ao gerar PDF: {str(e)}")
                            st.info("💡 Dica: Verifique se todos os campos estão preenchidos corretamente.")
            else:
                st.warning("⚠️ Preencha os dados do nutricionista (Nome e CRN)")
        else:
            st.warning("⚠️ Preencha todos os dados do paciente e gere o cardápio primeiro")
    
    # Rodapé
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; margin-top: 4rem; padding: 2rem 0; color: #666; border-top: 1px solid #e0e0e0; width: 100%;">
        <div style="font-weight: bold; font-size: 1.1rem; margin-bottom: 0.5rem;">
            © 2025 Data Analysis Cattapan. Todos os direitos reservados.
        </div>
        <div style="font-size: 0.9rem; opacity: 0.8;">
            Sistema desenvolvido para nutricionistas | 🥗 Nutrição Convencional | 🏊‍♂️🚴‍♂️🏃‍♂️ Nutrição para Triatletas
        </div>
    </div>
    """, unsafe_allow_html=True)
     
if __name__ == "__main__":
    main()




