import streamlit as st
import pandas as pd
import plotly.express as px
import json

# Carregar o CSV
df = pd.read_csv("estoque_sem_negativos.csv")

# Carregar GeoJSON para o mapa
@st.cache_data
def carregar_geojson():
    with open('geojs-43-mun.json', 'r', encoding='utf-8') as f:
        return json.load(f)

geojson_rs = carregar_geojson()

# Função para corrigir nomes de municípios para o mapa
def corrigir_nomes_municipios(df):
    """Corrige nomes de municípios para bater com o GeoJSON"""
    df_corrigido = df.copy()
    
    # Mapeamento de correções
    correcoes = {
        'Restinga Sêca': 'Restinga Seca',
        'Westfália': 'Westfalia', 
        "Sant'Ana do Livramento": "Sant' Ana do Livramento",
        'Vespasiano Corrêa': 'Vespasiano Correa'
    }
    
    # Aplicar correções
    for nome_original, nome_corrigido in correcoes.items():
        df_corrigido.loc[df_corrigido['municipio'] == nome_original, 'municipio'] = nome_corrigido
    
    return df_corrigido

# Função para classificar CNAE em seção
def classificar_secao_cnae(cnae):
    if 1000 <= cnae <= 3999:
        return "Agricultura, Pecuária, Produção Florestal, Pesca e Aquicultura"
    elif 5000 <= cnae <= 9999:
        return "Indústrias Extrativas"
    elif 10000 <= cnae <= 33999:
        return "Indústrias de Transformação"
    elif 35000 <= cnae <= 35999:
        return "Eletricidade e Gás"
    elif 36000 <= cnae <= 39999:
        return "Água, Esgoto, Atividades de Gestão de Resíduos e Descontaminação"
    elif 41000 <= cnae <= 43999:
        return "Construção"
    elif 45000 <= cnae <= 47999:
        return "Comércio, Reparação de Veículos Automotores e Motocicletas"
    elif 49000 <= cnae <= 53999:
        return "Transporte, Armazenagem e Correio"
    elif 55000 <= cnae <= 56999:
        return "Alojamento e Alimentação"
    elif 58000 <= cnae <= 63999:
        return "Informação e Comunicação"
    elif 64000 <= cnae <= 66999:
        return "Atividades Financeiras, de Seguros e Serviços Relacionados"
    elif 68000 <= cnae <= 68999:
        return "Atividades Imobiliárias"
    elif 69000 <= cnae <= 75999:
        return "Atividades Profissionais, Científicas e Técnicas"
    elif 77000 <= cnae <= 82999:
        return "Atividades Administrativas e Serviços Complementares"
    elif 84000 <= cnae <= 84999:
        return "Administração Pública, Defesa e Seguridade Social"
    elif 85000 <= cnae <= 85999:
        return "Educação"
    elif 86000 <= cnae <= 88999:
        return "Saúde Humana e Serviços Sociais"
    elif 90000 <= cnae <= 93999:
        return "Artes, Cultura, Esporte e Recreação"
    elif 94000 <= cnae <= 96999:
        return "Outras Atividades de Serviços"
    elif 97000 <= cnae <= 97999:
        return "Serviços Domésticos"
    elif 99000 <= cnae <= 99999:
        return "Organismos Internacionais e Outras Instituições Extraterritoriais"
    else:
        return "Não classificado"

# Criar coluna de seção CNAE
df["Seção CNAE"] = df["CNAE"].apply(classificar_secao_cnae)

# Listas para filtros
municipios = sorted(df["municipio"].unique())
secoes = sorted(df["Seção CNAE"].unique())

# Sidebar - Filtros globais
st.sidebar.header("Filtros")
municipios_selecionados = st.sidebar.multiselect(
    "Selecione o(s) município(s):", municipios, default=municipios[:1]
)
secoes_selecionadas = st.sidebar.multiselect(
    "Selecione a(s) seção(ões) CNAE:", secoes, default=secoes[:1]
)

# Navegação na sidebar
pagina = st.sidebar.radio(
    "Navegação",
    ("Gráfico Barras CNAE", "Gráfico Linha Temporal", "CNAEs da Seção", "Mapa do RS")
)

