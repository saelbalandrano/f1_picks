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

export default function DashboardTabs({ predictions, results }: { predictions: any[], results: any[] }) {
  const [activeTab, setActiveTab] = useState<'grid' | 'h2h' | 'audit'>('grid');
  
  // Get all unique rounds from both tables
  const rounds = useMemo(() => {
    const allRounds = Array.from(new Set([...predictions.map(p => p.round_number), ...results.map(r => r.round_number)]));
    return allRounds.sort((a, b) => b - a);
  }, [predictions, results]);

  const [selectedRound, setSelectedRound] = useState(rounds[0] || 4);

  // Filter predictions and results for the selected round
  const filteredPredictions = predictions.filter(p => p.round_number === selectedRound);
  const filteredResults = results.filter(r => r.round_number === selectedRound);

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
  const STORAGE_URL = supabaseUrl + "/storage/v1/object/public/f1_assets/";

  // Accuracy Statistics Calculation
  const stats = useMemo(() => {
    let totalH2H = 0;
    let hitsH2H = 0;

    // We calculate hits across all rounds where both predictions and results exist
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
          totalH2H++;
          const predictedWinner = d1.ai_predicted_pos < d2.ai_predicted_pos ? d1.code : d2.code;
          const officialWinner = r1.official_position < r2.official_position ? r1.code : r2.code;
          
          if (predictedWinner === officialWinner) {
            hitsH2H++;
          }
        }
      });
    });

    const accuracy = totalH2H > 0 ? Math.round((hitsH2H / totalH2H) * 100) : 0;
    return { totalH2H, hitsH2H, accuracy };
  }, [predictions, results]);

  return (
    <div className="w-full">
      {/* Tab Navigation & Selector */}
      <div className="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-6 mb-12 border-b border-white/10 pb-6">
        <nav className="flex items-center gap-8 overflow-x-auto whitespace-nowrap scrollbar-hide">
          <button 
            onClick={() => setActiveTab('grid')}
            className={`font-mono text-[11px] font-bold tracking-[0.2em] uppercase transition-all pb-6 -mb-[25px] ${activeTab === 'grid' ? 'text-[#E8002D] border-b-2 border-[#E8002D] shadow-[0_4px_12px_-2px_rgba(232,0,45,0.6)]' : 'text-zinc-500 hover:text-zinc-300'}`}
          >
            01. Master Grid
          </button>
          <button 
            onClick={() => setActiveTab('h2h')}
            className={`font-mono text-[11px] font-bold tracking-[0.2em] uppercase transition-all pb-6 -mb-[25px] ${activeTab === 'h2h' ? 'text-[#E8002D] border-b-2 border-[#E8002D] shadow-[0_4px_12px_-2px_rgba(232,0,45,0.6)]' : 'text-zinc-500 hover:text-zinc-300'}`}
          >
            02. Head-to-Head
          </button>
          <button 
            onClick={() => setActiveTab('audit')}
            className={`font-mono text-[11px] font-bold tracking-[0.2em] uppercase transition-all pb-6 -mb-[25px] ${activeTab === 'audit' ? 'text-[#E8002D] border-b-2 border-[#E8002D] shadow-[0_4px_12px_-2px_rgba(232,0,45,0.6)]' : 'text-zinc-500 hover:text-zinc-300'}`}
          >
            03. Accuracy Audit
          </button>
        </nav>

        {/* Improved Round Selector */}
        <div className="flex items-center gap-4 bg-zinc-900/80 backdrop-blur-xl p-1.5 rounded-xl border border-white/10 shadow-2xl">
          <div className="flex items-center gap-2 px-3 border-r border-white/5">
            <div className="w-2 h-2 rounded-full bg-[#E8002D] animate-pulse"></div>
            <span className="font-mono text-[10px] text-zinc-400 uppercase tracking-widest">Select Session</span>
          </div>
          <select 
            value={selectedRound}
            onChange={(e) => setSelectedRound(Number(e.target.value))}
            className="bg-transparent text-white font-mono text-xs border-none rounded-lg py-1.5 pl-2 pr-8 focus:ring-0 outline-none cursor-pointer hover:text-[#E8002D] transition-colors"
          >
            {rounds.map(r => (
              <option key={r} value={r} className="bg-zinc-900 text-white">
                Round {r}: {predictions.find(p => p.round_number === r)?.race_name || results.find(re => re.round_number === r)?.race_name || "Official Data Only"}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Grid Tab */}
      {activeTab === 'grid' && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {filteredPredictions.map((p, index) => {
            const details = DRIVER_DETAILS[p.code] || { name: p.code, team: "Unknown" };
            const teamColor = TEAM_COLORS[details.team] || "#00f3ff";
            const photoUrl = STORAGE_URL + "drivers/" + getDriverPhoto(p.code);
            const logoUrl = STORAGE_URL + "logos/" + getTeamLogo(details.team);
            
            return (
              <div key={p.code} className="bg-zinc-900/60 backdrop-blur-md border border-white/5 hover:border-[#E8002D]/40 transition-all rounded-lg overflow-hidden flex flex-col relative group h-full">
                {/* Ranking Number */}
                <div className="absolute top-2 right-2 z-10">
                  <span className="font-mono text-3xl italic font-black text-[#E8002D]/10 group-hover:text-[#E8002D]/30 transition-colors">
                    {(index + 1).toString().padStart(2, '0')}
                  </span>
                </div>
                
                {/* Driver Image Section */}
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
                    {/* Probabilities Grid */}
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

      {/* Head to Head Tab */}
      {activeTab === 'h2h' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {(() => {
            const teams: Record<string, any[]> = {};
            filteredPredictions.forEach(p => {
              const details = DRIVER_DETAILS[p.code] || { name: p.code, team: "Unknown" };
              if (!teams[details.team]) teams[details.team] = [];
              teams[details.team].push({ ...p, details });
            });

            return Object.entries(teams).map(([teamName, drivers]) => {
              if (drivers.length < 2) return null;
              
              // Determine the pick (predicted winner)
              const d1 = drivers[0];
              const d2 = drivers[1];
              const d1IsPick = d1.ai_predicted_pos < d2.ai_predicted_pos;
              
              const teamColor = TEAM_COLORS[teamName] || "#00f3ff";
              
              return (
                <div key={teamName} className="bg-zinc-900/40 backdrop-blur-md rounded-2xl border border-white/5 overflow-hidden flex flex-col relative">
                  <div className="p-3 border-b border-white/5 bg-white/5 flex justify-between items-center">
                    <span className="font-mono text-[10px] text-zinc-400 uppercase tracking-[0.3em]">{teamName}</span>
                    <Image src={STORAGE_URL + "logos/" + getTeamLogo(teamName)} alt={teamName} width={16} height={16} className="opacity-50 grayscale" unoptimized />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 p-4 relative">
                    {/* VS Center Badge */}
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-20">
                      <div className="w-8 h-8 rounded-full bg-[#121619] border border-white/10 flex items-center justify-center shadow-2xl">
                        <span className="text-[10px] italic font-black text-[#E8002D]">VS</span>
                      </div>
                    </div>

                    {/* Driver 1 */}
                    <div className={`relative p-3 rounded-xl border transition-all duration-500 ${d1IsPick ? 'border-[#E8002D] shadow-[0_0_20px_rgba(232,0,45,0.2)] bg-[#E8002D]/5' : 'border-white/5 bg-white/2'}`}>
                      {d1IsPick && <div className="absolute -top-2 left-1/2 -translate-x-1/2 bg-[#E8002D] text-white text-[7px] font-black uppercase px-2 py-0.5 rounded-full z-30">AI PICK</div>}
                      <div className="relative w-full aspect-square rounded-lg overflow-hidden bg-zinc-950 mb-3">
                         <Image 
                          src={STORAGE_URL + "drivers/" + getDriverPhoto(d1.code)}
                          alt={d1.details.name}
                          fill
                          className="object-cover object-top"
                          unoptimized
                        />
                      </div>
                      <div className="text-center">
                        <h3 className="text-xs font-black text-white uppercase">{d1.code}</h3>
                        <p className="text-xl font-black text-white mt-1">P{Math.round(d1.ai_predicted_pos)}</p>
                      </div>
                    </div>

                    {/* Driver 2 */}
                    <div className={`relative p-3 rounded-xl border transition-all duration-500 ${!d1IsPick ? 'border-[#E8002D] shadow-[0_0_20px_rgba(232,0,45,0.2)] bg-[#E8002D]/5' : 'border-white/5 bg-white/2'}`}>
                      {!d1IsPick && <div className="absolute -top-2 left-1/2 -translate-x-1/2 bg-[#E8002D] text-white text-[7px] font-black uppercase px-2 py-0.5 rounded-full z-30">AI PICK</div>}
                      <div className="relative w-full aspect-square rounded-lg overflow-hidden bg-zinc-950 mb-3">
                         <Image 
                          src={STORAGE_URL + "drivers/" + getDriverPhoto(d2.code)}
                          alt={d2.details.name}
                          fill
                          className="object-cover object-top"
                          unoptimized
                        />
                      </div>
                      <div className="text-center">
                        <h3 className="text-xs font-black text-white uppercase">{d2.code}</h3>
                        <p className="text-xl font-black text-white mt-1">P{Math.round(d2.ai_predicted_pos)}</p>
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
        <div className="space-y-8">
          {/* Global Statistics Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-zinc-900/60 backdrop-blur-md p-6 rounded-2xl border border-white/5 flex flex-col items-center justify-center text-center">
              <span className="font-mono text-[10px] text-zinc-500 uppercase tracking-widest mb-2">H2H Accuracy</span>
              <div className="relative w-24 h-24 flex items-center justify-center">
                <svg className="w-full h-full -rotate-90">
                  <circle cx="48" cy="48" r="40" stroke="currentColor" strokeWidth="4" fill="transparent" className="text-white/5" />
                  <circle cx="48" cy="48" r="40" stroke="currentColor" strokeWidth="4" fill="transparent" 
                    strokeDasharray={251.2} strokeDashoffset={251.2 - (251.2 * stats.accuracy) / 100}
                    className="text-[#E8002D]" />
                </svg>
                <span className="absolute text-2xl font-black text-white">{stats.accuracy}%</span>
              </div>
            </div>
            
            <div className="bg-zinc-900/60 backdrop-blur-md p-6 rounded-2xl border border-white/5 flex flex-col justify-center">
              <span className="font-mono text-[10px] text-zinc-500 uppercase tracking-widest mb-4">H2H Hit Rate</span>
              <div className="flex items-end gap-2">
                <span className="text-5xl font-black text-white">{stats.hitsH2H}</span>
                <span className="text-xl font-bold text-zinc-600 mb-1">/ {stats.totalH2H}</span>
              </div>
              <p className="text-xs text-zinc-500 mt-2 font-mono">Head-to-head predictions correctly identified within the same team.</p>
            </div>

            <div className="bg-zinc-900/60 backdrop-blur-md p-6 rounded-2xl border border-white/5 flex flex-col justify-center">
              <span className="font-mono text-[10px] text-zinc-500 uppercase tracking-widest mb-4">Total Predictions</span>
              <div className="flex items-end gap-2">
                <span className="text-5xl font-black text-[#00F3FF]">{predictions.length}</span>
              </div>
              <p className="text-xs text-zinc-500 mt-2 font-mono">Total data points analyzed across all sessions in the database.</p>
            </div>
          </div>

          {filteredResults.length > 0 ? (
            <div className="bg-zinc-900/60 backdrop-blur-md border border-white/5 rounded-xl overflow-hidden shadow-2xl">
              <div className="p-6 border-b border-white/5 bg-white/5 flex justify-between items-center">
                <h3 className="text-sm font-bold text-white uppercase tracking-widest flex items-center gap-3">
                  <span className="w-2 h-2 bg-[#E8002D] rounded-full animate-pulse"></span>
                  Round {selectedRound} Raw Audit
                </h3>
                <span className="font-mono text-[10px] text-zinc-500">REAL-TIME DATA FEED</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left font-mono text-xs">
                  <thead>
                    <tr className="bg-zinc-950/50 text-zinc-500 uppercase">
                      <th className="px-6 py-4">Driver</th>
                      <th className="px-6 py-4">AI Prediction</th>
                      <th className="px-6 py-4">Official Finish</th>
                      <th className="px-6 py-4">Error Delta</th>
                      <th className="px-6 py-4">System Status</th>
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
                          <td className="px-6 py-4 text-white font-bold group-hover:text-[#E8002D] transition-colors">{res.code}</td>
                          <td className="px-6 py-4 text-zinc-400">{predPos !== null ? `P${predPos}` : '-'}</td>
                          <td className="px-6 py-4 text-[#E8002D] font-bold">P{res.official_position}</td>
                          <td className="px-6 py-4 font-bold" style={{ color: delta === 0 ? '#00F3FF' : '#ffffff' }}>
                            {delta !== null ? (delta === 0 ? '±0' : `±${delta}`) : '-'}
                          </td>
                          <td className="px-6 py-4">
                            <span className={`px-2 py-1 rounded text-[9px] uppercase font-black ${isAccurate ? 'bg-[#00F3FF]/10 text-[#00F3FF]' : 'bg-red-500/10 text-red-500'}`}>
                              {delta !== null ? (isAccurate ? 'Within Range' : 'Outlier Detected') : 'Data Unavailable'}
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
            <div className="min-h-[400px] flex flex-col items-center justify-center border border-dashed border-white/10 rounded-2xl bg-zinc-900/20 backdrop-blur-sm relative overflow-hidden">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(232,0,45,0.03)_0%,transparent_70%)]"></div>
              <div className="text-center z-10 p-8">
                <div className="w-12 h-12 border-2 border-[#E8002D]/30 border-t-[#E8002D] rounded-full animate-spin mx-auto mb-6"></div>
                <h2 className="text-xl font-bold text-white mb-2 uppercase tracking-widest">Calibration Phase</h2>
                <p className="text-zinc-500 font-mono text-xs max-w-sm mx-auto leading-relaxed">
                  Official results for Round {selectedRound} have not been verified yet. 
                  The neural network comparison will activate once the FIA confirms the race order.
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
