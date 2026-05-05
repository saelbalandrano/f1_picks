import { createClient } from '@supabase/supabase-js';
import DashboardTabs from './DashboardTabs';

// Force dynamic rendering so it always fetches fresh data on load
export const dynamic = 'force-dynamic';

export default async function Home() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
  const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';
  
  if (!supabaseUrl || !supabaseKey) {
    return (
      <div className="min-h-screen bg-[#101417] text-[#e0e2e8] font-sans p-8 flex flex-col items-center justify-center">
        <div className="bg-[#1c2024] p-8 rounded-xl border border-[#93000a] max-w-lg text-center">
          <h1 className="text-2xl font-bold text-[#ffb4ab] mb-4">Configuration Error</h1>
          <p className="text-[#e0e2e8]">Missing Supabase environment variables.</p>
        </div>
      </div>
    );
  }

  const supabase = createClient(supabaseUrl, supabaseKey);

  const { data: predictions, error: pError } = await supabase
    .from('ai_predictions')
    .select('*')
    .order('ai_predicted_pos', { ascending: true });

  const { data: results, error: rError } = await supabase
    .from('official_race_results')
    .select('*');

  const { data: strategy, error: sError } = await supabase
    .from('strategy_simulations')
    .select('*');

  if (pError || !predictions || predictions.length === 0) {
    return (
      <div className="min-h-screen bg-[#101417] text-[#e0e2e8] font-sans p-8 flex flex-col items-center justify-center">
        <div className="bg-[#1c2024] p-8 rounded-xl border border-[#849495] max-w-lg text-center">
          <h1 className="text-2xl font-bold text-[#00f3ff] mb-4">Waiting for Data</h1>
          <p className="text-[#b9cacb]">The AI prediction engine is currently processing the next race. Please check back later.</p>
        </div>
      </div>
    );
  }

  const raceName = predictions.find(p => p.round_number === Math.max(...predictions.map(pr => pr.round_number)))?.race_name || "Unknown Race";
  const roundNumber = Math.max(...predictions.map(p => p.round_number));

  return (
    <div className="min-h-screen bg-[#101417] text-[#e0e2e8] font-sans selection:bg-[#E8002D]/30">
      {/* Background ambient glow */}
      <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-[#E8002D] rounded-full blur-[150px] opacity-[0.03]"></div>
        <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-[#E8002D] rounded-full blur-[150px] opacity-[0.03]"></div>
      </div>

      {/* Header */}
      <header className="relative z-10 border-b border-white/5 bg-[#181c20]/50 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <span className="bg-[#E8002D] text-white text-[10px] font-bold px-2 py-0.5 rounded-sm tracking-widest uppercase shadow-[0_0_10px_rgba(232,0,45,0.5)]">
                  Live Telemetry
                </span>
                <span className="font-mono text-xs text-[#E8002D] tracking-widest uppercase">
                  Latest: Round {roundNumber}
                </span>
              </div>
              <h1 className="text-4xl md:text-5xl font-black tracking-tight uppercase text-transparent bg-clip-text bg-gradient-to-r from-white to-[#b9cacb]">
                {raceName}
              </h1>
            </div>
            <div className="text-right">
              <p className="font-mono text-xs text-zinc-500 tracking-widest uppercase mb-1">System Status</p>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-[#E8002D] shadow-[0_0_8px_#E8002D] animate-pulse"></div>
                <span className="font-mono text-sm text-[#E8002D]">OPTIMAL</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="relative z-10 max-w-7xl mx-auto px-6 py-8">
        <DashboardTabs 
          predictions={predictions} 
          results={results || []} 
          strategy={strategy || []}
        />
      </main>
    </div>
  );
}