# Função para gráfico de barras agrupadas
def grafico_barras():
    df_filtrado = df[
        (df["municipio"].isin(municipios_selecionados)) &
        (df["Seção CNAE"].isin(secoes_selecionadas))
    ].copy()

    colunas_estoque = [col for col in df.columns if col.startswith("estoque_")]
    df_filtrado["total_empregados"] = df_filtrado[colunas_estoque].sum(axis=1)

    df_agg = (
        df_filtrado.groupby(["municipio", "Seção CNAE"])["total_empregados"]
        .sum()
        .reset_index()
    )

    fig = px.bar(
        df_agg,
        x="Seção CNAE",
        y="total_empregados",
        color="municipio",
        barmode="group",
        labels={"total_empregados": "Total de Empregados", "Seção CNAE": "Seção CNAE"},
        title="Total de Empregados por Seção CNAE e Município"
    )

    st.title("Empregados por Seção CNAE e Município")
    st.plotly_chart(fig, use_container_width=True)

# Função para gráfico de linha temporal
def grafico_linha():
    df_filtrado = df[
        (df["municipio"].isin(municipios_selecionados)) &
        (df["Seção CNAE"].isin(secoes_selecionadas))
    ].copy()

    meses = [
        "estoque_jan", "estoque_fev", "estoque_mar", "estoque_abr",
        "estoque_mai", "estoque_jun", "estoque_jul", "estoque_ago", 
        "estoque_set", "estoque_out", "estoque_nov", "estoque_dez"
    ]
    meses_legenda = [
        "Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"
    ]

    dados = []
    for _, row in df_filtrado.iterrows():
        for i, mes in enumerate(meses):
            dados.append({
                "Município": row["municipio"],
                "Seção CNAE": row["Seção CNAE"],
                "Mês": meses_legenda[i],
                "Empregados": row[mes]
            })

    df_linha = pd.DataFrame(dados)
    df_linha["Mês"] = pd.Categorical(df_linha["Mês"], categories=meses_legenda, ordered=True)

    df_linha_agg = (
        df_linha.groupby(["Município", "Seção CNAE", "Mês"])["Empregados"]
        .sum()
        .reset_index()
    )

    fig = px.line(
        df_linha_agg,
        x="Mês",
        y="Empregados",
        color="Município",
        line_dash="Seção CNAE" if len(secoes_selecionadas) > 1 else None,
        markers=True,
        labels={"Empregados": "Total de Empregados", "Mês": "Mês"},
        title="Evolução Mensal de Empregados por Município e Seção CNAE"
    )

    st.title("Evolução Mensal de Empregados")
    st.plotly_chart(fig, use_container_width=True)

def grafico_cnaes_secao():
    st.title("CNAEs de 5 Dígitos por Seção e Município")

    if not secoes_selecionadas:
        st.warning("Selecione pelo menos uma seção CNAE nos filtros.")
        return

    df_filtrado = df[
        (df["municipio"].isin(municipios_selecionados)) &
        (df["Seção CNAE"].isin(secoes_selecionadas))
    ].copy()

    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return

    colunas_estoque = [col for col in df.columns if col.startswith("estoque_")]
    df_filtrado["total_empregados"] = df_filtrado[colunas_estoque].sum(axis=1)

    df_agg = (
        df_filtrado.groupby(["municipio", "CNAE", "Seção CNAE"])["total_empregados"]
        .sum()
        .reset_index()
    )

    df_agg = df_agg[df_agg["total_empregados"] > 0]

    if df_agg.empty:
        st.warning("Nenhum CNAE com empregados encontrado para os filtros selecionados.")
        return

    secoes_titulo = ", ".join(secoes_selecionadas) if len(secoes_selecionadas) <= 3 else f"{len(secoes_selecionadas)} seções selecionadas"

    fig = px.bar(
        df_agg,
        x="CNAE",
        y="total_empregados",
        color="municipio",
        barmode="group",
        labels={"total_empregados": "Total de Empregados", "CNAE": "CNAE (5 dígitos)"},
        title=f"Total de Empregados por CNAE (5 dígitos) - {secoes_titulo}",
        hover_data=["Seção CNAE"]
    )

    if len(df_agg["CNAE"].unique()) > 10:
        fig.update_layout(xaxis_tickangle=-45)

    st.plotly_chart(fig, use_container_width=True)

