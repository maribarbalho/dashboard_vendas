import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# Configurações iniciais da página no Streamlit
st.set_page_config(
    page_title="DASHBOARD DE VENDAS",
    layout="wide"
)

# Função para formatar números em milhar/milhão com prefixo
def formata_numero(valor, prefixo = ''):
    for unidade in ['', 'mil']:
        if valor <1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'

# Título principal do dashboard
st.title('PROJETO DASHBOARD DE VENDAS 🛒')

# URL da API com os dados
url = 'https://labdados.com/produtos'
# Lista de regiões para o filtro
regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']

# Configuração do menu lateral (sidebar)
st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)

# Se a região for Brasil, define como vazio para pegar o total
if regiao == 'Brasil':
    regiao = ''

# Filtro de período (todos os anos ou seleção de um ano específico)
todos_anos = st.sidebar.checkbox('Dados de todo o período', value = True)
if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023)

# Montagem da query com os filtros selecionados
query_string = {'regiao': regiao.lower(), 'ano': ano}

# Requisição dos dados à API e conversão para DataFrame
response = requests.get(url, params=query_string)
dados = pd.DataFrame.from_dict(response.json())

# Converte a coluna de data para o tipo datetime
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y')

# Filtro por vendedores selecionados
filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

## ==========================
## Criação das tabelas base
## ==========================

### Tabelas de receita
receita_estados = dados.groupby('Local da compra')[['Preço']].sum()
receita_estados = dados.drop_duplicates(subset= 'Local da compra')[['Local da compra', 'lat', 'lon']]\
    .merge(receita_estados, left_on = 'Local da compra', right_index = True)\
    .sort_values('Preço', ascending= False)

# Receita mensal agrupada por ano e mês
receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq = 'M'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()

# Receita por categoria de produto
receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending = False)

### Tabelas de quantidade de vendas
# Vendas por estado
vendas_estados = pd.DataFrame(dados.groupby('Local da compra')['Preço'].count())
vendas_estados = dados.drop_duplicates(subset = 'Local da compra')[['Local da compra','lat', 'lon']]\
    .merge(vendas_estados, left_on = 'Local da compra', right_index = True)\
    .sort_values('Preço', ascending = False)

# Vendas mensais
vendas_mensal = pd.DataFrame(dados.set_index('Data da Compra').groupby(pd.Grouper(freq = 'M'))['Preço'].count()).reset_index()
vendas_mensal['Ano'] = vendas_mensal['Data da Compra'].dt.year
vendas_mensal['Mes'] = vendas_mensal['Data da Compra'].dt.month_name()

# Vendas por categoria
vendas_categorias = pd.DataFrame(dados.groupby('Categoria do Produto')['Preço'].count().sort_values(ascending = False))

### Tabelas de vendedores
# Receita e quantidade de vendas por vendedor
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))

## ==========================
## Criação dos gráficos
## ==========================

### Gráficos de receita
# Receita por estado (mapa)
fig_mapa_receita = px.scatter_geo(receita_estados,
                                  lat = 'lat',
                                  lon = 'lon',
                                  scope = 'south america',
                                  size = 'Preço',
                                  template = 'seaborn',
                                  hover_name = 'Local da compra',
                                  hover_data = {'lat': False, 'lon': False},
                                  title = 'Receita por estado',
                                  color_discrete_sequence=["#c97fd7"])

# Receita mensal (linha)
fig_receita_mensal = px.line(receita_mensal,
                             x = 'Mes',
                             y = 'Preço',
                             markers = True,
                             range_y = (0, receita_mensal.max()),
                             color = 'Ano',
                             line_dash = 'Ano',
                             title = 'Receita mensal',
                             color_discrete_sequence=["#e607b5", "#6c1e7f", "#c97fd7", "#1b1b3a"])
fig_receita_mensal.update_layout(yaxis_title = 'Receita')

