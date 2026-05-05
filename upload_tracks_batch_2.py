import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def upload_tracks_batch_2():
    tracks = {
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
    upload_tracks_batch_2()
