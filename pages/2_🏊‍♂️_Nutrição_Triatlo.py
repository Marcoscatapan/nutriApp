# Triatlo - SISTEMA DE NUTRIÇÃO PARA TRIATLETAS CORRIGIDO
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
import json

# PRIMEIRA LINHA após os imports
st.set_page_config(
    page_title="🏊‍♂️ Nutrição Triatlo", 
    page_icon="🏊‍♂️",
    layout="wide"
)

# =============================================================================
# CONFIGURAÇÃO E CONSTANTES - TRIATLO + CONVENCIONAL
# =============================================================================

# URLs do Google Drive
RECEITAS_URL = "https://drive.google.com/file/d/1VN4aGOjqsX0fdhN2H2OAVBL21jIjJy4V/view?usp=sharing"
ALIMENTOS_URL = "https://drive.google.com/file/d/1NKptsdF_dFGV9i4j6VYGCTP9PkrJIZV/view?usp=sharing"

DIAS_SEMANA = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]

# --- SISTEMA DE REFEIÇÕES ORGANIZADAS ---
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

# --- TIPOS OF DIETA ---
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

# --- OPÇÕES TRIATLO ---
NIVEIS_TRIATLO = ["Iniciante", "Intermediário", "Avançado", "Profissional"]
DISTANCIAS_TRIATLO = ["Sprint", "Olímpico", "Ironman 70.3", "Ironman Completo"]

