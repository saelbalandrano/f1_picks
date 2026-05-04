def format_pace(seconds):
    import pandas as pd
    if pd.isna(seconds) or seconds == 0: return "--:--"
    minutos = int(seconds // 60)
    segs = seconds % 60
    return f"{minutos}:{segs:06.3f}"

def render_grid_card(driver_row, index_pos, color, logo_url, photo_url, race_name):
    equipo = driver_row['Escudería']
    codigo = driver_row['Código']
    piloto_nombre = driver_row['Piloto']
    prob_win = driver_row['prob_win']
    prob_podium = driver_row['prob_podium']
    prob_top6 = driver_row['prob_top6']
    prob_top10 = driver_row['prob_top10']

    return f"""
<div class="grid-container" style="--team-color: {color};">
<img src="{logo_url}" class="logo-full-color">
<div class="driver-section">
<div class="pos-name-block">
<div class="pos-number">P{int(index_pos + 1)}</div>
<div>
<p class="driver-name">{piloto_nombre} <span style="font-size:12px; color:#666;">{codigo}</span></p>
<p class="team-name">{equipo}</p>
</div>
</div>

<img src="{photo_url}" class="driver-photo">
</div>
<div class="telemetry-section">
<div>
<p class="telemetry-title">MARKET PROBABILITIES: {race_name}</p>
<table class="data-table">
<tr><td class="label">Win (P1)</td><td class="value">{prob_win}</td></tr>
<tr><td class="label">Podium (Top 3)</td><td class="value">{prob_podium}</td></tr>
<tr><td class="label">Top 6 Finish</td><td class="value">{prob_top6}</td></tr>
<tr><td class="label">Points (Top 10)</td><td class="value">{prob_top10}</td></tr>
</table>
</div>
</div>
</div>
"""

def render_h2h_match(p_left, p_right, equipo, color_equipo, predicted_winner_code, logo_center, photo_left, photo_right):
    color_equipo_shadow = color_equipo + "40"
    left_highlight_class = "h2h-winner-unit" if p_left['Código'] == predicted_winner_code else ""
    right_highlight_class = "h2h-winner-unit" if p_right['Código'] == predicted_winner_code else ""
    
    pace_left = format_pace(p_left['ai_base_pace'])
    pace_right = format_pace(p_right['ai_base_pace'])

    return f"""
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
<p class="h2h-base-pace-text">Base Pace: <span class="h2h-base-pace-formatted">{pace_left}</span></p>
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
<p class="h2h-base-pace-text">Base Pace: <span class="h2h-base-pace-formatted">{pace_right}</span></p>
</div>
</div>
</div>
"""
