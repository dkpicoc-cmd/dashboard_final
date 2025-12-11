# ==========================================
# DASHBOARD DE ANÁLISIS DE LOS INCIDENTES DE DELINCUENCIA EN LA CIUDAD DE BOGOTÁ ENTRE (2008-2024)
# ==========================================

import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px

# ------------------------------------------
# CONFIGURACIÓN GENERAL
# ------------------------------------------
st.set_page_config(
    page_title="Análisis de los incidentes de delincuencia en la ciudad de Bogotá entre (2008-2024)",
    layout="wide"
)

st.title("Dashboard de Análisis de los incidentes de delincuencia en la ciudad de Bogotá entre (2008-2024)")
st.markdown("""
Análisis interactivo de delitos por **localidad**, **año** e **indicador**.  Incluye visualización geográfica oficial de Bogotá.
""")

# ------------------------------------------
# CARGA DE DATOS
# ------------------------------------------
# @st.cache_data
# def cargar_datos():
#     df = pd.read_csv("data_limpia.csv", encoding="latin1")
@st.cache_data
def cargar_datos():
    ruta = r"C:\Users\dkpic\OneDrive\Escritorio\katherine Pico Python\proyecto seguridad de bogota\datos_limpios.csv"
    
    df = pd.read_csv(ruta, encoding="latin1", sep=";")

    return df


@st.cache_data
def cargar_mapa():
    ruta = r"C:\Users\dkpic\OneDrive\Escritorio\katherine Pico Python\proyecto seguridad de bogota\localidades_bogota.geojson"
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

año_sel = st.sidebar.selectbox(
    "Año",
    ["Todos"] + años
)


indicador_sel = st.sidebar.multiselect(
    "Tipo de delito",
    sorted(df["Indicador"].unique()),
    default=df["Indicador"].unique()
)

localidades = sorted(df["Localidad"].unique())

localidad_sel = st.sidebar.multiselect(
    "Localidades",
    localidades,
    default=localidades  # ← TODAS seleccionadas por defecto
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
df_mapa = (
    df_filtrado
    .groupby("Localidad", as_index=False)["Valor"]
    .sum()
)

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

if año_sel == "Todos":
    st.caption("Mostrando datos acumulados de todos los años")
else:
    st.caption(f"Mostrando datos del año {año_sel}")

if localidad_sel == "Todas":
    st.caption("Mostrando todas las localidades")
else:
    st.caption(f"Mostrando únicamente {localidad_sel}")


# ------------------------------------------
# TOP 10 LOCALIDADES 
# ------------------------------------------
st.subheader("Top 10: Localidades con mayor número de delitos")

df_bar = (
    df_mapa
    .sort_values("Valor", ascending=False)
    .head(10)
    .reset_index(drop=True)
)

df_bar["Ranking"] = df_bar.index + 1  # ranking numérico

fig_bar = px.bar(
    df_bar,
    x="Valor",
    y="Localidad",
    orientation="h",
    color="Valor",
    color_continuous_scale="Blues",   # igual que el mapa
    text="Ranking",
    labels={
        "Valor": "Total de delitos",
        "Localidad": "Localidad"
    }
)

fig_bar.update_traces(
    textposition="outside"
)

st.plotly_chart(fig_bar, use_container_width=True)

# ------------------------------------------
# LOS 3 TIPOS DE DELITOS MAS FRECUENTES 
# ------------------------------------------
st.subheader("Tipos de delitos más frecuentes")

df_delitos = (
    df_filtrado
    .groupby("Indicador", as_index=False)["Valor"]
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
    labels={"Valor": "Total de delitos", "Indicador": "Tipo de delito"},
    text="Valor"
)

fig_delitos.update_traces(textposition="outside")

fig_delitos.update_layout(
    coloraxis_showscale=False
)

st.plotly_chart(fig_delitos, use_container_width=True)

# ------------------------------------------
# EVOLUCION DE LOS DELITOS EN EL TIEMPO
# ------------------------------------------
st.subheader("Evolución anual de los delitos en Bogotá (2008–2024)")

df_time = (
    df[df["Indicador"].isin(indicador_sel)]
    .groupby("Ano", as_index=False)["Valor"]
    .sum()
)

fig_time = px.line(
    df_time,
    x="Ano",
    y="Valor",
    markers=True,
)

fig_time.update_layout(
    title={
        "text": "Los años con mayor incidencia delictiva en Bogotá.",
        "x": 0.5
    },
    xaxis_title="Año",
    yaxis_title="Total de delitos registrados",
    plot_bgcolor="white",
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=True, gridcolor="lightgray"),
)

