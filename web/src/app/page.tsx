import { createClient } from '@supabase/supabase-js'
import Image from 'next/image'

export const revalidate = 0;

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

// Create client conditionally so the Vercel build doesn't crash if vars are forgotten
const supabase = supabaseUrl && supabaseKey ? createClient(supabaseUrl, supabaseKey) : null;

const TEAM_COLORS: Record<string, string> = {
  "RBR": "#3671C6", "FER": "#E8002D", "MCL": "#FF8000",
  "MER": "#27F4D2", "AMR": "#229971", "ALP": "#0093CC",
  "WIL": "#64C4FF", "RBU": "#6692FF", "HAA": "#B6BABD",
  "SAU": "#52E252", "VER": "#3671C6", "PER": "#3671C6",
  "LEC": "#E8002D", "SAI": "#E8002D", "NOR": "#FF8000",
  "PIA": "#FF8000", "HAM": "#27F4D2", "RUS": "#27F4D2",
  "ALO": "#229971", "STR": "#229971", "GAS": "#0093CC",
  "OCO": "#0093CC", "ALB": "#64C4FF", "SAR": "#64C4FF",
  "TSU": "#6692FF", "RIC": "#6692FF", "MAG": "#B6BABD",
  "HUL": "#B6BABD", "BOT": "#52E252", "ZHO": "#52E252"
};

export default async function Home() {
  if (!supabase) {
    return (
      <div className="min-h-screen bg-[#0b0f12] text-white flex items-center justify-center font-sans">
        <div className="text-center p-8 bg-white/5 border border-red-500 rounded-xl max-w-xl">
          <h1 className="text-3xl font-bold text-red-500 mb-4">Config Error</h1>
          <p className="text-zinc-300">
            Missing Supabase environment variables in Vercel. Go to Settings &gt; Environment Variables and add:
          </p>
          <ul className="mt-4 text-left font-mono text-sm text-yellow-400 inline-block">
            <li>NEXT_PUBLIC_SUPABASE_URL</li>
            <li>NEXT_PUBLIC_SUPABASE_ANON_KEY</li>
          </ul>
        </div>
      </div>
    )
  }

  const { data: predictions, error } = await supabase
    .from('ai_predictions')
    .select('*')
    .order('ai_predicted_pos', { ascending: true })

  if (error || !predictions || predictions.length === 0) {
    return (
      <div className="min-h-screen bg-[#0b0f12] text-white flex items-center justify-center font-sans">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-red-500 mb-4">No data available</h1>
          <p className="text-zinc-400">Run the F1 AI Prediction Engine first.</p>
        </div>
      </div>
    )
  }

  const raceName = predictions[0]?.race_name || "Unknown Race";
  const STORAGE_URL = supabaseUrl + "/storage/v1/object/public/f1_assets/";

  return (
    <div className="min-h-screen bg-[#0b0f12] bg-[radial-gradient(circle_at_50%_0%,#2a0000_0%,#0b0f12_40%)] text-white font-sans p-6">
      
      {/* Header section */}
      <header className="max-w-7xl mx-auto py-8">
        <div className="flex items-center gap-4">
          <div className="bg-red-600 px-3 py-1 rounded text-xs font-bold tracking-widest uppercase shadow-[0_0_15px_rgba(255,0,0,0.5)]">
            AI MONTE CARLO PROJECTION
          </div>
        </div>
        <h1 className="text-5xl font-black mt-4 uppercase tracking-tighter">{raceName}</h1>
        <p className="text-zinc-400 mt-2 font-mono uppercase tracking-widest text-sm border-l-2 border-red-500 pl-3">
          10,000 Simulations / Dynamic Degradation
        </p>
      </header>

      {/* Grid container */}
      <main className="max-w-7xl mx-auto mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {predictions.map((p, index) => {
          const color = TEAM_COLORS[p.code] || "#ffffff";
          const logoUrl = STORAGE_URL + "logos/" + p.team.replace(/\s+/g, '_') + ".png";
          const photoUrl = STORAGE_URL + "drivers/" + p.code + ".png";
          
          return (
            <div 
              key={p.code}
              className="relative rounded-xl overflow-hidden bg-white/5 backdrop-blur-xl border border-red-500/20 group hover:-translate-y-1 hover:shadow-[0_0_30px_rgba(255,0,0,0.3)] hover:border-red-500/50 transition-all duration-300 min-h-[220px] flex"
            >
              {/* Left Accent Bar */}
              <div className="absolute left-0 top-0 bottom-0 w-1 z-10" style={{ backgroundColor: color }}></div>
              
              {/* Driver Section */}
              <div className="flex-1 p-4 relative z-10 flex flex-col justify-start overflow-hidden">
                <div className="flex items-center gap-3">
                  <div className="text-2xl font-black text-red-500 bg-red-500/10 px-2 py-0.5 rounded border border-red-500/30 shadow-[0_0_10px_rgba(255,0,0,0.2)]">
                    P{index + 1}
                  </div>
                  <div>
                    <h2 className="text-xl font-bold uppercase leading-none tracking-tight">
                      {p.driver_name} <span className="text-xs text-zinc-500 font-mono ml-1">{p.code}</span>
                    </h2>
                    <p className="text-[10px] text-zinc-400 uppercase tracking-widest mt-1">{p.team}</p>
                  </div>
                </div>
                
                {/* Driver Photo */}
                <div className="absolute -bottom-4 -right-4 h-[180px] w-[180px] z-0 opacity-90 group-hover:scale-105 transition-transform duration-500 drop-shadow-2xl">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={photoUrl} alt={p.code} className="object-contain h-full w-full" 
                    onError={(e) => { e.currentTarget.style.display = 'none'; }} 
                  />
                </div>
              </div>

              {/* Telemetry Stats Section */}
              <div className="w-[220px] bg-black/40 p-4 pt-10 border-l border-white/5 z-10 flex flex-col justify-end">
                <h3 className="text-[9px] text-red-400 font-bold tracking-[0.2em] uppercase mb-2">Market Probabilities</h3>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between items-center border-b border-white/5 pb-1">
                    <span className="font-semibold text-zinc-300 uppercase">Win (P1)</span>
                    <span className="font-mono font-bold text-green-400 drop-shadow-[0_0_5px_rgba(0,255,0,0.3)]">{p.prob_win}</span>
                  </div>
                  <div className="flex justify-between items-center border-b border-white/5 pb-1">
                    <span className="font-semibold text-zinc-300 uppercase">Podium (Top 3)</span>
                    <span className="font-mono font-bold text-green-400">{p.prob_podium}</span>
                  </div>
                  <div className="flex justify-between items-center border-b border-white/5 pb-1">
                    <span className="font-semibold text-zinc-300 uppercase">Top 6 Finish</span>
                    <span className="font-mono font-bold text-green-400">{p.prob_top6}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-zinc-300 uppercase">Points (Top 10)</span>
                    <span className="font-mono font-bold text-green-400">{p.prob_top10}</span>
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </main>
    </div>
  )
}
