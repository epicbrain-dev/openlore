import React, { useState } from 'react';
import { ShieldCheck, Lock, Unlock, ArrowRight, AlertTriangle, CheckCircle, FileCheck, Sliders, Network } from 'lucide-react';

export default function PartnerEnclaveView() {
  const [decimationRatio, setDecimationRatio] = useState(0.25);
  const [clayMode, setClayMode] = useState(true);
  const [lockStatus, setLockStatus] = useState('UNLOCKED');
  const [promotionHistory, setPromotionHistory] = useState([
    {
      id: 1,
      deliverable: 'contractor_environment_prop.usda',
      stage: 'openlore://stages/main_production.usda',
      td: 'lead_td',
      status: 'PROMOTED',
      polycount: 24500,
      timestamp: '2026-09-14 09:15:00 UTC',
    },
  ]);

  const lintResults = {
    deliverable: './quarantine/vendor_alpha_fighter_v3.usda',
    passed: true,
    total_polycount: 42800,
    max_polycount_ceiling: 500000,
    hierarchy_errors: [],
    polycount_violations: [],
    namespace_violations: [],
  };

  const handlePromote = () => {
    setLockStatus('LOCKED (TD Optimistic Lock Acquired)');
    setTimeout(() => {
      setPromotionHistory((prev) => [
        {
          id: Date.now(),
          deliverable: 'vendor_alpha_fighter_v3.usda',
          stage: 'openlore://stages/main_production.usda',
          td: 'alice_supervising_td',
          status: 'PROMOTED',
          polycount: 42800,
          timestamp: new Date().toISOString().replace('T', ' ').slice(0, 19) + ' UTC',
        },
        ...prev,
      ]);
      setLockStatus('UNLOCKED (Sublayer Appended & Lock Released)');
    }, 800);
  };

  return (
    <div className="flex-1 p-6 overflow-y-auto max-w-7xl mx-auto w-full space-y-6">
      {/* Header Banner */}
      <div className="flex items-center justify-between bg-neutral-900/60 p-4 rounded-xl border border-neutral-800">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-semibold text-neutral-100">Partner Enclave Isolation & Ingestion</h2>
            <span className="flex items-center gap-1 text-[11px] font-mono text-indigo-400 bg-indigo-950/60 border border-indigo-800 px-2 py-0.5 rounded-full">
              <Network className="w-3 h-3" /> eBPF Zero-Egress Kernel Active
            </span>
          </div>
          <p className="text-xs text-neutral-400 mt-1">
            Outbound IP decimation/clay proxying and inbound quarantined linting with TD optimistic concurrency promotion gates.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Outbound IP Decimation Pipeline */}
        <div className="bg-neutral-900/60 p-5 rounded-xl border border-neutral-800 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-300 flex items-center gap-2">
            <Sliders className="w-4 h-4 text-indigo-400" /> Outbound IP Sanitization & Decimation
          </h3>
          <p className="text-xs text-neutral-400">
            Pre-export pipeline protecting proprietary production meshes by automatically decimating geometry and stripping shader networks before vendor delivery.
          </p>

          <div className="bg-neutral-950 p-4 rounded-lg border border-neutral-800 space-y-3 font-mono text-xs">
            <div>
              <div className="flex justify-between text-neutral-300 mb-1">
                <span>Mesh Decimation Ratio:</span>
                <span className="text-indigo-400 font-bold">{(decimationRatio * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.01"
                max="1.0"
                step="0.01"
                value={decimationRatio}
                onChange={(e) => setDecimationRatio(parseFloat(e.target.value))}
                className="w-full accent-indigo-500 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-neutral-500 mt-1">
                <span>1% (Aggressive Proxy)</span>
                <span>50% (Balanced)</span>
                <span>100% (Full Geometry)</span>
              </div>
            </div>

            {/* Quick Presets */}
            <div className="flex items-center gap-1.5 pt-1">
              <span className="text-[10px] text-neutral-500 mr-1">Presets:</span>
              {[
                { label: '10%', val: 0.10, desc: 'Ultra-Light Proxy' },
                { label: '25%', val: 0.25, desc: 'Standard Review' },
                { label: '50%', val: 0.50, desc: 'Balanced Layout' },
                { label: '75%', val: 0.75, desc: 'High-Res Preview' },
                { label: '100%', val: 1.00, desc: 'Full Mesh Fidelity' },
              ].map((p) => (
                <button
                  key={p.label}
                  onClick={() => setDecimationRatio(p.val)}
                  className={`px-2 py-0.5 rounded text-[10px] transition-all cursor-pointer ${
                    Math.abs(decimationRatio - p.val) < 0.01
                      ? 'bg-indigo-600 text-white font-semibold shadow-sm'
                      : 'bg-neutral-900 hover:bg-neutral-800 text-neutral-300 border border-neutral-800'
                  }`}
                  title={`${p.desc} (${(p.val * 100).toFixed(0)}%)`}
                >
                  {p.label}
                </button>
              ))}
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-neutral-800/80">
              <span className="text-neutral-400">Neutral Clay Shader Substitution:</span>
              <button
                onClick={() => setClayMode(!clayMode)}
                className={`px-3 py-1 rounded text-xs font-semibold cursor-pointer transition-colors ${
                  clayMode ? 'bg-emerald-950 border border-emerald-700 text-emerald-400' : 'bg-neutral-800 text-neutral-400'
                }`}
              >
                {clayMode ? 'ENABLED (RGB: 0.7, 0.7, 0.7)' : 'DISABLED'}
              </button>
            </div>

            <div className="pt-2 border-t border-neutral-800/80 text-[11px] text-neutral-400 flex items-center justify-between">
              <span>Estimated Outbound Faces:</span>
              <span className="text-indigo-300 font-bold font-mono">
                {Math.round(120000 * decimationRatio).toLocaleString()} / 120,000 faces ({decimationRatio < 1.0 ? `-${Math.round((1 - decimationRatio) * 100)}% reduced` : 'original mesh'})
              </span>
            </div>

            <div className="pt-2 border-t border-neutral-800/80 text-[11px] text-neutral-500">
              Stripped Attributes: <span className="text-neutral-400">openlore:pointCacheHash, openlore:assetHash, openlore:royaltyPercentage</span>
            </div>
          </div>
        </div>

        {/* Inbound Quarantined Pre-Flight Linter */}
        <div className="bg-neutral-900/60 p-5 rounded-xl border border-neutral-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-300 flex items-center gap-2">
              <FileCheck className="w-4 h-4 text-emerald-400" /> Inbound Quarantine Pre-Flight Linter
            </h3>
            <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950 border border-emerald-800 px-2 py-0.5 rounded flex items-center gap-1">
              <CheckCircle className="w-3 h-3" /> Linting PASSED
            </span>
          </div>

          <div className="bg-neutral-950 p-4 rounded-lg border border-neutral-800 font-mono text-xs space-y-2.5">
            <div>
              <span className="text-neutral-500 text-[10px]">Quarantined Deliverable:</span>
              <div className="text-neutral-200 truncate">{lintResults.deliverable}</div>
            </div>
            <div className="grid grid-cols-2 gap-2 pt-2 border-t border-neutral-800/80">
              <div>
                <span className="text-neutral-500 text-[10px]">Total Polycount:</span>
                <div className="text-emerald-400 font-bold">{lintResults.total_polycount.toLocaleString()} faces</div>
              </div>
              <div>
                <span className="text-neutral-500 text-[10px]">Maximum Ceiling:</span>
                <div className="text-neutral-400">{lintResults.max_polycount_ceiling.toLocaleString()} faces</div>
              </div>
            </div>
            <div className="pt-2 border-t border-neutral-800/80 text-[11px] text-neutral-400 space-y-1">
              <div className="flex items-center gap-1.5 text-emerald-400">
                <CheckCircle className="w-3.5 h-3.5" /> Root Hierarchy: Approved (/World, /Root)
              </div>
              <div className="flex items-center gap-1.5 text-emerald-400">
                <CheckCircle className="w-3.5 h-3.5" /> Prim Naming Rules: Compliant (Studio Regex)
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 1-Click TD Promotion Gate */}
      <div className="bg-neutral-900/60 p-5 rounded-xl border border-neutral-800">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-neutral-100">Technical Director (TD) One-Click Promotion Gate</h3>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-neutral-950 border border-neutral-800 text-neutral-400 flex items-center gap-1">
                {lockStatus.includes('LOCKED') ? <Lock className="w-3 h-3 text-amber-400" /> : <Unlock className="w-3 h-3 text-emerald-400" />}
                {lockStatus}
              </span>
            </div>
            <p className="text-xs text-neutral-400 mt-1">
              Atomically acquires an optimistic lock token, confirms SHACL lore continuity, and appends the deliverable to the production USD sublayer stack.
            </p>
          </div>

          <button
            onClick={handlePromote}
            className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shadow-lg transition-all flex items-center gap-2 whitespace-nowrap cursor-pointer"
          >
            <ShieldCheck className="w-4 h-4" /> 1-Click Promote Deliverable
          </button>
        </div>

        {/* Promotion History Ledger */}
        <div className="mt-4 pt-4 border-t border-neutral-800">
          <h4 className="text-[11px] font-mono uppercase tracking-wider text-neutral-500 mb-2">Recent Stage Promotions</h4>
          <div className="space-y-1.5 text-xs font-mono">
            {promotionHistory.map((h) => (
              <div key={h.id} className="bg-neutral-950 p-2.5 rounded-lg border border-neutral-800/80 flex items-center justify-between">
                <div>
                  <span className="text-indigo-400 font-medium">{h.deliverable}</span>
                  <span className="text-neutral-500 mx-2">&rarr;</span>
                  <span className="text-neutral-300">{h.stage}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-[11px] text-neutral-500">TD: {h.td}</span>
                  <span className="text-[10px] text-emerald-400 bg-emerald-950/60 border border-emerald-800 px-2 py-0.5 rounded">
                    {h.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
