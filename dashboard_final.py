# ==========================================
# DASHBOARD DE ANÁLISIS DE LOS INCIDENTES DE DELINCUENCIA EN LA CIUDAD DE BOGOTÁ ENTRE (2008–2024)
# ==========================================

import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import os

# ------------------------------------------
# CONFIGURACIÓN DE RUTAS RELATIVAS
# ------------------------------------------

# Ruta absoluta del directorio donde está este archivo .py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Carpeta donde guardas los archivos de datos
DATA_DIR = os.path.join(BASE_DIR, "data")

# ------------------------------------------
# CONFIGURACIÓN GENERAL DEL DASHBOARD
# ------------------------------------------

st.set_page_config(
    page_title="Análisis de los incidentes de delincuencia en Bogotá (2008-2024)",
    layout="wide"
)

st.title("Dashboard de Análisis de los incidentes de delincuencia en la ciudad de Bogotá entre (2008–2024)")

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
def cargar_mapa():
    ruta = os.path.join(DATA_DIR, "localidades_bogota.geojson")
    gdf = gpd.read_file(ruta)
    gdf["LOCNOMBRE"] = gdf["LOCNOMBRE"].str.upper().str.strip()
    return gdf

df = cargar_datos()
gdf = cargar_mapa()

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
# FILTRADO DE DATOS
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

df_mapa = df_filtrado.groupby("Localidad", as_index=False)["Valor"].sum()

# ------------------------------------------
# UNIÓN CON GEOJSON
# ------------------------------------------

gdf_mapa = gdf.merge(
    df_mapa,
    left_on="LOCNOMBRE",
    right_on="Localidad",
    how="left"
)

gdf_mapa["Seleccion"] = gdf_mapa["LOCNOMBRE"].isin(localidad_sel)
gdf_mapa["Valor"] = gdf_mapa["Valor"].fillna(0)

# ------------------------------------------
# MAPA COROPLÉTICO
# ------------------------------------------

st.subheader(f"Mapa de delitos por localidad – {año_sel}")

fig_mapa = px.choropleth_mapbox(
    gdf_mapa,
    geojson=gdf_mapa.geometry,
    locations=gdf_mapa.index,
    color="Valor",
    hover_name="LOCNOMBRE",
    opacity=gdf_mapa["Seleccion"].map({True: 0.9, False: 0.4}),
    mapbox_style="carto-positron",
    center={"lat": 4.65, "lon": -74.1},
    zoom=9,
    labels={"Valor": "Total de delitos"}
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
    labels={"Valor": "Total de delitos", "Localidad": "Localidad"}
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
    color_continuous_scale="Blues",
    text="Valor",
    labels={"Valor": "Total de delitos", "Indicador": "Tipo de delito"}
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
    title={"text": "Los años con mayor incidencia delictiva en Bogotá", "x": 0.5},
    xaxis_title="Año",
    yaxis_title="Total de delitos",
    plot_bgcolor="white"
)

if not df_time.empty:
    max_row = df_time.loc[df_time["Valor"].idxmax()]
    fig_time.add_annotation(
        x=max_row["Ano"],
        y=max_row["Valor"],
        text=f"Máximo: {max_row['Ano']}",
        showarrow=True
    )

st.plotly_chart(fig_time, use_container_width=True)

# ------------------------------------------
# HISTOGRAMA
# ------------------------------------------

st.subheader("Histograma: Distribución del total de delitos entre localidades")

fig_hist = px.histogram(
    df_mapa,
    x="Valor",
    nbins=8,
    opacity=0.6,
    color_discrete_sequence=px.colors.sequential.Blues_r,
    labels={"Valor": "Total de delitos por localidad"}
)

media = df_mapa["Valor"].mean()
mediana = df_mapa["Valor"].median()

fig_hist.add_vline(x=media, line_dash="dash", line_color="#2124d1", annotation_text="Media")
fig_hist.add_vline(x=mediana, line_dash="dot", line_color="#46c8e9", annotation_text="Mediana")

fig_hist.update_layout(
    template="plotly_white",
    font=dict(size=13)
)

st.plotly_chart(fig_hist, use_container_width=True)

# ------------------------------------------
# BOX PLOT
# ------------------------------------------

st.subheader("Variabilidad del total delitos por localidad")

fig_box = px.box(
    df_mapa,
    y="Valor",
    points="outliers",
    color_discrete_sequence=px.colors.sequential.Blues
)

fig_box.update_layout(
    template="plotly_white",
    font=dict(size=13),
    yaxis_title="Total de delitos"
)

st.plotly_chart(fig_box, use_container_width=True)

# ------------------------------------------
# RANKING NUMÉRICO
# ------------------------------------------

st.subheader("Ranking de localidades")
st.dataframe(df_bar[["Ranking", "Localidad", "Valor"]], use_container_width=True)

# ------------------------------------------
# TABLA FINAL
# ------------------------------------------

st.subheader("Tabla de datos filtrados")
st.dataframe(df_filtrado, use_container_width=True)

st.success("✅ Dashboard cargado correctamente.")

