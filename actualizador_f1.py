import os
import fastf1
import pandas as pd
import numpy as np
from supabase import create_client
from dotenv import load_dotenv

print("🏎️ Encendiendo el motor F1 (MODO SINCRONIZACIÓN INTELIGENTE)...")

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
# 🔍 TRADUCTOR DE RONDAS (FIA vs SUPABASE)
# ==========================================
def obtener_ronda_db(loc_fia, pais_fia, fia_round):
    res = supabase.table("events").select("round_number, country, circuit_name").execute()
    if not res.data: return fia_round
    
    loc_fia_clean = str(loc_fia).lower().strip()
    pais_fia_clean = str(pais_fia).lower().strip()
    
    # 1. Búsqueda de alta precisión: Por Ciudad / Nombre del Circuito
    for row in res.data:
        circ_db = str(row.get('circuit_name', '')).lower()
        if loc_fia_clean in circ_db:
            return row['round_number']
            
    # 2. Búsqueda secundaria: Por País (Para países con 1 sola carrera)
    for row in res.data:
        pais_db = str(row.get('country', '')).lower()
        if pais_fia_clean == pais_db or pais_fia_clean in pais_db or pais_db in pais_fia_clean:
            return row['round_number']
            
    return fia_round # Si no encuentra nada, usa el número de la FIA por defecto

# ==========================================
# ⏱️ 1. CLASIFICACIÓN (QUALY / SQ)
# ==========================================
def actualizar_qualy(year, fia_round, db_round):
    print(f"⏱️ Procesando Qualy... (Guardando en ID {db_round})")
    try:
        session = fastf1.get_session(year, fia_round, 'Q')
        session.load(telemetry=False, weather=False) 
        resultados = session.results
        
        if resultados.empty:
            print("⚠️ Qualy principal vacía. Intentando con Sprint Qualy (SQ)...")
            try:
                session = fastf1.get_session(year, fia_round, 'SQ')
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
                
            datos_qualy.append({"round_number": db_round, "code": code, "delta_to_pole_s": round(delta_s, 3), "best_lap_s": round(best_lap_s, 3)})
            
        supabase.table("qualy_profiles").delete().eq("round_number", db_round).execute()
        supabase.table("qualy_profiles").insert(datos_qualy).execute()
        print(f"✅ Parrilla guardada correctamente.\n")
    except Exception as e: print(f"❌ Error Qualy: {e}\n")

# ==========================================
# 🏆 2. RESULTADOS OFICIALES
# ==========================================
def actualizar_resultados(year, fia_round, db_round):
    print(f"🏆 Buscando Resultados... (Guardando en ID {db_round})")
    try:
        session = fastf1.get_session(year, fia_round, 'R')
        session.load(telemetry=False, weather=False)
        if session.results.empty: return
            
        datos_oficiales = []
        for index, row in session.results.iterrows():
            pos = row['Position'] if not pd.isnull(row['Position']) else 20.0
            datos_oficiales.append({"round_number": db_round, "code": row['Abbreviation'], "official_position": int(pos)})
            
        supabase.table("official_race_results").delete().eq("round_number", db_round).execute()
        supabase.table("official_race_results").insert(datos_oficiales).execute()
        print(f"✅ Resultados Oficiales guardados.\n")
    except Exception: print(f"⚠️ La carrera principal no se ha corrido aún.\n")

# ==========================================
# 📊 3. RITMOS MULTI-SESIÓN
# ==========================================
def actualizar_ritmos(year, fia_round, db_round):
    print(f"📊 Recolectando telemetría... (Guardando en ID {db_round})")
    try:
        vueltas_acumuladas = []
        for sesion_nombre in ['FP1', 'FP2', 'FP3', 'SQ', 'S']:
            try:
                session = fastf1.get_session(year, fia_round, sesion_nombre)
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
                    "round_number": db_round, "code": piloto, "compound": comp,
                    "base_pace_s": round(base_pace, 3), "deg_per_lap": round(max(0.02, min(deg, 0.15)), 3),
                    "deg_ms_per_lap": int(deg * 1000), "total_valid_sectors": len(v_c)
                })
        
        if datos_ritmo:
            supabase.table("race_profiles").delete().eq("round_number", db_round).execute()
            supabase.table("race_profiles").insert(datos_ritmo).execute()
            print(f"✅ Ritmos ({len(datos_ritmo)} perfiles) guardados.\n")
    except Exception as e: print(f"❌ Error Ritmos: {e}\n")

# ==========================================
# 🧠 4. AUTO-APRENDIZAJE DE PISTA
# ==========================================
def actualizar_info_pista(year, fia_round, db_round):
    print(f"🌍 Analizando metadata del circuito... (Guardando en ID {db_round})")
    try:
        event = fastf1.get_event(year, fia_round)
        event_name = event['EventName']
        laps = 50 
        
        try:
            print(f"   -> Consultando archivo histórico de {event_name} ({year-1})...")
            hist_session = fastf1.get_session(year - 1, event_name, 'R')
            hist_session.load(telemetry=False, weather=False)
            laps = int(hist_session.results['Laps'].max())
        except:
            print("   -> No hay datos del año pasado. Usando aproximación.")
        
        supabase.table("events").update({"total_laps": laps}).eq("round_number", db_round).execute()
        print(f"✅ Pista actualizada: {laps} Vueltas.\n")
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
        evento_objetivo = carreras_vigentes.iloc[0]
    else:
        evento_objetivo = calendario.iloc[-1]
        
    RONDA_FIA = int(evento_objetivo['RoundNumber'])
    nombre_gp = evento_objetivo['EventName']
    loc_fia = evento_objetivo['Location']
    pais_fia = evento_objetivo['Country']
    
    print(f"📍 GP Objetivo: {nombre_gp} | Ciudad: {loc_fia}")
    
    # ¡LA MAGIA OCURRE AQUÍ!
    RONDA_DB = obtener_ronda_db(loc_fia, pais_fia, RONDA_FIA)
    
    print(f"⚖️ TRADUCCIÓN: FIA dice Ronda {RONDA_FIA} ---> Supabase dice Ronda {RONDA_DB}")
    print(f"--- INICIANDO EXTRACCIÓN TOTAL ---\n")
    
    actualizar_info_pista(AÑO_ACTUAL, RONDA_FIA, RONDA_DB)
    actualizar_qualy(AÑO_ACTUAL, RONDA_FIA, RONDA_DB)
    actualizar_resultados(AÑO_ACTUAL, RONDA_FIA, RONDA_DB)
    actualizar_ritmos(AÑO_ACTUAL, RONDA_FIA, RONDA_DB)
    print("🏁 EXTRACCIÓN FINALIZADA 🏁")
