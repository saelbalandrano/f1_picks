'use client';

import { useState } from 'react';
import Image from 'next/image';

const DRIVER_DETAILS: Record<string, { name: string, team: string }> = {
  "LEC": { name: "Charles Leclerc", team: "Ferrari" },
  "HAM": { name: "Lewis Hamilton", team: "Ferrari" },
  "NOR": { name: "Lando Norris", team: "McLaren" },
  "PIA": { name: "Oscar Piastri", team: "McLaren" },
  "VER": { name: "Max Verstappen", team: "Red Bull Racing" },
  "HAD": { name: "Isack Hadjar", team: "Red Bull Racing" },
  "RUS": { name: "George Russell", team: "Mercedes" },
  "ANT": { name: "Kimi Antonelli", team: "Mercedes" },
  "ALO": { name: "Fernando Alonso", team: "Aston Martin" },
  "STR": { name: "Lance Stroll", team: "Aston Martin" },
  "ALB": { name: "Alexander Albon", team: "Williams" },
  "SAI": { name: "Carlos Sainz", team: "Williams" },
  "GAS": { name: "Pierre Gasly", team: "Alpine" },
  "COL": { name: "Franco Colapinto", team: "Alpine" },
  "HUL": { name: "Nico Hulkenberg", team: "Audi" },
  "BOR": { name: "Gabriel Bortoleto", team: "Audi" },
  "PER": { name: "Sergio Perez", team: "Cadillac" },
  "BOT": { name: "Valtteri Bottas", team: "Cadillac" },
  "LAW": { name: "Liam Lawson", team: "Racing Bulls" },
  "LIN": { name: "Arvid Lindblad", team: "Racing Bulls" },
  "OCO": { name: "Esteban Ocon", team: "Haas F1 Team" },
  "BEA": { name: "Oliver Bearman", team: "Haas F1 Team" }
};

const TEAM_COLORS: Record<string, string> = {
  "Ferrari": "#E8002D",
  "McLaren": "#FF8000",
  "Red Bull Racing": "#3671C6",
  "Mercedes": "#27F4D2",
  "Aston Martin": "#229971",
  "Williams": "#64C4FF",
  "Alpine": "#0093CC",
  "Audi": "#F50029",
  "Cadillac": "#FFB81C",
  "Racing Bulls": "#6692FF",
  "Haas F1 Team": "#B6BABD",
  "Unknown": "#ffffff"
};

const TEAM_ACRONYMS: Record<string, string> = {
  "Ferrari": "FER",
  "McLaren": "MCL",
  "Red Bull Racing": "RBR",
  "Mercedes": "MER",
  "Aston Martin": "AMR",
  "Williams": "WIL",
  "Alpine": "ALP",
  "Audi": "AUD",
  "Cadillac": "CAD",
  "Racing Bulls": "RBU",
  "Haas F1 Team": "HAA",
  "Unknown": "UNK"
};

