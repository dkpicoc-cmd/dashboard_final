# ==========================================
# DASHBOARD DE ANÁLISIS DE LOS INCIDENTES DE DELINCUENCIA EN BOGOTÁ (2008–2024)
# Versión compatible con Streamlit Cloud (SIN GeoPandas)
# ==========================================

import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

# ------------------------------------------
# CONFIGURACIÓN DE RUTAS RELATIVAS
# ------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# ------------------------------------------
# CONFIGURACIÓN GENERAL DEL DASHBOARD
# ------------------------------------------

st.set_page_config(
    page_title="Análisis de delitos en Bogotá (2008–2024)",
    layout="wide"
)

st.title("Dashboard de Análisis de los incidentes de delincuencia en Bogotá (2008–2024)")
st.markdown("""
Análisis interactivo de delitos por **localidad**, **año** e **indicador**, con visualización geográfica oficial de Bogotá.
""")

# ------------------------------------------
# CARGA DE DATOS
# ------------------------------------------

@st.cache_data
def cargar_datos():
    ruta = os.path.join(DATA_DIR, "datos_limpios.csv")
    df = pd.read_csv(ruta, encoding="latin1", sep=";")
    return df

@st.cache_data
def cargar_geojson():
    ruta = os.path.join(DATA_DIR, "localidades_bogota.geojson")
    with open(ruta, "r", encoding="utf-8") as f:
        gjson = json.load(f)
    return gjson

df = cargar_datos()
gjson = cargar_geojson()

# ------------------------------------------
# FILTROS LATERALES
# ------------------------------------------

st.sidebar.header("🔎 Filtros")

años = sorted(df["Ano"].unique())
año_sel = st.sidebar.selectbox("Año", ["Todos"] + años)

indicador_sel = st.sidebar.multiselect(
    "Tipo de delito",
    sorted(df["Indicador"].unique()),
    default=df["Indicador"].unique()
)

localidades = sorted(df["Localidad"].unique())
localidad_sel = st.sidebar.multiselect(
    "Localidades",
    localidades,
    default=localidades
)

# ------------------------------------------
# FILTRADO
# ------------------------------------------

df_filtrado = df[df["Indicador"].isin(indicador_sel)]

if año_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Ano"] == año_sel]

df_filtrado = df_filtrado[df_filtrado["Localidad"].isin(localidad_sel)]

total_delitos = int(df_filtrado["Valor"].sum())
num_localidades = df_filtrado["Localidad"].nunique()
num_indicadores = df_filtrado["Indicador"].nunique()

col1, col2, col3 = st.columns(3)
col1.metric("📈 Total de delitos", f"{total_delitos:,}")
col2.metric("🌐 Localidades", num_localidades)
col3.metric("📖 Tipos de delito", num_indicadores)

# ------------------------------------------
# AGREGACIÓN PARA MAPA
# ------------------------------------------

df_mapa = (
    df_filtrado
    .groupby("Localidad", as_index=False)["Valor"]
    .sum()
)

# ------------------------------------------
# MAPA COROPLÉTICO (SIN GEOPANDAS)
# ------------------------------------------

st.subheader(f"Mapa de delitos por localidad – {año_sel}")

fig_mapa = px.choropleth_mapbox(
    df_mapa,
    geojson=gjson,
    locations="Localidad",
    featureidkey="properties.LOCNOMBRE",
    color="Valor",
    hover_name="Localidad",
    mapbox_style="carto-positron",
    center={"lat": 4.65, "lon": -74.1},
    zoom=9,
    opacity=0.8,
    color_continuous_scale="Blues",
)

st.plotly_chart(fig_mapa, use_container_width=True)

# ------------------------------------------
# TOP 10 LOCALIDADES
# ------------------------------------------

st.subheader("Top 10: Localidades con mayor número de delitos")

df_bar = df_mapa.sort_values("Valor", ascending=False).head(10).reset_index(drop=True)
df_bar["Ranking"] = df_bar.index + 1

fig_bar = px.bar(
    df_bar,
    x="Valor",
    y="Localidad",
    orientation="h",
    color="Valor",
    color_continuous_scale="Blues",
    text="Ranking",
)

fig_bar.update_traces(textposition="outside")
st.plotly_chart(fig_bar, use_container_width=True)

# ------------------------------------------
# TIPOS DE DELITO MÁS FRECUENTES
# ------------------------------------------

st.subheader("Tipos de delitos más frecuentes")

df_delitos = (
    df_filtrado.groupby("Indicador", as_index=False)["Valor"]
    .sum()
    .sort_values("Valor", ascending=False)
    .head(3)
)

fig_delitos = px.bar(
    df_delitos,
    x="Indicador",
    y="Valor",
    color="Valor",
    text="Valor",
    color_continuous_scale="Blues",
)

fig_delitos.update_traces(textposition="outside")
fig_delitos.update_layout(coloraxis_showscale=False)
st.plotly_chart(fig_delitos, use_container_width=True)

# ------------------------------------------
# EVOLUCIÓN ANUAL
# ------------------------------------------

st.subheader("Evolución anual de los delitos en Bogotá (2008–2024)")

df_time = (
    df[df["Indicador"].isin(indicador_sel)]
    .groupby("Ano", as_index=False)["Valor"]
    .sum()
)

fig_time = px.line(df_time, x="Ano", y="Valor", markers=True)

fig_time.update_layout(
    title={"text": "Tendencia histórica de delitos en Bogotá", "x": 0.5},
    plot_bgcolor="white",
)

st.plotly_chart(fig_time, use_container_width=True)

# ------------------------------------------
# HISTOGRAMA
# ------------------------------------------

st.subheader("Distribución del total de delitos entre localidades")

fig_hist = px.histogram(
    df_mapa,
    x="Valor",
    nbins=8,
    opacity=0.7,
    color_discrete_sequence=px.colors.sequential.Blues_r
)

st.plotly_chart(fig_hist, use_container_width=True)

# ------------------------------------------
# BOX PLOT
# ------------------------------------------

st.subheader("Variabilidad del total de delitos por localidad")

fig_box = px.box(
    df_mapa,
    y="Valor",
    points="outliers",
    color_discrete_sequence=px.colors.sequential.Blues
)

st.plotly_chart(fig_box, use_container_width=True)

# ------------------------------------------
# RANKING FINAL
# ------------------------------------------

st.subheader("Ranking de localidades")
st.dataframe(df_bar[["Ranking", "Localidad", "Valor"]], use_container_width=True)

# ------------------------------------------
# TABLA
# ------------------------------------------

st.subheader("Tabla de datos filtrados")
st.dataframe(df_filtrado, use_container_width=True)

st.success("✅ Dashboard cargado correctamente.")
