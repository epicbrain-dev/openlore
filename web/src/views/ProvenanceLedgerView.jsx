import React, { useState } from 'react';
import { DollarSign, ShieldCheck, CheckCircle2, FileText, Key, Percent, PieChart, Download } from 'lucide-react';

export default function ProvenanceLedgerView() {
  const [manifest] = useState({
    stage_uri: 'openlore://stages/hero_scene.usda',
    total_assets: 4,
    digital_signature: 'd9e4551aa009f27c8b4172c918a598213f56b7cd',
    signature_verified: true,
    allow_export: true,
    unlicensed_prims: [],
    royalty_splits: {
      studio_vfx_london: 18.5,
      studio_game_la: 12.0,
      studio_tokyo: 9.5,
      studio_rigging_montreal: 5.0,
    },
    assets: [
      { path: '/World/Characters/Hero', hash: 'e3b0c44298fc1c14...', partner: 'studio_vfx_london', royalty: '15.0%', status: 'Approved' },
      { path: '/World/Characters/Hero/Armor', hash: '9f86d081884c7d65...', partner: 'studio_vfx_london', royalty: '3.5%', status: 'Approved' },
      { path: '/World/Environment/Props', hash: '4a6b29f081c7e62a...', partner: 'studio_game_la', royalty: '12.0%', status: 'Approved' },
      { path: '/World/Lighting/Rig', hash: '18b52c0098fab124...', partner: 'studio_tokyo', royalty: '9.5%', status: 'Approved' },
    ],
  });

  const totalRoyalties = Object.values(manifest.royalty_splits).reduce((a, b) => a + b, 0);

  const downloadProvenanceManifest = () => {
    const blob = new Blob([JSON.stringify(manifest, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'hero_scene_provenance_manifest.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex-1 p-6 overflow-y-auto max-w-7xl mx-auto w-full space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-neutral-900/60 p-4 rounded-xl border border-neutral-800">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-semibold text-neutral-100">Asset Provenance & OPA Royalty Ledger</h2>
            <span className="flex items-center gap-1 text-[11px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800 px-2 py-0.5 rounded-full">
              <CheckCircle2 className="w-3 h-3" /> OPA Policy Evaluated: PASSED
            </span>
          </div>
          <p className="text-xs text-neutral-400 mt-1">
            Cryptographic HMAC-SHA256 DAG manifests evaluated against Open Policy Agent (OPA) Rego rules for automated royalty accounting.
          </p>
        </div>

        <div className="flex items-center gap-3 self-end sm:self-center">
          <button
            onClick={downloadProvenanceManifest}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg border border-indigo-500 shadow-md transition-all cursor-pointer"
            title="Download cryptographic provenance manifest"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Manifest</span>
          </button>

          {/* Cryptographic Signature Card */}
          <div className="bg-neutral-950 p-3 rounded-lg border border-neutral-800 font-mono text-xs text-right">
            <div className="text-[10px] text-neutral-500 flex items-center justify-end gap-1">
              <Key className="w-3 h-3 text-indigo-400" /> HMAC-SHA256 Manifest Signature
            </div>
            <div className="text-emerald-400 font-bold tracking-wider">{manifest.digital_signature.slice(0, 16)}... [VERIFIED]</div>
          </div>
        </div>
      </div>

      {/* Royalty Distribution Splits & OPA Policy Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Partner Splits Breakdown */}
        <div className="bg-neutral-900/60 p-5 rounded-xl border border-neutral-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-300 flex items-center gap-2">
              <Percent className="w-4 h-4 text-emerald-400" /> Automated Partner Royalty Splits
            </h3>
            <span className="text-xs font-mono text-neutral-400">Total Allocated: <strong className="text-emerald-400">{totalRoyalties}%</strong></span>
          </div>

          <div className="space-y-3 font-mono text-xs">
            {Object.entries(manifest.royalty_splits).map(([partner, pct]) => (
              <div key={partner} className="bg-neutral-950 p-3 rounded-lg border border-neutral-800">
                <div className="flex justify-between text-neutral-200 mb-1.5">
                  <span className="font-semibold">{partner}</span>
                  <span className="text-emerald-400 font-bold">{pct}%</span>
                </div>
                {/* Visual Progress Bar */}
                <div className="w-full h-2 bg-neutral-900 rounded-full overflow-hidden border border-neutral-800">
                  <div
                    className="h-full bg-gradient-to-r from-indigo-500 to-emerald-400 rounded-full"
                    style={{ width: `${pct * 2}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* OPA Policy Compliance */}
        <div className="bg-neutral-900/60 p-5 rounded-xl border border-neutral-800 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-300 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-indigo-400" /> OPA Rego Licensing Audit
          </h3>

          <div className="bg-neutral-950 p-4 rounded-lg border border-neutral-800 font-mono text-xs space-y-3">
            <div className="flex justify-between text-neutral-300">
              <span className="text-neutral-500">Evaluated Policy File:</span>
              <span className="text-indigo-400">schemas/opa/royalties.rego</span>
            </div>
            <div className="flex justify-between text-neutral-300">
              <span className="text-neutral-500">Export Allowance Gate:</span>
              <span className="text-emerald-400 font-bold">APPROVED FOR PRODUCTION</span>
            </div>
            <div className="flex justify-between text-neutral-300">
              <span className="text-neutral-500">Referenced Stage DAG Assets:</span>
              <span className="text-neutral-200">{manifest.total_assets} Prims & Sublayers</span>
            </div>
            <div className="flex justify-between text-neutral-300">
              <span className="text-neutral-500">Unlicensed Assets:</span>
              <span className="text-neutral-400">0 (All licensed)</span>
            </div>
          </div>

          <div className="p-3 bg-indigo-950/20 border border-indigo-900/50 rounded-lg text-xs text-indigo-300 font-mono">
            &bull; Ready for downstream financial ledger dispatch and game engine bundle release.
          </div>
        </div>
      </div>

      {/* Harvested Stage DAG Prims Table */}
      <div className="bg-neutral-900/60 p-5 rounded-xl border border-neutral-800">
        <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-300 mb-3 flex items-center gap-2">
          <FileText className="w-4 h-4 text-indigo-400" /> Harvested OpenUSD Stage DAG Tree
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="border-b border-neutral-800 text-neutral-400">
                <th className="pb-2">Prim Path</th>
                <th className="pb-2">CAS Hash (BLAKE3)</th>
                <th className="pb-2">Partner Studio</th>
                <th className="pb-2">Royalty Share</th>
                <th className="pb-2 text-right">License Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-800/60">
              {manifest.assets.map((a) => (
                <tr key={a.path} className="hover:bg-neutral-950/40">
                  <td className="py-2.5 text-neutral-200 font-medium">{a.path}</td>
                  <td className="py-2.5 text-indigo-400">{a.hash}</td>
                  <td className="py-2.5 text-neutral-300">{a.partner}</td>
                  <td className="py-2.5 text-emerald-400 font-semibold">{a.royalty}</td>
                  <td className="py-2.5 text-right">
                    <span className="text-[10px] text-emerald-400 bg-emerald-950/60 border border-emerald-800 px-2 py-0.5 rounded">
                      {a.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
