🥼 Sistema de Nutrição Clínica e Esportiva
📱 Aplicativo profissional desenvolvido para nutricionistas

Este repositório contém o projeto completo do aplicativo de nutrição desenvolvido especialmente para uso de nutricionistas, com foco em:

Nutrição clínica (pacientes)

Nutrição esportiva (atletas)

Geração automática de cardápios

Inteligência artificial para cálculo nutricional

Avaliação de fotos de refeições

Controle, análises e automações do atendimento profissional

O projeto foi construído de forma iterativa, amadurecendo todas as funcionalidades ao longo do desenvolvimento.

🚀 Objetivo do Projeto

Criar um aplicativo completo, prático e poderoso, que permita ao nutricionista:

Montar planos alimentares personalizados

Gerar dietas automáticas com IA

Ajustar estratégias para pacientes comuns e atletas

Classificar fotos enviadas pelos pacientes (usando modelo de IA)

Controlar hidratação, carboidratos, proteínas e lipídios

Montar refeições por períodos:

Café da manhã

Lanches

Almoço

Jantar

Ceia

Pré-treino

Pós-treino

Criar substituições automáticas de alimentos

Exportar tudo em PDF, CSV ou interface web

Usar banco de dados completo de alimentos (TBCA)

O foco é entregar um sistema moderno, rápido, visual e com lógica nutricional real — evitando receitas e combinações irreais.

🧠 Tecnologias Utilizadas

Python

Streamlit para interface do app

Pandas para manipulação da base alimentar

TBCA (Tabela Brasileira de Composição de Alimentos)

Modelos de IA para classificação nutricional

FPDF para geração de documentos

Excel/CSV para entrada e saída de dados

APIs auxiliares para análise de imagens

🥗 Principais Funcionalidades Desenvolvidas
✔ 1. Montagem Inteligente de Refeições

Regras de combinação baseadas em alimentos reais, usando TBCA:

Carboidratos

Proteínas

Lipídios

Substituições reais

Hidratação estimada

✔ 2. Receitas Reais

Todas as receitas utilizadas no app são:

Simples

Baseadas em alimentos reais

Sem invenções absurdas

Calcularam macros automaticamente

✔ 3. IA para Classificação de Fotos

Avalia fotos dos servimentos enviados pelas escolas/pacientes:

Atende

Atende parcialmente

Não atende

N/A

(de acordo com seu fluxo profissional na merenda escolar)

✔ 4. Exportação Profissional

Gera:

Relatórios em PDF

Planilhas CSV e Excel

Tabelas completas de refeições

✔ 5. Interface intuitiva

Organizada por:

Pacientes

Atletas

Refeições

Macros

Planos

Receitas

Substituições

Exportações

🧩 Estrutura do Projeto
/
├── app.py                  # Aplicação principal (Streamlit)
├── receitas.csv            # Banco de receitas reais
├── alimentos.csv           # Banco de alimentos TBCA
├── classificacao_ia/       # Código da inteligência artificial
├── utils/                  # Funções auxiliares
├── pdf/                    # Exportação de relatórios
└── assets/                 # Ícones, imagens, logos

📦 Como Executar o Projeto
pip install -r requirements.txt
streamlit run app.py

👨‍⚕️ Público-Alvo

Nutricionistas clínicos

Nutricionistas esportivos

Personal trainers

Atletas

Pacientes acompanhados

Serviços de alimentação escolar (merenda)

Avaliação nutricional automatizada

✨ Status Atual

O app está em desenvolvimento contínuo, com:

✔ IA integrada
✔ Banco de receitas reais
✔ Módulos de pacientes e atletas
✔ Exportação completa
✔ Interface funcional

Novas funcionalidades estão sendo adicionadas conforme evolução do projeto.

🤝 Contribuições

Contribuições são bem-vindas!
Abra uma issue ou envie um pull request.

🧑‍💻 Desenvolvido por

Marcos Vinicius Catapan
Data Analyst & Nutrição Digital Developer
