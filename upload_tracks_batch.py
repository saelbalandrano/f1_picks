import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def upload_tracks_batch():
    tracks = {
        5: r"C:\Users\sael_\.gemini\antigravity\brain\fdd6c20b-1397-458a-8e67-20c0fd530185\bahrain_track_layout_1777952616714.png",
        6: r"C:\Users\sael_\.gemini\antigravity\brain\fdd6c20b-1397-458a-8e67-20c0fd530185\saudi_track_layout_1777952629438.png",
        7: r"C:\Users\sael_\.gemini\antigravity\brain\fdd6c20b-1397-458a-8e67-20c0fd530185\canada_track_layout_1777952642857.png",
        8: r"C:\Users\sael_\.gemini\antigravity\brain\fdd6c20b-1397-458a-8e67-20c0fd530185\monaco_track_layout_1777952660930.png",
        9: r"C:\Users\sael_\.gemini\antigravity\brain\fdd6c20b-1397-458a-8e67-20c0fd530185\spain_track_layout_1777952672003.png",
        10: r"C:\Users\sael_\.gemini\antigravity\brain\fdd6c20b-1397-458a-8e67-20c0fd530185\austria_track_layout_v2_1777952691297.png"
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
    upload_tracks_batch()
