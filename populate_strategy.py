import os
import random
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def populate_strategy():
    drivers = ["LEC", "HAM", "NOR", "PIA", "VER", "HAD", "RUS", "ANT", "ALO", "STR", "ALB", "SAI", "GAS", "COL", "HUL", "BOR", "PER", "BOT", "LAW", "LIN", "OCO", "BEA"]
    rounds = list(range(1, 25)) # Full 24 rounds
    
    strategies = ["S-M-H", "M-H", "S-H", "S-M-M", "M-H-H"]
    risk_levels = ["LOW", "MED", "HIGH"]
    
    for r in rounds:
        supabase.table("strategy_simulations").delete().eq("round_number", r).execute()
        
        data_to_insert = []
        for d in drivers:
            pit_start = random.randint(12, 18)
            pit_end = pit_start + random.randint(3, 5)
            tire_life = random.randint(70, 95)
            
            data_to_insert.append({
                "round_number": r,
                "code": d,
                "pit_window": f"Laps {pit_start}-{pit_end}",
                "tire_life": f"S: {tire_life}%",
                "optimal_strategy": random.choice(strategies),
                "risk_level": random.choice(risk_levels)
            })
        
        supabase.table("strategy_simulations").insert(data_to_insert).execute()
    print("Full season strategy data populated.")

def upload_tracks():
    # Mapping of all generated tracks so far
    tracks = {
        1: r"C:\Users\sael_\.gemini\antigravity\brain\fdd6c20b-1397-458a-8e67-20c0fd530185\australia_track_layout_1777951645096.png",
        2: r"C:\Users\sael_\.gemini\antigravity\brain\fdd6c20b-1397-458a-8e67-20c0fd530185\china_track_layout_1777951663899.png",
        3: r"C:\Users\sael_\.gemini\antigravity\brain\fdd6c20b-1397-458a-8e67-20c0fd530185\japan_track_layout_1777951682253.png",
        4: r"C:\Users\sael_\.gemini\antigravity\brain\fdd6c20b-1397-458a-8e67-20c0fd530185\miami_track_layout_1777951615581.png",
        5: r"C:\Users\sael_\.gemini\antigravity\brain\fdd6c20b-1397-458a-8e67-20c0fd530185\bahrain_track_layout_1777952616714.png",
        6: r"C:\Users\sael_\.gemini\antigravity\brain\fdd6c20b-1397-458a-8e67-20c0fd530185\saudi_track_layout_1777952629438.png",
        7: r"C:\Users\sael_\.gemini\antigravity\brain\fdd6c20b-1397-458a-8e67-20c0fd530185\canada_track_layout_1777952642857.png",
        8: r"C:\Users\sael_\.gemini\antigravity\brain\fdd6c20b-1397-458a-8e67-20c0fd530185\monaco_track_layout_1777952660930.png",
        9: r"C:\Users\sael_\.gemini\antigravity\brain\fdd6c20b-1397-458a-8e67-20c0fd530185\spain_track_layout_1777952672003.png",
        10: r"C:\Users\sael_\.gemini\antigravity\brain\fdd6c20b-1397-458a-8e67-20c0fd530185\austria_track_layout_v2_1777952691297.png",
        11: r"C:\Users\sael_\.gemini\antigravity\brain\fdd6c20b-1397-458a-8e67-20c0fd530185\uk_track_layout_1777952730434.png",
        12: r"C:\Users\sael_\.gemini\antigravity\brain\fdd6c20b-1397-458a-8e67-20c0fd530185\belgium_track_layout_v2_1777952744066.png",
        13: r"C:\Users\sael_\.gemini\antigravity\brain\fdd6c20b-1397-458a-8e67-20c0fd530185\hungary_track_layout_v2_1777952755976.png",
        14: r"C:\Users\sael_\.gemini\antigravity\brain\fdd6c20b-1397-458a-8e67-20c0fd530185\netherlands_track_layout_v2_1777952772302.png",
        15: r"C:\Users\sael_\.gemini\antigravity\brain\fdd6c20b-1397-458a-8e67-20c0fd530185\italy_track_layout_v2_1777952787946.png",
        16: r"C:\Users\sael_\.gemini\antigravity\brain\fdd6c20b-1397-458a-8e67-20c0fd530185\madrid_track_layout_v2_1777952802194.png",
        17: r"C:\Users\sael_\.gemini\antigravity\brain\fdd6c20b-1397-458a-8e67-20c0fd530185\azerbaijan_track_layout_v2_1777952820070.png"
    }
    
    for r, path in tracks.items():
        if os.path.exists(path):
            with open(path, 'rb') as f:
                supabase.storage.from_("f1_assets").upload(
                    path=f"tracks/track_{r}.png",
                    file=f,
                    file_options={"content-type": "image/png", "x-upsert": "true"}
                )
            print(f"Track map for Round {r} uploaded.")

if __name__ == "__main__":
    populate_strategy()
    upload_tracks()
