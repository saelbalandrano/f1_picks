import pandas as pd
import numpy as np

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

def run_ai_prediction_engine(target_round, supabase, calendar):
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

    driver_codes = df_target['code'].unique()
    talent_bonuses = []
    
    past_rounds = [r for r in calendar.keys() if r < target_round]

    # Calculate talent bonuses from past rounds
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
            grid_ronda = df_qualy[df_qualy['round_number'] == ronda]
            if grid_ronda.empty: continue
            grid_ronda = grid_ronda.sort_values('delta_to_pole_s').reset_index(drop=True)
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

    # EARLY PREDICTION FALLBACK: Si no hay Qualy, usamos Driver Momentum para armar una parrilla teórica
    grid_target_raw = df_qualy[df_qualy['round_number'] == target_round]
    if not grid_target_raw.empty:
        grid_target = grid_target_raw.sort_values('delta_to_pole_s').reset_index(drop=True)
        grid_target['Grid_Slot'] = grid_target.index + 1
    else:
        # Fallback pre-qualy (viernes)
        res_momentum = supabase.table("driver_momentum").select("drivers(code), current_form_score").execute()
        momentum_data = [{"code": r['drivers']['code'], "score": r['current_form_score']} for r in res_momentum.data]
        grid_target = pd.DataFrame(momentum_data)
        if not grid_target.empty:
            grid_target = grid_target.sort_values('score', ascending=False).reset_index(drop=True)
            grid_target['Grid_Slot'] = grid_target.index + 1
        else:
            return pd.DataFrame() # Sin datos para simular

    df_final_sim = pd.merge(grid_target[['Grid_Slot', 'code']], driver_race_stats, on='code', how='inner')
    df_final_sim = pd.merge(df_final_sim, df_talent, on='code', how='left').fillna(0)

    if target_round not in calendar:
        return pd.DataFrame()
        
    laps = calendar[target_round]['laps']
    diff_track = calendar[target_round]['diff']
    num_simulations = 10000
    num_drivers = len(df_final_sim)

    if num_drivers == 0:
        return pd.DataFrame()

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
    
    # Cálculo de Probabilidades de Mercado
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