fig_time.update_traces(
    line=dict(color="#0b3e63", width=2),
    marker=dict(size=9, color="#1f77b4"),
    hovertemplate="<b>Año:</b> %{x}<br><b>Delitos:</b> %{y:,}<extra></extra>"
)

# max_row = df_time.loc[df_time["Valor"].idxmax()]
# Evitar ValueError cuando df_time está vacío
if df_time.empty or df_time["Valor"].dropna().empty:
    st.info("No hay datos temporales para las selecciones actuales.")
else:
    max_row = df_time.loc[df_time["Valor"].idxmax()]

    fig_time.add_annotation(
        x=max_row["Ano"],
        y=max_row["Valor"],
        text=f"Máximo histórico: {max_row['Ano']}",
        showarrow=True,
        arrowhead=2,
        arrowcolor="gray",
        font=dict(size=12)
    )

st.plotly_chart(fig_time, use_container_width=True)


# ------------------------------------------
# DISTRIBUCION DEL NUMERO DE DELITOS 
# ------------------------------------------
st.subheader("Histograma:Distribución del total de delitos entre localidades")
st.caption("Permite identificar si la criminalidad está concentrada en pocas localidades "
    "o distribuida de forma homogénea en la ciudad.")

fig_hist = px.histogram(
    df_mapa,
    x="Valor",
    nbins=8,
    opacity=0.6,
    color_discrete_sequence=px.colors.sequential.Blues_r, 
    labels={
        "Valor": "Total de delitos por localidad",
    }
)
# Cálculo de métricas
media = df_mapa["Valor"].mean()
mediana = df_mapa["Valor"].median()

# Líneas de referencia
fig_hist.add_vline(
    x=media,
    line_dash="dash",
    line_color="#2124d1",
    annotation_text="Media",
    annotation_position="top"
)

fig_hist.add_vline(
    x=mediana,
    line_dash="dot",
    line_color="#46c8e9",
    annotation_text="Mediana",
    annotation_position="top"
)

# Ajustes visuales
fig_hist.update_layout(
    xaxis_title="Total de delitos",
    yaxis_title="Número de localidades",
    bargap=0.1,
    template="plotly_white",
    font=dict(size=13)
)

st.plotly_chart(fig_hist, use_container_width=True)

# ------------------------------------------
# LOCALIDADES ATIPICAS
# ------------------------------------------

st.subheader("Variabilidad del total delitos por localidad")
st.caption("Identifica localidades con niveles de criminalidad significativamente "
    "superiores al promedio de la ciudad.")

fig_box = px.box(
    df_mapa,
    y="Valor",
    points="outliers",
    color_discrete_sequence=px.colors.sequential.Blues,
    labels={"Valor": "Total de delitos por localidad"}
)

fig_box.update_layout(
    yaxis_title="Total de delitos",
    xaxis_title="",
    template="plotly_white",
    font=dict(size=13)
)

fig_box.update_traces(
    marker=dict(
        size=10,
        color="#08306b",  # azul oscuro
        opacity=0.9
    ),
    line=dict(width=2)
)

st.plotly_chart(fig_box, use_container_width=True)
# ------------------------------------------
# RANKING NUMÉRICO DE LOCALIDADES
# ------------------------------------------
st.subheader("Ranking de localidades")

st.dataframe(
    df_bar[["Ranking", "Localidad", "Valor"]],
    use_container_width=True
)
q1 = df_mapa["Valor"].quantile(0.25)
q3 = df_mapa["Valor"].quantile(0.75)
iqr = q3 - q1
limite_superior = q3 + 1.5 * iqr

outliers = df_mapa[df_mapa["Valor"] > limite_superior]

# ------------------------------------------
# RESUMEN TABLA DE DATOS
# ------------------------------------------
st.subheader("Tabla de datos filtrados")
st.dataframe(df_filtrado, use_container_width=True)

st.success("✅ Dashboard cargado correctamente")


