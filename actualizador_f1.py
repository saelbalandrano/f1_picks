import os
import fastf1
import pandas as pd
import numpy as np
from supabase import create_client
from dotenv import load_dotenv

print("🏎️ Encendiendo el motor F1 (MODO 100% AUTÓNOMO)...")

# 1. Configuración inicial
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

cache_dir = "f1_cache"
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)
fastf1.Cache.enable_cache(cache_dir)

# ==========================================
# ⏱️ 1. CLASIFICACIÓN (QUALY / SQ)
# ==========================================
def actualizar_qualy(year, round_num):
    print(f"⏱️ Procesando Clasificación (Ronda {round_num})...")
    try:
        session = fastf1.get_session(year, round_num, 'Q')
        session.load(telemetry=False, weather=False) 
        resultados = session.results
        
        if resultados.empty:
            print("⚠️ Qualy principal vacía. Intentando con Sprint Qualy (SQ)...")
            try:
                session = fastf1.get_session(year, round_num, 'SQ')
                session.load(telemetry=False, weather=False)
                resultados = session.results
            except:
                return

        pole_time = resultados.iloc[0]['Q3'] if 'Q3' in resultados.columns and not pd.isnull(resultados.iloc[0]['Q3']) else resultados.iloc[0].get('SQ3', None)
        
        datos_qualy = []
        for index, row in resultados.iterrows():
            code = row['Abbreviation']
            if 'Q3' in row:
                best_time = row['Q3'] if not pd.isnull(row['Q3']) else (row['Q2'] if not pd.isnull(row['Q2']) else row['Q1'])
            else:
                best_time = row['SQ3'] if not pd.isnull(row['SQ3']) else (row['SQ2'] if not pd.isnull(row['SQ2']) else row['SQ1'])
            
            if pd.isnull(best_time) or pd.isnull(pole_time):
                delta_s, best_lap_s = 5.0, 99.999 
            else:
                delta_s = (best_time - pole_time).total_seconds()
                best_lap_s = best_time.total_seconds()
                
            datos_qualy.append({"round_number": round_num, "code": code, "delta_to_pole_s": round(delta_s, 3), "best_lap_s": round(best_lap_s, 3)})
            
        supabase.table("qualy_profiles").delete().eq("round_number", round_num).execute()
        supabase.table("qualy_profiles").insert(datos_qualy).execute()
        print(f"✅ Parrilla de salida guardada.\n")
    except Exception as e: print(f"❌ Error Qualy: {e}\n")

# ==========================================
# 🏆 2. RESULTADOS OFICIALES
# ==========================================
def actualizar_resultados(year, round_num):
    print(f"🏆 Buscando Resultados Oficiales (Ronda {round_num})...")
    try:
        session = fastf1.get_session(year, round_num, 'R')
        session.load(telemetry=False, weather=False)
        if session.results.empty: return
            
        datos_oficiales = []
        for index, row in session.results.iterrows():
            pos = row['Position'] if not pd.isnull(row['Position']) else 20.0
            datos_oficiales.append({"round_number": round_num, "code": row['Abbreviation'], "official_position": int(pos)})
            
        supabase.table("official_race_results").delete().eq("round_number", round_num).execute()
        supabase.table("official_race_results").insert(datos_oficiales).execute()
        print(f"✅ Resultados Oficiales guardados.\n")
    except Exception: print(f"⚠️ La carrera principal no se ha corrido aún.\n")

