import os
os.environ["PGCLIENTENCODING"] = "utf-8"

import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px

# 1. CONFIGURACIÓN GENERAL PRO
st.set_page_config(page_title="Analytics Bancario Pro", layout="wide", page_icon="🏦")

# Estilo personalizado simple
st.markdown("""
    <style>
    .big-font { font-size: 24px !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🏦 Sistema Inteligente de Analítica y Riesgo Bancario")
st.caption("Conexión en vivo a Data Warehouse PostgreSQL | Motor Analítico")

# 2. CONEXIÓN A LA BASE DE DATOS
@st.cache_data
def obtener_datos():
    conexion = psycopg2.connect(
        host="localhost",
        port="5432",
        database="datosFinancieros",
        user="postgres",
        password="12345678", # <-- Asegúrate que sea tu contraseña
        client_encoding="utf8"
    )
    df = pd.read_sql("SELECT * FROM vw_dashboard_bancario;", conexion)
    conexion.close()
    return df

try:
    df_raw = obtener_datos()

    # 3. BARRA LATERAL DE FILTROS INTERACTIVOS (SIDEBAR)
    st.sidebar.header("🎛️ Panel de Filtros")
    
    ciudades_list = ["Todas"] + list(df_raw['ciudad'].unique())
    filtro_ciudad = st.sidebar.selectbox("Seleccionar Ciudad / Sucursal:", ciudades_list)
    
    tipos_list = ["Todos"] + list(df_raw['tipo_prestamo'].unique())
    filtro_tipo = st.sidebar.selectbox("Tipo de Producto Bancario:", tipos_list)

    # Aplicar filtros
    df = df_raw.copy()
    if filtro_ciudad != "Todas":
        df = df[df['ciudad'] == filtro_ciudad]
    if filtro_tipo != "Todos":
        df = df[df['tipo_prestamo'] == filtro_tipo]

    # 4. TARJETAS DE INDICADORES CLAVE (KPIs)
    st.markdown("---")
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    
    total_colocado = df['monto_prestamo'].sum()
    total_recuperado = df['total_pagado'].sum()
    tasa_morosidad = (len(df[df['estado_prestamo'] != 'Al Día']) / len(df) * 100) if len(df) > 0 else 0
    
    kpi1.metric("Cartera Colocada", f"${total_colocado:,.0f}")
    kpi2.metric("Total Recuperado", f"${total_recuperado:,.0f}", delta=f"{total_recuperado/total_colocado*100:.1f}% Cobrado")
    kpi3.metric("Créditos Activos", f"{len(df):,}")
    kpi4.metric("Ticket Promedio", f"${df['monto_prestamo'].mean():,.0f}")
    kpi5.metric("Tasa de Mora", f"{tasa_morosidad:.1f}%", delta_color="inverse")

    # 5. PESTAÑAS INTERACTIVAS PARA ORGANIZAR EL VISUALIZADOR
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Visión Estratégica", "🏢 Análisis por Sucursal", "⚠️ Perfil de Riesgo", "📑 Base de Datos"])

    # --- PESTAÑA 1: VISIÓN ESTRATÉGICA ---
    with tab1:
        colA, colB = st.columns(2)
        with colA:
            st.subheader("Distribución de Cartera por Producto")
            fig_tree = px.treemap(
                df, path=['tipo_prestamo', 'estado_prestamo'], values='monto_prestamo',
                color='monto_prestamo', color_continuous_scale='Blues'
            )
            st.plotly_chart(fig_tree, use_container_width=True)
            
        with colB:
            st.subheader("Estado General de Cobranzas")
            fig_donut = px.pie(
                df, names='estado_prestamo', values='monto_prestamo', hole=0.5,
                color_discrete_map={'Al Día':'#2ecc71', 'En Mora (30-60 días)':'#f39c12', 'Incobrable':'#e74c3c'}
            )
            st.plotly_chart(fig_donut, use_container_width=True)

    # --- PESTAÑA 2: POR SUCURSAL ---
    with tab2:
        st.subheader("Comparativa de Colocación de Créditos por Ciudad")
        df_sucursal = df.groupby(['ciudad', 'estado_prestamo'])['monto_prestamo'].sum().reset_index()
        fig_bar_suc = px.bar(
            df_sucursal, x='ciudad', y='monto_prestamo', color='estado_prestamo',
            barmode='stack', labels={'monto_prestamo': 'Monto Total ($)', 'ciudad': 'Ciudad'},
            color_discrete_map={'Al Día':'#2ecc71', 'En Mora (30-60 días)':'#f39c12', 'Incobrable':'#e74c3c'}
        )
        st.plotly_chart(fig_bar_suc, use_container_width=True)

    # --- PESTAÑA 3: RIESGO Y DEMOGRAFÍA ---
    with tab3:
        colC, colD = st.columns(2)
        with colC:
            st.subheader("Ingreso vs. Monto Prestado (Matriz de Riesgo)")
            fig_scatter = px.scatter(
                df, x="ingreso_anual", y="monto_prestamo", color="nivel_riesgo",
                size="tasa_interes", hover_data=["ciudad", "edad"],
                color_discrete_map={'Bajo':'#3498db', 'Medio':'#f1c40f', 'Alto':'#e74c3c'}
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
            
        with colD:
            st.subheader("Edades de Clientes Morosos vs. Al Día")
            fig_box = px.box(df, x="estado_prestamo", y="edad", color="genero")
            st.plotly_chart(fig_box, use_container_width=True)

    # --- PESTAÑA 4: BASE DE DATOS CRUDOS ---
    with tab4:
        st.subheader("Registros Relacionales Exportables")
        st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"❌ Error de conexión al servidor PostgreSQL:\n{repr(e)}")