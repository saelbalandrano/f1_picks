import streamlit as st
import pandas as pd
import numpy as np
from supabase import create_client
import os
from dotenv import load_dotenv
import urllib.request
from ai_engine import run_ai_prediction_engine
from ui_components import render_grid_card, render_h2h_match

# 1. Configuración de la página
st.set_page_config(page_title="F1 2026 AI Predictor", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 🔌 CONEXIÓN A SUPABASE
# ==========================================
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

@st.cache_resource
def init_connection():
    return create_client(url, key)

supabase = init_connection()

# ==========================================
# 📅 CALENDARIO DINÁMICO DESDE LA NUBE
# ==========================================
PHYSICS_FALLBACK = {
    1: {"laps": 58, "diff": 1.10},
    2: {"laps": 56, "diff": 0.90},
    3: {"laps": 53, "diff": 1.20},
    4: {"laps": 57, "diff": 1.15}, 
}

@st.cache_data(ttl=86400) 
def load_dynamic_calendar():
    res = supabase.table("events").select("round_number, country, circuit_name, status").order("round_number").execute()
    cal = {}
    if res.data:
        for row in res.data:
            if row['status'] != 'cancelled':
                r_num = row['round_number']
                cal[r_num] = {
                    "name": f"Ronda {r_num}: {row['country']} - {row['circuit_name']}",
                    "circuit_name": row['circuit_name'],
                    "laps": PHYSICS_FALLBACK.get(r_num, {"laps": 50})["laps"],
                    "diff": PHYSICS_FALLBACK.get(r_num, {"diff": 1.0})["diff"]
                }
    return cal

CALENDAR = load_dynamic_calendar()

if not CALENDAR:
    st.error("⚠️ No se pudo cargar el calendario. Revisa la conexión a la tabla 'events'.")
    st.stop()

# 2. CSS Inyectado (Premium Red & Glassmorphism)
st.markdown("""
<style>
    /* Fondo global oscuro para resaltar el Glassmorphism */
    .stApp, [data-testid="stAppViewContainer"] {
        background-color: #0b0f12 !important;
        background-image: radial-gradient(circle at 50% 0%, #2a0000 0%, #0b0f12 40%) !important;
    }
    [data-testid="stHeader"] {
        background: transparent !important;
    }
    
    /* Efecto Glassmorphism y Grid Cards */
    .grid-container {
        background: rgba(20, 24, 28, 0.6); 
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 0, 0, 0.15);
        border-radius: 8px; padding: 0px; margin-bottom: 20px;
        color: white; position: relative; overflow: hidden; min-height: 220px; display: flex;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5); width: 100%; box-sizing: border-box;
        transition: all 0.3s ease;
    }
    .grid-container:hover {
        box-shadow: 0 0 20px rgba(255, 0, 0, 0.4);
        border: 1px solid rgba(255, 0, 0, 0.5);
        transform: translateY(-2px);
    }
    .grid-container::before { 
        content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
        background-color: var(--team-color); z-index: 5;
    }
    .logo-full-color { position: absolute; top: 10px; right: 10px; opacity: 1.0; height: 40px; z-index: 10; }
    .driver-section {
        flex: 1; position: relative; z-index: 2; padding: 15px 10px 10px 15px; 
        display: flex; flex-direction: column; justify-content: flex-start;
    }
    .pos-name-block { display: flex; align-items: center; margin-bottom: 5px; }
    .pos-number {
        font-size: 28px; font-weight: 900; color: #ff0000; background-color: rgba(255,0,0,0.1);
        padding: 2px 10px; border-radius: 4px; margin-right: 10px; border: 1px solid rgba(255,0,0,0.3);
        text-shadow: 0 0 8px rgba(255,0,0,0.6);
    }
    .driver-name { font-size: 18px; font-weight: bold; text-transform: uppercase; margin: 0; letter-spacing: -0.5px; }
    .team-name { color: #a0a0a0; font-size: 11px; text-transform: uppercase; margin: 0; letter-spacing: 1px; }
    
    .driver-photo { position: absolute; bottom: 0px; right: 10px; height: 160px; z-index: 3; filter: drop-shadow(2px 4px 6px rgba(0,0,0,0.5)); transition: transform 0.3s ease; }
    .grid-container:hover .driver-photo { transform: scale(1.05); }

    .telemetry-section {
        width: 250px; background: rgba(10, 14, 18, 0.8); position: relative; z-index: 2; padding: 15px 10px;
        padding-top: 55px; border-left: 1px solid rgba(255,0,0,0.1); display: flex; flex-direction: column; justify-content: flex-end; 
    }
    .telemetry-title { font-size: 10px; color: #ff3333; text-transform: uppercase; font-weight: bold; margin-bottom: 5px; letter-spacing: 1.5px;}
    
    .data-table { width: 100%; border-collapse: collapse; font-size: 12px; }
    .data-table tr { border-bottom: 1px solid rgba(255,255,255,0.05); }
    .data-table td { padding: 4px 0; color: #ccc; }
    .data-table td.label { font-weight: bold; text-transform: uppercase; color: #fff; width: 60%;}
    .data-table td.value { font-family: 'Courier New', monospace; font-weight: bold; text-align: right; color: #00ff00; text-shadow: 0 0 5px rgba(0,255,0,0.3); }
    .data-table tr:last-child { border-bottom: none; }
    
    .stSelectbox label { font-weight: bold; color: #ff0000; text-transform: uppercase; letter-spacing: 1px; }

    /* ========================================== */
    /* CSS para H2H Broadcast Style              */
    /* ========================================== */
    .h2h-match-wrapper {
        background: rgba(20, 24, 28, 0.6); backdrop-filter: blur(12px); border-radius: 10px; padding: 15px 20px; margin-bottom: 20px;
        border: 1px solid rgba(255,0,0,0.15); display: flex; justify-content: space-between; align-items: center;
        position: relative; overflow: hidden; transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    .h2h-match-wrapper:hover {
        box-shadow: 0 0 20px rgba(255, 0, 0, 0.3); border: 1px solid rgba(255,0,0,0.4);
    }
    
    .h2h-driver-unit {
        display: flex; align-items: center; flex-grow: 1; border-radius: 8px; padding: 10px; transition: all 0.3s ease;
    }
    
    /* Highlight para el ganador proyectado */
    .h2h-winner-unit {
        border: 1px solid var(--team-color);
        box-shadow: inset 0 0 20px var(--team-color-shadow);
        background-color: rgba(255, 255, 255, 0.05);
    }
    
    .h2h-driver-unit-left { text-align: left; }
    .h2h-driver-unit-right { text-align: right; flex-direction: row-reverse; }
    
    .h2h-photo-container { width: 80px; flex-shrink: 0; }
    .h2h-photo-img { height: 100px; object-fit: cover; border-radius: 8px; filter: drop-shadow(2px 2px 4px rgba(0,0,0,0.5)); }
    
    .h2h-info-container { flex-grow: 1; padding: 0 15px; }
    
    .h2h-driver-unit-title { font-size: 18px; font-weight: bold; text-transform: uppercase; margin: 0; color: white; letter-spacing: -0.5px;}
    .h2h-team-name { color: #aaa; font-size: 11px; text-transform: uppercase; margin: 0; }
    
    .h2h-pos-num { font-size: 26px; font-weight: bold; margin: 5px 0; display: block; line-height: 1; }
    .h2h-pos-prefix { font-weight: 900; color: #ff0000; margin-right: 3px; }
    .h2h-pos-value { color: white; text-shadow: 0 0 8px rgba(255,255,255,0.3); }
    
    .h2h-base-pace-text { font-size: 12px; color: #aaa; font-weight: bold; }
    .h2h-base-pace-formatted { color: #00ff00; font-family: 'Courier New', monospace; text-shadow: 0 0 5px rgba(0,255,0,0.3);}

    .h2h-team-logo-center { width: 60px; flex-shrink: 0; text-align: center; display: flex; justify-content: center; align-items: center; margin: 0 15px;}
    .h2h-team-logo-img { height: 60px; width: auto; object-fit: contain; opacity: 0.8;}
    
    /* Track Image Placeholder */
    .track-placeholder {
        background: rgba(20,24,28,0.5); border: 1px dashed rgba(255,0,0,0.3); border-radius: 8px;
        display: flex; justify-content: center; align-items: center; height: 150px; color: #ff4444; font-weight: bold;
        text-transform: uppercase; letter-spacing: 2px; margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏎️ F1 2026 - AI Race Predictor")

# ==========================================
# 🎛️ SELECTOR DE CARRERAS
# ==========================================
col_sel1, col_sel2 = st.columns([1, 2])
with col_sel1:
    race_options = {v['name']: k for k, v in CALENDAR.items()}
    default_index = list(race_options.values()).index(3) if 3 in race_options.values() else (len(race_options) - 1 if len(race_options) > 0 else 0)
    selected_race_name = st.selectbox("Selecciona la Carrera a Simular:", list(race_options.keys()), index=default_index)
    selected_round = race_options[selected_race_name]

st.markdown(f"Predicciones generadas por el **Modelo A (Física Base + Factor Manos + Monte Carlo)** para **{selected_race_name}**.")
st.write("---")

# ==========================================
# 🧠 EL CEREBRO DE LA IA (MONTE CARLO PROBABILITIES)
# ==========================================
@st.cache_data(ttl=3600)
def cached_run_ai_prediction(target_round):
    # Call the external logic
    return run_ai_prediction_engine(target_round, supabase, CALENDAR)

# ==========================================
# 📊 FUSIÓN UI + IA
# ==========================================
@st.cache_data(ttl=600)
def build_master_dataframe(target_round):
    df_ai = cached_run_ai_prediction(target_round)
    if df_ai.empty: return pd.DataFrame() 

    res_drv = supabase.table("driver_momentum").select("current_form_score, drivers(driver_number, name, team, code)").execute()
    datos = [{"driver_number": r['drivers']['driver_number'], "Piloto": r['drivers']['name'], 
              "Código": r['drivers']['code'], "Escudería": r['drivers']['team']} for r in res_drv.data]
    df_ui = pd.DataFrame(datos)

    final_data = []
    for _, d in df_ui.iterrows():
        info = d.to_dict()
        ai_row = df_ai[df_ai['code'] == d['Código']]
        if not ai_row.empty:
            info.update({
                "ai_predicted_pos": ai_row.iloc[0]['ai_predicted_pos'],
                "ai_talent_bonus": ai_row.iloc[0]['ai_talent_bonus'],
                "ai_base_pace": ai_row.iloc[0]['ai_base_pace'],
                "prob_win": f"{ai_row.iloc[0]['prob_win']:.1f}%",
                "prob_podium": f"{ai_row.iloc[0]['prob_podium']:.1f}%",
                "prob_top6": f"{ai_row.iloc[0]['prob_top6']:.1f}%",
                "prob_top10": f"{ai_row.iloc[0]['prob_top10']:.1f}%"
            })
            final_data.append(info)
        
    return pd.DataFrame(final_data).sort_values(by="ai_predicted_pos", ascending=True).reset_index(drop=True)

master_df = build_master_dataframe(selected_round)

STORAGE_BASE_URL = "https://pfbhpvddzodwtlykbvma.supabase.co/storage/v1/object/public/f1_assets"
PIXEL_TRANSPARENTE = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
team_colors = {
    "Mercedes": "#00d2ff", "Ferrari": "#e10600", "Red Bull Racing": "#0600ef", 
    "McLaren": "#ff8700", "Aston Martin": "#006f62", "Aston Martin Aramco": "#006f62", 
    "Alpine": "#0090ff", "Haas F1 Team": "#e10600", "Racing Bulls": "#001ccf", 
    "Sauber": "#52e252", "Williams": "#005aff", "Williams Racing": "#005aff"
}

@st.cache_data
def obtener_url_valida(urls_posibles):
    for url in urls_posibles:
        url_segura = url.replace(" ", "%20")
        try:
            req = urllib.request.Request(url_segura, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
            res = urllib.request.urlopen(req, timeout=1.5) 
            if res.getcode() == 200:
                return url_segura
        except: continue
    return PIXEL_TRANSPARENTE

# ==========================================
# GRÁFICA EVOLUTIVA DE ACERTIVIDAD (CACHED)
# ==========================================
@st.cache_data(ttl=3600)
def get_historical_accuracy(current_round):
    history = []
    res_off = supabase.table("official_race_results").select("*").execute()
    df_off_all = pd.DataFrame(res_off.data)
    
    if df_off_all.empty: return pd.DataFrame()

    for r in range(1, current_round + 1):
        if df_off_all[df_off_all['round_number'] == r].empty:
            continue
        
        df_master_r = build_master_dataframe(r)
        if df_master_r.empty: continue
        
        df_off_r = df_off_all[df_off_all['round_number'] == r]
        df_eval_r = pd.merge(df_master_r, df_off_r, left_on='Código', right_on='code', how='inner')
        
        if df_eval_r.empty: continue
        
        mae = abs(df_eval_r['ai_predicted_pos'] - df_eval_r['official_position']).mean()
        
        equipos_eval = df_eval_r['Escudería'].unique()
        h2h_aciertos = 0
        h2h_total = 0
        for eq in equipos_eval:
            pilotos_eq = df_eval_r[df_eval_r['Escudería'] == eq]
            if len(pilotos_eq) >= 2:
                p1 = pilotos_eq.iloc[0]
                p2 = pilotos_eq.iloc[1]
                pred_win = p1['Código'] if p1['ai_predicted_pos'] < p2['ai_predicted_pos'] else p2['Código']
                real_win = p1['Código'] if p1['official_position'] < p2['official_position'] else p2['Código']
                if pred_win == real_win: h2h_aciertos += 1
                h2h_total += 1
                
        win_rate = (h2h_aciertos / h2h_total) * 100 if h2h_total > 0 else 0
        
        history.append({
            "Ronda": f"R{r}",
            "MAE": round(mae, 2),
            "Win Rate H2H (%)": round(win_rate, 1)
        })
    return pd.DataFrame(history)

# ==========================================
# 🗂️ SISTEMA DE PESTAÑAS (TABS)
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 Power Ranking Master Grid", "🥊 Head-to-Head Predictor", "🎯 Auditoría de Acertividad"])

# ==========================================
# TAB 1: MASTER GRID (AHORA CON PROBABILIDADES)
# ==========================================
with tab1:
    if master_df.empty:
        st.warning(f"⚠️ Aún no hay telemetría suficiente en la base de datos para simular **{selected_race_name}**. Asegúrate de correr el actualizador.")
    else:
        with st.spinner(f'Calculando Probabilidades de Monte Carlo para {selected_race_name}...'):
            # Track Layout Placeholder
            st.markdown(f"""
            <div class="track-placeholder">
                [ TRACK LAYOUT: {selected_race_name.split(': ')[-1]} ]<br>
                <span style="font-size:10px; color:#aaa; margin-top:5px; font-weight:normal;">ESPACIO RESERVADO PARA MAPA DEL CIRCUITO (Próximamente desde Supabase)</span>
            </div>
            """, unsafe_allow_html=True)
            
            for i in range(0, len(master_df), 3):
                drivers_chunk = master_df.iloc[i : i+3]
                cols = st.columns(3)
                for col, (_, driver) in zip(cols, drivers_chunk.iterrows()):
                    equipo = driver['Escudería']
                    color = team_colors.get(equipo, "#555")
                    equipo_archivo = equipo.replace(' ', '_')
                    p_low = driver['Piloto'].lower().replace(' ', '_')
                    p_tit = driver['Piloto'].replace(' ', '_')
                    
                    logo_url = obtener_url_valida([
                        f"{STORAGE_BASE_URL}/logos/{equipo_archivo}.webp", 
                        f"{STORAGE_BASE_URL}/logos/{equipo_archivo}.png",
                        f"{STORAGE_BASE_URL}/logos/{equipo_archivo}.svg"
                    ])
                    photo_url = obtener_url_valida([
                        f"{STORAGE_BASE_URL}/drivers/{p_low}.webp", 
                        f"{STORAGE_BASE_URL}/drivers/{p_low}.png",
                        f"{STORAGE_BASE_URL}/drivers/{p_tit}.webp",
                        f"{STORAGE_BASE_URL}/drivers/{p_tit}.png"
                    ])

                    # Render via UI components module
                    index_pos = master_df.index[master_df['driver_number'] == driver['driver_number']][0]
                    race_name_short = selected_race_name.split(': ')[-1]
                    html_content = render_grid_card(driver, index_pos, color, logo_url, photo_url, race_name_short)
                    
                    with col:
                        st.markdown(html_content, unsafe_allow_html=True)

# ==========================================
# TAB 2: HEAD-TO-HEAD (H2H) Broadcast Look
# ==========================================
with tab2:
    st.markdown("### 🥊 Batallas Internas de Escudería")
    st.markdown("Comparación directa de compañeros basada en la proyección final del Modelo A.")
    st.write("")
    
    if master_df.empty:
        st.warning(f"⚠️ No se pueden generar batallas H2H sin telemetría para **{selected_race_name}**.")
    else:
        equipos = master_df['Escudería'].unique()
        col_left, col_right = st.columns(2)
        col_index = 0
        
        for equipo in equipos:
            pilotos_equipo_raw = master_df[master_df['Escudería'] == equipo]
            
            if len(pilotos_equipo_raw) >= 2:
                pilotos_visual_order = pilotos_equipo_raw.sort_values(by="driver_number")
                p_left = pilotos_visual_order.iloc[0]
                p_right = pilotos_visual_order.iloc[1]
                
                pilotos_by_prediction = pilotos_equipo_raw.sort_values(by="ai_predicted_pos")
                predicted_winner_code = pilotos_by_prediction.iloc[0]['Código']
                
                color_equipo = team_colors.get(equipo, "#555")
                equipo_archivo = equipo.replace(' ', '_')
                
                p_left_low = p_left['Piloto'].lower().replace(' ', '_')
                p_left_tit = p_left['Piloto'].replace(' ', '_')
                p_right_low = p_right['Piloto'].lower().replace(' ', '_')
                p_right_tit = p_right['Piloto'].replace(' ', '_')

                photo_left = obtener_url_valida([
                    f"{STORAGE_BASE_URL}/drivers/{p_left_low}.webp", 
                    f"{STORAGE_BASE_URL}/drivers/{p_left_low}.png",
                    f"{STORAGE_BASE_URL}/drivers/{p_left_tit}.webp",
                    f"{STORAGE_BASE_URL}/drivers/{p_left_tit}.png"
                ])
                photo_right = obtener_url_valida([
                    f"{STORAGE_BASE_URL}/drivers/{p_right_low}.webp", 
                    f"{STORAGE_BASE_URL}/drivers/{p_right_low}.png",
                    f"{STORAGE_BASE_URL}/drivers/{p_right_tit}.webp",
                    f"{STORAGE_BASE_URL}/drivers/{p_right_tit}.png"
                ])
                logo_center = obtener_url_valida([
                    f"{STORAGE_BASE_URL}/logos/{equipo_archivo}.webp", 
                    f"{STORAGE_BASE_URL}/logos/{equipo_archivo}.png",
                    f"{STORAGE_BASE_URL}/logos/{equipo_archivo}.svg"
                ])
                
                html_h2h = render_h2h_match(p_left, p_right, equipo, color_equipo, predicted_winner_code, logo_center, photo_left, photo_right)
                
                if col_index % 2 == 0:
                    with col_left: st.markdown(html_h2h, unsafe_allow_html=True)
                else:
                    with col_right: st.markdown(html_h2h, unsafe_allow_html=True)
                col_index += 1

# ==========================================
# TAB 3: AUDITORÍA DE ACERTIVIDAD CON GRÁFICOS
# ==========================================
with tab3:
    st.markdown("### 🎯 Auditoría de Rendimiento (Accuracy Track)")
    st.markdown("Cruce matemático entre las proyecciones de la IA y los resultados oficiales de la pista.")
    st.write("---")

    if master_df.empty:
        st.warning(f"⚠️ No hay telemetría ni predicciones para evaluar en **{selected_race_name}**.")
    else:
        res_official_tab3 = supabase.table("official_race_results").select("code, official_position").eq("round_number", selected_round).execute()
        df_off = pd.DataFrame(res_official_tab3.data)

        if df_off.empty:
            st.info(f"⏳ La carrera de **{selected_race_name}** aún no tiene resultados oficiales en la base de datos para medir la acertividad.")
            
            # Aún sin resultados actuales, mostramos el histórico hasta la carrera anterior si existe
            st.write("---")
            st.markdown("#### 📈 Evolución Histórica del Algoritmo")
            df_history = get_historical_accuracy(selected_round - 1)
            if not df_history.empty and len(df_history) >= 1:
                col_chart1, col_chart2 = st.columns(2)
                with col_chart1:
                    st.markdown("**Progresión del Win Rate H2H**")
                    st.line_chart(df_history.set_index("Ronda")[["Win Rate H2H (%)"]], color="#00ff00")
                with col_chart2:
                    st.markdown("**Evolución del Error (MAE) - Menos es mejor**")
                    st.line_chart(df_history.set_index("Ronda")[["MAE"]], color="#ff4444")
            else:
                st.info("Necesitamos al menos 1 carrera finalizada en la historia para mostrar la gráfica de evolución.")

        else:
            df_eval = pd.merge(master_df, df_off, left_on='Código', right_on='code', how='inner')
            if df_eval.empty:
                st.info("No se pudieron cruzar los pilotos con los resultados oficiales.")
            else:
                df_eval['Error_Absoluto'] = abs(df_eval['ai_predicted_pos'] - df_eval['official_position'])
                mae_ronda = df_eval['Error_Absoluto'].mean()

                equipos_eval = df_eval['Escudería'].unique()
                h2h_aciertos = 0
                h2h_total = 0

                for eq in equipos_eval:
                    pilotos_eq = df_eval[df_eval['Escudería'] == eq]
                    if len(pilotos_eq) >= 2:
                        p1 = pilotos_eq.iloc[0]
                        p2 = pilotos_eq.iloc[1]

                        pred_win = p1['Código'] if p1['ai_predicted_pos'] < p2['ai_predicted_pos'] else p2['Código']
                        real_win = p1['Código'] if p1['official_position'] < p2['official_position'] else p2['Código']

                        if pred_win == real_win:
                            h2h_aciertos += 1
                        h2h_total += 1

                win_rate_h2h = (h2h_aciertos / h2h_total) * 100 if h2h_total > 0 else 0

                c1, c2, c3 = st.columns(3)
                c1.metric(label="📉 Error Promedio de Grid (MAE)", value=f"± {mae_ronda:.2f} pos", delta="Ideal: < 3.0", delta_color="inverse")
                c2.metric(label="⚔️ Aciertos Head-to-Head", value=f"{h2h_aciertos} / {h2h_total}")
                c3.metric(label="💰 Win Rate H2H", value=f"{win_rate_h2h:.1f}%", delta="Rentabilidad > 60%", delta_color="normal")

                st.write("---")
                st.markdown("#### 📈 Evolución Histórica del Algoritmo")
                
                df_history = get_historical_accuracy(selected_round)
                if not df_history.empty and len(df_history) >= 1:
                    col_chart1, col_chart2 = st.columns(2)
                    with col_chart1:
                        st.markdown("**Progresión del Win Rate H2H**")
                        st.line_chart(df_history.set_index("Ronda")[["Win Rate H2H (%)"]], color="#00ff00")
                    with col_chart2:
                        st.markdown("**Evolución del Error (MAE) - Menos es mejor**")
                        st.line_chart(df_history.set_index("Ronda")[["MAE"]], color="#ff4444")
                else:
                    st.info("Necesitamos al menos 1 carrera finalizada para mostrar la gráfica de evolución.")

                st.write("---")
                st.markdown("#### 📊 Desglose de Predicción por Piloto (Ronda Actual)")
                
                df_display = df_eval[['Piloto', 'Escudería', 'ai_predicted_pos', 'official_position', 'Error_Absoluto']].copy()
                df_display.rename(columns={
                    'ai_predicted_pos': 'Predicción IA',
                    'official_position': 'Posición Oficial',
                    'Error_Absoluto': 'Margen de Error'
                }, inplace=True)
                
                df_display['Predicción IA'] = df_display['Predicción IA'].round(1)
                df_display['Margen de Error'] = df_display['Margen de Error'].round(1)
                df_display = df_display.sort_values('Posición Oficial')

                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Predicción IA": st.column_config.NumberColumn("Predicción IA", format="P%.1f"),
                        "Posición Oficial": st.column_config.NumberColumn("Posición Real", format="P%d"),
                        "Margen de Error": st.column_config.ProgressColumn(
                            "Margen de Error (Posiciones)",
                            help="Diferencia absoluta entre la predicción y el resultado final.",
                            format="±%.1f",
                            min_value=0,
                            max_value=20,
                        )
                    }
                )