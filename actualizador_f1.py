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
def actualizar_qualy(year, fia_round, db_round):
    print(f"⏱️ Procesando Clasificación (Descarga: {fia_round} | Guarda: {db_round})...")
    try:
        session = fastf1.get_session(year, fia_round, 'Q')
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
                
            datos_qualy.append({"round_number": db_round, "code": code, "delta_to_pole_s": round(delta_s, 3), "best_lap_s": round(best_lap_s, 3)})
            
        supabase.table("qualy_profiles").delete().eq("round_number", db_round).execute()
        supabase.table("qualy_profiles").insert(datos_qualy).execute()
        print(f"✅ Qualy guardada.\n")
    except Exception as e: print(f"❌ Error Qualy: {e}\n")

# ==========================================
# 🏆 2. RESULTADOS OFICIALES
# ==========================================
def actualizar_resultados(year, fia_round, db_round):
    print(f"🏆 Procesando Resultados Oficiales (Descarga: {fia_round} | Guarda: {db_round})...")
    try:
        session = fastf1.get_session(year, fia_round, 'R')
        session.load(telemetry=False, weather=False)
        resultados = session.results
        
        datos_oficiales = []
        for index, row in resultados.iterrows():
            code = row['Abbreviation']
            pos = row['Position']
            
            if pd.isnull(pos): pos = 20.0
                
            datos_oficiales.append({"round_number": db_round, "code": code, "official_position": int(pos)})
            
        supabase.table("official_race_results").delete().eq("round_number", db_round).execute()
        supabase.table("official_race_results").insert(datos_oficiales).execute()
        print(f"✅ Resultados guardados.\n")
    except Exception as e: print(f"❌ Error Resultados: {e}\n")

# ==========================================
# 📊 3. RITMOS MULTI-SESIÓN (PRÁCTICAS Y SPRINT)
# ==========================================
def actualizar_ritmos(year, fia_round, db_round):
    print(f"📊 Procesando Ritmos Multi-Sesión (Descarga: {fia_round} | Guarda: {db_round})...")
    try:
        vueltas_acumuladas = []
        
        # BÚCLE MÁGICO: Busca en todas las sesiones previas a la carrera
        sesiones_pre_carrera = ['FP1', 'FP2', 'FP3', 'SQ', 'S']
        for sesion_nombre in sesiones_pre_carrera:
            try:
                session = fastf1.get_session(year, fia_round, sesion_nombre)
                session.load(telemetry=False, weather=False)
                if not session.laps.empty:
                    vueltas_acumuladas.append(session.laps.pick_quicklaps())
                    print(f"   -> Datos extraídos de: {sesion_nombre}")
            except:
                pass # Si la sesión no existe, la salta en silencio
                
        if not vueltas_acumuladas:
            print("⚠️ No se encontró telemetría en ninguna sesión.")
            return

        # Juntamos todas las vueltas del fin de semana
        laps_master = pd.concat(vueltas_acumuladas, ignore_index=True)
        datos_ritmo = []
        pilotos = laps_master['Driver'].unique()
        
        for piloto in pilotos:
            vueltas_piloto = laps_master[laps_master['Driver'] == piloto]
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
                
                datos_ritmo.append({
                    "round_number": db_round,
                    "code": piloto,
                    "compound": comp,
                    "base_pace_s": round(base_pace, 3),
                    "deg_per_lap": round(deg, 3),
                    "deg_ms_per_lap": int(deg * 1000),
                    "total_valid_sectors": len(vueltas_comp)
                })
        
        supabase.table("race_profiles").delete().eq("round_number", db_round).execute()
        supabase.table("race_profiles").insert(datos_ritmo).execute()
        print(f"✅ Ritmos guardados.\n")
    except Exception as e: print(f"❌ Error Ritmos: {e}\n")

# ==========================================
# 🚀 DISPARADOR MAESTRO (CONTROL MANUAL)
# ==========================================
if __name__ == "__main__":
    AÑO_ACTUAL = 2026
    
    # ---------------------------------------------------------
    # ⚙️ CONTROL DE DESFASE: Modifica esto para cada carrera
    # ---------------------------------------------------------
    RONDA_FIA = 6  # El número oficial de la FIA (Miami = 6)
    RONDA_DB  = 4  # El número en TU base de datos (Miami = 4)
    # ---------------------------------------------------------
    
    print(f"--- INICIANDO ACTUALIZACIÓN TOTAL ---\n")
    print(f"🌍 Extrayendo de FIA Ronda {RONDA_FIA}...")
    print(f"💾 Guardando en Supabase Ronda {RONDA_DB}...\n")
    
    actualizar_qualy(AÑO_ACTUAL, RONDA_FIA, RONDA_DB)
    actualizar_resultados(AÑO_ACTUAL, RONDA_FIA, RONDA_DB)
    actualizar_ritmos(AÑO_ACTUAL, RONDA_FIA, RONDA_DB)
    print("🏁 ACTUALIZACIÓN COMPLETA FINALIZADA 🏁")