# Nova função para o mapa do RS
def mapa_rs():
    st.title("Mapa de Estoque por Município - Rio Grande do Sul")
    
    # Aplicar filtros se selecionados
    if municipios_selecionados or secoes_selecionadas:
        df_filtrado = df.copy()
        
        if municipios_selecionados:
            df_filtrado = df_filtrado[df_filtrado["municipio"].isin(municipios_selecionados)]
        
        if secoes_selecionadas:
            df_filtrado = df_filtrado[df_filtrado["Seção CNAE"].isin(secoes_selecionadas)]
        
        # Mostrar informações dos filtros aplicados
        col1, col2 = st.columns(2)
        with col1:
            if municipios_selecionados:
                st.info(f"🏙️ Municípios: {len(municipios_selecionados)} selecionados")
        with col2:
            if secoes_selecionadas:
                st.info(f"🏭 Seções CNAE: {len(secoes_selecionadas)} selecionadas")
    else:
        df_filtrado = df.copy()
        st.info("📍 Mostrando todos os municípios e seções CNAE")
    
    # Agrupar por município
    estoque_por_municipio = df_filtrado.groupby('municipio')['estoque_2023'].sum().reset_index()
    
    if estoque_por_municipio.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return
    
    # Corrigir nomes para corresponder ao GeoJSON
    estoque_corrigido = corrigir_nomes_municipios(estoque_por_municipio)
    
    # Preparar dados para o mapa
    resultado = estoque_corrigido.copy()
    resultado = resultado.rename(columns={'municipio': 'name', 'estoque_2023': 'estoque'})
    
    # Criar o mapa
    fig = px.choropleth(
        resultado,
        geojson=geojson_rs,
        featureidkey="properties.name",
        locations="name",
        color="estoque",
        color_continuous_scale="YlOrRd",
        range_color=[resultado['estoque'].min(), resultado['estoque'].max()],
        labels={'estoque': 'Estoque 2023'},
        title='Estoque Total por Município - Rio Grande do Sul (2023)',
        hover_name="name",
        hover_data={'estoque': ':,'}
    )
    
    # Configurações do mapa
    fig.update_geos(
        fitbounds="locations",
        visible=False
    )
    
    # Layout
    fig.update_layout(
        margin={"r":0,"t":60,"l":0,"b":0},
        width=1000,
        height=700,
        title_x=0.5,
        font=dict(size=12)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Estatísticas resumidas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Municípios Mapeados", len(resultado))
    with col2:
        st.metric("Estoque Total", f"{resultado['estoque'].sum():,}")
    with col3:
        maior_estoque = resultado.loc[resultado['estoque'].idxmax()]
        st.metric("Maior Estoque", f"{maior_estoque['name']}", f"{maior_estoque['estoque']:,}")
    
    # Top 10 municípios
    if len(resultado) > 10:
        st.subheader("🏆 Top 10 Municípios por Estoque")
        top_10 = resultado.nlargest(10, 'estoque')[['name', 'estoque']]
        top_10.columns = ['Município', 'Estoque 2023']
        top_10['Estoque 2023'] = top_10['Estoque 2023'].apply(lambda x: f"{x:,}")
        st.dataframe(top_10, use_container_width=True, hide_index=True)

# Verificar se há municípios selecionados antes de executar
if not municipios_selecionados and pagina != "Mapa do RS":
    st.warning("Selecione pelo menos um município nos filtros da barra lateral.")
elif pagina == "Gráfico Barras CNAE":
    grafico_barras()
elif pagina == "Gráfico Linha Temporal":
    grafico_linha()
elif pagina == "CNAEs da Seção":
    grafico_cnaes_secao()
elif pagina == "Mapa do RS":
    mapa_rs()
