import os
import fastf1
import pandas as pd
import numpy as np
from supabase import create_client
from dotenv import load_dotenv

print("🏎️ Encendiendo el motor de actualización F1...")

# 1. Configuración inicial
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

cache_dir = "f1_cache"
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)
fastf1.Cache.enable_cache(cache_dir)

print("✅ Conexión y Caché listos.\n")

# ==========================================
# ⏱️ 1. CLASIFICACIÓN (QUALY)
# ==========================================
def actualizar_qualy(year, round_num):
    print(f"⏱️ Procesando Clasificación (Ronda {round_num})...")
    try:
        session = fastf1.get_session(year, round_num, 'Q')
        session.load(telemetry=False, weather=False) 
        resultados = session.results
        pole_time = resultados.iloc[0]['Q3'] 
        
        datos_qualy = []
        for index, row in resultados.iterrows():
            code = row['Abbreviation']
            best_time = row['Q3'] if not pd.isnull(row['Q3']) else (row['Q2'] if not pd.isnull(row['Q2']) else row['Q1'])
            
            if pd.isnull(best_time) or pd.isnull(pole_time):
                delta_s, best_lap_s = 5.0, 99.999 
            else:
                delta_s = (best_time - pole_time).total_seconds()
                best_lap_s = best_time.total_seconds()
                
            datos_qualy.append({"round_number": round_num, "code": code, "delta_to_pole_s": round(delta_s, 3), "best_lap_s": round(best_lap_s, 3)})
            
        supabase.table("qualy_profiles").delete().eq("round_number", round_num).execute()
        supabase.table("qualy_profiles").insert(datos_qualy).execute()
        print(f"✅ Qualy guardada.\n")
    except Exception as e: print(f"❌ Error Qualy: {e}\n")

# ==========================================
# 🏆 2. RESULTADOS OFICIALES
# ==========================================
def actualizar_resultados(year, round_num):
    print(f"🏆 Procesando Resultados Oficiales (Ronda {round_num})...")
    try:
        session = fastf1.get_session(year, round_num, 'R')
        session.load(telemetry=False, weather=False)
        resultados = session.results
        
        datos_oficiales = []
        for index, row in resultados.iterrows():
            code = row['Abbreviation']
            pos = row['Position']
            
            # Si el piloto abandonó (DNF), Position suele ser NaN. Lo mandamos al P20.
            if pd.isnull(pos): pos = 20.0
                
            datos_oficiales.append({"round_number": round_num, "code": code, "official_position": int(pos)})
            
        supabase.table("official_race_results").delete().eq("round_number", round_num).execute()
        supabase.table("official_race_results").insert(datos_oficiales).execute()
        print(f"✅ Resultados guardados.\n")
    except Exception as e: print(f"❌ Error Resultados: {e}\n")

# ==========================================
# 📊 3. RITMOS Y DEGRADACIÓN (RACE PROFILES)
# ==========================================
def actualizar_ritmos(year, round_num):
    print(f"📊 Procesando Ritmos y Degradación (Ronda {round_num})...")
    try:
        session = fastf1.get_session(year, round_num, 'R')
        session.load(telemetry=False, weather=False)
        laps = session.laps.pick_quicklaps() 
        
        datos_ritmo = []
        pilotos = laps['Driver'].unique()
        
        for piloto in pilotos:
            vueltas_piloto = laps[laps['Driver'] == piloto]
            compuestos = vueltas_piloto['Compound'].dropna().unique()
            
            for comp in compuestos:
                vueltas_comp = vueltas_piloto[vueltas_piloto['Compound'] == comp]
                if len(vueltas_comp) < 3: continue 
                
                base_pace = vueltas_comp['LapTime'].dt.total_seconds().median()
                
                if len(vueltas_comp) >= 5:
                    x = np.arange(len(vueltas_comp))
                    y = vueltas_comp['LapTime'].dt.total_seconds().values
                    deg = np.polyfit(x, y, 1)[0]
                    deg = max(0.02, min(deg, 0.15)) 
                else:
                    deg = 0.05 
                
                # CORRECCIÓN SUPABASE: Mapeo exacto basado en tu captura de pantalla
                datos_ritmo.append({
                    "round_number": round_num,
                    "code": piloto,
                    "compound": comp,
                    "base_pace_s": round(base_pace, 3),
                    "deg_per_lap": round(deg, 3),
                    "deg_ms_per_lap": int(deg * 1000),           # Columna confirmada
                    "total_valid_sectors": len(vueltas_comp)     # Llenamos la columna extra de tu DB
                })
        
        supabase.table("race_profiles").delete().eq("round_number", round_num).execute()
        supabase.table("race_profiles").insert(datos_ritmo).execute()
        print(f"✅ Ritmos guardados.\n")
    except Exception as e: print(f"❌ Error Ritmos: {e}\n")

# ==========================================
# 🚀 DISPARADOR MAESTRO AUTÓNOMO
# ==========================================
import datetime

if __name__ == "__main__":
    AÑO_ACTUAL = 2026
    
    # 1. Obtenemos el calendario oficial de la FIA
    calendario = fastf1.get_event_schedule(AÑO_ACTUAL)
    
    # 2. Comparamos con la fecha actual para saber qué carrera acaba de pasar
    hoy = pd.Timestamp.now()
    carreras_completadas = calendario[calendario['EventDate'] < hoy]
    
    # 3. Extraemos el número de la última ronda disputada
    if no carreras_completadas.empty:
        RONDA_A_ACTUALIZAR = int(carreras_completadas.iloc[-1]['RoundNumber'])
    else:
        RONDA_A_ACTUALIZAR = 1
        
    print(f"--- INICIANDO ACTUALIZACIÓN TOTAL PARA RONDA {RONDA_A_ACTUALIZAR} ---\n")
    actualizar_qualy(AÑO_ACTUAL, RONDA_A_ACTUALIZAR)
    actualizar_resultados(AÑO_ACTUAL, RONDA_A_ACTUALIZAR)
    actualizar_ritmos(AÑO_ACTUAL, RONDA_A_ACTUALIZAR)
    print("🏁 ACTUALIZACIÓN COMPLETA FINALIZADA 🏁")
