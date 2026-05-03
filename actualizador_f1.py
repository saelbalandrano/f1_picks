import os
import fastf1
import pandas as pd
import numpy as np
from supabase import create_client
from dotenv import load_dotenv

print("🏎️ Encendiendo el motor F1 (MODO PRE-CARRERA MULTI-SESIÓN)...")

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
# ⏱️ 1. CLASIFICACIÓN (QUALY / SPRINT QUALY)
# ==========================================
def actualizar_qualy(year, round_num):
    print(f"⏱️ Procesando Clasificación (Ronda {round_num})...")
    try:
        # Intentamos descargar la Qualy principal
        session = fastf1.get_session(year, round_num, 'Q')
        session.load(telemetry=False, weather=False) 
        resultados = session.results
        
        if resultados.empty:
            print("⚠️ La Qualy principal no se ha corrido. Intentando con Sprint Qualy (SQ)...")
            try:
                session = fastf1.get_session(year, round_num, 'SQ')
                session.load(telemetry=False, weather=False)
                resultados = session.results
            except:
                print("⚠️ Ninguna sesión de clasificación disponible aún.")
                return

        pole_time = resultados.iloc[0]['Q3'] if 'Q3' in resultados.columns and not pd.isnull(resultados.iloc[0]['Q3']) else resultados.iloc[0].get('SQ3', None)
        
        datos_qualy = []
        for index, row in resultados.iterrows():
            code = row['Abbreviation']
            
            # Buscamos el mejor tiempo dependiendo del formato (Q o SQ)
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
# 🏆 2. RESULTADOS OFICIALES (SOLO SI YA PASÓ)
# ==========================================
def actualizar_resultados(year, round_num):
    print(f"🏆 Intentando buscar Resultados de Carrera Oficial (Ronda {round_num})...")
    try:
        session = fastf1.get_session(year, round_num, 'R')
        session.load(telemetry=False, weather=False)
        resultados = session.results
        
        if resultados.empty:
            print("⚠️ La carrera principal aún no tiene resultados. Omitiendo.\n")
            return
            
        datos_oficiales = []
        for index, row in resultados.iterrows():
            code = row['Abbreviation']
            pos = row['Position']
            
            if pd.isnull(pos): pos = 20.0
            datos_oficiales.append({"round_number": round_num, "code": code, "official_position": int(pos)})
            
        supabase.table("official_race_results").delete().eq("round_number", round_num).execute()
        supabase.table("official_race_results").insert(datos_oficiales).execute()
        print(f"✅ Resultados Oficiales guardados.\n")
    except Exception as e: print(f"⚠️ La carrera principal no se ha corrido aún.\n")

# ==========================================
# 📊 3. RITMOS MULTI-SESIÓN (EL CEREBRO REAL)
# ==========================================
def actualizar_ritmos(year, round_num):
    print(f"📊 Recolectando telemetría de TODAS las sesiones previas (Ronda {round_num})...")
    try:
        sesiones_pre_carrera = ['FP1', 'FP2', 'FP3', 'SQ', 'S']
        vueltas_acumuladas = []
        
        for sesion_nombre in sesiones_pre_carrera:
            try:
                session = fastf1.get_session(year, round_num, sesion_nombre)
                session.load(telemetry=False, weather=False)
                laps = session.laps.pick_quicklaps() 
                
                if not laps.empty:
                    print(f"   -> Datos extraídos con éxito de: {sesion_nombre}")
                    vueltas_acumuladas.append(laps)
            except Exception:
                pass # Si la sesión no existe (ej. FP3 en fin de semana Sprint), la salta sin romper nada.
        
        if not vueltas_acumuladas:
            print("⚠️ No se encontró telemetría en ninguna sesión previa. Intenta más tarde.")
            return
            
        # Unimos absolutamente todas las vueltas válidas del fin de semana
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
                    "round_number": round_num,
                    "code": piloto,
                    "compound": comp,
                    "base_pace_s": round(base_pace, 3),
                    "deg_per_lap": round(deg, 3),
                    "deg_ms_per_lap": int(deg * 1000),
                    "total_valid_sectors": len(vueltas_comp)
                })
        
        if datos_ritmo:
            supabase.table("race_profiles").delete().eq("round_number", round_num).execute()
            supabase.table("race_profiles").insert(datos_ritmo).execute()
            print(f"✅ Ritmos consolidados ({len(datos_ritmo)} perfiles) guardados en Supabase.\n")
        else:
            print("⚠️ No se recolectaron ritmos suficientes tras filtrar las vueltas.")
            
    except Exception as e: print(f"❌ Error Ritmos: {e}\n")

# ==========================================
# 🚀 DISPARADOR MAESTRO AUTÓNOMO (VENTANA DE TIEMPO INTELIGENTE)
# ==========================================
if __name__ == "__main__":
    AÑO_ACTUAL = 2026
    
    print("🔎 Analizando el calendario oficial de la FIA...")
    calendario = fastf1.get_event_schedule(AÑO_ACTUAL)
    
    # Quitamos los tests de pretemporada de la lista
    calendario = calendario[calendario['EventFormat'] != 'testing']
    
    # Estandarizamos fechas para evitar que el reloj de GitHub se vuelva loco
    calendario['EventDate'] = pd.to_datetime(calendario['EventDate']).dt.tz_localize(None)
    hoy = pd.Timestamp.now().tz_localize(None)
    
    # LÓGICA MAESTRA: Buscamos la carrera actual o la PRÓXIMA.
    # Consideramos que una carrera "sigue siendo la actual" hasta 2 días después de su fecha.
    carreras_vigentes = calendario[calendario['EventDate'] >= (hoy - pd.Timedelta(days=2))]
    
    if not carreras_vigentes.empty:
        evento_objetivo = carreras_vigentes.iloc[0]
        RONDA_A_ACTUALIZAR = int(evento_objetivo['RoundNumber'])
        nombre_gp = evento_objetivo['EventName']
        print(f"📍 Radar fijado en: {nombre_gp} (Ronda Oficial FIA: {RONDA_A_ACTUALIZAR})")
    else:
        print("⚠️ Temporada terminada. Usando la última carrera del año.")
        RONDA_A_ACTUALIZAR = int(calendario.iloc[-1]['RoundNumber'])
        
    print(f"\n--- INICIANDO EXTRACCIÓN TOTAL PARA RONDA {RONDA_A_ACTUALIZAR} ---\n")
    actualizar_qualy(AÑO_ACTUAL, RONDA_A_ACTUALIZAR)
    actualizar_resultados(AÑO_ACTUAL, RONDA_A_ACTUALIZAR)
    actualizar_ritmos(AÑO_ACTUAL, RONDA_A_ACTUALIZAR)
    print("🏁 EXTRACCIÓN FINALIZADA 🏁")
