'use client';

import { useState, useMemo } from 'react';
import Image from 'next/image';

const getDriverPhoto = (code: string) => {
  const mapping: Record<string, string> = {
    "LEC": "charles_leclerc.png",
    "HAM": "lewis_hamilton.webp",
    "NOR": "lando_norris.png",
    "PIA": "oscar_piastri.png",
    "VER": "max_verstappen.png",
    "HAD": "isack_hadjar.png",
    "RUS": "george_russell.png",
    "ANT": "kimi_antonelli.png",
    "ALO": "fernando_alonso.png",
    "STR": "lance_stroll.png",
    "ALB": "alexander_albon.png",
    "SAI": "carlos_sainz.png",
    "GAS": "pierre_gasly.png",
    "COL": "Franco_Colapinto.webp",
    "HUL": "nico_hulkenberg.png",
    "BOR": "gabriel_bortoleto.png",
    "PER": "sergio_perez.png",
    "BOT": "valtteri_bottas.png",
    "LAW": "liam_lawson.png",
    "LIN": "arvid_lindblad.png",
    "OCO": "esteban_ocon.png",
    "BEA": "oliver_bearman.png"
  };
  return mapping[code] || (code.toLowerCase() + ".png");
};

const getTeamLogo = (team: string) => {
  const mapping: Record<string, string> = {
    "Ferrari": "Ferrari.webp",
    "Red Bull Racing": "Red_Bull_Racing.webp",
    "Mercedes": "Mercedes.svg",
    "McLaren": "McLaren.png",
    "Aston Martin": "Aston_Martin.svg",
    "Alpine": "Alpine.png",
    "Williams": "Williams.png",
    "Racing Bulls": "Racing_Bulls.png",
    "Haas F1 Team": "Haas_F1_Team.png",
    "Audi": "Audi.svg",
    "Cadillac": "Cadillac.png"
  };
  return mapping[team] || "Ferrari.webp";
};

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
  "PER": { name: "Sergio Perez", team: "Racing Bulls" },
  "BOT": { name: "Valtteri Bottas", team: "Racing Bulls" },
  "LAW": { name: "Liam Lawson", team: "Haas F1 Team" },
  "LIN": { name: "Arvid Lindblad", team: "Haas F1 Team" },
  "OCO": { name: "Esteban Ocon", team: "Cadillac" },
  "BEA": { name: "Oliver Bearman", team: "Cadillac" }
};

const TEAM_COLORS: Record<string, string> = {
  "Ferrari": "#E8002D",
  "Red Bull Racing": "#0600EF",
  "Mercedes": "#00D2BE",
  "McLaren": "#FF8700",
  "Aston Martin": "#006F62",
  "Alpine": "#0090FF",
  "Williams": "#005AFF",
  "Racing Bulls": "#6692FF",
  "Haas F1 Team": "#FFFFFF",
  "Audi": "#F1102A",
  "Cadillac": "#FFD700"
};