# ==========================================
# 📊 3. RITMOS MULTI-SESIÓN
# ==========================================
def actualizar_ritmos(year, round_num):
    print(f"📊 Recolectando telemetría de TODAS las sesiones (Ronda {round_num})...")
    try:
        vueltas_acumuladas = []
        for sesion_nombre in ['FP1', 'FP2', 'FP3', 'SQ', 'S']:
            try:
                session = fastf1.get_session(year, round_num, sesion_nombre)
                session.load(telemetry=False, weather=False)
                if not session.laps.empty: vueltas_acumuladas.append(session.laps.pick_quicklaps())
            except: pass 
        
        if not vueltas_acumuladas: return
            
        laps_master = pd.concat(vueltas_acumuladas, ignore_index=True)
        datos_ritmo = []
        
        for piloto in laps_master['Driver'].unique():
            vueltas_piloto = laps_master[laps_master['Driver'] == piloto]
            for comp in vueltas_piloto['Compound'].dropna().unique():
                v_c = vueltas_piloto[vueltas_piloto['Compound'] == comp]
                if len(v_c) < 3: continue 
                
                base_pace = v_c['LapTime'].dt.total_seconds().median()
                deg = np.polyfit(np.arange(len(v_c)), v_c['LapTime'].dt.total_seconds().values, 1)[0] if len(v_c) >= 5 else 0.05 
                
                datos_ritmo.append({
                    "round_number": round_num, "code": piloto, "compound": comp,
                    "base_pace_s": round(base_pace, 3), "deg_per_lap": round(max(0.02, min(deg, 0.15)), 3),
                    "deg_ms_per_lap": int(deg * 1000), "total_valid_sectors": len(v_c)
                })
        
        if datos_ritmo:
            supabase.table("race_profiles").delete().eq("round_number", round_num).execute()
            supabase.table("race_profiles").insert(datos_ritmo).execute()
            print(f"✅ Ritmos consolidados ({len(datos_ritmo)} perfiles) guardados.\n")
    except Exception as e: print(f"❌ Error Ritmos: {e}\n")

# ==========================================
# 🧠 4. AUTO-APRENDIZAJE DE PISTA (NUEVO)
# ==========================================
def actualizar_info_pista(year, round_num):
    print(f"🌍 Analizando metadata del circuito (Ronda {round_num})...")
    try:
        event = fastf1.get_event(year, round_num)
        event_name = event['EventName']
        laps = 50 # Default
        
        # Viajamos un año al pasado para ver cuántas vueltas dieron en este mismo GP
        try:
            print(f"   -> Consultando archivo histórico de {event_name} ({year-1})...")
            hist_session = fastf1.get_session(year - 1, event_name, 'R')
            hist_session.load(telemetry=False, weather=False)
            laps = int(hist_session.results['Laps'].max())
        except:
            print("   -> No hay datos del año pasado. Usando aproximación.")
        
        # Guardamos el dato matemáticamente comprobado en la base de datos
        supabase.table("events").update({"total_laps": laps}).eq("round_number", round_num).execute()
        print(f"✅ Pista actualizada automáticamente en Supabase: {laps} Vueltas.\n")
    except Exception as e:
        print(f"❌ Error al calcular metadata de pista: {e}")

# ==========================================
# 🚀 DISPARADOR MAESTRO 
# ==========================================
if __name__ == "__main__":
    AÑO_ACTUAL = 2026
    
    calendario = fastf1.get_event_schedule(AÑO_ACTUAL)
    calendario = calendario[calendario['EventFormat'] != 'testing']
    calendario['EventDate'] = pd.to_datetime(calendario['EventDate']).dt.tz_localize(None)
    hoy = pd.Timestamp.now().tz_localize(None)
    
    carreras_vigentes = calendario[calendario['EventDate'] >= (hoy - pd.Timedelta(days=2))]
    
    if not carreras_vigentes.empty:
        RONDA_A_ACTUALIZAR = int(carreras_vigentes.iloc[0]['RoundNumber'])
    else:
        RONDA_A_ACTUALIZAR = int(calendario.iloc[-1]['RoundNumber'])
        
    print(f"\n--- INICIANDO EXTRACCIÓN TOTAL PARA RONDA {RONDA_A_ACTUALIZAR} ---\n")
    actualizar_info_pista(AÑO_ACTUAL, RONDA_A_ACTUALIZAR) # <-- APRENDE LA PISTA
    actualizar_qualy(AÑO_ACTUAL, RONDA_A_ACTUALIZAR)
    actualizar_resultados(AÑO_ACTUAL, RONDA_A_ACTUALIZAR)
    actualizar_ritmos(AÑO_ACTUAL, RONDA_A_ACTUALIZAR)
    print("🏁 EXTRACCIÓN FINALIZADA 🏁")
