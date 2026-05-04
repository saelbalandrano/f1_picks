import os
import sys
import fastf1
import pandas as pd
import numpy as np
import datetime
from supabase import create_client
from dotenv import load_dotenv
sys.stdout.reconfigure(encoding='utf-8')

print("🏎️ Encendiendo el motor de actualización F1...")

# 1. Configuración inicial
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

import logging

cache_dir = "f1_cache"
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)
fastf1.Cache.enable_cache(cache_dir)

# Silence FastF1 warnings
logging.getLogger("fastf1").setLevel(logging.ERROR)

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
    except Exception as e: print(f"❌ Error Qualy: la sesión aún no sucede o hubo un problema. ({e})\n")

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
        
        # También actualizamos el status del evento a 'completed'
        supabase.table("events").update({"status": "completed"}).eq("round_number", round_num).execute()
        
        print(f"✅ Resultados guardados.\n")
    except Exception as e: print(f"❌ Error Resultados: la carrera aún no sucede o hubo un problema. ({e})\n")

# ==========================================
# 📊 3. RITMOS Y DEGRADACIÓN (RACE PROFILES DE TODAS LAS SESIONES)
# ==========================================
def actualizar_ritmos(year, round_num):
    print(f"📊 Procesando Ritmos y Degradación (Ronda {round_num}) a partir de todas las sesiones...")
    session_types = ['FP1', 'FP2', 'FP3', 'SQ', 'S', 'R']
    todos_datos_ritmo = []
    
    for s_type in session_types:
        try:
            print(f"   -> Intentando cargar sesión: {s_type}")
            session = fastf1.get_session(year, round_num, s_type)
            session.load(telemetry=False, weather=False)
            laps = session.laps.pick_quicklaps() 
            
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
                    
                    todos_datos_ritmo.append({
                        "round_number": round_num,
                        "code": piloto,
                        "compound": comp,
                        "base_pace_s": round(base_pace, 3),
                        "deg_per_lap": round(deg, 3),
                        "deg_ms_per_lap": int(deg * 1000),           
                        "total_valid_sectors": len(vueltas_comp)     
                    })
            print(f"   ✅ Ritmos de {s_type} extraídos.")
        except Exception as e: 
            print(f"   ⚠️ Sesión {s_type} ignorada o no disponible.")

    if todos_datos_ritmo:
        df_ritmos = pd.DataFrame(todos_datos_ritmo)
        # Agrupar por piloto y compuesto para quedarnos con el mejor base_pace_s y promedio de deg
        df_agrupado = df_ritmos.groupby(['round_number', 'code', 'compound']).agg({
            'base_pace_s': 'min',
            'deg_per_lap': 'mean',
            'deg_ms_per_lap': 'mean',
            'total_valid_sectors': 'sum'
        }).reset_index()
        
        datos_ritmo_final = df_agrupado.to_dict('records')
        
        try:
            supabase.table("race_profiles").delete().eq("round_number", round_num).execute()
            supabase.table("race_profiles").insert(datos_ritmo_final).execute()
            print(f"✅ Todos los Ritmos guardados correctamente.\n")
        except Exception as e:
            print(f"❌ Error al guardar ritmos en supabase: {e}\n")
    else:
        print("⚠️ No se encontraron ritmos válidos en ninguna sesión.\n")

# ==========================================
# 🚀 DISPARADOR MAESTRO
# ==========================================
if __name__ == "__main__":
    AÑO_ACTUAL = 2026
    
    if len(sys.argv) > 1:
        RONDA_A_ACTUALIZAR = int(sys.argv[1])
    else:
        # Detectar automáticamente la ronda más cercana a hoy
        try:
            res = supabase.table("events").select("round_number, race_date").execute()
            df_events = pd.DataFrame(res.data)
            df_events['race_date'] = pd.to_datetime(df_events['race_date'])
            hoy = pd.to_datetime(datetime.date.today())
            df_events['diff'] = (df_events['race_date'] - hoy).dt.total_seconds().abs()
            RONDA_A_ACTUALIZAR = int(df_events.loc[df_events['diff'].idxmin()]['round_number'])
            print(f"📍 Ronda detectada automáticamente: {RONDA_A_ACTUALIZAR}")
        except Exception as e:
            print("⚠️ No se pudo auto-detectar la ronda. Usando ronda 4 por defecto.")
            RONDA_A_ACTUALIZAR = 4
    
    print(f"--- INICIANDO ACTUALIZACIÓN TOTAL PARA RONDA {RONDA_A_ACTUALIZAR} ---\n")
    actualizar_ritmos(AÑO_ACTUAL, RONDA_A_ACTUALIZAR)
    actualizar_qualy(AÑO_ACTUAL, RONDA_A_ACTUALIZAR)
    actualizar_resultados(AÑO_ACTUAL, RONDA_A_ACTUALIZAR)
    print("🏁 ACTUALIZACIÓN COMPLETA FINALIZADA 🏁")