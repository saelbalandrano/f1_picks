"use client";

import { useState } from 'react';

const TEAM_COLORS: Record<string, string> = {
  "VER": "#3671C6", "PER": "#3671C6",
  "LEC": "#E8002D", "SAI": "#E8002D",
  "NOR": "#FF8000", "PIA": "#FF8000",
  "HAM": "#6CD3BF", "RUS": "#6CD3BF",
  "ALO": "#229971", "STR": "#229971",
  "GAS": "#0093CC", "OCO": "#0093CC",
  "ALB": "#37BEDD", "COL": "#37BEDD",
  "TSU": "#6692FF", "LAW": "#6692FF",
  "BOT": "#52E252", "ZHO": "#52E252",
  "HUL": "#B6BABD", "MAG": "#B6BABD"
};

const STORAGE_URL = "https://pfbhpvddzodwtlykbvma.supabase.co/storage/v1/object/public/f1_assets/";

export default function DashboardTabs({ predictions }: { predictions: any[] }) {
  const [activeTab, setActiveTab] = useState('grid');
  
  // Group drivers by team for H2H
  const teams: Record<string, any[]> = {};
  predictions.forEach(p => {
    const teamName = p.team || "Unknown";
    if (!teams[teamName]) teams[teamName] = [];
    teams[teamName].push(p);
  });

  return (
    <div className="w-full">
      {/* Navigation Tabs */}
      <div className="flex border-b border-white/10 mb-8">
        <button 
          onClick={() => setActiveTab('grid')}
          className={`py-3 px-6 font-mono text-sm tracking-widest uppercase transition-all duration-300 relative ${activeTab === 'grid' ? 'text-[#00F3FF]' : 'text-zinc-500 hover:text-zinc-300'}`}
        >
          Master Grid Power Ranking
          {activeTab === 'grid' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#00F3FF] shadow-[0_0_10px_rgba(0,243,255,0.8)]"></div>
          )}
        </button>
        <button 
          onClick={() => setActiveTab('h2h')}
          className={`py-3 px-6 font-mono text-sm tracking-widest uppercase transition-all duration-300 relative ${activeTab === 'h2h' ? 'text-[#00F3FF]' : 'text-zinc-500 hover:text-zinc-300'}`}
        >
          Head-to-Head Race Predictor
          {activeTab === 'h2h' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#00F3FF] shadow-[0_0_10px_rgba(0,243,255,0.8)]"></div>
          )}
        </button>
      </div>

      {activeTab === 'grid' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {predictions.map((p, index) => {
            const color = TEAM_COLORS[p.code] || "#ffffff";
            const teamName = p.team || "Unknown";
            const driverName = p.driver_name || p.code || "Unknown";
            // Fallback strategy for images
            const logoUrl = STORAGE_URL + "logos/" + teamName.replace(/\s+/g, '_') + ".png";
            const photoUrl = STORAGE_URL + "drivers/" + p.code + ".png";
            
            return (
              <div 
                key={p.code}
                className="relative rounded-xl overflow-hidden bg-[#181c20]/80 backdrop-blur-xl border border-white/5 group hover:-translate-y-1 hover:shadow-[0_0_30px_rgba(0,243,255,0.15)] hover:border-[#00f3ff]/30 transition-all duration-300 min-h-[220px] flex"
              >
                {/* Left Accent Bar */}
                <div className="absolute left-0 top-0 bottom-0 w-1 z-10" style={{ backgroundColor: color }}></div>
                
                {/* Driver Section */}
                <div className="flex-1 p-5 relative z-10 flex flex-col justify-between overflow-hidden w-2/3">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="text-xl font-black text-[#00f3ff] bg-[#00f3ff]/10 px-2 py-0.5 rounded border border-[#00f3ff]/30 shadow-[0_0_10px_rgba(0,243,255,0.2)]">
                      P{index + 1}
                    </div>
                    <div>
                      <h2 className="text-xl font-bold uppercase leading-none tracking-tight text-[#e0e2e8]">
                        {driverName} <span className="text-xs text-zinc-500 font-mono ml-1">{p.code}</span>
                      </h2>
                      <p className="text-[10px] text-zinc-400 uppercase tracking-widest mt-1">{teamName}</p>
                    </div>
                  </div>
                  
                  {/* Telemetry Section */}
                  <div className="bg-black/40 rounded-lg p-3 border border-white/5 w-full">
                    <p className="text-[10px] text-[#00f3ff] uppercase tracking-widest mb-2 font-mono font-bold">Market Probabilities</p>
                    <div className="space-y-1.5 text-xs w-full">
                      <div className="flex justify-between items-center border-b border-white/5 pb-1">
                        <span className="font-semibold text-zinc-300 uppercase">Win (P1)</span>
                        <span className="font-mono font-bold text-white">{p.prob_win}</span>
                      </div>
                      <div className="flex justify-between items-center border-b border-white/5 pb-1">
                        <span className="font-semibold text-zinc-300 uppercase">Podium (Top 3)</span>
                        <span className="font-mono font-bold text-white">{p.prob_podium}</span>
                      </div>
                      <div className="flex justify-between items-center border-b border-white/5 pb-1">
                        <span className="font-semibold text-zinc-300 uppercase">Top 6 Finish</span>
                        <span className="font-mono font-bold text-white">{p.prob_top6}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="font-semibold text-zinc-300 uppercase">Points (Top 10)</span>
                        <span className="font-mono font-bold text-white">{p.prob_top10}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Driver Photo & Logo Background */}
                <div className="w-1/3 relative flex items-end justify-end p-2 z-0">
                    <img 
                      src={logoUrl} 
                      alt={teamName} 
                      className="absolute inset-0 m-auto opacity-10 object-contain w-32 h-32 blur-[2px]" 
                      onError={(e) => { e.currentTarget.style.display = 'none'; }} 
                    />
                    <img 
                      src={photoUrl} 
                      alt={p.code} 
                      className="relative z-10 object-contain h-[160px] max-w-none transform translate-x-2 translate-y-4 drop-shadow-2xl opacity-90 group-hover:scale-105 transition-transform duration-500" 
                      onError={(e) => { 
                        // Fallback generic helmet icon if image fails to load
                        e.currentTarget.src = "https://upload.wikimedia.org/wikipedia/commons/4/4e/Racing_Helmet_icon.svg"; 
                        e.currentTarget.className = "relative z-10 object-contain h-[120px] opacity-20 transform translate-x-0 translate-y-2";
                      }} 
                    />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {activeTab === 'h2h' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {Object.entries(teams).map(([teamName, drivers]) => {
            if (drivers.length < 2) return null; // Need 2 drivers for H2H
            
            // Determine winner based on predicted position
            const d1 = drivers[0];
            const d2 = drivers[1];
            const d1Wins = d1.ai_predicted_pos < d2.ai_predicted_pos;
            const color = TEAM_COLORS[d1.code] || "#ffffff";
            const logoUrl = STORAGE_URL + "logos/" + teamName.replace(/\s+/g, '_') + ".png";

            return (
              <div key={teamName} className="relative w-full rounded-2xl bg-[#181c20]/80 backdrop-blur-xl border border-white/5 overflow-hidden shadow-2xl flex flex-col p-1">
                {/* Team Header */}
                <div className="w-full text-center py-2 relative z-10 flex flex-col items-center border-b border-white/5 mb-2">
                  <h3 className="font-mono text-sm tracking-[0.2em] uppercase text-zinc-400">{teamName}</h3>
                </div>

                <div className="flex w-full relative h-full">
                  {/* Left Driver */}
                  <div className={`flex-1 relative p-4 flex flex-col items-center border-r border-white/5 transition-all duration-300 ${d1Wins ? 'bg-gradient-to-b from-[#00f3ff]/5 to-transparent' : 'opacity-60 grayscale-[50%]'}`}>
                    {d1Wins && <div className="absolute top-2 right-2 text-xs font-bold bg-[#00f3ff] text-black px-2 py-0.5 rounded shadow-[0_0_10px_rgba(0,243,255,0.5)]">WINNER</div>}
                    <div className="w-24 h-24 relative mb-4 rounded-full overflow-hidden bg-white/5 border-2 border-white/10 flex items-center justify-center">
                        <img 
                          src={STORAGE_URL + "drivers/" + d1.code + ".png"} 
                          alt={d1.code} 
                          className="object-cover h-full"
                          onError={(e) => { 
                            e.currentTarget.src = "https://upload.wikimedia.org/wikipedia/commons/4/4e/Racing_Helmet_icon.svg"; 
                            e.currentTarget.className = "object-contain h-12 opacity-30";
                          }} 
                        />
                    </div>
                    <h4 className="text-xl font-bold uppercase text-white mb-1">{d1.driver_name || d1.code}</h4>
                    <span className="text-sm font-mono text-zinc-500 mb-4">{d1.code}</span>
                    
                    <div className="w-full bg-black/40 rounded p-3 text-center border border-white/5">
                      <p className="text-[10px] text-zinc-500 uppercase tracking-widest mb-1">Predicted Pos</p>
                      <p className="text-3xl font-black text-white">P{Math.round(d1.ai_predicted_pos)}</p>
                    </div>
                  </div>

                  {/* VS Divider / Logo */}
                  <div className="absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 z-20 flex flex-col items-center justify-center bg-[#101417] p-2 rounded-full border border-white/10 shadow-2xl">
                     <span className="font-mono font-bold text-[#00f3ff] text-xs">VS</span>
                  </div>

                  {/* Right Driver */}
                  <div className={`flex-1 relative p-4 flex flex-col items-center transition-all duration-300 ${!d1Wins ? 'bg-gradient-to-b from-[#00f3ff]/5 to-transparent' : 'opacity-60 grayscale-[50%]'}`}>
                    {!d1Wins && <div className="absolute top-2 left-2 text-xs font-bold bg-[#00f3ff] text-black px-2 py-0.5 rounded shadow-[0_0_10px_rgba(0,243,255,0.5)]">WINNER</div>}
                    <div className="w-24 h-24 relative mb-4 rounded-full overflow-hidden bg-white/5 border-2 border-white/10 flex items-center justify-center">
                        <img 
                          src={STORAGE_URL + "drivers/" + d2.code + ".png"} 
                          alt={d2.code} 
                          className="object-cover h-full"
                          onError={(e) => { 
                            e.currentTarget.src = "https://upload.wikimedia.org/wikipedia/commons/4/4e/Racing_Helmet_icon.svg"; 
                            e.currentTarget.className = "object-contain h-12 opacity-30";
                          }} 
                        />
                    </div>
                    <h4 className="text-xl font-bold uppercase text-white mb-1">{d2.driver_name || d2.code}</h4>
                    <span className="text-sm font-mono text-zinc-500 mb-4">{d2.code}</span>
                    
                    <div className="w-full bg-black/40 rounded p-3 text-center border border-white/5">
                      <p className="text-[10px] text-zinc-500 uppercase tracking-widest mb-1">Predicted Pos</p>
                      <p className="text-3xl font-black text-white">P{Math.round(d2.ai_predicted_pos)}</p>
                    </div>
                  </div>
                </div>
                
                {/* Team Accent Bar Bottom */}
                <div className="w-full h-1 mt-auto" style={{ backgroundColor: color }}></div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