# Top estados por receita (barra)
fig_receita_estados = px.bar(receita_estados.head(),
                             x = 'Local da compra',
                             y = 'Preço',
                             text_auto = True,
                             title = 'Top estados (receita)',
                             color_discrete_sequence=["#c97fd7"])
fig_receita_estados.update_layout(yaxis_title = 'Receita')

# Receita por categoria
fig_receita_categorias = px.bar(receita_categorias,
                                text_auto = True,
                                title = 'Receita por categoria',
                                color_discrete_sequence=["#c97fd7"])
fig_receita_categorias.update_layout(yaxis_title = 'Receita')

### Gráficos de vendas
# Vendas por estado (mapa)
fig_mapa_vendas = px.scatter_geo(vendas_estados, 
                     lat = 'lat', 
                     lon= 'lon', 
                     scope = 'south america', 
                     template='seaborn', 
                     size = 'Preço', 
                     hover_name ='Local da compra', 
                     hover_data = {'lat':False,'lon':False},
                     title = 'Vendas por estado',
                     color_discrete_sequence=["#c97fd7"])

# Top estados por vendas
fig_vendas_estados = px.bar(vendas_estados.head(),
                             x ='Local da compra',
                             y = 'Preço',
                             text_auto = True,
                             title = 'Top 5 estados',
                             color_discrete_sequence=["#c97fd7"])
fig_vendas_estados.update_layout(yaxis_title='Quantidade de vendas')

# Vendas mensais
fig_vendas_mensal = px.line(vendas_mensal, 
              x = 'Mes',
              y='Preço',
              markers = True, 
              range_y = (0,vendas_mensal.max()), 
              color = 'Ano', 
              line_dash = 'Ano',
              title = 'Quantidade de vendas mensal',
              color_discrete_sequence=["#e607b5", "#6c1e7f", "#c97fd7", "#1b1b3a"])
fig_vendas_mensal.update_layout(yaxis_title='Quantidade de vendas')

# Vendas por categoria
fig_vendas_categorias = px.bar(vendas_categorias, 
                                text_auto = True,
                                title = 'Vendas por categoria',
                                color_discrete_sequence=["#c97fd7"])
fig_vendas_categorias.update_layout(showlegend=False, yaxis_title='Quantidade de vendas')

## ==========================
## Visualização no Streamlit
## ==========================

# Separação em abas (Receita, Vendas e Vendedores)
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de vendas', 'Vendedores'])

# Aba Receita
with aba1:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_width= True)
        st.plotly_chart(fig_receita_estados, use_container_width= True)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width= True)
        st.plotly_chart(fig_receita_categorias, use_container_width= True)

# Aba Vendas
with aba2:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_vendas, use_container_width = True)
        st.plotly_chart(fig_vendas_estados, use_container_width = True)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_vendas_mensal, use_container_width = True)
        st.plotly_chart(fig_vendas_categorias, use_container_width = True)

# Aba Vendedores
with aba3:
    qtd_vendedores = st.number_input('Quantidade de vendedores', 2, 10, 5)
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        # Gráfico dos top vendedores por receita
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending = False).head(qtd_vendedores),
                                        x = 'sum',
                                        y = vendedores[['sum']].sort_values('sum', ascending = False).head(qtd_vendedores).index,
                                        text_auto = True,
                                        title = f'Top {qtd_vendedores} vendedores (receita)',
                                        color_discrete_sequence=["#c97fd7"])
        st.plotly_chart(fig_receita_vendedores, use_container_width = True)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        # Gráfico dos top vendedores por quantidade de vendas
        fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending = False).head(qtd_vendedores),
                                        x = 'count',
                                        y = vendedores[['count']].sort_values('count', ascending = False).head(qtd_vendedores).index,
                                        text_auto = True,
                                        title = f'Top {qtd_vendedores} vendedores (quantidade de vendas)',
                                        color_discrete_sequence=["#c97fd7"])
        st.plotly_chart(fig_vendas_vendedores, use_container_width = True)