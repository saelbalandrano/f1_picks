import os
import fastf1
import pandas as pd
import numpy as np
from supabase import create_client
from dotenv import load_dotenv

print("🏎️ Encendiendo el motor de actualización F1 (MODO BLINDADO)...")

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
        
        if resultados is None or resultados.empty:
            print("⚠️ No hay datos de Qualy disponibles aún en FastF1.")
            return

        # Protección para buscar Q3 o SQ3 si es formato Sprint
        pole_time = None
        if 'Q3' in resultados.columns:
            pole_time = resultados.iloc[0]['Q3']
        elif 'SQ3' in resultados.columns:
            pole_time = resultados.iloc[0]['SQ3']
            
        datos_qualy = []
        for index, row in resultados.iterrows():
            code = row['Abbreviation']
            best_time = None
            
            # Buscar el mejor tiempo en cualquier bloque de Qualy
            for q_col in ['Q3', 'Q2', 'Q1', 'SQ3', 'SQ2', 'SQ1']:
                if q_col in row and not pd.isnull(row[q_col]):
                    best_time = row[q_col]
                    break
            
            if pd.isnull(best_time) or pd.isnull(pole_time):
                delta_s, best_lap_s = 5.0, 99.999 
            else:
                delta_s = (best_time - pole_time).total_seconds()
                best_lap_s = best_time.total_seconds()
                
            datos_qualy.append({
                "round_number": db_round, 
                "code": code, 
                "delta_to_pole_s": round(delta_s, 3), 
                "best_lap_s": round(best_lap_s, 3)
            })
            
        if datos_qualy:
            supabase.table("qualy_profiles").delete().eq("round_number", db_round).execute()
            supabase.table("qualy_profiles").insert(datos_qualy).execute()
            print(f"✅ Qualy guardada ({len(datos_qualy)} pilotos).")
        else:
            print("⚠️ Datos de Qualy procesados pero vacíos.")
            
    except Exception as e: 
        print(f"❌ Error interno en Qualy: {e}")

# ==========================================
# 🏆 2. RESULTADOS OFICIALES
# ==========================================
def actualizar_resultados(year, fia_round, db_round):
    print(f"🏆 Procesando Resultados Oficiales (Descarga: {fia_round} | Guarda: {db_round})...")
    try:
        session = fastf1.get_session(year, fia_round, 'R')
        session.load(telemetry=False, weather=False)
        resultados = session.results
        
        if resultados is None or resultados.empty:
            print("⚠️ No hay resultados de carrera disponibles aún en FastF1.")
            return
            
        datos_oficiales = []
        for index, row in resultados.iterrows():
            code = row['Abbreviation']
            pos = row['Position']
            
            if pd.isnull(pos): pos = 20.0
                
            datos_oficiales.append({
                "round_number": db_round, 
                "code": code, 
                "official_position": int(pos)
            })
            
        if datos_oficiales:
            supabase.table("official_race_results").delete().eq("round_number", db_round).execute()
            supabase.table("official_race_results").insert(datos_oficiales).execute()
            print(f"✅ Resultados guardados ({len(datos_oficiales)} pilotos).")
        else:
            print("⚠️ Resultados procesados pero vacíos.")
            
    except Exception as e: 
        print(f"❌ Error interno en Resultados: {e}")

# ==========================================
# 📊 3. RITMOS Y DEGRADACIÓN MULTI-SESIÓN
# ==========================================
def actualizar_ritmos(year, fia_round, db_round):
    print(f"📊 Procesando Ritmos (Descarga: {fia_round} | Guarda: {db_round})...")
    try:
        vueltas_acumuladas = []
        
        # BÚCLE DEVORADOR: Busca absolutamente en todas las sesiones del fin de semana
        sesiones_todas = ['FP1', 'FP2', 'FP3', 'SQ', 'S', 'Q', 'R']
        
        for sesion_nombre in sesiones_todas:
            try:
                session = fastf1.get_session(year, fia_round, sesion_nombre)
                session.load(telemetry=False, weather=False)
                
                if session.laps is not None and not session.laps.empty:
                    vueltas_validas = session.laps.pick_quicklaps()
                    if not vueltas_validas.empty:
                        vueltas_acumuladas.append(vueltas_validas)
                        print(f"   -> Vueltas extraídas con éxito de: {sesion_nombre}")
            except Exception:
                pass # Silencioso si la sesión simplemente no existió en este GP
                
        if not vueltas_acumuladas:
            print("⚠️ Falla Crítica: No se encontró telemetría útil en ninguna sesión de FastF1.")
            return

        laps_master = pd.concat(vueltas_acumuladas, ignore_index=True)
        datos_ritmo = []
        pilotos = laps_master['Driver'].unique()
        
        for piloto in pilotos:
            vueltas_piloto = laps_master[laps_master['Driver'] == piloto]
            compuestos = vueltas_piloto['Compound'].dropna().unique()
            
            for comp in compuestos:
                vueltas_comp = vueltas_piloto[vueltas_piloto['Compound'] == comp]
                
                # Exigimos al menos 3 vueltas para poder hacer una matemática real
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
        
        # CANDADO ANTI-CRASH: Solo inserta si hay datos reales
        if datos_ritmo:
            supabase.table("race_profiles").delete().eq("round_number", db_round).execute()
            supabase.table("race_profiles").insert(datos_ritmo).execute()
            print(f"✅ Ritmos consolidados ({len(datos_ritmo)} perfiles de llantas guardados).")
        else:
            print("⚠️ Se descargaron vueltas pero ningún piloto hizo 3 seguidas con la misma llanta.")
            
    except Exception as e: 
        print(f"❌ Error interno en Ritmos: {e}")

# ==========================================
# 🚀 DISPARADOR MAESTRO (CONTROL MANUAL)
# ==========================================
if __name__ == "__main__":
    AÑO_ACTUAL = 2026
    
    # ---------------------------------------------------------
    # ⚙️ CONTROL DE DESFASE: Modifica esto para cada carrera
    # ---------------------------------------------------------
    RONDA_FIA = 6  # El número oficial de la FIA (Miami = 6)
    RONDA_DB  = 4  # El número en TU base de datos limpia (Miami = 4)
    # ---------------------------------------------------------
    
    print(f"--- INICIANDO ACTUALIZACIÓN TOTAL ---\n")
    print(f"🌍 Extrayendo de FIA Ronda {RONDA_FIA}...")
    print(f"💾 Guardando en Supabase Ronda {RONDA_DB}...\n")
    
    actualizar_qualy(AÑO_ACTUAL, RONDA_FIA, RONDA_DB)
    actualizar_resultados(AÑO_ACTUAL, RONDA_FIA, RONDA_DB)
    actualizar_ritmos(AÑO_ACTUAL, RONDA_FIA, RONDA_DB)
    print("\n🏁 ACTUALIZACIÓN COMPLETA FINALIZADA 🏁")
