import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
import os
import numpy as np

# ==============================================================================
# PROYECTO SITS - TABLERO DE INTELIGENCIA SOCIAL Y ESTRATÉGICA
# DIAGNÓSTICO MUNICIPAL CATEMACO 2026
# ==============================================================================
# MÓDULO VISUALIZADOR "SITS MANAGER"
# Versión: 7.3 (FIX FINAL: Visualización de Ríos en Capa Superior)
# ==============================================================================

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    layout="wide", 
    page_title="SITS Catemaco Social 2026", 
    page_icon="🦅",
    initial_sidebar_state="expanded"
)

# 2. ESTILOS CSS (ESTRUCTURA COMPLETA Y ROBUSTA)
st.markdown("""
<style>
    /* Tarjetas de KPI Principales */
    .kpi-card { 
        background-color: #ffffff; 
        border-radius: 8px; 
        padding: 20px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
        border-left: 5px solid #e74c3c; 
        text-align: center; 
        margin-bottom: 10px; 
    }
    
    /* Contenedor de Filtros */
    .filter-container { 
        background-color: #f1f2f6; 
        padding: 15px; 
        border-radius: 8px; 
        border: 1px solid #dfe4ea; 
        margin-bottom: 15px; 
    }
    
    /* Pie de Página Institucional */
    .footer-ccpi { 
        font-size: 11px; 
        color: #999; 
        text-align: center; 
        margin-top: 40px; 
        border-top: 1px solid #ccc; 
        padding-top: 15px; 
    }
    
    /* Cajas de Semáforo (Tab 1) */
    .semaforo-box { 
        padding: 10px; 
        border-radius: 5px; 
        color: white; 
        text-align: center; 
        margin-bottom: 5px; 
        font-size: 12px; 
        font-weight: bold;
    }
    
    /* Cajas de Interpretación */
    .interpretacion-box { 
        background-color: #e8f6f3; 
        padding: 15px; 
        border-radius: 5px; 
        border-left: 5px solid #1abc9c; 
        margin-bottom: 20px; 
    }
    
    /* Cajas de Conceptos MCR */
    .concepto-box { 
        background-color: #fff8e1; 
        padding: 10px; 
        border-radius: 5px; 
        border-left: 4px solid #ffc107; 
        font-size: 14px; 
        margin-bottom: 15px;
    }
    
    /* Cajas Marco de Sendai */
    .sendai-box { 
        background-color: #e3f2fd; 
        padding: 15px; 
        border-radius: 5px; 
        border-left: 5px solid #2196f3; 
        margin-bottom: 20px; 
        font-size: 14px; 
    }
    
    /* Cajas Economía */
    .eco-box { 
        background-color: #e8f5e9; 
        padding: 15px; 
        border-radius: 5px; 
        border-left: 5px solid #2e7d32; 
        margin-bottom: 20px; 
        font-size: 14px; 
    }
    
    /* Títulos de Sección */
    .section-title { 
        font-size: 18px; 
        font-weight: bold; 
        color: #2c3e50; 
        margin-top: 20px; 
        margin-bottom: 10px; 
        border-bottom: 2px solid #ecf0f1; 
        padding-bottom: 5px;
    }
    
    /* Cajas de Alerta (Rojas) */
    .alert-box { 
        background-color: #ffebee; 
        padding: 15px; 
        border-radius: 5px; 
        border-left: 5px solid #c62828; 
        color: #c62828; 
        font-weight: bold; 
        font-size: 15px; 
    }
    
    /* Cajas Legales (Naranjas) */
    .legal-box { 
        background-color: #fdf2e9; 
        padding: 15px; 
        border-radius: 5px; 
        border-left: 5px solid #d35400; 
        font-size: 13px; 
        margin-bottom: 20px; 
    }
    
    /* Cajas de Dictamen Técnico (Nueva Pestaña) */
    .dictamen-ok {
        background-color: #e8f5e9;
        color: #1b5e20;
        font-weight: bold;
        padding: 5px;
        border-radius: 4px;
        text-align: center;
    }
    .dictamen-error {
        background-color: #ffebee;
        color: #b71c1c;
        font-weight: bold;
        padding: 5px;
        border-radius: 4px;
        text-align: center;
    }
    /* Explicaciones Fáciles (Caja Azul) */
    .facil-box { 
        background-color: #e3f2fd; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 6px solid #2196f3; 
        font-size: 15px; 
        margin-bottom: 20px; 
        color: #0d47a1;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏛️ SITS: Sistema de Inteligencia Territorial")
st.markdown("**Diagnóstico Estratégico Municipal 2026 (Metodología ONU/OPHI + Ingeniería Territorial)**")

# 3. CARGA DE DATOS (CON CACHE Y FIX DE RÍOS)
@st.cache_data
def cargar_datos():
    """
    Carga los archivos GeoJSON procesados que contienen TODA la inteligencia:
    Social, Económica, Riesgo e Ingeniería (Pendientes/Restricciones).
    """
    f_urb = "output/sits_capa_urbana.geojson"
    f_rur = "output/sits_capa_rural.geojson"
    
    # --- LÓGICA DE BÚSQUEDA DE RÍOS ---
    # Buscamos en varias rutas y con el nombre original o el renombrado
    posibles_rios = [
        "data/mapas/rios.shp", 
        "shp/rios.shp", 
        "rios.shp",
        "data/mapas/RH28Ar_hl.shp", # Nombre original INEGI
        "shp/RH28Ar_hl.shp"
    ]
    
    gdf_rios = None
    for ruta in posibles_rios:
        if os.path.exists(ruta):
            try:
                # IMPORTANTE: Forzamos la conversión a EPSG:4326 (Lat/Lon)
                # Si no se hace esto, el río no se ve en el mapa web.
                temp = gpd.read_file(ruta)
                gdf_rios = temp.to_crs(epsg=4326)
                break
            except Exception as e:
                continue

    # Carga de Mapas Base
    u = gpd.read_file(f_urb) if os.path.exists(f_urb) else None
    r = gpd.read_file(f_rur) if os.path.exists(f_rur) else None
    
    if u is not None:
        u['TIPO'] = 'Urbano'
        if 'NOM_LOC' not in u.columns: u['NOM_LOC'] = 'Catemaco (Cabecera)'
        if 'CVE_AGEB' not in u.columns: u['CVE_AGEB'] = u.get('AGEB', 'SN')
    
    if r is not None:
        r['TIPO'] = 'Rural'
        if 'NOM_LOC' not in r.columns: r['NOM_LOC'] = r.get('NOMGEO', 'Rural')
        r['CVE_AGEB'] = 'RURAL'
        
    return u, r, gdf_rios

# Desempaquetamos los 3 objetos
gdf_u, gdf_r, gdf_rios = cargar_datos()

if gdf_u is None or gdf_r is None:
    st.error("🚨 ERROR CRÍTICO: No se encuentran los archivos GeoJSON en la carpeta 'output/'. Ejecuta primero 'generar_datos_final.py'.")
    st.stop()

# 4. BARRA LATERAL (FILTROS)
with st.sidebar:
    st.header("🎛️ Filtros de Control")
    st.info("Utiliza estos controles para segmentar la información en todo el tablero.")
    
    # Filtro Tipo Comunidad
    tipo_comunidad = st.radio(
        "🌎 Tipo de Comunidad:", 
        ["TODO EL MUNICIPIO", "Urbana (Cabecera)", "Rural"]
    )
    
    # Crear copias para no afectar cache
    du = gdf_u.copy()
    dr = gdf_r.copy()
    
    # Aplicar Filtro Tipo
    if tipo_comunidad == "Urbana (Cabecera)":
        dr = dr[dr['TIPO'] == 'Imposible'] # Vaciar rural
    elif tipo_comunidad == "Rural":
        du = du[du['TIPO'] == 'Imposible'] # Vaciar urbano
        
    # Filtro Localidad
    locs = sorted(list(set(du['NOM_LOC'].unique()) | set(dr['NOM_LOC'].unique())))
    sel_loc = st.selectbox("📍 Localidad Específica:", ["TODAS"] + locs)
    
    if sel_loc != "TODAS":
        du = du[du['NOM_LOC'] == sel_loc]
        dr = dr[dr['NOM_LOC'] == sel_loc]
        
    # Filtro AGEB (Solo Urbano)
    sel_ageb = "TODAS"
    if not du.empty and tipo_comunidad != "Rural":
        agebs = sorted(du['CVE_AGEB'].unique())
        sel_ageb = st.selectbox("🏘️ AGEB (Urbano):", ["TODAS"] + agebs)
        if sel_ageb != "TODAS":
            du = du[du['CVE_AGEB'] == sel_ageb]

    st.markdown("---")
    st.markdown("**Indicador de Carencia (Mapas Generales):**")
    dict_inds = {
        "SITS_INDEX": "🔥 Índice Pobreza Multidimensional",
        "CAR_POBREZA_20": "💰 Línea de Pobreza (Ingresos)",
        "CAR_SERV_20": "🚰 Servicios Básicos y Energía",
        "CAR_VIV_20": "🏠 Calidad y Espacios Vivienda",
        "CAR_SALUD_20": "🏥 Acceso a Salud",
        "CAR_EDU_20": "🎓 Rezago Educativo"
    }
    carencia_key = st.radio("Variable a Visualizar:", list(dict_inds.keys()), format_func=lambda x: dict_inds[x])
    
    st.markdown("""
    <div class="footer-ccpi">
        <b>CCPI</b><br>Consultoría en Comunicación Política Integral<br><br>
        Autor:<br><b>Mtro. Roberto Ibarra Suárez</b><br><br>
        DERECHOS RESERVADOS © 2026
    </div>
    """, unsafe_allow_html=True)

# Unificar dataframes filtrados
df_zona = pd.concat([du, dr], ignore_index=True)
lbl_zona = sel_loc if sel_ageb == "TODAS" else f"{sel_loc} - AGEB {sel_ageb}"

# ==============================================================================
# 🛡️ BLINDAJE DE DATOS (NUEVO) - Evita que la App se rompa si faltan columnas
# ==============================================================================
cols_ing = ['PENDIENTE_PROMEDIO', 'RESTRICCION_GAS', 'RESTRICCION_AGUA', 'DICTAMEN_VIABILIDAD', 'CLASIFICACION_TOPOGRAFICA']
for col in cols_ing:
    # 1. Blindar DataFrame Principal
    if col not in df_zona.columns:
        val = 0 if 'PENDIENTE' in col or 'RESTRICCION' in col else "Sin Análisis"
        df_zona[col] = val
    
    # 2. Blindar Copias de Mapas (Para visualización)
    if col not in du.columns: du[col] = 0 if 'PENDIENTE' in col or 'RESTRICCION' in col else "Sin Análisis"
    if col not in dr.columns: dr[col] = 0 if 'PENDIENTE' in col or 'RESTRICCION' in col else "Sin Análisis"
# ==============================================================================

# 5. ESTRUCTURA DE PESTAÑAS (TABS) - AHORA CON 9 PESTAÑAS
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "🗺️ MAPA GENERAL", 
    "📊 ESTADÍSTICA", 
    "📋 PADRÓN", 
    "⚖️ COMPARATIVA", 
    "🛡️ RESILIENCIA (MCR)", 
    "🌍 MARCO DE SENDAI", 
    "🎯 TOMA DE DECISIONES", 
    "🏭 ECONOMÍA",
    "🏗️ VIABILIDAD URBANA"
])

# --- TAB 1: MAPA GENERAL ---
with tab1:
    col_map, col_ley = st.columns([3, 1])
    
    with col_map:
        if not df_zona.empty:
            # Centrar mapa
            lat = df_zona.geometry.centroid.y.mean()
            lon = df_zona.geometry.centroid.x.mean()
            m = folium.Map([lat, lon], zoom_start=13, tiles="CartoDB positron")
            
            # Capa Urbana (Polígonos)
            if not du.empty:
                folium.Choropleth(
                    geo_data=du, 
                    data=du, 
                    columns=['CVEGEO', carencia_key],
                    key_on='feature.properties.CVEGEO', 
                    fill_color='YlOrRd', 
                    fill_opacity=0.7, 
                    line_opacity=0.1, 
                    name="Urbano",
                    legend_name=f"{dict_inds[carencia_key]}"
                ).add_to(m)
            
            # Capa Rural (Puntos)
            if not dr.empty:
                for _, r in dr.iterrows():
                    if r.geometry.is_empty: continue
                    val = r[carencia_key]
                    # Lógica de colores manual para puntos
                    if val >= 0.4: c = '#800000' # Crítico
                    elif val >= 0.25: c = '#ff0000' # Alto
                    elif val >= 0.15: c = '#ffa500' # Medio
                    else: c = '#27ae60' # Bajo
                    
                    folium.CircleMarker(
                        location=[r.geometry.centroid.y, r.geometry.centroid.x],
                        radius=7, 
                        color='white', 
                        weight=1, 
                        fill=True, 
                        fill_color=c, 
                        fill_opacity=0.9,
                        popup=f"<b>{r['NOM_LOC']}</b><br>Valor: {val:.1%}"
                    ).add_to(m)
            
            st_folium(m, height=550, use_container_width=True)
        else: 
            st.warning("No hay datos para la selección actual.")
            
    with col_ley:
        st.subheader("Semáforo de Interpretación")
        st.markdown(f"**Variable:** {dict_inds[carencia_key]}")
        st.markdown("""
        <div style="background-color:#800000;" class="semaforo-box">CRÍTICO (>40%)</div>
        <div style="background-color:#ff0000;" class="semaforo-box">ALTO (25-40%)</div>
        <div style="background-color:#ffa500;" class="semaforo-box">MEDIO (15-25%)</div>
        <div style="background-color:#27ae60;" class="semaforo-box">BAJO (<15%)</div>
        <br>
        <div style='font-size:11px; text-align:justify;'>
        Este mapa muestra la intensidad de la carencia seleccionada. Las zonas rojas requieren intervención prioritaria inmediata según los lineamientos del CONEVAL.
        </div>
        """, unsafe_allow_html=True)

# --- TAB 2: ESTADÍSTICA ---
with tab2:
    st.subheader("📊 Análisis Demográfico y Social")
    
    # KPIs Superiores
    if not df_zona.empty:
        pob_tot = df_zona['P25_TOT'].sum()
        pob_u = df_zona[df_zona['TIPO']=='Urbano']['P25_TOT'].sum()
        pob_r = df_zona[df_zona['TIPO']=='Rural']['P25_TOT'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Población Total (Proyección 2025)", f"{int(pob_tot):,}")
        c2.metric("Población Urbana", f"{int(pob_u):,}")
        c3.metric("Población Rural", f"{int(pob_r):,}")
        st.divider()

    c_sel, c_res = st.columns([1, 3])
    with c_sel:
        st.markdown("**Analizar Grupo Vulnerable:**")
        grupos = {
            "Población Total": "P25_TOT", 
            "Mujeres": "P25_FEM", 
            "Hombres": "P25_MAS",
            "Jefas de Familia": "P25_JEFAS", 
            "Indígena": "P25_IND", 
            "Afromexicana": "P25_AFRO",
            "Discapacidad": "P25_DISC", 
            "Niños (0-14)": "P25_NINOS", 
            "Adultos Mayores": "P25_MAYORES"
        }
        sel_g = st.selectbox("Seleccione Grupo:", list(grupos.keys()))
        col_g = grupos[sel_g]

    # Gráfico de Afectación
    if not df_zona.empty and col_g in df_zona.columns:
        tot_g = df_zona[col_g].sum()
        # Cálculo ponderado de afectación
        afec = (df_zona[col_g] * df_zona[carencia_key]).sum()
        pct_afec = (afec / tot_g * 100) if tot_g > 0 else 0
        
        with c_res:
            k1, k2 = st.columns(2)
            k1.metric(f"Total {sel_g}", f"{int(tot_g):,}")
            k2.metric(f"Personas Afectadas ({dict_inds[carencia_key]})", f"{int(afec):,}", f"{pct_afec:.1f}% de incidencia")
        
        # Gráfico de Barras por Dimensión
        dims_vals = []
        dims_names = ['Ingreso', 'Servicios', 'Vivienda', 'Salud', 'Educación']
        dims_keys = ['CAR_POBREZA_20', 'CAR_SERV_20', 'CAR_VIV_20', 'CAR_SALUD_20', 'CAR_EDU_20']
        
        for d in dims_keys:
            val_d = (df_zona[col_g] * df_zona[d]).sum()
            dims_vals.append(val_d)
            
        fig_bar = px.bar(
            x=dims_names, 
            y=dims_vals, 
            title=f"Afectación Multidimensional en {sel_g}",
            labels={'x':'Dimensión', 'y':'Personas Afectadas'},
            color=dims_vals,
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# --- TAB 3: PADRÓN ---
with tab3:
    st.subheader("📋 Padrón Focalizado (Gestión de Apoyos)")
    st.info("Listado priorizado para la distribución eficiente de recursos (Despensas/Apoyos). Se incluye el cálculo de familias estimadas.")
    
    if not df_zona.empty and col_g in df_zona.columns:
        # CÁLCULOS MEJORADOS (VISIÓN ALCALDE)
        df_zona['PERSONAS_PRIORITARIAS'] = df_zona[col_g] * df_zona[carencia_key]
        
        # Cálculo de Familias (Promedio 3.6 habitantes por hogar en Veracruz)
        df_zona['FAMILIAS_ESTIMADAS'] = df_zona['PERSONAS_PRIORITARIAS'] / 3.6 
        
        # Selección de columnas que incluyan las 6 dimensiones básicas
        cols_base = ['NOM_LOC', 'TIPO', 'CVE_AGEB', 'P25_TOT', col_g, 'PERSONAS_PRIORITARIAS', 'FAMILIAS_ESTIMADAS', 'SITS_INDEX']
        cols_dimensiones = ['CAR_POBREZA_20', 'CAR_SERV_20', 'CAR_VIV_20', 'CAR_SALUD_20', 'CAR_EDU_20']
        
        cols_deseadas = cols_base + cols_dimensiones
        cols_unicas = list(dict.fromkeys(cols_deseadas))
        
        top = df_zona[cols_unicas].sort_values('PERSONAS_PRIORITARIAS', ascending=False).head(100).reset_index(drop=True)
        
        # ESTILO: ALERTA VISUAL EN ROJO SI SITS_INDEX > 0.3
        def resaltar_critico(val):
            color = '#ffcccc' if val > 0.3 else '' # Rojo claro
            return f'background-color: {color}'

        # Formateo
        fmt_dims = {d: "{:.1%}" for d in cols_dimensiones}
        fmt_base = {
            col_g: "{:,.0f}", 
            'PERSONAS_PRIORITARIAS': "{:,.0f}", 
            'FAMILIAS_ESTIMADAS': "{:,.0f}",
            'SITS_INDEX': "{:.2f}"
        }
        fmt_all = {**fmt_base, **fmt_dims}

        st.dataframe(
            top.style
            .format(fmt_all)
            .applymap(resaltar_critico, subset=['SITS_INDEX'])
            .background_gradient(cmap='Reds', subset=['FAMILIAS_ESTIMADAS']), 
            use_container_width=True
        )
        
        st.download_button(
            "💾 Descargar Padrón para Logística (CSV)", 
            top.to_csv(index=False).encode('utf-8'), 
            "padron_familias_2026.csv", 
            "text/csv"
        )

# --- TAB 4: COMPARATIVA ---
with tab4:
    st.subheader("⚖️ Evolución Comparativa 2020-2025")
    st.markdown("Análisis de brechas y cumplimiento de metas de la administración.")
    
    if not df_zona.empty:
        p20 = df_zona['P20_TOT'].sum()
        p25 = df_zona['P25_TOT'].sum()
        st.metric("Crecimiento Demográfico Total", f"{int(p25-p20):,}", f"{(p25-p20)/p20*100:.1f}%")
        
        col_charts = st.columns(2)
        dims = ['CAR_POBREZA_20', 'CAR_SERV_20', 'CAR_VIV_20', 'CAR_SALUD_20', 'CAR_EDU_20']
        noms = ['Ingreso', 'Servicios', 'Vivienda', 'Salud', 'Educación']
        
        # Generar gráficos comparativos uno por uno
        for i, (d, n) in enumerate(zip(dims, noms)):
             v20 = df_zona[d].mean()*100
             v25 = v20*0.95 # Simulación de meta del 5%
             
             fig = go.Figure(data=[
                 go.Bar(name='2020 (Base)', x=[n], y=[v20], marker_color='#95a5a6'),
                 go.Bar(name='2025 (Meta)', x=[n], y=[v25], marker_color='#27ae60')
             ])
             fig.update_layout(title=f"Evolución Indicador: {n}", height=300)
             
             with col_charts[i % 2]:
                 st.plotly_chart(fig, use_container_width=True)

# --- TAB 5: RESILIENCIA (MCR2030) ---
with tab5:
    st.header("🛡️ Gestión de Riesgos y Resiliencia (MCR2030)")
    
    col_izq, col_der = st.columns([1, 2])
    
    with col_izq:
        st.markdown("<div class='section-title'>1. Configuración</div>", unsafe_allow_html=True)
        eje = st.radio("Eje de Impacto (MCR):", ["💧 Hídrica (Agua)", "🌳 Ambiental (Salud)", "🚨 Social (Economía)"])
        
        if "Hídrica" in eje: 
            ind = "IND_RESILIENCIA_HIDRICA"; clr = "Blues"
            titulo_c = "💧 Gestión de Agua (Pipas)"; txt_c = "Zonas sin almacenamiento (tinacos) que requieren abasto inmediato en estiaje."
        elif "Ambiental" in eje: 
            ind = "IND_PRESION_AMBIENTAL"; clr = "Reds"
            titulo_c = "🌳 Presión Ambiental"; txt_c = "Hogares que generan humo (leña) o no tienen drenaje, afectando la salud pública."
        else: 
            ind = "IND_RIESGO_SOCIAL"; clr = "Oranges"
            titulo_c = "🚨 Riesgo Social"; txt_c = "Dificultad de recuperación económica ante desastres."
            
        st.markdown(f"<div class='concepto-box'><b>{titulo_c}</b><br>{txt_c}</div>", unsafe_allow_html=True)

    with col_der:
        st.markdown("<div class='section-title'>2. Dossier Estratégico</div>", unsafe_allow_html=True)
        if not df_zona.empty and ind in df_zona.columns:
            # En Hídrica, MENOR valor es PEOR (menos tinacos). En otros, MAYOR es PEOR.
            ascending_sort = True if "Hídrica" in eje else False
            
            critico = df_zona.sort_values(ind, ascending=ascending_sort).iloc[0] 
            nom_crit = critico['NOM_LOC']
            prom = df_zona[ind].mean()
            
            txt = f"""REPORTE MCR2030 - CATEMACO:\nEl municipio tiene un índice promedio de {prom:.2f}.\nFoco Rojo: La localidad '{nom_crit}' presenta valores extremos que comprometen su resiliencia."""
            st.text_area("📋 Ficha Técnica para Cabildo:", txt, height=120)

    st.markdown("---")
    st.markdown("<div class='section-title'>3. Mapa de Riesgos</div>", unsafe_allow_html=True)
    if not df_zona.empty:
        lat = df_zona.geometry.centroid.y.mean()
        lon = df_zona.geometry.centroid.x.mean()
        m2 = folium.Map([lat, lon], zoom_start=13, tiles="CartoDB positron")
        
        if not du.empty:
            folium.Choropleth(
                geo_data=du, 
                data=du, 
                columns=['CVEGEO', ind], 
                key_on='feature.properties.CVEGEO', 
                fill_color=clr, 
                fill_opacity=0.7, 
                line_opacity=0.1,
                legend_name=f"Índice {eje}"
            ).add_to(m2)
            
        st_folium(m2, height=450, use_container_width=True)

    st.markdown("<div class='section-title'>4. Detalle Operativo (Logística de Pipas/Apoyos)</div>", unsafe_allow_html=True)
    if not df_zona.empty:
        # LÓGICA DE ALCALDE: DEFINICIÓN DE ESTATUS OPERATIVO SEGÚN EJE
        
        # 1. HÍDRICA
        if "Hídrica" in eje:
            def status_hidrico(val):
                if val < 0.4: return "🔴 URGENTE (24 HRS - Sin Tinaco)"
                elif val < 0.7: return "🟡 PROGRAMADA (48 HRS)"
                else: return "🟢 RESILIENTE (Tiene Cisterna)"
            df_zona['ESTATUS_OPERATIVO'] = df_zona[ind].apply(status_hidrico)
            nombre_archivo = "logistica_pipas_agua.csv"
            
        # 2. AMBIENTAL
        elif "Ambiental" in eje:
            def status_ambiental(val):
                if val > 0.4: return "🔴 FOCO INFECCIÓN (Drenaje/Humo)"
                elif val > 0.2: return "🟡 RIESGO LATENTE"
                else: return "🟢 SANEADO"
            df_zona['ESTATUS_OPERATIVO'] = df_zona[ind].apply(status_ambiental)
            nombre_archivo = "focos_infeccion_ambiental.csv"
            
        # 3. SOCIAL
        else: # Social
            def status_social(val):
                if val > 0.3: return "🔴 PROGRAMA EMPLEO TEMPORAL"
                elif val > 0.15: return "🟡 CAPACITACIÓN/MICROCRÉDITO"
                else: return "🟢 ESTABLE"
            df_zona['ESTATUS_OPERATIVO'] = df_zona[ind].apply(status_social)
            nombre_archivo = "apoyos_empleo_social.csv"

        cols_tb = ['NOM_LOC', 'TIPO', 'CVE_AGEB', 'P25_TOT', ind, 'ESTATUS_OPERATIVO']
        # Ordenamos: si es agua, los que tienen menos (ascendente). Si es riesgo, los que tienen más (descendente).
        ascending_order = True if "Hídrica" in eje else False
        tb = df_zona[list(dict.fromkeys(cols_tb))].sort_values(ind, ascending=ascending_order).reset_index(drop=True)
        
        st.dataframe(
            tb.style.format({ind: "{:.2f}", 'P25_TOT': "{:,.0f}"})
            .background_gradient(cmap=clr, subset=[ind]), 
            use_container_width=True
        )
        
        st.download_button(
            f"💾 Descargar Reporte Operativo ({eje})", 
            tb.to_csv(index=False).encode('utf-8'), 
            nombre_archivo, 
            "text/csv"
        )

# --- TAB 6: MARCO DE SENDAI ---
with tab6:
    st.header("🌍 Marco de Sendai (Protección Civil)")
    col_s1, col_s2 = st.columns([1, 2])
    
    with col_s1:
        st.markdown("<div class='section-title'>1. Prioridades de Acción</div>", unsafe_allow_html=True)
        prioridad = st.radio("Fase de Gestión:", ["1. Preparación (Evacuación)", "3. Prevención (Vivienda)", "4. Respuesta (Capacidad)"])
        
        if "1." in prioridad:
            ind_sendai = "SENDAI_P1_VULNERABILIDAD"; color_s = "Oranges"; 
            titulo_p = "🚑 Población Requiere Evacuación Asistida"; 
            desc_p = "Personas (Ancianos, Discapacitados, Niños) que **NO PUEDEN SALIR SOLOS** ante una emergencia."
        elif "3." in prioridad:
            ind_sendai = "SENDAI_P3_FRAGILIDAD"; color_s = "Reds"; 
            titulo_p = "🏗️ Fragilidad Física (Vivienda)"; 
            desc_p = "Viviendas en riesgo de colapso por materiales precarios (Paredes/Techos endebles)."
        else:
            ind_sendai = "SENDAI_P4_FALTACAPACIDAD"; color_s = "Purples"; 
            titulo_p = "📡 Falta de Capacidad (Comunicaciones)"; 
            desc_p = "Zonas incomunicadas (Sin celular/internet/transporte) que requieren alerta temprana."
            
        st.markdown(f"<div class='sendai-box'><b>{titulo_p}</b><br>{desc_p}</div>", unsafe_allow_html=True)

    with col_s2:
        st.markdown("<div class='section-title'>2. Cálculo de Recursos</div>", unsafe_allow_html=True)
        
        # CÁLCULOS ESPECÍFICOS POR PRIORIDAD (Visión Alcalde)
        if "1." in prioridad and not df_zona.empty:
            # Evacuación
            df_zona['POB_VULNERABLE_TOTAL'] = df_zona['P25_TOT'] * df_zona[ind_sendai]
            df_zona['RECURSO_NECESARIO'] = df_zona['POB_VULNERABLE_TOTAL'] / 10 
            label_recurso = "Camionetas de Rescate (10 pax)"
            total_recurso = df_zona['RECURSO_NECESARIO'].sum()
            st.metric(f"Total {label_recurso}", f"{int(total_recurso)} Unidades")
            
        elif "3." in prioridad and not df_zona.empty:
            # Vivienda (Prevención)
            # Estimamos viviendas precarias = (Pob Total / 3.6) * Índice Fragilidad
            df_zona['VIVIENDAS_RIESGO'] = (df_zona['P25_TOT'] / 3.6) * df_zona[ind_sendai]
            df_zona['RECURSO_NECESARIO'] = df_zona['VIVIENDAS_RIESGO']
            label_recurso = "Viviendas a Reforzar (Techo/Muro)"
            total_recurso = df_zona['RECURSO_NECESARIO'].sum()
            st.metric(f"Total {label_recurso}", f"{int(total_recurso)} Casas")
            
        elif "4." in prioridad and not df_zona.empty:
            # Capacidad (Respuesta)
            # Si el índice es alto (>0.8), la zona está en "Silencio". 
            # Calculamos población en zonas de silencio.
            df_zona['POB_INCOMUNICADA'] = df_zona.apply(lambda x: x['P25_TOT'] if x[ind_sendai] > 0.7 else 0, axis=1)
            df_zona['RECURSO_NECESARIO'] = df_zona.apply(lambda x: 1 if x[ind_sendai] > 0.7 else 0, axis=1) # 1 Antena/Radio por zona crítica
            label_recurso = "Puntos Ciegos (Requieren Radio/Antena)"
            total_recurso = df_zona['RECURSO_NECESARIO'].sum()
            st.metric(f"Total {label_recurso}", f"{int(total_recurso)} Sitios")

    st.markdown("---")
    st.markdown("<div class='section-title'>3. Mapa de Riesgos ONU</div>", unsafe_allow_html=True)
    if not df_zona.empty:
        lat = df_zona.geometry.centroid.y.mean()
        lon = df_zona.geometry.centroid.x.mean()
        ms = folium.Map([lat, lon], zoom_start=13, tiles="CartoDB dark_matter")
        
        if not du.empty:
             folium.Choropleth(
                 geo_data=du, 
                 data=du, 
                 columns=['CVEGEO', ind_sendai], 
                 key_on='feature.properties.CVEGEO', 
                 fill_color=color_s, 
                 fill_opacity=0.8, 
                 line_opacity=0.1
             ).add_to(ms)
             
        st_folium(ms, height=450, use_container_width=True)  

    st.markdown("<div class='section-title'>4. Plan de Acción (Política Pública)</div>", unsafe_allow_html=True)
    if not df_zona.empty:
        cols_ts = ['NOM_LOC', 'TIPO', 'CVE_AGEB', 'P25_TOT', ind_sendai, 'RECURSO_NECESARIO']
        
        tb_s = df_zona[list(dict.fromkeys(cols_ts))].sort_values(ind_sendai, ascending=False).head(100).reset_index(drop=True)
        
        fmt = {ind_sendai: "{:.1%}", 'P25_TOT': "{:,.0f}", 'RECURSO_NECESARIO': "{:,.1f}"}
        
        st.dataframe(tb_s.style.format(fmt).background_gradient(cmap=color_s), use_container_width=True)
        
        # Nombre de archivo dinámico
        if "1." in prioridad: fname = "sendai_plan_evacuacion.csv"
        elif "3." in prioridad: fname = "sendai_plan_vivienda.csv"
        else: fname = "sendai_plan_comunicaciones.csv"
        
        st.download_button(f"💾 Descargar Plan Operativo ({prioridad})", tb_s.to_csv().encode('utf-8'), fname, "text/csv")

# --- TAB 7: TOMA DE DECISIONES ---
with tab7:
    st.header("🎯 Toma de Decisiones y Cruce Estratégico")
    st.markdown("Identificación de **Zonas de Atención Prioritaria (ZAP)** mediante la intersección de variables.")

    # TEXTO LEGAL RECUPERADO (ARTÍCULOS COMPLETOS)
    st.markdown("""
    <div class="legal-box">
    <b>⚖️ FUNDAMENTO JURÍDICO PARA ASIGNACIÓN DE RECURSOS (DECRETO 491 - PRESUPUESTO 2026):</b><br><br>
    <ul>
        <li><b>ARTÍCULO 7 (Prioridad Social):</b> Los entes públicos están obligados a priorizar la asignación presupuestal a la población con indicadores de pobreza y marginación (Zonas Azules). Las inversiones deben dirigirse preferentemente a reducir las brechas de desigualdad identificadas en los diagnósticos oficiales.</li>
        <li><b>ARTÍCULO 68 (Inversión Pública):</b> Se define legalmente como "Inversión Pública" prioritaria las acciones de protección civil, remediación ambiental, combate a la pobreza y <b>reactivación económica regional (incluyendo infraestructura para Turismo)</b>. Toda obra debe contar con justificación socioeconómica.</li>
        <li><b>ARTÍCULO 38 (Recursos Extraordinarios):</b> Faculta a la Secretaría de Finanzas para autorizar <b>modificaciones presupuestales inmediatas</b> ante situaciones de contingencia y riesgo de desastres (Zonas Rojas/Sendai), permitiendo la reasignación de partidas para salvaguardar la vida de la población.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

    # 1. VISUALIZACIÓN ESTRATÉGICA
    st.markdown("<div class='section-title'>1. Visualización de Capas</div>", unsafe_allow_html=True)
    capa_activa = st.radio("Seleccione Capa de Análisis:", 
             ["1. Pobreza Multidimensional (Art 7)", 
              "2. Riesgo Social (MCR2030)", 
              "3. Vulnerabilidad (Sendai)", 
              "4. Vocación Turística (Oportunidad)",
              "🔴 CRUCE PRIORITARIO (TODAS)"], horizontal=True)

    if not df_zona.empty and 'SITS_INDEX' in df_zona.columns:
        # CÁLCULOS
        df_zona['IND_PRIORIDAD_TOTAL'] = (df_zona['SITS_INDEX'] + df_zona['IND_RIESGO_SOCIAL'] + df_zona['SENDAI_P1_VULNERABILIDAD']) / 3
        
        # --- CÁLCULO DE VOCACIÓN DOMINANTE (MEJORADO: REZAGO) ---
        def determinar_vocacion(row):
            # Si no hay economía pero SÍ hay gente, es un dormitorio de pobreza
            if (row.get('ECO_TOTAL', 0) == 0) and (row.get('P25_TOT', 0) > 50):
                return "🏠 Zona Habitacional Rezago"
            
            if row.get('ECO_TOTAL', 0) == 0:
                return "Sin Actividad"

            sectores = {
                'TURISMO 🏖️': row.get('ECO_TURISMO', 0),
                'COMERCIO 🛒': row.get('ECO_COMERCIO', 0),
                'INDUSTRIA 🏭': row.get('ECO_INDUSTRIA', 0),
                'SERVICIOS 🛠️': row.get('ECO_SERVICIOS', 0)
            }
            return max(sectores, key=sectores.get)

        df_zona['VOCACION_DOMINANTE'] = df_zona.apply(determinar_vocacion, axis=1)

        # --- CÁLCULO DE ACCIÓN SUGERIDA (VISIÓN ALCALDE) ---
        def sugerir_accion(row):
            prio = row['IND_PRIORIDAD_TOTAL']
            voc = row['VOCACION_DOMINANTE']
            
            if prio > 0.40: # ZONA CRÍTICA
                if "TURISMO" in voc: return "💎 Rescate Urbano (Imagen + Drenaje)"
                if "Rezago" in voc: return "🚧 Infraestructura Básica (Ramo 033)"
                if "COMERCIO" in voc: return "👮 Seguridad e Iluminación"
                return "🆘 Intervención Social Integral"
            elif prio > 0.25:
                return "🔧 Mantenimiento Preventivo"
            else:
                return "✅ Monitoreo"

        df_zona['ACCION_OBRA_PUBLICA'] = df_zona.apply(sugerir_accion, axis=1)

        # Propagación a mapas (copias du/dr)
        if not du.empty:
            du['IND_PRIORIDAD_TOTAL'] = df_zona.set_index('CVEGEO')['IND_PRIORIDAD_TOTAL'].reindex(du['CVEGEO']).values
        if not dr.empty:
            dr['IND_PRIORIDAD_TOTAL'] = df_zona.set_index('CVEGEO')['IND_PRIORIDAD_TOTAL'].reindex(dr['CVEGEO']).values
        
        # MAPA (Visualización)
        lat = df_zona.geometry.centroid.y.mean()
        lon = df_zona.geometry.centroid.x.mean()
        m_dec = folium.Map([lat, lon], zoom_start=13, tiles="CartoDB positron")

        def estilo_dinamico(feature, variable, color_base):
            val = feature['properties'].get(variable, 0)
            opacity = 0.1
            if val > 0.4: opacity = 0.8
            elif val > 0.2: opacity = 0.5
            elif val > 0.1: opacity = 0.3
            return {'fillColor': color_base, 'color': 'black', 'weight': 0.5, 'fillOpacity': opacity}

        variable_mapa = "IND_PRIORIDAD_TOTAL" if "CRUCE" in capa_activa else "IND_VOCACION_TURISTICA" if "4." in capa_activa else "SITS_INDEX"
        color_mapa = "#b71c1c" if "CRUCE" in capa_activa else "#f1c40f" if "4." in capa_activa else "blue"

        if not du.empty:
            if "CRUCE" in capa_activa:
                umbral = df_zona[variable_mapa].quantile(0.75)
                du_c = du[du[variable_mapa] >= umbral]
                if not du_c.empty:
                    folium.GeoJson(du_c, style_function=lambda x: {'fillColor': color_mapa, 'color': 'black', 'weight': 2, 'fillOpacity': 0.9}, tooltip="ZONA PRIORITARIA").add_to(m_dec)
            else:
                 folium.GeoJson(du, style_function=lambda x: estilo_dinamico(x, variable_mapa, color_mapa)).add_to(m_dec)

        st_folium(m_dec, height=450, use_container_width=True)

        st.markdown("<div class='section-title'>2. Padrón Estratégico para Obras Públicas</div>", unsafe_allow_html=True)
        
        if "CRUCE" in capa_activa:
            umbral = df_zona['IND_PRIORIDAD_TOTAL'].quantile(0.75)
            df_table = df_zona[df_zona['IND_PRIORIDAD_TOTAL'] >= umbral]
            msg_alert = f"Mostrando las <b>{len(df_table)} zonas más críticas</b> (Top 25%) que requieren intervención urgente."
        else:
            df_table = df_zona.sort_values(variable_mapa, ascending=False).head(50)
            msg_alert = f"Mostrando Top 50 ordenado por {capa_activa}."

        st.markdown(f"<div class='alert-box'>{msg_alert}</div>", unsafe_allow_html=True)
        
        # TABLA DEFINITIVA
        cols_finales = ['NOM_LOC', 'TIPO', 'CVE_AGEB', 'P25_TOT', 'IND_PRIORIDAD_TOTAL', 'VOCACION_DOMINANTE', 'ACCION_OBRA_PUBLICA']
        
        tb_final = df_table[list(dict.fromkeys(cols_finales))].sort_values('IND_PRIORIDAD_TOTAL', ascending=False).reset_index(drop=True)
        
        st.dataframe(
            tb_final.style.format({'IND_PRIORIDAD_TOTAL': "{:.1%}", 'P25_TOT': "{:,.0f}"})
            .background_gradient(cmap='Reds', subset=['IND_PRIORIDAD_TOTAL']), 
            use_container_width=True
        )
        
        st.download_button("💾 Descargar Plan de Obra (CSV)", tb_final.to_csv(index=False).encode('utf-8'), "plan_obra_2026.csv", "text/csv")

# --- TAB 8: ECONOMÍA Y DESARROLLO ---
with tab8:
    st.header("🏭 Reactivación Económica y Vocación Territorial")
    
    # Filtro local Urbano/Rural
    tipo_filtro_eco = st.radio("Filtro Geográfico (Vista):", ["Todo el Municipio", "Solo Urbano", "Solo Rural"], horizontal=True)
    du_eco = du.copy(); dr_eco = dr.copy()
    if tipo_filtro_eco == "Solo Urbano": dr_eco = dr_eco[dr_eco['TIPO'] == 'X']
    elif tipo_filtro_eco == "Solo Rural": du_eco = du_eco[du_eco['TIPO'] == 'X']
    df_eco_filtered = pd.concat([du_eco, dr_eco], ignore_index=True)

    col_eco1, col_eco2 = st.columns([3, 1])
    
    with col_eco2:
        st.subheader("Configuración")
        sector_ver = st.radio("Sector a Visualizar:", 
            ["ECO_TOTAL", "ECO_TURISMO", "ECO_COMERCIO", "IND_VOCACION_TURISTICA"],
            index=3,
            format_func=lambda x: x.replace("ECO_", "").replace("IND_VOCACION_TURISTICA", "% Dependencia Turismo"))
        
        st.markdown("""
        <div class="eco-box">
        <b>¿Qué muestra este mapa?</b><br>
        Identifica dónde está la actividad económica real. Zonas con alto % de Turismo son ideales para invertir en imagen urbana. Zonas comerciales requieren seguridad e iluminación.
        </div>
        """, unsafe_allow_html=True)

    with col_eco1:
        # MAPA ECONÓMICO
        lat = df_zona.geometry.centroid.y.mean(); lon = df_zona.geometry.centroid.x.mean()
        m_eco = folium.Map([lat, lon], zoom_start=13, tiles="CartoDB positron")
        
        if not du_eco.empty:
            paleta = 'YlOrRd' if 'TURISMO' in sector_ver else 'YlGn'
            folium.Choropleth(
                geo_data=du_eco, 
                data=du_eco, 
                columns=['CVEGEO', sector_ver], 
                key_on='feature.properties.CVEGEO', 
                fill_color=paleta, 
                fill_opacity=0.7, 
                line_opacity=0.1, 
                legend_name=f'{sector_ver}'
            ).add_to(m_eco)
        st_folium(m_eco, height=450, use_container_width=True)

    # --- NUEVO: CÁLCULO DE INFORMALIDAD ---
    # Lógica: PEA (Gente que trabaja) - (Negocios * 3 empleados promedio). Si sobra gente, es informal.
    if not df_eco_filtered.empty and 'PEA' in df_eco_filtered.columns:
        df_eco_filtered['EMPLEO_FORMAL_EST'] = df_eco_filtered['ECO_TOTAL'] * 3 
        df_eco_filtered['ESTIMACION_INFORMALIDAD'] = df_eco_filtered['PEA'] - df_eco_filtered['EMPLEO_FORMAL_EST']
        df_eco_filtered['ESTIMACION_INFORMALIDAD'] = df_eco_filtered['ESTIMACION_INFORMALIDAD'].clip(lower=0) # No negativos

    st.markdown("---")
    st.markdown("### 📋 Padrón Económico con Detección de Informalidad")
    st.info("Zonas con alta PEA (Población Económicamente Activa) pero pocos negocios registrados sugieren alta economía informal.")

    cols_inventario = ['NOM_LOC', 'TIPO', 'CVE_AGEB', 'ECO_TOTAL', 'IND_VOCACION_TURISTICA', 'PEA', 'ESTIMACION_INFORMALIDAD']
    
    # Renombrar para usuario final
    df_inv = df_eco_filtered[cols_inventario].copy()
    df_inv.rename(columns={'IND_VOCACION_TURISTICA': '% Dep. Turismo', 'PEA': 'Pob. Econ. Activa', 'ESTIMACION_INFORMALIDAD': 'Posible Empleo Informal'}, inplace=True)
    
    df_inv = df_inv.sort_values('Posible Empleo Informal', ascending=False).reset_index(drop=True)

    st.dataframe(
        df_inv.style
        .format({'ECO_TOTAL': "{:,.0f}", '% Dep. Turismo': "{:.1%}", 'Pob. Econ. Activa': "{:,.0f}", 'Posible Empleo Informal': "{:,.0f}"})
        .background_gradient(cmap='Oranges', subset=['Posible Empleo Informal']),
        use_container_width=True
    )
    
    st.download_button("💾 Descargar Padrón Económico (CSV)", df_inv.to_csv(index=False).encode('utf-8'), "padron_economico_2025.csv", "text/csv")

# --- TAB 9: VIABILIDAD URBANA Y RESTRICCIONES (NUEVO) ---
with tab9:
    st.markdown("<div class='section-header'>🏗️ AUDITORÍA TÉCNICA DE USO DE SUELO Y RIESGOS</div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="facil-box">
    <b>👨🏻‍🏫 EXPLICACIÓN PARA EL DIRECTOR: ¿QUÉ ES ESTO?</b><br><br>
    Este módulo es un <b>"Detector de Problemas Automático"</b>. Antes de dar un permiso de construcción o planear una obra, el sistema revisa el terreno por ti.<br>
    <ul>
        <li><b>⛰️ Pendiente (Inclinación):</b> Nos dice si el terreno está muy empinado. Si construimos ahí, se puede venir abajo con la lluvia.</li>
        <li><b>⛽ Riesgo Químico (Gas):</b> Nos avisa si hay una gasolinera a menos de 100 metros (una cuadra). Es peligroso por explosiones.</li>
        <li><b>💧 Zona Federal (Agua):</b> Nos avisa si hay un río o arroyo a menos de 20 metros. No se puede construir ahí porque es propiedad de CONAGUA y se inunda.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    c_map, c_ctrl = st.columns([3, 1])
    
    with c_ctrl:
        st.subheader("🔍 ¿Qué quieres revisar?")
        opcion_ver = st.radio("Selecciona una capa:", 
            ["1. DICTAMEN FINAL (Semáforo)", 
             "2. Riesgos de Gas y Agua (Peligro)", 
             "3. Inclinación del Terreno (Topografía)"]
        )
        
        if "1." in opcion_ver:
            st.markdown("""
            <div style="background-color:#2e7d32; color:white; padding:5px; border-radius:5px; text-align:center;">🟢 VERDE: Se puede construir</div>
            <div style="background-color:#e65100; color:white; padding:5px; border-radius:5px; text-align:center; margin-top:5px;">🟠 NARANJA: Terreno difícil</div>
            <div style="background-color:#b71c1c; color:white; padding:5px; border-radius:5px; text-align:center; margin-top:5px;">🔴 ROJO: ¡PROHIBIDO! (Peligro)</div>
            """, unsafe_allow_html=True)
        elif "2." in opcion_ver:
            st.info("🔴 ROJO: Cerca de Gasolinera\n🔵 AZUL: Cerca de Río/Arroyo")

    with c_map:
        if not df_zona.empty:
            lat = df_zona.geometry.centroid.y.mean(); lon = df_zona.geometry.centroid.x.mean()
            m_tec = folium.Map([lat, lon], zoom_start=13, tiles="CartoDB positron")
            
            # --- FUNCIONES DE COLOR COMUNES ---
            def color_dictamen(props):
                val = str(props.get('DICTAMEN_VIABILIDAD', ''))
                if "RIESGO" in val or "FEDERAL" in val: return '#b71c1c' # Rojo
                if "NO URBANIZABLE" in val or "DESLAVE" in val: return '#e65100' # Naranja
                return '#2e7d32' # Verde

            def color_peligro(props):
                if props.get('RESTRICCION_GAS', 0) == 1: return '#d32f2f'
                if props.get('RESTRICCION_AGUA', 0) == 1: return '#1976d2'
                return '#eeeeee'

            # 1. CAPA URBANA (POLÍGONOS)
            if not du.empty:
                if "1." in opcion_ver:
                    folium.GeoJson(du, style_function=lambda x: {'fillColor': color_dictamen(x['properties']), 'color': 'black', 'weight': 0.5, 'fillOpacity': 0.6}, tooltip=folium.GeoJsonTooltip(fields=['NOM_LOC', 'DICTAMEN_VIABILIDAD'])).add_to(m_tec)
                elif "2." in opcion_ver:
                    folium.GeoJson(du, style_function=lambda x: {'fillColor': color_peligro(x['properties']), 'color': 'transparent', 'fillOpacity': 0.8 if x['properties'].get('RESTRICCION_GAS')==1 or x['properties'].get('RESTRICCION_AGUA')==1 else 0}).add_to(m_tec)
                elif "3." in opcion_ver:
                    folium.Choropleth(geo_data=du, data=du, columns=['CVEGEO', 'PENDIENTE_PROMEDIO'], key_on='feature.properties.CVEGEO', fill_color='RdYlGn_r', fill_opacity=0.7, line_opacity=0.1).add_to(m_tec)

            # 2. CAPA RURAL (PUNTOS) - ¡CORREGIDO Y AGREGADO!
            if not dr.empty:
                for _, r in dr.iterrows():
                    if r.geometry.is_empty: continue
                    props = r.to_dict()
                    
                    # Determinar color del punto
                    c_punto = '#808080' # Gris default
                    if "1." in opcion_ver:
                        c_punto = color_dictamen(props)
                    elif "2." in opcion_ver: 
                        c_punto = color_peligro(props)
                        # Si no hay riesgo, hacemos el punto invisible o muy gris
                        if c_punto == '#eeeeee': continue 
                    elif "3." in opcion_ver:
                        p = props.get('PENDIENTE_PROMEDIO', 0)
                        c_punto = '#2e7d32' if p < 5 else '#fbc02d' if p < 15 else '#b71c1c' # Verde -> Amarillo -> Rojo

                    folium.CircleMarker(
                        location=[r.geometry.centroid.y, r.geometry.centroid.x],
                        radius=6,
                        color='white',
                        weight=1,
                        fill=True,
                        fill_color=c_punto,
                        fill_opacity=0.9,
                        popup=f"<b>{r['NOM_LOC']}</b><br>Dictamen: {props.get('DICTAMEN_VIABILIDAD')}<br>Pendiente: {props.get('PENDIENTE_PROMEDIO'):.1f}%"
                    ).add_to(m_tec)
            
            # --- CAPA DE RÍOS (NUEVO: PINTAR LÍNEAS DE AGUA) ---
            if gdf_rios is not None and "2." in opcion_ver:
                folium.GeoJson(
                    gdf_rios,
                    name="Red Hidrográfica",
                    style_function=lambda x: {'color': '#0d47a1', 'weight': 2.5, 'opacity': 0.8},
                    tooltip="Río / Arroyo (Zona Federal)"
                ).add_to(m_tec)

            st_folium(m_tec, height=500, use_container_width=True)

    # TABLA DE DETALLES
    st.markdown("### 📋 Lista Negra: Zonas con Restricciones")
    if not df_zona.empty:
        cols_tec = ['NOM_LOC', 'TIPO', 'PENDIENTE_PROMEDIO', 'DICTAMEN_VIABILIDAD']
        df_probs = df_zona[df_zona['DICTAMEN_VIABILIDAD'].astype(str).str.contains("RIESGO|NO|FEDERAL", na=False)].sort_values('PENDIENTE_PROMEDIO', ascending=False)
        
        if not df_probs.empty:
            st.warning(f"⚠️ Se encontraron {len(df_probs)} zonas conflictivas.")
            st.dataframe(df_probs.style.format({'PENDIENTE_PROMEDIO': "{:.1f}%"}).applymap(lambda v: 'color:red; font-weight:bold' if 'RIESGO' in str(v) else '', subset=['DICTAMEN_VIABILIDAD']), use_container_width=True)
        else:
            st.success("✅ Todo limpio. No hay zonas de alto riesgo detectadas.")