export default function DashboardTabs({ predictions, results, strategy }: { predictions: any[], results: any[], strategy: any[] }) {
  const [activeTab, setActiveTab] = useState<'grid' | 'h2h' | 'audit' | 'strategy'>('grid');
  
  const rounds = useMemo(() => {
    const allRounds = Array.from(new Set([
      ...predictions.map(p => p.round_number), 
      ...results.map(r => r.round_number),
      ...strategy.map(s => s.round_number)
    ]));
    return allRounds.sort((a, b) => b - a);
  }, [predictions, results, strategy]);

  const [selectedRound, setSelectedRound] = useState(rounds[0] || 4);

  const filteredPredictions = predictions.filter(p => p.round_number === selectedRound);
  const filteredResults = results.filter(r => r.round_number === selectedRound);
  const filteredStrategy = strategy.filter(s => s.round_number === selectedRound);

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
  const STORAGE_URL = supabaseUrl + "/storage/v1/object/public/f1_assets/";

  const stats = useMemo(() => {
    let globalTotal = 0;
    let globalHits = 0;
    let sessionTotal = 0;
    let sessionHits = 0;

    const allRoundsWithData = Array.from(new Set(predictions.map(p => p.round_number)));
    
    allRoundsWithData.forEach(rNum => {
      const roundPreds = predictions.filter(p => p.round_number === rNum);
      const roundRes = results.filter(r => r.round_number === rNum);
      
      if (roundRes.length === 0) return;

      const teams: Record<string, any[]> = {};
      roundPreds.forEach(p => {
        const team = DRIVER_DETAILS[p.code]?.team || "Unknown";
        if (!teams[team]) teams[team] = [];
        teams[team].push(p);
      });

      Object.entries(teams).forEach(([teamName, drivers]) => {
        if (drivers.length < 2) return;
        
        const d1 = drivers[0];
        const d2 = drivers[1];
        
        const r1 = roundRes.find(r => r.code === d1.code);
        const r2 = roundRes.find(r => r.code === d2.code);

        if (r1 && r2) {
          globalTotal++;
          if (rNum === selectedRound) sessionTotal++;

          const predictedWinner = d1.ai_predicted_pos < d2.ai_predicted_pos ? d1.code : d2.code;
          const officialWinner = r1.official_position < r2.official_position ? r1.code : r2.code;
          
          if (predictedWinner === officialWinner) {
            globalHits++;
            if (rNum === selectedRound) sessionHits++;
          }
        }
      });
    });

    return { 
      globalAccuracy: globalTotal > 0 ? Math.round((globalHits / globalTotal) * 100) : 0,
      globalHits,
      globalTotal,
      sessionAccuracy: sessionTotal > 0 ? Math.round((sessionHits / sessionTotal) * 100) : 0,
      sessionHits,
      sessionTotal
    };
  }, [predictions, results, selectedRound]);

  return (
    <div className="w-full">
      {/* Header Container: Two Rows */}
      <div className="flex flex-col gap-8 mb-12 border-b border-white/10 pb-2">
        
        {/* Row 1: Session Selector (Full Width) */}
        <div className="flex justify-center xl:justify-end">
          <div className="flex items-center gap-4 bg-zinc-900/80 backdrop-blur-xl p-2 rounded-2xl border border-white/10 shadow-2xl w-full max-w-2xl">
            <div className="flex items-center gap-3 px-4 border-r border-white/5">
              <div className="w-2.5 h-2.5 rounded-full bg-[#E8002D] animate-pulse shadow-[0_0_8px_rgba(232,0,45,0.6)]"></div>
              <span className="font-mono text-[11px] text-zinc-400 uppercase tracking-[0.2em] font-bold">Select Session</span>
            </div>
            <select 
              value={selectedRound}
              onChange={(e) => setSelectedRound(Number(e.target.value))}
              className="flex-1 bg-transparent text-white font-mono text-sm border-none rounded-lg py-2 pl-2 pr-8 focus:ring-0 outline-none cursor-pointer hover:text-[#E8002D] transition-colors"
            >
              {rounds.map(r => (
                <option key={r} value={r} className="bg-zinc-900 text-white">
                  Round {r}: {predictions.find(p => p.round_number === r)?.race_name || results.find(re => re.round_number === r)?.race_name || "Official Data Only"}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Row 2: Navigation Tabs */}
        <nav className="flex items-center justify-center xl:justify-start gap-12 overflow-x-auto whitespace-nowrap scrollbar-hide py-2">
          {[
            { id: 'grid', label: '01. Master Grid' },
            { id: 'strategy', label: '02. Strategy & Map' },
            { id: 'h2h', label: '03. Head-to-Head' },
            { id: 'audit', label: '04. Accuracy Audit' }
          ].map((tab) => (
            <button 
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`font-mono text-[12px] font-bold tracking-[0.25em] uppercase transition-all pb-4 relative ${activeTab === tab.id ? 'text-[#E8002D]' : 'text-zinc-500 hover:text-zinc-300'}`}
            >
              {tab.label}
              {activeTab === tab.id && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#E8002D] shadow-[0_4px_12px_rgba(232,0,45,0.6)]"></div>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Grid Tab */}
      {activeTab === 'grid' && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 animate-in fade-in duration-500">
          {filteredPredictions.map((p, index) => {
            const details = DRIVER_DETAILS[p.code] || { name: p.code, team: "Unknown" };
            const teamColor = TEAM_COLORS[details.team] || "#00f3ff";
            const photoUrl = STORAGE_URL + "drivers/" + getDriverPhoto(p.code);
            
            return (
              <div key={p.code} className="bg-zinc-900/60 backdrop-blur-md border border-white/5 hover:border-[#E8002D]/40 transition-all rounded-lg overflow-hidden flex flex-col relative group h-full">
                <div className="absolute top-2 right-2 z-10">
                  <span className="font-mono text-3xl italic font-black text-[#E8002D]/10 group-hover:text-[#E8002D]/30 transition-colors">
                    {(index + 1).toString().padStart(2, '0')}
                  </span>
                </div>
                
                <div className="relative h-48 w-full bg-zinc-950 overflow-hidden">
                  <Image 
                    src={photoUrl} 
                    alt={details.name}
                    fill
                    sizes="(max-width: 768px) 50vw, 16vw"
                    className="object-cover object-top transition-all duration-700 scale-105 group-hover:scale-100 z-10"
                    unoptimized
                    onError={(e) => { e.currentTarget.style.display = 'none'; }}
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-[#121619] via-transparent to-transparent z-20"></div>
                </div>

                <div className="p-3 -mt-6 relative z-30 flex-1 flex flex-col">
                  <div className="flex justify-between items-end mb-2">
                    <div className="flex-1 truncate">
                      <span className="font-mono text-[8px] text-zinc-400 uppercase tracking-widest block truncate" style={{ color: teamColor }}>{details.team}</span>
                      <h2 className="text-sm font-bold uppercase italic text-white tracking-tight truncate">{details.name.split(' ').pop()}</h2>
                    </div>
                  </div>

                  <div className="space-y-2.5 pt-2 border-t border-white/5 mt-auto">
                    <div className="grid grid-cols-2 gap-2">
                       <div className="bg-white/5 p-1.5 rounded flex flex-col items-center">
                        <span className="font-mono text-[7px] text-zinc-500 uppercase">Win</span>
                        <span className="text-xs font-bold text-white">{p.prob_win}</span>
                      </div>
                      <div className="bg-white/5 p-1.5 rounded flex flex-col items-center">
                        <span className="font-mono text-[7px] text-zinc-500 uppercase">Podium</span>
                        <span className="text-xs font-bold text-[#00F3FF]">{p.prob_podium}</span>
                      </div>
                      <div className="bg-white/5 p-1.5 rounded flex flex-col items-center">
                        <span className="font-mono text-[7px] text-zinc-500 uppercase">Top 6</span>
                        <span className="text-xs font-bold text-yellow-500">{p.prob_top6}</span>
                      </div>
                      <div className="bg-white/5 p-1.5 rounded flex flex-col items-center">
                        <span className="font-mono text-[7px] text-zinc-500 uppercase">Top 10</span>
                        <span className="text-xs font-bold text-green-500">{p.prob_top10}</span>
                      </div>
                    </div>

                    <div className="flex justify-between items-center bg-[#E8002D]/5 p-1.5 rounded border border-[#E8002D]/10">
                      <span className="font-mono text-[7px] text-zinc-400 uppercase">Pace</span>
                      <span className="font-mono text-[10px] font-bold text-[#E8002D]">
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

      {/* Strategy & Map Tab */}
      {activeTab === 'strategy' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {/* Strategy Matrix */}
          <div className="lg:col-span-2 bg-zinc-900/60 backdrop-blur-md rounded-2xl border border-white/5 overflow-hidden flex flex-col shadow-2xl">
            <div className="p-6 border-b border-white/5 flex justify-between items-center bg-white/5">
               <h3 className="text-sm font-black text-white uppercase tracking-[0.3em]">Strategy Simulation Matrix</h3>
               <div className="flex items-center gap-2">
                 <span className="w-2 h-2 rounded-full bg-[#E8002D] animate-pulse"></span>
                 <span className="font-mono text-[10px] text-zinc-400 uppercase tracking-widest">Live Updates</span>
               </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs">
                <thead>
                  <tr className="bg-zinc-950/50 text-zinc-500 uppercase">
                    <th className="px-6 py-5">Driver</th>
                    <th className="px-6 py-5">Pit Window</th>
                    <th className="px-6 py-5">Tire Life</th>
                    <th className="px-6 py-5">Optimal Strategy</th>
                    <th className="px-6 py-5">Risk</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {filteredStrategy.map((s) => {
                    const color = TEAM_COLORS[DRIVER_DETAILS[s.code]?.team || ""] || "#E8002D";
                    return (
                      <tr key={s.id} className="hover:bg-white/5 transition-colors">
                        <td className="px-6 py-4 font-black italic text-sm" style={{ color }}>{s.code}</td>
                        <td className="px-6 py-4 text-white font-bold">{s.pit_window}</td>
                        <td className="px-6 py-4 text-zinc-400">{s.tire_life}</td>
                        <td className="px-6 py-4 text-white font-black tracking-wide">{s.optimal_strategy}</td>
                        <td className="px-6 py-4">
                           <span className={`px-3 py-1 rounded-md text-[9px] font-black ${
                             s.risk_level === 'LOW' ? 'bg-green-500/10 text-green-500 border border-green-500/20' :
                             s.risk_level === 'MED' ? 'bg-yellow-500/10 text-yellow-500 border border-yellow-500/20' :
                             'bg-red-500/10 text-red-500 border border-red-500/20'
                           }`}>
                             {s.risk_level}
                           </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Track Map */}
          <div className="bg-zinc-900/60 backdrop-blur-md rounded-2xl border border-white/5 overflow-hidden flex flex-col shadow-2xl relative h-fit sticky top-8">
            <div className="p-6 border-b border-white/5 flex justify-between items-center bg-white/5">
               <div>
                  <h3 className="text-sm font-black text-white uppercase tracking-[0.3em]">Track Map</h3>
                  <p className="font-mono text-[10px] text-zinc-500 mt-1 uppercase tracking-widest">
                    {predictions.find(p => p.round_number === selectedRound)?.race_name || "Circuit Layout"}
                  </p>
               </div>
               <div className="w-10 h-10 rounded-xl bg-[#E8002D] flex items-center justify-center shadow-[0_0_20px_rgba(232,0,45,0.4)]">
                 <svg viewBox="0 0 24 24" fill="white" className="w-5 h-5"><path d="M7 2v11h3v9l7-12h-4l4-8z"/></svg>
               </div>
            </div>
            <div className="p-8 flex items-center justify-center relative min-h-[400px]">
               <div className="absolute inset-0 bg-gradient-to-t from-zinc-950/90 to-transparent pointer-events-none z-10"></div>
               <Image 
                src={`${STORAGE_URL}tracks/track_${selectedRound}.png`} 
                alt="Track Layout" 
                fill 
                className="object-contain p-8 opacity-90 group-hover:opacity-100 transition-opacity drop-shadow-[0_0_30px_rgba(255,255,255,0.05)]"
                unoptimized
                onError={(e) => {
                  e.currentTarget.src = 'https://raw.githubusercontent.com/saelbalandrano/f1_picks/main/public/track_placeholder.png'; // Fallback if exists or just hide
                  e.currentTarget.style.opacity = '0.2';
                }}
               />
               <div className="absolute bottom-12 left-1/2 -translate-x-1/2 z-20 flex gap-4">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-[#E8002D] shadow-[0_0_10px_#E8002D]"></div>
                    <span className="font-mono text-[8px] text-zinc-400 uppercase">Sector 1</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-[#00F3FF] shadow-[0_0_10px_#00F3FF]"></div>
                    <span className="font-mono text-[8px] text-zinc-400 uppercase">Sector 2</span>
                  </div>
               </div>
            </div>
            <div className="p-6 border-t border-white/5 bg-zinc-950/30">
               <button className="w-full py-4 bg-white/5 border border-white/10 rounded-xl font-mono text-[11px] text-white font-black uppercase tracking-[0.2em] hover:bg-white/10 hover:border-white/20 transition-all shadow-xl">
                 Expand Live Telemetry
               </button>
            </div>
          </div>
        </div>
      )}

      {/* Head to Head Tab */}
      {activeTab === 'h2h' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {(() => {
            const teams: Record<string, any[]> = {};
            filteredPredictions.forEach(p => {
              const details = DRIVER_DETAILS[p.code] || { name: p.code, team: "Unknown" };
              if (!teams[details.team]) teams[details.team] = [];
              teams[details.team].push({ ...p, details });
            });

            return Object.entries(teams).map(([teamName, drivers]) => {
              if (drivers.length < 2) return null;
              const d1 = drivers[0];
              const d2 = drivers[1];
              const d1IsPick = d1.ai_predicted_pos < d2.ai_predicted_pos;
              
              return (
                <div key={teamName} className="bg-zinc-900/40 backdrop-blur-md rounded-2xl border border-white/5 overflow-hidden flex flex-col relative">
                  <div className="p-3 border-b border-white/5 bg-white/5 flex justify-between items-center">
                    <span className="font-mono text-[10px] text-zinc-400 uppercase tracking-[0.3em]">{teamName}</span>
                    <Image src={STORAGE_URL + "logos/" + getTeamLogo(teamName)} alt={teamName} width={16} height={16} className="opacity-50 grayscale" unoptimized />
                  </div>
                  <div className="grid grid-cols-2 gap-4 p-4 relative">
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-20">
                      <div className="w-8 h-8 rounded-full bg-[#121619] border border-white/10 flex items-center justify-center shadow-2xl">
                        <span className="text-[10px] italic font-black text-[#E8002D]">VS</span>
                      </div>
                    </div>
                    {[d1, d2].map((d, i) => {
                      const isPick = (i === 0 && d1IsPick) || (i === 1 && !d1IsPick);
                      return (
                        <div key={d.code} className={`relative p-3 rounded-xl border transition-all duration-500 ${isPick ? 'border-[#E8002D] shadow-[0_0_20px_rgba(232,0,45,0.2)] bg-[#E8002D]/5' : 'border-white/5 bg-white/2'}`}>
                          {isPick && <div className="absolute -top-2 left-1/2 -translate-x-1/2 bg-[#E8002D] text-white text-[7px] font-black uppercase px-2 py-0.5 rounded-full z-30">AI PICK</div>}
                          <div className="relative w-full aspect-square rounded-lg overflow-hidden bg-zinc-950 mb-3">
                             <Image src={STORAGE_URL + "drivers/" + getDriverPhoto(d.code)} alt={d.details.name} fill className="object-cover object-top" unoptimized />
                          </div>
                          <div className="text-center">
                            <h3 className="text-xs font-black text-white uppercase">{d.code}</h3>
                            <p className="text-xl font-black text-white mt-1">P{Math.round(d.ai_predicted_pos)}</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )
            });
          })()}
        </div>
      )}

      {/* Accuracy Audit Tab */}
      {activeTab === 'audit' && (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-zinc-900/60 backdrop-blur-md p-6 rounded-2xl border border-white/5 relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                <svg viewBox="0 0 24 24" fill="currentColor" className="w-24 h-24 text-white"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
              </div>
              <span className="font-mono text-[10px] text-[#E8002D] uppercase tracking-[0.3em] font-black block mb-6">Global Season Performance</span>
              <div className="flex items-center gap-8">
                <div className="relative w-28 h-28 flex items-center justify-center">
                  <svg className="w-full h-full -rotate-90">
                    <circle cx="56" cy="56" r="48" stroke="currentColor" strokeWidth="6" fill="transparent" className="text-white/5" />
                    <circle cx="56" cy="56" r="48" stroke="currentColor" strokeWidth="6" fill="transparent" 
                      strokeDasharray={301.6} strokeDashoffset={301.6 - (301.6 * stats.globalAccuracy) / 100}
                      className="text-[#E8002D]" />
                  </svg>
                  <div className="absolute flex flex-col items-center">
                    <span className="text-3xl font-black text-white">{stats.globalAccuracy}%</span>
                    <span className="text-[8px] text-zinc-500 font-mono">ACCURACY</span>
                  </div>
                </div>
                <div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-black text-white">{stats.globalHits}</span>
                    <span className="text-sm font-bold text-zinc-500">Hits</span>
                  </div>
                  <p className="text-[10px] text-zinc-500 font-mono mt-1 uppercase tracking-widest">Across {stats.globalTotal} Head-to-Head Duels</p>
                  <div className="mt-4 h-1 w-32 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-[#E8002D]" style={{ width: `${stats.globalAccuracy}%` }}></div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-zinc-900/60 backdrop-blur-md p-6 rounded-2xl border border-white/10 relative overflow-hidden group shadow-[0_0_40px_rgba(232,0,45,0.05)]">
              <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                 <div className="text-4xl font-black text-white italic">R{selectedRound}</div>
              </div>
              <span className="font-mono text-[10px] text-[#00F3FF] uppercase tracking-[0.3em] font-black block mb-6">Current Session Audit</span>
              <div className="flex items-center gap-8">
                <div className="relative w-28 h-28 flex items-center justify-center">
                  <svg className="w-full h-full -rotate-90">
                    <circle cx="56" cy="56" r="48" stroke="currentColor" strokeWidth="6" fill="transparent" className="text-white/5" />
                    <circle cx="56" cy="56" r="48" stroke="currentColor" strokeWidth="6" fill="transparent" 
                      strokeDasharray={301.6} strokeDashoffset={301.6 - (301.6 * stats.sessionAccuracy) / 100}
                      className="text-[#00F3FF]" />
                  </svg>
                  <div className="absolute flex flex-col items-center">
                    <span className="text-3xl font-black text-white">{stats.sessionAccuracy}%</span>
                    <span className="text-[8px] text-zinc-500 font-mono">PRECISION</span>
                  </div>
                </div>
                <div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-black text-white">{stats.sessionHits}</span>
                    <span className="text-sm font-bold text-zinc-500">Hits</span>
                  </div>
                  <p className="text-[10px] text-zinc-500 font-mono mt-1 uppercase tracking-widest">In Round {selectedRound} matchups</p>
                  <div className="mt-4 h-1 w-32 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-[#00F3FF]" style={{ width: `${stats.sessionAccuracy}%` }}></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {filteredResults.length > 0 ? (
            <div className="bg-zinc-900/60 backdrop-blur-md border border-white/5 rounded-xl overflow-hidden shadow-2xl">
              <div className="p-6 border-b border-white/5 bg-white/5 flex justify-between items-center">
                <h3 className="text-sm font-bold text-white uppercase tracking-widest flex items-center gap-3">
                  <span className="w-2 h-2 bg-[#E8002D] rounded-full animate-pulse"></span>
                  Round {selectedRound} Raw Comparison
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left font-mono text-sm">
                  <thead>
                    <tr className="bg-zinc-950/50 text-zinc-500 uppercase">
                      <th className="px-6 py-5">Driver</th>
                      <th className="px-6 py-5">AI Prediction</th>
                      <th className="px-6 py-5">Official Finish</th>
                      <th className="px-6 py-5">Error Delta</th>
                      <th className="px-6 py-5">Session Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {filteredResults.map(res => {
                      const pred = filteredPredictions.find(p => p.code === res.code);
                      const predPos = pred ? Math.round(pred.ai_predicted_pos) : null;
                      const delta = (predPos !== null) ? Math.abs(predPos - res.official_position) : null;
                      const isAccurate = delta !== null && delta <= 2;
                      
                      return (
                        <tr key={res.id} className="hover:bg-white/5 transition-colors group">
                          <td className="px-6 py-5 text-white font-black group-hover:text-[#E8002D] transition-colors flex items-center gap-2 text-sm">
                            <span className="w-1.5 h-5 bg-[#E8002D]"></span>
                            {res.code}
                          </td>
                          <td className="px-6 py-5 text-zinc-400 font-bold">{predPos !== null ? `P${predPos}` : '-'}</td>
                          <td className="px-6 py-5 text-[#E8002D] font-black text-base">P{res.official_position}</td>
                          <td className="px-6 py-5 font-black text-sm" style={{ color: delta === 0 ? '#00F3FF' : (delta !== null && delta <= 2 ? '#ffffff' : '#ef4444') }}>
                            {delta !== null ? (delta === 0 ? '±0' : `±${delta}`) : '-'}
                          </td>
                          <td className="px-6 py-5">
                            <span className={`px-3 py-1 rounded-md text-[10px] font-black uppercase ${isAccurate ? 'bg-[#00F3FF]/10 text-[#00F3FF] border border-[#00F3FF]/20' : 'bg-red-500/10 text-red-500 border border-red-500/20'}`}>
                              {delta !== null ? (isAccurate ? 'Within Range' : 'Outlier Detected') : 'N/A'}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="min-h-[300px] flex flex-col items-center justify-center border border-dashed border-white/10 rounded-2xl bg-zinc-900/20">
               <p className="text-zinc-500 font-mono text-xs">Waiting for FIA confirmation for Round {selectedRound}...</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