export default function DashboardTabs({ predictions }: { predictions: any[] }) {
  const [activeTab, setActiveTab] = useState<'grid' | 'h2h' | 'audit'>('grid');

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
  const STORAGE_URL = supabaseUrl + "/storage/v1/object/public/f1_assets/";

  return (
    <div className="w-full">
      {/* Tab Navigation */}
      <nav className="flex items-center gap-6 mb-8 border-b border-white/10 pb-4 overflow-x-auto whitespace-nowrap">
        <button 
          onClick={() => setActiveTab('grid')}
          className={`font-mono text-xs font-bold tracking-widest uppercase transition-all pb-4 -mb-[17px] ${activeTab === 'grid' ? 'text-[#E8002D] border-b-2 border-[#E8002D] shadow-[0_4px_10px_-2px_rgba(232,0,45,0.5)]' : 'text-zinc-500 hover:text-zinc-300'}`}
        >
          Master Grid
        </button>
        <button 
          onClick={() => setActiveTab('h2h')}
          className={`font-mono text-xs font-bold tracking-widest uppercase transition-all pb-4 -mb-[17px] ${activeTab === 'h2h' ? 'text-[#E8002D] border-b-2 border-[#E8002D] shadow-[0_4px_10px_-2px_rgba(232,0,45,0.5)]' : 'text-zinc-500 hover:text-zinc-300'}`}
        >
          Head-to-Head
        </button>
        <button 
          onClick={() => setActiveTab('audit')}
          className={`font-mono text-xs font-bold tracking-widest uppercase transition-all pb-4 -mb-[17px] ${activeTab === 'audit' ? 'text-[#E8002D] border-b-2 border-[#E8002D] shadow-[0_4px_10px_-2px_rgba(232,0,45,0.5)]' : 'text-zinc-500 hover:text-zinc-300'}`}
        >
          Accuracy Audit
        </button>
      </nav>

      {/* Grid Tab */}
      {activeTab === 'grid' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {predictions.map((p, index) => {
            const details = DRIVER_DETAILS[p.code] || { name: p.code, team: "Unknown" };
            const teamColor = TEAM_COLORS[details.team] || "#00f3ff";
            const teamAcronym = TEAM_ACRONYMS[details.team] || "UNK";
            const photoUrl = STORAGE_URL + "drivers/" + p.code + ".png";
            
            return (
              <div key={p.code} className="bg-zinc-900/60 backdrop-blur-md border border-white/5 hover:border-[#E8002D]/40 hover:shadow-[0_0_20px_rgba(232,0,45,0.15)] transition-all rounded-lg overflow-hidden flex flex-col relative group">
                <div className="absolute top-0 right-0 p-4 z-10">
                  <span className="font-mono text-6xl italic font-black text-[#E8002D]/20 group-hover:text-[#E8002D] transition-colors duration-500 drop-shadow-[0_0_10px_rgba(232,0,45,0.7)]">
                    {(index + 1).toString().padStart(2, '0')}
                  </span>
                </div>
                
                {/* Driver Image Section */}
                <div className="relative h-64 w-full bg-zinc-950 overflow-hidden">
                  {/* Default Silhouette fallback, layered behind */}
                  <div className="absolute inset-0 flex items-end justify-center opacity-30 group-hover:opacity-10 transition-opacity">
                    <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full text-zinc-700 translate-y-8 scale-150">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 4c1.93 0 3.5 1.57 3.5 3.5S13.93 13 12 13s-3.5-1.57-3.5-3.5S10.07 6 12 6zm0 14c-2.03 0-4.43-.82-6.14-2.88a9.947 9.947 0 0112.28 0C16.43 19.18 14.03 20 12 20z" />
                    </svg>
                  </div>
                  
                  <Image 
                    src={photoUrl} 
                    alt={details.name}
                    fill
                    sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                    className="object-cover object-top grayscale group-hover:grayscale-0 transition-all duration-700 scale-105 group-hover:scale-100 z-10"
                    unoptimized
                    onError={(e) => {
                      // Hide image if it fails to load
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-[#121619] via-transparent to-transparent z-20"></div>
                </div>

                {/* Details Section */}
                <div className="p-6 -mt-12 relative z-30">
                  <div className="flex justify-between items-end mb-4">
                    <div>
                      <span className="font-mono text-[10px] text-zinc-400 uppercase tracking-[0.2em]" style={{ color: teamColor }}>{details.team}</span>
                      <h2 className="text-xl font-bold uppercase italic text-white tracking-tight">{details.name}</h2>
                    </div>
                    <div className="w-10 h-10 bg-zinc-800 rounded-full flex items-center justify-center font-black italic text-[10px] border border-white/10 text-zinc-300" style={{ borderColor: teamColor + '40', boxShadow: `0 0 10px ${teamColor}20` }}>
                      {teamAcronym}
                    </div>
                  </div>

                  <div className="space-y-4 pt-4 border-t border-white/5">
                    <div className="flex justify-between items-center">
                      <span className="font-mono text-[10px] text-zinc-400 uppercase">Win Probability</span>
                      <div className="flex items-center gap-3 flex-1 ml-4">
                        <div className="h-1 bg-white/5 flex-1 overflow-hidden rounded-full">
                          <div className="h-full" style={{ width: p.prob_win, backgroundColor: '#E8002D', boxShadow: `0 0 8px #E8002D` }}></div>
                        </div>
                        <span className="font-mono text-sm font-bold w-12 text-right text-white">{p.prob_win}</span>
                      </div>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="font-mono text-[10px] text-zinc-400 uppercase">Podium Chance</span>
                      <div className="flex items-center gap-3 flex-1 ml-4">
                        <div className="h-1 bg-white/5 flex-1 overflow-hidden rounded-full">
                          <div className="h-full" style={{ width: p.prob_podium, backgroundColor: '#00F3FF', boxShadow: `0 0 8px #00F3FF` }}></div>
                        </div>
                        <span className="font-mono text-sm font-bold w-12 text-right text-white">{p.prob_podium}</span>
                      </div>
                    </div>

                    <div className="flex justify-between items-center bg-white/5 p-3 rounded-md">
                      <span className="font-mono text-[10px] text-zinc-400 uppercase">Base Pace Avg.</span>
                      <span className="font-mono text-sm font-bold text-[#E8002D]">
                        {p.ai_base_pace ? parseFloat(p.ai_base_pace).toFixed(3) : "1:31.000"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Head to Head Tab */}
      {activeTab === 'h2h' && (
        <div className="space-y-12">
          {(() => {
            // Group predictions by team
            const teams: Record<string, any[]> = {};
            predictions.forEach(p => {
              const details = DRIVER_DETAILS[p.code] || { name: p.code, team: "Unknown" };
              if (!teams[details.team]) teams[details.team] = [];
              teams[details.team].push({ ...p, details });
            });

            return Object.entries(teams).map(([teamName, drivers], index) => {
              if (drivers.length < 2) return null; // Need 2 drivers for H2H
              
              const d1 = drivers[0];
              const d2 = drivers[1];
              const d1Color = TEAM_COLORS[teamName] || "#00f3ff";
              const d2Color = "#ea0011"; // Accent color for second driver
              
              return (
                <div key={teamName} className="relative grid grid-cols-1 lg:grid-cols-11 gap-4 items-center">
                  
                  {/* Driver 1 */}
                  <div className="lg:col-span-5 group">
                    <div className="bg-zinc-900/40 backdrop-blur-md p-6 rounded-xl border-l-4 transition-all duration-500 hover:bg-white/5 border-t border-r border-b border-white/5" style={{ borderLeftColor: d1Color }}>
                      <div className="flex justify-between items-start mb-6">
                        <div className="relative w-32 h-32 rounded-lg overflow-hidden border border-white/10 grayscale group-hover:grayscale-0 transition-all bg-zinc-950">
                           <div className="absolute inset-0 flex items-end justify-center opacity-30 group-hover:opacity-10 transition-opacity">
                            <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full text-zinc-700 translate-y-4 scale-125">
                              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 4c1.93 0 3.5 1.57 3.5 3.5S13.93 13 12 13s-3.5-1.57-3.5-3.5S10.07 6 12 6zm0 14c-2.03 0-4.43-.82-6.14-2.88a9.947 9.947 0 0112.28 0C16.43 19.18 14.03 20 12 20z" />
                            </svg>
                          </div>
                          <Image 
                            src={STORAGE_URL + "drivers/" + d1.code + ".png"}
                            alt={d1.details.name}
                            fill
                            className="object-cover object-top z-10"
                            unoptimized
                            onError={(e) => { e.currentTarget.style.display = 'none'; }}
                          />
                          <div className="absolute bottom-0 left-0 text-white font-mono px-2 py-1 text-xs z-20" style={{ backgroundColor: d1Color }}>
                            {d1.code}
                          </div>
                        </div>
                        <div className="text-right">
                          <h2 className="text-3xl font-bold uppercase italic tracking-tighter text-white">{d1.details.name.split(' ').pop()}</h2>
                          <p className="font-mono text-[10px] text-zinc-400 uppercase tracking-widest">{teamName}</p>
                          <div className="mt-4 flex flex-col items-end">
                            <span className="font-mono text-[10px] text-zinc-500 mb-1">PREDICTED POS</span>
                            <span className="text-4xl font-black" style={{ color: d1Color, textShadow: `0 0 15px ${d1Color}80` }}>P{Math.round(d1.ai_predicted_pos)}</span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="space-y-2">
                        <div className="flex justify-between items-end font-mono text-[10px] text-zinc-400 mb-2">
                          <span>BASE PACE</span>
                          <span style={{ color: d1Color }}>{d1.ai_base_pace ? parseFloat(d1.ai_base_pace).toFixed(3) : "1:31.000"}</span>
                        </div>
                        <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                           <div className="h-full" style={{ width: '85%', backgroundColor: d1Color }}></div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* VS Centerpiece */}
                  <div className="lg:col-span-1 flex flex-col items-center justify-center z-10 py-8 lg:py-0">
                    <div className="relative w-20 h-20 flex items-center justify-center">
                      <div className="absolute inset-0 bg-[#E8002D]/20 rounded-full blur-2xl animate-pulse"></div>
                      <div className="relative w-16 h-16 rounded-full flex items-center justify-center border border-[#E8002D]/40 bg-zinc-900/80 backdrop-blur-md">
                        <span className="text-xl italic text-[#E8002D] font-black">VS</span>
                      </div>
                    </div>
                  </div>

                  {/* Driver 2 */}
                  <div className="lg:col-span-5 group">
                     <div className="bg-zinc-900/40 backdrop-blur-md p-6 rounded-xl border-r-4 transition-all duration-500 hover:bg-white/5 border-t border-l border-b border-white/5" style={{ borderRightColor: d2Color }}>
                      <div className="flex justify-between items-start mb-6">
                        <div className="order-2 relative w-32 h-32 rounded-lg overflow-hidden border border-white/10 grayscale group-hover:grayscale-0 transition-all bg-zinc-950">
                           <div className="absolute inset-0 flex items-end justify-center opacity-30 group-hover:opacity-10 transition-opacity">
                            <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full text-zinc-700 translate-y-4 scale-125">
                              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 4c1.93 0 3.5 1.57 3.5 3.5S13.93 13 12 13s-3.5-1.57-3.5-3.5S10.07 6 12 6zm0 14c-2.03 0-4.43-.82-6.14-2.88a9.947 9.947 0 0112.28 0C16.43 19.18 14.03 20 12 20z" />
                            </svg>
                          </div>
                          <Image 
                            src={STORAGE_URL + "drivers/" + d2.code + ".png"}
                            alt={d2.details.name}
                            fill
                            className="object-cover object-top z-10"
                            unoptimized
                            onError={(e) => { e.currentTarget.style.display = 'none'; }}
                          />
                          <div className="absolute bottom-0 right-0 text-white font-mono px-2 py-1 text-xs z-20" style={{ backgroundColor: d2Color }}>
                            {d2.code}
                          </div>
                        </div>
                        <div className="order-1 text-left">
                          <h2 className="text-3xl font-bold uppercase italic tracking-tighter text-white">{d2.details.name.split(' ').pop()}</h2>
                          <p className="font-mono text-[10px] text-zinc-400 uppercase tracking-widest">{teamName}</p>
                          <div className="mt-4 flex flex-col items-start">
                            <span className="font-mono text-[10px] text-zinc-500 mb-1">PREDICTED POS</span>
                            <span className="text-4xl font-black" style={{ color: d2Color, textShadow: `0 0 15px ${d2Color}80` }}>P{Math.round(d2.ai_predicted_pos)}</span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="space-y-2">
                        <div className="flex justify-between items-end font-mono text-[10px] text-zinc-400 mb-2">
                           <span style={{ color: d2Color }}>{d2.ai_base_pace ? parseFloat(d2.ai_base_pace).toFixed(3) : "1:31.250"}</span>
                          <span>BASE PACE</span>
                        </div>
                        <div className="h-1 bg-white/5 rounded-full overflow-hidden flex justify-end">
                           <div className="h-full" style={{ width: '80%', backgroundColor: d2Color }}></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )
            });
          })()}
        </div>
      )}

      {/* Accuracy Audit Tab */}
      {activeTab === 'audit' && (
        <div className="min-h-[400px] flex items-center justify-center border border-white/5 rounded-xl bg-zinc-900/30 backdrop-blur-sm relative overflow-hidden">
           <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(232,0,45,0.05)_0%,transparent_50%)]"></div>
           <div className="text-center z-10">
             <div className="w-16 h-16 border-t-2 border-r-2 border-[#E8002D] rounded-full animate-spin mx-auto mb-6"></div>
             <h2 className="text-2xl font-bold text-white mb-2 uppercase tracking-widest">Model Calibration</h2>
             <p className="text-zinc-400 font-mono text-sm max-w-md mx-auto">
               Historical accuracy audit module is currently processing the latest race deltas.
               Come back after the race weekend to view AI performance metrics.
             </p>
           </div>
        </div>
      )}

    </div>
  );
}
