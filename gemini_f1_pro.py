import streamlit as st
import pandas as pd
import numpy as np
from supabase import create_client
import os
from dotenv import load_dotenv
import urllib.request

# 1. Configuración de la página
st.set_page_config(page_title="F1 2026 AI Predictor", layout="wide", initial_sidebar_state="collapsed")

def format_pace(seconds):
    if pd.isna(seconds) or seconds == 0: return "--:--"
    minutos = int(seconds // 60)
    segs = seconds % 60
    return f"{minutos}:{segs:06.3f}"

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

# 2. CSS Inyectado (AHORA CON DISEÑO RESPONSIVO MÓVIL)
st.markdown("""
<style>
    .grid-container {
        background-color: #15151e; border-radius: 4px; padding: 0px; margin-bottom: 20px;
        color: white; position: relative; overflow: hidden; min-height: 220px; display: flex;
        box-shadow: 4px 4px 15px rgba(0,0,0,0.7); width: 100%; box-sizing: border-box;
    }
    .grid-container::before { 
        content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 6px;
        background-color: var(--team-color); z-index: 5;
    }
    .logo-full-color { position: absolute; top: 10px; right: 10px; opacity: 1.0; height: 40px; z-index: 10; }
    .driver-section {
        flex: 1; position: relative; z-index: 2; padding: 10px 10px 10px 15px; 
        display: flex; flex-direction: column; justify-content: flex-start;
    }
    .pos-name-block { display: flex; align-items: center; margin-bottom: 5px; }
    .pos-number {
        font-size: 30px; font-weight: 900; color: #ffffff; background-color: var(--team-color);
        padding: 0px 10px; border-radius: 4px; margin-right: 10px;
    }
    .driver-name { font-size: 18px; font-weight: bold; text-transform: uppercase; margin: 0; letter-spacing: -1px; }
    .team-name { color: #a0a0a0; font-size: 11px; text-transform: uppercase; margin: 0; letter-spacing: 1px; }
    
    .driver-photo { position: absolute; bottom: -5px; right: 0px; height: 160px; z-index: 3; }

    .telemetry-section {
        width: 250px; background-color: #1f1f2b; position: relative; z-index: 2; padding: 10px;
        padding-top: 55px; border-left: 1px solid #38383e; display: flex; flex-direction: column; justify-content: flex-end; 
    }
    .telemetry-title { font-size: 10px; color: #00d2ff; text-transform: uppercase; font-weight: bold; margin-bottom: 5px; letter-spacing: 1.5px;}
    
    .data-table { width: 100%; border-collapse: collapse; font-size: 11px; }
    .data-table tr { border-bottom: 1px solid #333; }
    .data-table td { padding: 3px 0; color: #ccc; }
    .data-table td.label { font-weight: bold; text-transform: uppercase; color: #fff; width: 60%;}
    .data-table td.value { font-family: 'Courier New', monospace; font-weight: bold; text-align: right; color: #00ff00; }
    .data-table tr:last-child { border-bottom: none; }
    
    .stSelectbox label { font-weight: bold; color: #00d2ff; text-transform: uppercase; letter-spacing: 1px; }

    /* ========================================== */
    /* CSS para H2H Broadcast Style              */
    /* ========================================== */
    .h2h-match-wrapper {
        background-color: #1e1e24; border-radius: 10px; padding: 15px 20px; margin-bottom: 20px;
        border: 1px solid #38383e; display: flex; justify-content: space-between; align-items: center;
        position: relative; overflow: hidden;
    }
    
    .h2h-driver-unit {
        display: flex; align-items: center; flex-grow: 1; border-radius: 8px; padding: 10px;
    }
    
    /* Highlight para el ganador proyectado */
    .h2h-winner-unit {
        border: 2px solid var(--team-color);
        box-shadow: 0 0 12px var(--team-color-shadow);
        background-color: rgba(255, 255, 255, 0.03);
    }
    
    .h2h-driver-unit-left { text-align: left; }
    .h2h-driver-unit-right { text-align: right; flex-direction: row-reverse; }
    
    /* Contenedores de fotos a las orillas */
    .h2h-photo-container { width: 80px; flex-shrink: 0; }
    .h2h-photo-img { height: 100px; object-fit: cover; border-radius: 8px; }
    
    /* Contenedores de información */
    .h2h-info-container { flex-grow: 1; padding: 0 15px; }
    
    .h2h-driver-unit-title { font-size: 18px; font-weight: bold; text-transform: uppercase; margin: 0; color: white; }
    .h2h-team-name { color: #aaa; font-size: 11px; text-transform: uppercase; margin: 0; }
    
    .h2h-pos-num { font-size: 24px; font-weight: bold; margin: 5px 0; display: block; line-height: 1; }
    .h2h-pos-prefix { font-weight: 900; color: var(--team-color); margin-right: 3px; }
    .h2h-pos-value { color: white; }
    
    .h2h-base-pace-text { font-size: 12px; color: #aaa; font-weight: bold; }
    .h2h-base-pace-formatted { color: #00ff00; font-family: 'Courier New', monospace; }

    /* Team logo centrado */
    .h2h-team-logo-center { width: 60px; flex-shrink: 0; text-align: center; display: flex; justify-content: center; align-items: center; margin: 0 15px;}
    .h2h-team-logo-img { height: 60px; width: auto; object-fit: contain; }

    /* ========================================== */
    /* 📱 REGLAS MÓVILES (MEDIA QUERIES)         */
    /* ========================================== */
    @media (max-width: 768px) {
        /* Ajustes Tab 1 (Master Grid) */
        .grid-container {
            flex-direction: column; /* Apila la sección del piloto arriba y la telemetría abajo */
            min-height: auto;
        }
        .driver-photo {
            opacity: 0.25; /* Transparente para no estorbar con el texto en pantallas chicas */
            right: -20px;
        }
        .telemetry-section {
            width: 100%;
            border-left: none;
            border-top: 1px solid #38383e; /* Línea divisoria horizontal */
            padding-top: 15px;
        }

        /* Ajustes Tab 2 (H2H) */
        .h2h-match-wrapper {
            flex-direction: column; /* Apila a los pilotos verticalmente */
            padding: 10px;
        }
        .h2h-driver-unit {
            width: 100%;
            margin-bottom: 5px;
        }
        .h2h-driver-unit-right {
            flex-direction: row; /* Quita el modo reverso para que la foto y el texto se alineen igual que el piloto 1 */
            text-align: left;
        }
        .h2h-team-logo-center {
            width: 100%;
            height: 40px;
            margin: 5px 0;
        }
        .h2h-team-logo-img {
            height: 40px;
        }
    }
</style>
""", unsafe_allow_html=True)

st.title("🏎️ F1 2026 - AI Race Predictor")

# ==========================================
# 🎛️ SELECTOR DE CARRERAS
# ==========================================
@st.cache_data(ttl=60)
def obtener_ronda_activa():
    # Traemos todas las rondas que realmente tengan telemetría guardada
    res = supabase.table("race_profiles").select("round_number").execute()
    if res.data:
        rondas_con_datos = [r['round_number'] for r in res.data]
        return max(rondas_con_datos) # Forzamos el número máximo real
    return 1 # Solo si la base de datos está 100% vacía

ronda_activa = obtener_ronda_activa()

col_sel1, col_sel2 = st.columns([1, 2])
with col_sel1:
    race_options = {v['name']: k for k, v in CALENDAR.items()}
    valores_rondas = list(race_options.values())
    
    # Buscamos el índice exacto de la última carrera con datos
    if ronda_activa in valores_rondas:
        default_index = valores_rondas.index(ronda_activa)
    else:
        default_index = 0
        
    selected_race_name = st.selectbox("Selecciona la Carrera a Simular:", list(race_options.keys()), index=default_index)
    selected_round = race_options[selected_race_name]

st.markdown(f"Predicciones generadas por el **Modelo A (Física Base + Factor Manos + Monte Carlo)** para **{selected_race_name}**.")
st.write("---")

# ==========================================
# 🧠 EL CEREBRO DE LA IA (MONTE CARLO PROBABILITIES)
# ==========================================
@st.cache_data(ttl=3600)
def run_ai_prediction_engine(target_round):
    res_race = supabase.table("race_profiles").select("*").execute()
    df_race = pd.DataFrame(res_race.data)
    
    if df_race.empty: return pd.DataFrame()
    
    df_race['benchmark_pace'] = df_race.groupby(['round_number', 'compound'])['base_pace_s'].transform('min')
    df_race['pace_delta'] = df_race['base_pace_s'] - df_race['benchmark_pace']
    df_race['deg_per_lap'] = df_race['deg_per_lap'].apply(lambda x: max(float(x), 0.02))

    df_target = df_race[df_race['round_number'] == target_round]
    if df_target.empty:
        return pd.DataFrame() 

    res_official = supabase.table("official_race_results").select("*").execute()
    df_official = pd.DataFrame(res_official.data)

    res_qualy = supabase.table("qualy_profiles").select("*").execute()
    df_qualy = pd.DataFrame(res_qualy.data)

    def calculate_weighted_deltas(group):
        weights = {'MEDIUM': 0.50, 'HARD': 0.30, 'SOFT': 0.20}
        delta, deg, total_w = 0, 0, 0
        for _, row in group.iterrows():
            comp = row['compound']
            w = weights.get(comp, 0)
            delta += row['pace_delta'] * w
            deg += row['deg_per_lap'] * w
            total_w += w
        if total_w == 0: return pd.Series({'avg_delta': np.nan, 'avg_deg': np.nan})
        return pd.Series({'avg_delta': delta / total_w, 'avg_deg': deg / total_w})

    driver_codes = df_target['code'].unique()
    talent_bonuses = []
    
    past_rounds = [r for r in CALENDAR.keys() if r < target_round]

    for code in driver_codes:
        bonus_acumulado = 0.0
        carreras_evaluadas = 0
        for ronda in past_rounds:
            real_pos_row = df_official[(df_official['round_number'] == ronda) & (df_official['code'] == code)]
            if real_pos_row.empty or real_pos_row.iloc[0]['official_position'] > 17: continue
            real_pos = real_pos_row.iloc[0]['official_position']
            
            all_round_data = df_race[df_race['round_number'] == ronda]
            if all_round_data.empty: continue
            deltas_ronda = all_round_data.groupby('code').apply(calculate_weighted_deltas, include_groups=False).reset_index()
            grid_ronda = df_qualy[df_qualy['round_number'] == ronda].sort_values('delta_to_pole_s').reset_index(drop=True)
            grid_ronda['Grid_Slot'] = grid_ronda.index + 1
            df_sim = pd.merge(grid_ronda[['code', 'Grid_Slot']], deltas_ronda, on='code', how='inner')
            if df_sim.empty: continue
            
            df_sim['theo_time'] = df_sim['avg_delta'] * 50 + (df_sim['Grid_Slot'] * 1.5)
            df_sim = df_sim.sort_values('theo_time').reset_index(drop=True)
            pred_pos = df_sim.index[df_sim['code'] == code].tolist()
            if pred_pos:
                raw_bonus = ((pred_pos[0] + 1) - real_pos) * -0.015 
                bonus_acumulado += max(-0.15, min(raw_bonus, 0.15))
                carreras_evaluadas += 1
                
        final_bonus = bonus_acumulado / carreras_evaluadas if carreras_evaluadas > 0 else 0.0
        talent_bonuses.append({'code': code, 'talent_bonus_s': final_bonus})

    df_talent = pd.DataFrame(talent_bonuses)

    driver_race_stats = df_target.groupby('code').apply(calculate_weighted_deltas, include_groups=False).reset_index()
    grid_target = df_qualy[df_qualy['round_number'] == target_round].sort_values('delta_to_pole_s').reset_index(drop=True)
    grid_target['Grid_Slot'] = grid_target.index + 1

    df_final_sim = pd.merge(grid_target[['Grid_Slot', 'code']], driver_race_stats, on='code', how='inner')
    df_final_sim = pd.merge(df_final_sim, df_talent, on='code', how='left').fillna(0)

    laps = CALENDAR[target_round]['laps']
    diff_track = CALENDAR[target_round]['diff']
    num_simulations = 10000
    num_drivers = len(df_final_sim)

    base_paces = 90.0 + df_final_sim['avg_delta'].values + df_final_sim['talent_bonus_s'].values
    degradations = df_final_sim['avg_deg'].values
    grid_slots = df_final_sim['Grid_Slot'].values

    total_race_deg = degradations * ((17 * 18) / 2) * (laps / 17)
    launch_penalty = (grid_slots - 1) * 1.5 * diff_track
    dirty_air_penalty = (grid_slots - 1) * 0.03 * laps * diff_track

    np.random.seed(42)
    caos_matrix = np.random.normal(loc=0, scale=6.0, size=(num_simulations, num_drivers))
    theoretical_times_base = (base_paces * laps) + total_race_deg + launch_penalty + dirty_air_penalty
    
    ranks_A = np.argsort(np.argsort(theoretical_times_base + caos_matrix, axis=1), axis=1) + 1
    
    prob_win = (ranks_A == 1).mean(axis=0) * 100
    prob_podium = (ranks_A <= 3).mean(axis=0) * 100
    prob_top6 = (ranks_A <= 6).mean(axis=0) * 100
    prob_top10 = (ranks_A <= 10).mean(axis=0) * 100
    
    df_prediction = pd.DataFrame({
        'code': df_final_sim['code'], 
        'ai_predicted_pos': [np.mean(ranks_A[:, i]) for i in range(num_drivers)],
        'ai_talent_bonus': df_final_sim['talent_bonus_s'].values,
        'ai_base_pace': base_paces,
        'prob_win': prob_win,
        'prob_podium': prob_podium,
        'prob_top6': prob_top6,
        'prob_top10': prob_top10
    })
    return df_prediction

# ==========================================
# 📊 FUSIÓN UI + IA
# ==========================================
@st.cache_data(ttl=600)
def build_master_dataframe(target_round):
    df_ai = run_ai_prediction_engine(target_round)
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
        st.warning(f"⚠️ Aún no hay telemetría en la base de datos para **{selected_race_name}**. Sube los datos a Supabase.")
    else:
        with st.spinner(f'Calculando Probabilidades de Monte Carlo para {selected_race_name}...'):
            for i in range(0, len(master_df), 3):
                drivers_chunk = master_df.iloc[i : i+3]
                cols = st.columns(3)
                for col, (_, driver) in zip(cols, drivers_chunk.iterrows()):
                    equipo = driver['Escudería']
                    codigo = driver['Código']
                    
                    equipo_archivo = equipo.replace(' ', '_')
                    p_low = driver['Piloto'].lower().replace(' ', '_')
                    p_tit = driver['Piloto'].replace(' ', '_')
                    color = team_colors.get(equipo, "#555")

                    logo_w = obtener_url_valida([
                        f"{STORAGE_BASE_URL}/logos/{equipo_archivo}.webp", 
                        f"{STORAGE_BASE_URL}/logos/{equipo_archivo}.png",
                        f"{STORAGE_BASE_URL}/logos/{equipo_archivo}.svg"
                    ])
                    photo = obtener_url_valida([
                        f"{STORAGE_BASE_URL}/drivers/{p_low}.webp", 
                        f"{STORAGE_BASE_URL}/drivers/{p_low}.png",
                        f"{STORAGE_BASE_URL}/drivers/{p_tit}.webp",
                        f"{STORAGE_BASE_URL}/drivers/{p_tit}.png"
                    ])

                    with col:
                        st.markdown(f"""
<div class="grid-container" style="--team-color: {color};">
<img src="{logo_w}" class="logo-full-color">
<div class="driver-section">
<div class="pos-name-block">
<div class="pos-number">P{int(master_df.index[master_df['driver_number'] == driver['driver_number']][0] + 1)}</div>
<div>
<p class="driver-name">{driver['Piloto']} <span style="font-size:12px; color:#666;">{codigo}</span></p>
<p class="team-name">{equipo}</p>
</div>
</div>

<img src="{photo}" class="driver-photo">
</div>
<div class="telemetry-section">
<div>
<p class="telemetry-title">MARKET PROBABILITIES: {selected_race_name.split(': ')[-1]}</p>
<table class="data-table">
<tr><td class="label">Win (P1)</td><td class="value">{driver['prob_win']}</td></tr>
<tr><td class="label">Podium (Top 3)</td><td class="value">{driver['prob_podium']}</td></tr>
<tr><td class="label">Top 6 Finish</td><td class="value">{driver['prob_top6']}</td></tr>
<tr><td class="label">Points (Top 10)</td><td class="value">{driver['prob_top10']}</td></tr>
</table>
</div>
</div>
</div>
""", unsafe_allow_html=True)

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
                
                left_highlight_class = "h2h-winner-unit" if p_left['Código'] == predicted_winner_code else ""
                right_highlight_class = "h2h-winner-unit" if p_right['Código'] == predicted_winner_code else ""
                
                color_equipo = team_colors.get(equipo, "#555")
                color_equipo_shadow = color_equipo + "40"
                
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
                
                html_h2h = f"""
<div class="h2h-match-wrapper" style="--team-color: {color_equipo}; --team-color-shadow: {color_equipo_shadow}; border-left: 5px solid {color_equipo};">
<div class="h2h-driver-unit h2h-driver-unit-left {left_highlight_class}">
<div class="h2h-photo-container">
<img src="{photo_left}" class="h2h-photo-img">
</div>
<div class="h2h-info-container">
<p class="h2h-driver-unit-title">{p_left['Piloto']} ({p_left['Código']})</p>
<p class="h2h-team-name">{equipo}</p>
<span class="h2h-pos-num">
<span class="h2h-pos-prefix">P</span>
<span class="h2h-pos-value">{int(round(p_left['ai_predicted_pos']))}</span>
</span>
<p class="h2h-base-pace-text">Base Pace: <span class="h2h-base-pace-formatted">{format_pace(p_left['ai_base_pace'])}</span></p>
</div>
</div>
    
<div class="h2h-team-logo-center">
<img src="{logo_center}" class="h2h-team-logo-img">
</div>
    
<div class="h2h-driver-unit h2h-driver-unit-right {right_highlight_class}">
<div class="h2h-photo-container">
<img src="{photo_right}" class="h2h-photo-img">
</div>
<div class="h2h-info-container">
<p class="h2h-driver-unit-title">{p_right['Piloto']} ({p_right['Código']})</p>
<p class="h2h-team-name">{equipo}</p>
<span class="h2h-pos-num">
<span class="h2h-pos-prefix">P</span>
<span class="h2h-pos-value">{int(round(p_right['ai_predicted_pos']))}</span>
</span>
<p class="h2h-base-pace-text">Base Pace: <span class="h2h-base-pace-formatted">{format_pace(p_right['ai_base_pace'])}</span></p>
</div>
</div>
</div>
"""
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