# =============================================================================
# CSS PERSONALIZADO - TRIATLO
# =============================================================================

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .section-header {
        font-size: 1.5rem;
        color: #A23B72;
        margin: 1.5rem 0 1rem 0;
        border-bottom: 2px solid #A23B72;
        padding-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #2E86AB;
        margin: 0.5rem 0;
    }
    .editavel {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
    }
    .pdf-button {
        width: 50% !important;
        margin: 0 auto !important;
        display: block !important;
    }
    .sidebar-section {
        margin-bottom: 2rem;
    }
    .historico-item {
        background-color: #f8f9fa;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
        border-left: 4px solid #28a745;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# FUNÇÕES DO SISTEMA TRIATLO (MANTIDAS ORIGINAIS)
# =============================================================================

def inicializar_dados_triatlo():
    """Inicializa os dados específicos para triatlo"""
    if 'dados_triatlo' not in st.session_state:
        st.session_state.dados_triatlo = {
            'periodizacao': {},
            'timing_nutricional': {},
            'brick_training': {},
            'carb_loading': {},
            'hidratacao': {},
            'suplementacao': {},
            'monitoramento': {},
            'competicoes': {},
            'volume_intensidade': {},
            'analise_dados': {}
        }

def analisar_cardapio_triatlo(cardapio_semanal, tge_alvo, distancia, peso):
    """Analisa o cardápio semanal em relação às necessidades do triatlo"""
    if not cardapio_semanal:
        return {"status": "vazio", "mensagem": "Nenhum cardápio gerado"}
    
    # Calcular totais semanais
    totais_semana = {
        'calorias': 0,
        'carboidratos': 0,
        'proteinas': 0,
        'gorduras': 0
    }
    
    dias_com_cardapio = 0
    
    for dia, cardapio_dia in cardapio_semanal.items():
        if hasattr(cardapio_dia, 'empty'):
            if not cardapio_dia.empty:
                dias_com_cardapio += 1
                for _, receita in cardapio_dia.iterrows():
                    totais_semana['calorias'] += receita.get('Total_Calorias', 0)
                    totais_semana['carboidratos'] += receita.get('Macro_Carboidratos', 0)
                    totais_semana['proteinas'] += receita.get('Macro_Proteinas', 0)
                    totais_semana['gorduras'] += receita.get('Macro_Lipidios', 0)
        elif cardapio_dia and isinstance(cardapio_dia, dict) and len(cardapio_dia) > 0:
            dias_com_cardapio += 1
            for refeicao_info in REFEICOES_ORGANIZADAS:
                tipo_refeicao = refeicao_info["tipo"]
                if tipo_refeicao in cardapio_dia:
                    receita = cardapio_dia[tipo_refeicao]['receita']
                    totais_semana['calorias'] += receita.get('Total_Calorias', 0)
                    totais_semana['carboidratos'] += receita.get('Macro_Carboidratos', 0)
                    totais_semana['proteinas'] += receita.get('Macro_Proteinas', 0)
                    totais_semana['gorduras'] += receita.get('Macro_Lipidios', 0)
    
    if dias_com_cardapio == 0:
        return {"status": "vazio", "mensagem": "Cardápio vazio"}
    
    # Calcular médias diárias
    media_diaria = {
        'calorias': totais_semana['calorias'] / dias_com_cardapio,
        'carboidratos': totais_semana['carboidratos'] / dias_com_cardapio,
        'proteinas': totais_semana['proteinas'] / dias_com_cardapio,
        'gorduras': totais_semana['gorduras'] / dias_com_cardapio
    }
    
    # Análise de adequação
    diferenca_calorias = ((media_diaria['calorias'] - tge_alvo) / tge_alvo) * 100
    
    # Recomendações por distância
    recomendacoes_carb = {
        "Sprint": 5,  # g/kg
        "Olímpico": 6,
        "Ironman 70.3": 7,
        "Ironman Completo": 8
    }
    
    carb_recomendado = recomendacoes_carb.get(distancia, 6)
    carb_atual = (media_diaria['carboidratos'] / peso) if peso > 0 else 0
    
    # Avaliação
    status = "adequado"
    if abs(diferenca_calorias) > 15:
        status = "ajuste_necesario"
    elif carb_atual < carb_recomendado * 0.8:
        status = "carb_insuficiente"
    
    return {
        "status": status,
        "media_diaria": media_diaria,
        "diferenca_calorias": diferenca_calorias,
        "carb_atual": carb_atual,
        "carb_recomendado": carb_recomendado,
        "dias_analisados": dias_com_cardapio
    }

# =============================================================================
# FUNÇÕES ESPECÍFICAS DO TRIATLO - COM EDIÇÃO
# =============================================================================

def calcular_necessidades_triatlo(peso, altura, idade, sexo, nivel, distancia, fator_calorico=1.15):
    """Calcula necessidades específicas para triatletas com fator personalizável"""
    # Cálculo base
    tmb = calcular_tmb(peso, altura, idade, sexo)
    
    # Ajustes por nível
    fatores_nivel = {
        "Iniciante": 1.7,
        "Intermediário": 1.9,
        "Avançado": 2.1,
        "Profissional": 2.3
    }
    
    # Ajustes por distância
    ajustes_distancia = {
        "Sprint": 1.0,
        "Olímpico": 1.1,
        "Ironman 70.3": 1.2,
        "Ironman Completo": 1.3
    }
    
    # Fator personalizável para desempenho esportivo
    fator_triatlo = (fatores_nivel.get(nivel, 1.8) * 
                     ajustes_distancia.get(distancia, 1.0) * 
                     fator_calorico)
    
    tge_triatlo = tmb * fator_triatlo
    
    return tge_triatlo

def obter_estrategia_periodizacao(nivel, distancia, semanas_treino=None):
    """Retorna estratégia de periodização baseada no nível e distância com semanas personalizáveis"""
    
    if semanas_treino is None:
        # Semanas padrão baseadas no nível e distância
        semanas_config = {
            "Iniciante": {
                "Sprint": "8-12 semanas",
                "Olímpico": "12-16 semanas",
                "Ironman 70.3": "Não recomendado",
                "Ironman Completo": "Não recomendado"
            },
            "Intermediário": {
                "Sprint": "8-10 semanas",
                "Olímpico": "12-16 semanas", 
                "Ironman 70.3": "20-24 semanas",
                "Ironman Completo": "24-28 semanas"
            },
            "Avançado": {
                "Sprint": "6-8 semanas",
                "Olímpico": "10-12 semanas",
                "Ironman 70.3": "16-20 semanas", 
                "Ironman Completo": "20-24 semanas"
            },
            "Profissional": {
                "Sprint": "4-6 semanas",
                "Olímpico": "8-10 semanas",
                "Ironman 70.3": "12-16 semanas",
                "Ironman Completo": "16-20 semanas"
            }
        }
        semanas = semanas_config.get(nivel, {}).get(distancia, "12-16 semanas")
    else:
        semanas = f"{semanas_treino} semanas"
    
    estrategias = {
        "Iniciante": {
            "Sprint": f"Foco em adaptação - {semanas}, ênfase em técnica",
            "Olímpico": f"Periodização linear - {semanas}",
            "Ironman 70.3": "Não recomendado para iniciantes",
            "Ironman Completo": "Não recomendado para iniciantes"
        },
        "Intermediário": {
            "Sprint": f"Periodização por blocos - {semanas}",
            "Olímpico": f"Periodização linear - {semanas}", 
            "Ironman 70.3": f"Periodização tradicional - {semanas}",
            "Ironman Completo": f"Periodização tradicional - {semanas}"
        },
        "Avançado": {
            "Sprint": f"Periodização inversa - {semanas}",
            "Olímpico": f"Periodização por blocos - {semanas}",
            "Ironman 70.3": f"Periodização por blocos - {semanas}", 
            "Ironman Completo": f"Periodização por blocos - {semanas}"
        },
        "Profissional": {
            "Sprint": f"Periodização por blocos - {semanas}",
            "Olímpico": f"Periodização por blocos - {semanas}",
            "Ironman 70.3": f"Periodização integrada - {semanas}",
            "Ironman Completo": f"Periodização integrada - {semanas}"
        }
    }
    
    return estrategias.get(nivel, {}).get(distancia, f"Estratégia não definida - {semanas}")

def obter_timing_nutricional(distancia, carb_pre_treino=None, carb_durante=None, liquidos_durante=None):
    """Retorna estratégias de timing nutricional personalizáveis"""
    
    if carb_pre_treino is None:
        carb_pre_treino = {
            "Sprint": "200-300kcal",
            "Olímpico": "300-400kcal", 
            "Ironman 70.3": "400-600kcal",
            "Ironman Completo": "600-800kcal"
        }
    
    if carb_durante is None:
        carb_durante = {
            "Sprint": "30-45g/hora",
            "Olímpico": "45-60g/hora",
            "Ironman 70.3": "60-90g/hora",
            "Ironman Completo": "60-90g/hora"
        }
    
    if liquidos_durante is None:
        liquidos_durante = {
            "Sprint": "500-750ml/hora",
            "Olímpico": "750-1000ml/hora",
            "Ironman 70.3": "1000-1500ml/hora", 
            "Ironman Completo": "1000-1500ml/hora"
        }
    
    return {
        "pre_treino": f"Refeição sólida 3-4h antes ({carb_pre_treino.get(distancia, '300-400kcal')} de carboidratos)",
        "durante": f"{carb_durante.get(distancia, '45-60g/hora')} carboidratos + {liquidos_durante.get(distancia, '750-1000ml/hora')} líquidos",
        "pos_treino": "Proteína 0.3g/kg + carboidratos 1g/kg em até 30min após"
    }

def obter_estrategia_carb_loading(distancia, dias_antes=None, carb_por_kg=None):
    """Retorna estratégias de carb loading personalizáveis"""
    
    if dias_antes is None:
        dias_antes = {
            "Sprint": "2 dias antes",
            "Olímpico": "3 dias antes",
            "Ironman 70.3": "3 dias antes",
            "Ironman Completo": "3-4 dias antes"
        }
    
    if carb_por_kg is None:
        carb_por_kg = {
            "Sprint": "3-4g/kg/dia",
            "Olímpico": "5-6g/kg/dia", 
            "Ironman 70.3": "6-8g/kg/dia",
            "Ironman Completo": "8-10g/kg/dia"
        }
    
    return f"Carb loading por {dias_antes.get(distancia, '3 dias')} com {carb_por_kg.get(distancia, '5-6g/kg/dia')} de carboidratos"

def calcular_hidratacao_triatlo(peso, distancia, ml_por_kg=35):
    """Calcula hidratação específica para triatletas"""
    hidratacao_base = peso * ml_por_kg
    
    # Ajuste por distância
    ajustes_distancia = {
        "Sprint": 1.0,
        "Olímpico": 1.2,
        "Ironman 70.3": 1.4,
        "Ironman Completo": 1.6
    }
    
    return hidratacao_base * ajustes_distancia.get(distancia, 1.2)

def obter_suplementacao_triatlo(nivel, distancia, suplementos_personalizados=None):
    """Retorna suplementação específica para triatletas"""
    
    suplementos_base = [
        "Bebida Esportiva",
        "Géis de Carboidrato", 
        "Eletrólitos",
        "BCAA"
    ]
    
    if nivel in ["Avançado", "Profissional"]:
        suplementos_base.extend([
            "Beta-alanina",
            "Creatina", 
            "Cafeína"
        ])
    
    if distancia in ["Ironman 70.3", "Ironman Completo"]:
        suplementos_base.extend([
            "Barras Energéticas",
            "Sal em Cápsulas"
        ])
    
    if suplementos_personalizados:
        suplementos_base.extend(suplementos_personalizados)
    
    return suplementos_base

# =============================================================================
# SISTEMA DE CARDÁPIO AUTOMÁTICO (CONVENCIONAL)
# =============================================================================

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

# =============================================================================
# FUNÇÕES PARA CARREGAR DADOS (CONVENCIONAL)
# =============================================================================

@st.cache_data(ttl=3600)
def carregar_csv_google_drive(url):
    """Carrega dados do Google Drive con tratamiento robusto"""
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
        df_receitas['Macro_Proteinas'] = df_receitas['Proteinas']
    
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

# =============================================================================
# FUNÇÕES DE CÁLCULO NUTRICIONAL (CONVENCIONAL)
# =============================================================================

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

def calcular_hidratacao_basica(peso_kg):
    """Calcula hidratação básica"""
    return peso_kg * 35

def calcular_macros_por_dieta(tge, tipo_dieta):
    """Calcula macros baseado no tipo de dieta selecionado"""
    if tipo_dieta not in TIPOS_DIETA:
        tipo_dieta = 'Equilibrada'
    
    macros_percent = TIPOS_DIETA[tipo_dieta]
    
    cho_g = (tge * macros_percent['carbs'] / 100) / 4
    ptn_g = (tge * macros_percent['proteinas'] / 100) / 4
    lip_g = (tge * macros_percent['gorduras'] / 100) / 9
    
    return macros_percent['carbs'], macros_percent['proteinas'], macros_percent['gorduras'], cho_g, ptn_g, lip_g

# =============================================================================
# FUNÇÕES ESPECÍFICAS PARA TIPOS OF DIETA (CONVENCIONAL)
# =============================================================================

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
            'alimentos_recomendados': ['Leguminosas', 'Grãos integras', 'Nozes', 'Sementes', 'Vegetais variados'],
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

# =============================================================================
# FUNÇÕES PARA INTERAÇÃO DAS ABAS (CONVENCIONAL)
# =============================================================================

def obter_suplementos_recomendados(tipo_dieta):
    """Retorna suplementos recomendados baseados no perfil do paciente"""
    suplementos_recomendados = set()
    
    base_suplementos = {
        'Whey Protein', 'Multivitamínico', 'Ômega-3', 'Vitamina D', 'Magnésio'
    }
    
    suplementos_recomendados.update(base_suplementos)
    
    # Para triatletas, sempre incluir suplementos de desempenho
    suplementos_recomendados.update(['BCAA', 'Creatina', 'Glutamina'])
    
    if tipo_dieta == 'Cetogênica':
        suplementos_recomendados.update(['Eletrólitos', 'Óleo MCT'])
    
    return suplementos_recomendados

def obter_lista_compras_recomendada(cardapio_semanal, tipo_dieta):
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
    
    # Para triatletas, sempre incluir bebidas esportivas
    alimentos_recomendados.update(['Bebidas Esportivas'])
    
    return alimentos_recomendados

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

# =============================================================================
# FUNÇÕES PARA GERAR PDF DO TRIATLO - CORRIGIDAS
# =============================================================================

def gerar_html_para_pdf_triatlo(dados_paciente, cardapio_semanal, nome_nutri, crn, tipo_dieta, nivel_triatlo, distancia_alvo, estrategias_triatlo):
    """Gera HTML formatado para conversão em PDF integrando triatlo - CORRIGIDA"""
    
    data_emissao = datetime.now().strftime("%d/%m/%Y")
    hora_emissao = datetime.now().strftime("%H:%M")
    
    nome_nutri_final = nome_nutri if nome_nutri else "Nutricionista"
    crn_final = crn if crn else "CRN"
    
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
        .triatlo-info {
            margin: 10px 0;
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
        .estrategia-item {
            margin: 8px 0;
            padding: 5px;
            background-color: #f8f9fa;
            border-radius: 3px;
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
    <title>Plano Nutricional - Triatlo - {dados_paciente['nome']}</title>
    {css}
</head>
<body>
    <div class="header">
        <h1>PLANO NUTRICIONAL PARA TRIATLO</h1>
        <h2>Personalizado para {dados_paciente['nome']}</h2>
    </div>
    
    <!-- 1. DADOS DO PACIENTE -->
    <div class="section-title">DADOS DO PACIENTE</div>
    <div class="paciente-info">
        <p><strong>Nome:</strong> {dados_paciente['nome']}</p>
        <p><strong>Idade:</strong> {dados_paciente['idade']} anos | <strong>Faixa Etária:</strong> {dados_paciente['faixa_etaria']}</p>
        <p><strong>Peso:</strong> {dados_paciente['peso']} kg | <strong>Altura:</strong> {dados_paciente['altura']} cm</p>
        <p><strong>IMC:</strong> {dados_paciente['imc']:.1f} - {dados_paciente['classificacao_imc']}</p>
        <p><strong>TGE:</strong> {dados_paciente['tge']:.0f} kcal</p>
        <p><strong>Tipo de Dieta:</strong> {tipo_dieta}</p>
        <p><strong>Macronutrientes:</strong> C{dados_paciente['cho_p']}% P{dados_paciente['ptn_p']}% G{dados_paciente['lip_p']}%</p>
        <p><strong>Hidratação:</strong> {dados_paciente['hidratacao']:.0f} ml/dia</p>
    </div>
    
    <!-- 2. CARDÁPIO SEMANAL -->
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
            
            if hasattr(cardapio_dia, 'empty'):
                if not cardapio_dia.empty:
                    for _, receita_data in cardapio_dia.iterrows():
                        html += f"""<div class="refeicao">
                            <span class="refeicao-tipo">{receita_data['Tipo_Refeicao']}:</span>
                            <span class="refeicao-nome">{receita_data['Nome_Receita']}</span>
                        </div>"""
                        
                        total_cal += receita_data.get('Total_Calorias', 0)
                        total_cho += receita_data.get('Macro_Carboidratos', 0)
                        total_ptn += receita_data.get('Macro_Proteinas', 0)
                        total_lip += receita_data.get('Macro_Lipidios', 0)
            elif isinstance(cardapio_dia, dict) and len(cardapio_dia) > 0:
                for refeicao_info in REFEICOES_ORGANIZADAS:
                    tipo_refeicao = refeicao_info["tipo"]
                    horario = refeicao_info["horario"]
                    
                    if tipo_refeicao in cardapio_dia:
                        receita_data = cardapio_dia[tipo_refeicao]['receita']
                        
                        html += f"""<div class="refeicao">
                            <span class="refeicao-tipo">{tipo_refeicao} ({horario}):</span>
                            <span class="refeicao-nome">{receita_data['Nome_Receita']}</span>
                        </div>"""
                        
                        total_cal += receita_data.get('Total_Calorias', 0)
                        total_cho += receita_data.get('Macro_Carboidratos', 0)
                        total_ptn += receita_data.get('Macro_Proteinas', 0)
                        total_lip += receita_data.get('Macro_Lipidios', 0)
            
            html += f"""<div class="totais-dia">
                <strong>TOTAIS DO DIA:</strong><br>
                Calorias: {total_cal:.0f} kcal | Carboidratos: {total_cho:.0f}g | Proteínas: {total_ptn:.0f}g | Gorduras: {total_lip:.0f}g
            </div>"""
        else:
            html += """<div class="refeicao">
                <div class="refeicao-info">Cardápio em ajuste - consulte nutricionista</div>
            </div>"""
        
        html += "</div>"
    
    html += f"""<div style="page-break-before: always;"></div>
    
    <!-- 3. INFORMAÇÕES ESPECÍFICAS DO TRIATLO -->
    <div class="section-title">INFORMAÇÕES ESPECÍFICAS DO TRIATLO</div>
    <div class="triatlo-info">
        <p><strong>Nível:</strong> {nivel_triatlo}</p>
        <p><strong>Distância Alvo:</strong> {distancia_alvo}</p>
        <p><strong>Meta:</strong> Desempenho Esportivo</p>
    </div>
    
    <!-- 4. ESTRATÉGIAS PARA TRIATLO -->
    <div class="section-title">ESTRATÉGIAS PARA TRIATLO</div>"""
    
    if estrategias_triatlo:
        for estrategia_nome, estrategia_desc in estrategias_triatlo.items():
            html += f"""
            <div class="estrategia-item">
                <strong>{estrategia_nome}:</strong> {estrategia_desc}
            </div>"""
    
    html += f"""
    <!-- 5. ORIENTAÇÕES ESPECÍFICAS PARA TRIATLO -->
    <div class="section-title">ORIENTAÇÕES ESPECÍFICAS PARA TRIATLO</div>
    <div class="orientacoes">
        <p>• Plano desenvolvido especificamente para triatletas</p>
        <p>• Mantenha hidratação adequada antes, durante e após treinos</p>
        <p>• Ajuste porções conforme intensidade do treino</p>
        <p>• Respeite o timing nutricional para cada disciplina</p>
        <p>• Monitore peso e composição corporal regularmente</p>
        <p>• Comunique desconfortos gastrointestinais durante exercícios</p>
        <p>• Acompanhamento regular com nutricionista especializado</p>
        <p>• Varie os alimentos dentro das opções permitidas</p>
    </div>
    
    <!-- 6. ASSINATURA -->
    <div class="assinatura-container">
        <div class="linha-assinatura"></div>
        <div class="assinatura-conteudo">
            <div class="assinatura-nome">{nome_nutri_final}</div>
            <div class="assinatura-crn">CRN: {crn_final}</div>
            <div class="assinatura-data">Data de emissão: {data_emissao} às {hora_emissao}</div>
        </div>
    </div>
</body>
</html>"""
    
    return html

def gerar_pdf_triatlo(dados_paciente, cardapio_semanal, nome_nutri, crn, tipo_dieta, nivel_triatlo, distancia_alvo):
    """Gera PDF integrado para triatlo - CORRIGIDA"""
    try:
        estrategias_triatlo = {
            "Periodização": obter_estrategia_periodizacao(nivel_triatlo, distancia_alvo),
            "Timing Nutricional": obter_timing_nutricional(distancia_alvo).get('pre_treino', 'Estratégia específica'),
            "Carb Loading": obter_estrategia_carb_loading(distancia_alvo),
            "Hidratação": f"{calcular_hidratacao_triatlo(dados_paciente['peso'], distancia_alvo):.0f} ml/dia"
        }
        
        html_content = gerar_html_para_pdf_triatlo(
            dados_paciente, cardapio_semanal, nome_nutri, crn, tipo_dieta, 
            nivel_triatlo, distancia_alvo, estrategias_triatlo
        )
        
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
        st.error(f"Erro ao gerar PDF do triatlo: {str(e)}")
        return None

# =============================================================================
# FUNÇÕES DE INTERFACE DO TRIATLO (MANTIDAS ORIGINAIS)
# =============================================================================

def mostrar_timing_nutricional_com_edicao(distancia):
    """Mostra estratégias de timing nutricional com edição"""
    st.header("⏱️ Timing Nutricional - Personalizável")
    
    with st.expander("⚙️ Configurar Timing Nutricional", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("🍽️ Pré-Treino")
            carb_pre_sprint = st.text_input("Sprint - kcal", "200-300kcal", key="carb_pre_sprint")
            carb_pre_olimpico = st.text_input("Olímpico - kcal", "300-400kcal", key="carb_pre_olimpico")
            carb_pre_ironman70 = st.text_input("Ironman 70.3 - kcal", "400-600kcal", key="carb_pre_ironman70")
            carb_pre_ironman = st.text_input("Ironman - kcal", "600-800kcal", key="carb_pre_ironman")
        
        with col2:
            st.subheader("⚡ Durante - Carboidratos")
            carb_durante_sprint = st.text_input("Sprint - g/hora", "30-45g", key="carb_durante_sprint")
            carb_durante_olimpico = st.text_input("Olímpico - g/hora", "45-60g", key="carb_durante_olimpico")
            carb_durante_ironman70 = st.text_input("Ironman 70.3 - g/hora", "60-90g", key="carb_durante_ironman70")
            carb_durante_ironman = st.text_input("Ironman - g/hora", "60-90g", key="carb_durante_ironman")
        
        with col3:
            st.subheader("💧 Durante - Líquidos")
            liquidos_sprint = st.text_input("Sprint - ml/hora", "500-750ml", key="liquidos_sprint")
            liquidos_olimpico = st.text_input("Olímpico - ml/hora", "750-1000ml", key="liquidos_olimpico")
            liquidos_ironman70 = st.text_input("Ironman 70.3 - ml/hora", "1000-1500ml", key="liquidos_ironman70")
            liquidos_ironman = st.text_input("Ironman - ml/hora", "1000-1500ml", key="liquidos_ironman")
    
    carb_pre_treino = {
        "Sprint": carb_pre_sprint,
        "Olímpico": carb_pre_olimpico,
        "Ironman 70.3": carb_pre_ironman70,
        "Ironman Completo": carb_pre_ironman
    }
    
    carb_durante = {
        "Sprint": carb_durante_sprint,
        "Olímpico": carb_durante_olimpico,
        "Ironman 70.3": carb_durante_ironman70,
        "Ironman Completo": carb_durante_ironman
    }
    
    liquidos_durante = {
        "Sprint": liquidos_sprint,
        "Olímpico": liquidos_olimpico,
        "Ironman 70.3": liquidos_ironman70,
        "Ironman Completo": liquidos_ironman
    }
    
    timing = obter_timing_nutricional(distancia, carb_pre_treino, carb_durante, liquidos_durante)
    
    if timing:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("🍽️ Pré-Treino")
            st.markdown(f'<div class="editavel">{timing["pre_treino"]}</div>', unsafe_allow_html=True)
            
        with col2:
            st.subheader("⚡ Durante")
            st.markdown(f'<div class="editavel">{timing["durante"]}</div>', unsafe_allow_html=True)
            
        with col3:
            st.subheader("🔄 Pós-Treino")
            st.markdown(f'<div class="editavel">{timing["pos_treino"]}</div>', unsafe_allow_html=True)
    
    st.subheader("📊 Recomendações por Distância")
    
    dados_timing = {
        "Distância": ["Sprint", "Olímpico", "Ironman 70.3", "Ironman Completo"],
        "Carboidratos/hora": [
            carb_durante_sprint, carb_durante_olimpico, 
            carb_durante_ironman70, carb_durante_ironman
        ],
        "Líquidos/hora": [
            liquidos_sprint, liquidos_olimpico,
            liquidos_ironman70, liquidos_ironman
        ],
        "Eletrólitos": ["Moderado", "Moderado", "Alto", "Muito Alto"]
    }
    
    df_timing = pd.DataFrame(dados_timing)
    st.dataframe(df_timing, use_container_width=True)

def mostrar_brick_training_com_edicao():
    """Mostra estratégias para brick training com edição"""
    st.header("🧱 Brick Training - Personalizável")
    st.subheader("🎯 O que é Brick Training?")
    st.info("Brick training são sessões de treino que combinam duas disciplinas consecutivas, simulando as transições do triatlo.")
    
    with st.expander("⚙️ Configurar Estratégias Nutricionais", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏊‍♂️→🚴‍♂️ Natação-Ciclismo")
            estrategia_natacao_ciclismo = st.text_area(
                "Estratégia Nutricional Natação→Ciclismo",
                "• Pré-natação: Carboidratos líquidos\n• Transição: Gel energético + água\n• Durante ciclismo: Bebida esportiva + géis",
                height=100,
                key="estrategia_natacao_ciclismo"
            )
            
        with col2:
            st.subheader("🚴‍♂️→🏃‍♂️ Ciclismo-Corrida")
            estrategia_ciclismo_corrida = st.text_area(
                "Estratégia Nutricional Ciclismo→Corrida", 
                "• Últimos 20min ciclismo: Reduza sólidos\n• Transição: Gel líquido + água\n• Durante corrida: Bebida esportiva",
                height=100,
                key="estrategia_ciclismo_corrida"
            )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏊‍♂️→🚴‍♂️ Natação-Ciclismo")
        st.markdown(f'<div class="editavel">{estrategia_natacao_ciclismo}</div>', unsafe_allow_html=True)
        
        st.subheader("💡 Dicas")
        st.markdown("""
        <div class="editavel">
        • Pratique a nutrição durante o ciclismo<br>
        • Teste diferentes produtos nas sessões de brick<br>
        • Mantenha hidratação constante
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("🚴‍♂️→🏃‍♂️ Ciclismo-Corrida")
        st.markdown(f'<div class="editavel">{estrategia_ciclismo_corrida}</div>', unsafe_allow_html=True)
        
        st.subheader("⚠️ Cuidados")
        st.markdown("""
        <div class="editavel">
        • Evite alimentos sólidos na última hora de ciclismo<br>
        • Teste a tolerância gastrointestinal<br>
        • Mantenha eletrólitos adequados
        </div>
        """, unsafe_allow_html=True)

def mostrar_monitoramento_sem_diario():
    """Mostra monitoramento do triatleta"""
    st.header("📈 Monitoramento do Triatleta")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Métricas de Performance")
        
        st.write("**Indicadores Chave:**")
        metricas = [
            "Frequência cardíaca em repouso",
            "Variabilidade da frequência cardíaca",
            "Peso corporal matinal", 
            "Qualidade do sono",
            "Fadiga percebida",
            "Desejo de treinar"
        ]
        
        for metrica in metricas:
            st.checkbox(metrica, value=True, key=f"met_{metrica}")
    
    with col2:
        st.subheader("🩺 Saúde e Recuperação")
        
        st.write("**Sinais de Overtraining:**")
        sinais = [
            "Aumento da FC em repouso",
            "Queda no desempenho", 
            "Distúrbios do sono",
            "Fadiga persistente",
            "Mudanças de mood",
            "Maior incidência de lesões"
        ]
        
        for sinal in sinais:
            st.checkbox(sinal, value=False, key=f"sinal_{sinal}")
        
        st.subheader("📅 Próxima Avaliação")
        st.date_input("Data da próxima avaliação:", key="proxima_avaliacao")

def mostrar_relatorio_completo_triatlo_com_pdf(nome_triatleta, nivel, distancia, peso, altura, idade, sexo, tipo_dieta, cardapio_semanal, nome_nutri, crn):
    """Mostra relatório completo integrando todos os dados com botão de download PDF - CORRIGIDA"""
    st.header("📋 Relatório Completo do Triatleta")
    
    tge_triatlo = calcular_necessidades_triatlo(peso, altura, idade, sexo, nivel, distancia)
    hidratacao_triatlo = calcular_hidratacao_triatlo(peso, distancia)
    estrategia_periodizacao = obter_estrategia_periodizacao(nivel, distancia)
    
    cardapio_analise = analisar_cardapio_triatlo(cardapio_semanal, tge_triatlo, distancia, peso)
    suplementos = obter_suplementacao_triatlo(nivel, distancia)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👤 Dados do Triatleta")
        st.write(f"**Nome:** {nome_triatleta}")
        st.write(f"**Nível:** {nivel}")
        st.write(f"**Distância Alvo:** {distancia}")
        st.write(f"**Peso:** {peso} kg")
        st.write(f"**Altura:** {altura} cm") 
        st.write(f"**Idade:** {idade} anos")
        st.write(f"**Sexo:** {sexo}")
        st.write(f"**Tipo de Dieta:** {tipo_dieta}")
        st.write(f"**Meta:** Desempenho Esportivo")
    
    with col2:
        st.subheader("🎯 Recomendações Nutricionais")
        st.write(f"**TGE:** {tge_triatlo:.0f} kcal/dia")
        st.write(f"**Hidratação:** {hidratacao_triatlo:.0f} ml/dia")
        st.write(f"**Periodização:** {estrategia_periodizacao}")
        
        st.subheader("💊 Suplementação")
        for suplemento in suplementos:
            st.write(f"• {suplemento}")
        
        st.subheader("📊 Status do Cardápio")
        if cardapio_analise['status'] == 'vazio':
            st.error("❌ Nenhum cardápio gerado")
        else:
            st.write(f"**Calorias/dia:** {cardapio_analise['media_diaria']['calorias']:.0f}")
            st.write(f"**Adequação:** {cardapio_analise['diferenca_calorias']:+.1f}%")
            st.write(f"**Carboidratos:** {cardapio_analise['carb_atual']:.1f}g/kg")
    
    st.markdown("---")
    st.subheader("📄 Gerar Relatório em PDF")
    
    col_centro = st.columns([1, 2, 1])[1]
    
    with col_centro:
        if st.button("🖨️ Gerar PDF Completo", type="primary", use_container_width=True, key="gerar_pdf_principal"):
            dados_paciente = {
                'nome': nome_triatleta,
                'idade': idade,
                'faixa_etaria': obter_faixa_etaria(idade),
                'peso': peso,
                'altura': altura,
                'imc': calcular_imc_e_classificar(peso, altura)[0],
                'classificacao_imc': calcular_imc_e_classificar(peso, altura)[1],
                'tge': tge_triatlo,
                'cho_p': TIPOS_DIETA[tipo_dieta]['carbs'],
                'ptn_p': TIPOS_DIETA[tipo_dieta]['proteinas'],
                'lip_p': TIPOS_DIETA[tipo_dieta]['gorduras'],
                'hidratacao': hidratacao_triatlo
            }
            
            with st.spinner("Gerando PDF..."):
                pdf_bytes = gerar_pdf_triatlo(
                    dados_paciente, cardapio_semanal, nome_nutri, crn, 
                    tipo_dieta, nivel, distancia
                )
            
            if pdf_bytes:
                st.success("✅ PDF gerado com sucesso!")
                
                st.download_button(
                    label="📥 Baixar Relatório em PDF",
                    data=pdf_bytes,
                    file_name=f"plano_triatlo_{nome_triatleta.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True,
                    key="download_pdf_principal"
                )
            else:
                st.error("❌ Erro ao gerar PDF. Verifique se há cardápio gerado.")

# =============================================================================
# FUNÇÕES ORIGINAIS MANTIDAS
# =============================================================================

def mostrar_dashboard_triatlo_com_edicao(nome_triatleta, nivel, distancia, peso, altura, idade, sexo, tipo_dieta, cardapio_semanal):
    """Mostra dashboard específico para triatletas com opções de edição"""
    st.header("📊 Dashboard do Triatleta - Personalizável")
    
    with st.expander("⚙️ Configurações de Cálculo", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            fator_calorico = st.slider(
                "Fator Calórico para Desempenho", 
                min_value=1.0, 
                max_value=1.5, 
                value=1.15,
                step=0.05,
                help="Ajuste o fator de aumento calórico para desempenho esportivo"
            )
        
        with col2:
            ml_por_kg = st.slider(
                "ml de Água por kg", 
                min_value=25, 
                max_value=50, 
                value=35,
                step=1,
                help="Base de cálculo para hidratação diária"
            )
    
    tge_triatlo = calcular_necessidades_triatlo(peso, altura, idade, sexo, nivel, distancia, fator_calorico)
    hidratacao_triatlo = calcular_hidratacao_triatlo(peso, distancia, ml_por_kg)
    
    cardapio_analise = analisar_cardapio_triatlo(cardapio_semanal, tge_triatlo, distancia, peso)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🏊‍♂️ Nível", nivel)
    with col2:
        st.metric("🎯 Distância", distancia)
    with col3:
        st.metric("🔥 TGE Triatlo", f"{tge_triatlo:.0f} kcal")
        st.caption(f"Fator: {fator_calorico}")
    with col4:
        st.metric("💧 Hidratação", f"{hidratacao_triatlo:.0f} ml")
        st.caption(f"Base: {ml_por_kg}ml/kg")
    
    st.subheader("📋 Status do Cardápio")
    if cardapio_analise['status'] == 'vazio':
        st.error("❌ Nenhum cardápio gerado")
    elif cardapio_analise['status'] == 'adequado':
        st.success("✅ Cardápio adequado para o triatlo")
    elif cardapio_analise['status'] == 'ajuste_necesario':
        st.warning("⚠️ Ajuste necessário no cardápio")
    elif cardapio_analise['status'] == 'carb_insuficiente':
        st.warning("⚠️ Carboidratos insuficientes para a distância")
    
    if cardapio_analise['status'] != 'vazio':
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Calorias/dia", f"{cardapio_analise['media_diaria']['calorias']:.0f}", 
                     f"{cardapio_analise['diferenca_calorias']:+.1f}%")
        with col2:
            st.metric("Carboidratos", f"{cardapio_analise['media_diaria']['carboidratos']:.0f}g")
        with col3:
            st.metric("Proteínas", f"{cardapio_analise['media_diaria']['proteinas']:.0f}g")
        with col4:
            st.metric("Gorduras", f"{cardapio_analise['media_diaria']['gorduras']:.0f}g")

def mostrar_periodizacao_com_edicao(nivel, distancia):
    """Mostra detalhes da periodização com opções de edição"""
    st.header("🔄 Periodização do Treino - Personalizável")
    
    with st.expander("⚙️ Configurar Periodização", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            semanas_base = st.number_input("Semanas Fase Base", min_value=2, max_value=12, value=4)
        with col2:
            semanas_build = st.number_input("Semanas Fase Build", min_value=2, max_value=12, value=4)
        with col3:
            semanas_peak = st.number_input("Semanas Fase Peak", min_value=1, max_value=6, value=2)
    
    semanas_totais = semanas_base + semanas_build + semanas_peak
    
    estrategia = obter_estrategia_periodizacao(nivel, distancia, semanas_totais)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Estratégia Recomendada")
        st.success(estrategia)
        
        st.subheader("🎯 Fases do Treino")
        fases = {
            "Base": f"Desenvolvimento da capacidade aeróbica ({semanas_base} semanas)",
            "Build": f"Aumento de intensidade e volume ({semanas_build} semanas)",
            "Peak": f"Ajuste fino para competição ({semanas_peak} semanas)",
            "Race": "Período da competição",
            "Recovery": "Recuperação pós-competição"
        }
        
        for fase, descricao in fases.items():
            with st.expander(f"🏃‍♂️ {fase}"):
                st.write(descricao)
    
    with col2:
        st.subheader("🥗 Nutrição por Fase")
        
        nutricao_fases = {
            "Base": "Ênfase em proteínas para recuperação, carboidratos moderados",
            "Build": "Alta ingestão de carboidratos, proteínas adequadas",
            "Peak": "Carb loading estratégico, hidratação otimizada",
            "Race": "Timing nutricional preciso, suplementação específica", 
            "Recovery": "Proteínas para reparo, antioxidantes, hidratação"
        }
        
        for fase, nutricao in nutricao_fases.items():
            st.markdown(f'<div class="editavel"><strong>{fase}:</strong> {nutricao}</div>', unsafe_allow_html=True)

def mostrar_carb_loading_com_edicao(distancia):
    """Mostra estratégias de carb loading com edição"""
    st.header("🍚 Carb Loading - Personalizável")
    
    with st.expander("⚙️ Configurar Carb Loading", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Dias Antes")
            dias_sprint = st.text_input("Sprint - dias", "2 dias antes")
            dias_olimpico = st.text_input("Olímpico - dias", "3 dias antes")
            dias_ironman70 = st.text_input("Ironman 70.3 - dias", "3 dias antes")
            dias_ironman = st.text_input("Ironman - dias", "3-4 dias antes")
        
        with col2:
            st.subheader("Carboidratos por kg")
            carb_sprint = st.text_input("Sprint - g/kg", "3-4g/kg/dia")
            carb_olimpico = st.text_input("Olímpico - g/kg", "5-6g/kg/dia")
            carb_ironman70 = st.text_input("Ironman 70.3 - g/kg", "6-8g/kg/dia")
            carb_ironman = st.text_input("Ironman - g/kg", "8-10g/kg/dia")
    
    dias_antes = {
        "Sprint": dias_sprint,
        "Olímpico": dias_olimpico,
        "Ironman 70.3": dias_ironman70,
        "Ironman Completo": dias_ironman
    }
    
    carb_por_kg = {
        "Sprint": carb_sprint,
        "Olímpico": carb_olimpico,
        "Ironman 70.3": carb_ironman70,
        "Ironman Completo": carb_ironman
    }
    
    estrategia = obter_estrategia_carb_loading(distancia, dias_antes, carb_por_kg)
    
    st.subheader("🎯 Estratégia Recomendada")
    st.markdown(f'<div class="editavel">{estrategia}</div>', unsafe_allow_html=True)
    
    st.subheader("📋 Protocolos de Carb Loading")
    
    protocolos = {
        "Modificado (2 dias)": {
            "descricao": "Para distâncias mais curtas",
            "dias": dias_sprint, 
            "carbs": carb_sprint,
            "treino": "Redução gradual de volume"
        },
        "Tradicional (3 dias)": {
            "descricao": "Para distâncias olímpicas",
            "dias": dias_olimpico,
            "carbs": carb_olimpico, 
            "treino": "Descanso ativo"
        },
        "Avançado (3-4 dias)": {
            "descricao": "Para Ironman", 
            "dias": dias_ironman,
            "carbs": carb_ironman,
            "treino": "Depleção inicial + carga"
        }
    }
    
    for protocolo, detalhes in protocolos.items():
        with st.expander(f"📖 {protocolo}"):
            st.write(f"**Descrição:** {detalhes['descricao']}")
            st.write(f"**Duração:** {detalhes['dias']}")
            st.write(f"**Carboidratos:** {detalhes['carbs']}")
            st.write(f"**Treino:** {detalhes['treino']}")

def mostrar_hidratacao_triatlo_com_edicao(peso, distancia):
    """Mostra estratégias de hidratação com edição"""
    st.header("💧 Estratégias de Hidratação - Personalizável")
    
    with st.expander("⚙️ Configurar Hidratação", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            ml_base = st.slider("ml por kg (base)", min_value=25, max_value=50, value=35)
            temp_referencia = st.slider("Temperatura de Referência (°C)", min_value=15, max_value=35, value=20)
        
        with col2:
            st.subheader("Ajuste por Distância")
            fator_sprint = st.number_input("Sprint", min_value=0.8, max_value=2.0, value=1.0, step=0.1)
            fator_olimpico = st.number_input("Olímpico", min_value=0.8, max_value=2.0, value=1.2, step=0.1)
            fator_ironman70 = st.number_input("Ironman 70.3", min_value=0.8, max_value=2.0, value=1.4, step=0.1)
            fator_ironman = st.number_input("Ironman", min_value=0.8, max_value=2.0, value=1.6, step=0.1)
    
    ajuste_distancia = {
        "Sprint": fator_sprint,
        "Olímpico": fator_olimpico,
        "Ironman 70.3": fator_ironman70,
        "Ironman Completo": fator_ironman
    }
    
    def calcular_hidratacao_personalizada(peso, distancia, ml_por_kg, temperatura):
        if temperatura > 30:
            ajuste_temp = 1.3
        elif temperatura > 25:
            ajuste_temp = 1.2
        elif temperatura > 20:
            ajuste_temp = 1.1
        else:
            ajuste_temp = 1.0
        
        hidratacao_base = peso * ml_por_kg
        hidratacao_ajustada = hidratacao_base * ajuste_distancia.get(distancia, 1.0) * ajuste_temp
        
        return int(hidratacao_ajustada)
    
    hidratacao_base = calcular_hidratacao_personalizada(peso, distancia, ml_base, temp_referencia)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💧 Hidratação Diária")
        st.metric("Recomendação Base", f"{hidratacao_base:.0f} ml/dia")
        st.caption(f"Base: {ml_base}ml/kg × {ajuste_distancia.get(distancia, 1.0):.1f} (distância)")
        
        st.subheader("🌡️ Ajuste por Temperatura")
        temperaturas = [15, 20, 25, 30, 35]
        for temp in temperaturas:
            ajuste = calcular_hidratacao_personalizada(peso, distancia, ml_base, temp)
            st.write(f"{temp}°C: {ajuste:.0f} ml/dia")
    
    with col2:
        st.subheader("🏊‍♂️ Durante Competição")
        
        st.write("**Natação:**")
        st.markdown('<div class="editavel">Hidratação prévia apenas - não é possível durante</div>', unsafe_allow_html=True)
        
        st.write("**Ciclismo:**")
        st.markdown('<div class="editavel">500-1000ml/hora com eletrólitos</div>', unsafe_allow_html=True)
        
        st.write("**Corrida:**")
        st.markdown('<div class="editavel">400-800ml/hora conforme tolerância</div>', unsafe_allow_html=True)

def mostrar_suplementacao_triatlo_com_edicao(nivel, distancia):
    """Mostra suplementação específica com edição"""
    st.header("💊 Suplementação para Triatlo - Personalizável")
    
    with st.expander("⚙️ Configurar Suplementação", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Suplementos Base")
            bebida_esportiva = st.checkbox("Bebida Esportiva", value=True)
            geis_carboidrato = st.checkbox("Géis de Carboidrato", value=True)
            eletrolitos = st.checkbox("Eletrólitos", value=True)
            bcaa = st.checkbox("BCAA", value=True)
        
        with col2:
            st.subheader("Suplementos Avançados")
            beta_alanina = st.checkbox("Beta-alanina", value=(nivel in ["Avançado", "Profissional"]))
            creatina = st.checkbox("Creatina", value=(nivel in ["Avançado", "Profissional"]))
            cafeina = st.checkbox("Cafeína", value=(nivel in ["Avançado", "Profissional"]))
            barras_energeticas = st.checkbox("Barras Energéticas", value=(distancia in ["Ironman 70.3", "Ironman Completo"]))
            sal_capsulas = st.checkbox("Sal em Cápsulas", value=(distancia in ["Ironman 70.3", "Ironman Completo"]))
        
        st.subheader("Suplementos Personalizados")
        suplementos_personalizados = st.text_area(
            "Adicionar Suplementos Personalizados (um por linha)",
            placeholder="Exemplo:\nÓleo MCT\nGlutamina\nVitamina C",
            help="Digite um suplemento por linha"
        )
    
    suplementos_base = []
    if bebida_esportiva: suplementos_base.append("Bebida Esportiva")
    if geis_carboidrato: suplementos_base.append("Géis de Carboidrato")
    if eletrolitos: suplementos_base.append("Eletrólitos")
    if bcaa: suplementos_base.append("BCAA")
    
    if beta_alanina: suplementos_base.append("Beta-alanina")
    if creatina: suplementos_base.append("Creatina")
    if cafeina: suplementos_base.append("Cafeína")
    if barras_energeticas: suplementos_base.append("Barras Energéticas")
    if sal_capsulas: suplementos_base.append("Sal em Cápsulas")
    
    suplementos_pers = []
    if suplementos_personalizados:
        suplementos_pers = [s.strip() for s in suplementos_personalizados.split('\n') if s.strip()]
    
    suplementos = obter_suplementacao_triatlo(nivel, distancia, suplementos_pers + suplementos_base)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("✅ Suplementos Recomendados")
        for i, suplemento in enumerate(suplementos):
            st.checkbox(suplemento, value=True, key=f"sup_{suplemento}_{i}")
        
        st.subheader("🎯 Timing de Suplementação")
        st.markdown("""
        <div class="editavel">
        • <strong>Pré-treino:</strong> 30-60min antes<br>
        • <strong>Durante:</strong> A cada 45-60min<br>
        • <strong>Pós-treino:</strong> 30min após<br>
        • <strong>Diário:</strong> Conforme orientação
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("📊 Dosagens Recomendadas")
        
        dosagens = {
            "Bebida Esportiva": "500-1000ml/hora",
            "Géis de Carboidrato": "1-2 géis/hora", 
            "Eletrólitos": "500-1000mg sódio/hora",
            "BCAA": "5-10g durante exercício",
            "Cafeína": "3-6mg/kg 1h antes",
            "Creatina": "5g/dia",
            "Beta-alanina": "3-6g/dia"
        }
        
        for suplemento, dosagem in dosagens.items():
            if suplemento in suplementos:
                st.markdown(f'<div class="editavel"><strong>{suplemento}:</strong> {dosagem}</div>', unsafe_allow_html=True)

def mostrar_competicoes():
    """Mostra planejamento para competições"""
    st.header("🏆 Planejamento para Competições")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Checklist Pré-Competição")
        
        checklist = {
            "7 dias antes": ["Testar equipamentos", "Confirmar inscrição", "Planejar deslocamento"],
            "3 dias antes": ["Iniciar carb loading", "Reduzir volume de treino", "Confirmar previsão do tempo"],
            "1 dia antes": ["Preparar transições", "Organizar nutrição", "Hidratação adequada"],
            "Dia da prova": ["Café da manhã familiar", "Chegar cedo ao local", "Aquecimento específico"]
        }
        
        for periodo, tarefas in checklist.items():
            with st.expander(f"📅 {periodo}"):
                for tarefa in tarefas:
                    st.checkbox(tarefa, key=f"check_{periodo}_{tarefa}")
    
    with col2:
        st.subheader("🥗 Nutrição na Semana da Prova")
        
        st.write("**7 Dias Antes:**")
        st.info("Dieta equilibrada, ênfase em carboidratos complexos")
        
        st.write("**3 Dias Antes:**")
        st.warning("Aumento progressivo de carboidratos, redução de fibras")
        
        st.write("**1 Dia Antes:**")
        st.success("Refeições familiares, alimentos de fácil digestão")
        
        st.write("**Dia da Prova:**")
        st.error("Café da manhã 3-4h antes, alimentos testados previamente")

# =============================================================================
# INTERFACE PRINCIPAL - TRIATLO INTEGRADO
# =============================================================================

def main():
    # Header principal
    st.markdown('<h1 class="main-header">🏊‍♂️ 🚴‍♂️ 🏃‍♂️ Nutrição para Triatletas</h1>', unsafe_allow_html=True)
    
    # Inicializar dados
    inicializar_dados_triatlo()
    if 'cardapio_semanal' not in st.session_state:
        st.session_state.cardapio_semanal = {}
    if 'sistema_cardapio' not in st.session_state:
        st.session_state.sistema_cardapio = None
    if 'cardapio_editavel' not in st.session_state:
        st.session_state.cardapio_editavel = {}
    
    # Carregar dados
    try:
        df_alimentos, df_receitas = carregar_dados_completos()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        df_alimentos, df_receitas = carregar_dados_fallback_alimentos(), carregar_dados_fallback_receitas()
    
    # Inicializar sistema de cardápio automático
    if st.session_state.sistema_cardapio is None:
        st.session_state.sistema_cardapio = SistemaCardapioAutomatico(df_receitas)
    
    # =========================================================================
    # BARRA LATERAL
    # =========================================================================
    with st.sidebar:
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.header("🎯 Dados do Triatleta")
        
        # Dados básicos
        if 'nome_paciente' not in st.session_state:
            st.session_state.nome_paciente = ""
        if 'peso' not in st.session_state:
            st.session_state.peso = 0.0
        if 'altura' not in st.session_state:
            st.session_state.altura = 0.0
        if 'idade' not in st.session_state:
            st.session_state.idade = 0
        
        nome_triatleta = st.text_input("Nome do Triatleta", value=st.session_state.nome_paciente, placeholder="Digite o nome do triatleta", key="nome_triatleta_input")
        peso = st.number_input("Peso (kg)", min_value=0.0, value=st.session_state.peso, key="peso_input")
        altura = st.number_input("Altura (cm)", min_value=0.0, value=st.session_state.altura, key="altura_input")
        idade = st.number_input("Idade", min_value=0, value=st.session_state.idade, key="idade_input")
        
        st.session_state.nome_paciente = nome_triatleta
        st.session_state.peso = peso
        st.session_state.altura = altura
        st.session_state.idade = idade
        
        # DADOS ESPECÍFICOS DO TRIATLO
        st.header("🏊‍♂️ Dados do Triatlo")
        nivel_triatlo = st.selectbox("Nível do Triatleta", ['- Selecione -'] + NIVEIS_TRIATLO, key="nivel_triatlo")
        distancia_alvo = st.selectbox("Distância Alvo", ['- Selecione -'] + DISTANCIAS_TRIATLO, key="distancia_alvo")
        
        faixa_etaria = obter_faixa_etaria(idade) if idade > 0 else 'Não definida'
        st.info(f"**Faixa Etária:** {faixa_etaria}")
        
        # Dados convencionais
        sexo = st.selectbox("Sexo", SEXO_OPCOES, key="sexo_input")
        
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
        st.markdown('</div>', unsafe_allow_html=True)
        
        # =====================================================================
        # PAINEL DO TRIATLETA - MENU VERTICAL
        # =====================================================================
        dados_validos_sidebar = all([
            peso > 0, altura > 0, idade > 0, 
            sexo != '- Selecione -', 
            tipo_dieta != '- Selecione -',
            nivel_triatlo != '- Selecione -',
            distancia_alvo != '- Selecione -',
            nome_triatleta != ""
        ])
        
        if dados_validos_sidebar:
            st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
            st.header("🏆 Painel do Triatleta")
            
            opcoes_triatlo = [
                "🍽️ Cardápio Automático",
                "📊 Dashboard Triatlo",
                "🔄 Periodização", 
                "⏱️ Timing Nutricional", 
                "🧱 Brick Training",
                "🍚 Carb Loading", 
                "💧 Hidratação", 
                "💊 Suplementação", 
                "📈 Monitoramento",
                "🏆 Competições", 
                "📋 Relatório Completo"
            ]
            
            st.write("**Selecione a Seção:**")
            
            if 'pagina_atual' not in st.session_state:
                st.session_state.pagina_atual = "🍽️ Cardápio Automático"
            
            for opcao in opcoes_triatlo:
                if st.button(opcao, key=f"btn_{opcao}", use_container_width=True):
                    st.session_state.pagina_atual = opcao
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("⚠️ Preencha todos os dados acima para acessar o Painel do Triatleta")
        
        # Botão Limpar Todos os Dados
        st.markdown("---")
        if st.button("🔴 Limpar Todos os Dados", type="secondary", key="limpar_dados"):
            keys_to_clear = [
                'nome_triatleta_input', 'peso_input', 'altura_input', 'idade_input',
                'nivel_triatlo', 'distancia_alvo', 'sexo_input', 'tipo_dieta_input',
                'celiaca_input', 'lactose_input', 'alergia_leite_input', 'alergia_ovo_input',
                'alergia_oleaginosas_input', 'diabetico_input', 'hipertenso_input',
                'vegetariano_input', 'vegano_input', 'ovo_lacto_input', 'pesco_vegetariano_input',
                'nome_nutri_input', 'crn_input'
            ]
            
            for key in list(st.session_state.keys()):
                if any(k in key for k in keys_to_clear) or key in ['nome_paciente', 'peso', 'altura', 'idade', 'pagina_atual']:
                    del st.session_state[key]
            
            if 'cardapio_semanal' in st.session_state:
                del st.session_state.cardapio_semanal
            if 'cardapio_editavel' in st.session_state:
                del st.session_state.cardapio_editavel
            
            st.rerun()
    
    # =========================================================================
    # CONTEÚDO PRINCIPAL BASEADO NA SELEÇÃO
    # =========================================================================
    
    # Cálculos
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
    
    atividade = 'Ativo'
    
    dados_validos = all([
        peso > 0, altura > 0, idade > 0, 
        sexo != '- Selecione -', 
        tipo_dieta != '- Selecione -',
        nivel_triatlo != '- Selecione -',
        distancia_alvo != '- Selecione -'
    ])
    
    if dados_validos:
        imc, classificacao = calcular_imc_e_classificar(peso, altura)
        tmb = calcular_tmb(peso, altura, idade, sexo)
        
        tge = tmb * NAF_OPCOES[atividade] + 400
        
        cho_p, ptn_p, lip_p, cho_g, ptn_g, lip_g = calcular_macros_por_dieta(tge, tipo_dieta)
        
        hidratacao = calcular_hidratacao_basica(peso)
        
        st.session_state.ultimo_calculo = {
            'tge': tge,
            'imc': imc,
            'classificacao_imc': classificacao,
            'hidratacao': hidratacao,
            'cho_p': cho_p,
            'ptn_p': ptn_p,
            'lip_p': lip_p,
            'cho_g': cho_g,
            'ptn_g': ptn_g,
            'lip_g': lip_g,
            'faixa_etaria': faixa_etaria
        }
        
        cardapio_analise = analisar_cardapio_triatlo(st.session_state.cardapio_semanal, tge, distancia_alvo, peso)
    else:
        imc = classificacao = tmb = tge = hidratacao = 0
        cho_p = ptn_p = lip_p = cho_g = ptn_g = lip_g = 0
        cardapio_analise = {"status": "vazio"}
    
    dados_validos_sidebar = all([
        st.session_state.peso > 0, 
        st.session_state.altura > 0, 
        st.session_state.idade > 0, 
        sexo != '- Selecione -', 
        tipo_dieta != '- Selecione -',
        nivel_triatlo != '- Selecione -',
        distancia_alvo != '- Selecione -',
        st.session_state.nome_paciente != ""
    ])
    
    if dados_validos_sidebar and 'pagina_atual' in st.session_state:
        pagina_selecionada = st.session_state.pagina_atual
        
        if pagina_selecionada == "🍽️ Cardápio Automático":
            st.header("📊 Avaliação do Triatleta")
            if st.session_state.nome_paciente:
                st.subheader(f"Triatleta: {st.session_state.nome_paciente}")
                if st.session_state.idade > 0:
                    st.caption(f"Faixa Etária: {faixa_etaria}")
                st.caption(f"Nível: {nivel_triatlo} | Distância Alvo: {distancia_alvo} | Meta: Desempenho Esportivo")
            
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            col1.metric("IMC", f"{imc:.1f}", classificacao)
            col2.metric("TGE Diário", f"{tge:.0f} kcal")
            col3.metric("Hidratação", f"{hidratacao:.0f} ml")
            col4.metric("Tipo de Dieta", tipo_dieta)
            col5.metric("Macros", f"C:{cho_p}% P:{ptn_p}% G:{lip_p}%")
            col6.metric("Meta", "Desempenho")
            
            if cardapio_analise['status'] != 'vazio':
                st.info(f"📊 Cardápio atual: {cardapio_analise['dias_analisados']} dias analisados | {cardapio_analise['media_diaria']['calorias']:.0f} kcal/dia")
            
            tab1, tab2, tab3 = st.tabs([
                "🎯 Cardápio Automático", "🥗 Tipos de Dieta", "🛒 Lista de Compras"
            ])
            
            with tab1:
                st.header("🍽️ Sistema de Cardápio Automático")
                
                if perfil:
                    st.info(f"**Perfil com restrições:** {', '.join(perfil)}")
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("📊 Otimizar Cardápio", type="primary", key="otimizar_cardapio", use_container_width=True):
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
                    if st.button("🔄 Gerar Cardápio Sem Repetições", type="secondary", key="gerar_cardapio", use_container_width=True):
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
                st.header("🛒 Lista de Compras Recomendada")
                alimentos_recomendados = obter_lista_compras_recomendada(st.session_state.cardapio_semanal, tipo_dieta)
                
                if alimentos_recomendados:
                    st.subheader("📋 Alimentos Essenciais")
                    col1, col2 = st.columns(2)
                    
                    alimentos_lista = list(alimentos_recomendados)
                    metade = len(alimentos_lista) // 2
                    
                    with col1:
                        for alimento in alimentos_lista[:metade]:
                            st.checkbox(alimento, value=True, key=f"compra_{alimento}")
                    
                    with col2:
                        for alimento in alimentos_lista[metade:]:
                            st.checkbox(alimento, value=True, key=f"compra_{alimento}")
                else:
                    st.info("Gere um cardápio primeiro para ver a lista de compras recomendada")
        
        elif pagina_selecionada == "📊 Dashboard Triatlo":
            mostrar_dashboard_triatlo_com_edicao(
                st.session_state.nome_paciente, 
                nivel_triatlo, 
                distancia_alvo, 
                st.session_state.peso, 
                st.session_state.altura, 
                st.session_state.idade, 
                sexo, 
                tipo_dieta, 
                st.session_state.cardapio_semanal
            )
            
        elif pagina_selecionada == "🔄 Periodização":
            mostrar_periodizacao_com_edicao(nivel_triatlo, distancia_alvo)
            
        elif pagina_selecionada == "⏱️ Timing Nutricional":
            mostrar_timing_nutricional_com_edicao(distancia_alvo)
            
        elif pagina_selecionada == "🧱 Brick Training":
            mostrar_brick_training_com_edicao()
            
        elif pagina_selecionada == "🍚 Carb Loading":
            mostrar_carb_loading_com_edicao(distancia_alvo)
            
        elif pagina_selecionada == "💧 Hidratação":
            mostrar_hidratacao_triatlo_com_edicao(st.session_state.peso, distancia_alvo)
            
        elif pagina_selecionada == "💊 Suplementação":
            mostrar_suplementacao_triatlo_com_edicao(nivel_triatlo, distancia_alvo)
            
        elif pagina_selecionada == "📈 Monitoramento":
            mostrar_monitoramento_sem_diario()
            
        elif pagina_selecionada == "🏆 Competições":
            mostrar_competicoes()
            
        elif pagina_selecionada == "📋 Relatório Completo":
            mostrar_relatorio_completo_triatlo_com_pdf(
                st.session_state.nome_paciente, 
                nivel_triatlo, 
                distancia_alvo, 
                st.session_state.peso, 
                st.session_state.altura, 
                st.session_state.idade, 
                sexo, 
                tipo_dieta, 
                st.session_state.cardapio_semanal, 
                nome_nutri, 
                crn
            )
            
    else:
        st.info("👆 Preencha todos os dados na barra lateral para acessar o sistema completo")
        st.header("Bem-vindo ao Sistema de Nutrição para Triatletas")
        st.write("""
        Este sistema integra nutrição convencional com estratégias específicas para triatletas.
        
        **Para começar:**
        1. Preencha os dados do triatleta na barra lateral
        2. Selecione o nível e distância do triatlo
        3. Escolha o tipo de dieta desejada
        4. Acesse o Painel do Triatleta para funcionalidades completas
        
        **Funcionalidades Específicas para Triatlo:**
        • 📊 Dashboard com métricas específicas e análise do cardápio
        • 🔄 Periodização integrada com nutrição  
        • ⏱️ Timing nutricional personalizado
        • 🧱 Estratégias para brick training
        • 🍚 Protocolos de carb loading
        • 💧 Hidratação personalizada
        • 💊 Suplementação específica
        • 📈 Monitoramento completo
        • 🏆 Planejamento para competições
        • 📋 Relatório PDF integrado
        """)
    
    # =========================================================================
    # RODAPÉ CENTRALIZADO
    # =========================================================================
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
