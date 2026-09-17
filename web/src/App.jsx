import React, { useState } from 'react';
import StageViewportView from './views/StageViewportView';
import NarrativeLoreView from './views/NarrativeLoreView';
import CollaborationView from './views/CollaborationView';
import PartnerEnclaveView from './views/PartnerEnclaveView';
import ProvenanceLedgerView from './views/ProvenanceLedgerView';
import CompilationGridView from './views/CompilationGridView';

import {
  Box,
  GitBranch,
  Activity,
  ShieldCheck,
  FileCheck,
  Package,
  Layers,
  HardDrive,
  Radio,
  Server,
  Zap,
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('viewport');
  const [activeStudio, setActiveStudio] = useState('studio_london');

  const tabs = [
    { id: 'viewport', label: '3D Stage Viewport', icon: Box, badge: 'Live OpenUSD' },
    { id: 'narrative', label: 'Narrative Multiverse', icon: GitBranch, badge: 'SHACL Validated' },
    { id: 'collab', label: 'Studio Collaboration', icon: Activity, badge: 'CRDT Sync' },
    { id: 'partner', label: 'Partner Enclave', icon: ShieldCheck, badge: '1-Click Promotion' },
    { id: 'provenance', label: 'Provenance & OPA', icon: FileCheck, badge: 'Royalties' },
    { id: 'compilation', label: 'Compilation Grid', icon: Package, badge: 'Temporal/Argo' },
  ];

  return (
    <div className="flex flex-col h-screen w-screen bg-neutral-950 text-neutral-100 overflow-hidden font-sans">
      {/* Top Studio Cockpit Navigation Bar */}
      <header className="h-16 bg-neutral-900/90 backdrop-blur-md border-b border-neutral-800/80 px-4 flex items-center justify-between z-30 shrink-0">
        {/* Left: Brand & Tagline */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-600 to-pink-500 p-0.5 shadow-lg shadow-indigo-500/20 flex items-center justify-center">
            <div className="w-full h-full bg-neutral-950 rounded-[10px] flex items-center justify-center">
              <span className="text-lg">🌌</span>
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm font-bold tracking-tight text-white flex items-center gap-1.5">
                OpenLore <span className="text-xs text-indigo-400 font-mono font-medium">Studio Cockpit</span>
              </h1>
              <span className="text-[10px] font-mono px-1.5 py-0.5 bg-neutral-800 text-neutral-400 rounded border border-neutral-700">
                v1.0.2
              </span>
            </div>
            <p className="text-[11px] text-neutral-400 font-normal">Git for 3D worlds, game lore, and Hollywood pipelines</p>
          </div>
        </div>

        {/* Center: System Status Indicators */}
        <div className="hidden xl:flex items-center gap-3 bg-neutral-950/80 px-3 py-1.5 rounded-lg border border-neutral-800 text-xs font-mono">
          <div className="flex items-center gap-1.5 text-neutral-300">
            <HardDrive className="w-3.5 h-3.5 text-indigo-400" />
            <span>CAS:</span>
            <span className="text-emerald-400 font-semibold">BLAKE3</span>
          </div>
          <span className="text-neutral-700">&bull;</span>
          <div className="flex items-center gap-1.5 text-neutral-300">
            <Radio className="w-3.5 h-3.5 text-purple-400" />
            <span>Kafka:</span>
            <span className="text-emerald-400 font-semibold">ONLINE</span>
          </div>
          <span className="text-neutral-700">&bull;</span>
          <div className="flex items-center gap-1.5 text-neutral-300">
            <ShieldCheck className="w-3.5 h-3.5 text-sky-400" />
            <span>OPA:</span>
            <span className="text-emerald-400 font-semibold">ACTIVE</span>
          </div>
          <span className="text-neutral-700">&bull;</span>
          <div className="flex items-center gap-1.5 text-neutral-300">
            <Server className="w-3.5 h-3.5 text-amber-400" />
            <span>Temporal:</span>
            <span className="text-emerald-400 font-semibold">HEALTHY</span>
          </div>
        </div>

        {/* Right: Studio Node Selector */}
        <div className="flex items-center gap-2">
          <div className="text-right hidden sm:block">
            <div className="text-[10px] uppercase font-mono tracking-wider text-neutral-500">Active Node</div>
            <div className="text-xs font-mono font-semibold text-neutral-200">{activeStudio}</div>
          </div>
          <select
            value={activeStudio}
            onChange={(e) => setActiveStudio(e.target.value)}
            className="bg-neutral-900 border border-neutral-800 text-neutral-200 rounded-lg px-2.5 py-1.5 text-xs font-mono focus:outline-none focus:border-indigo-500"
          >
            <option value="studio_london">Studio London (LED Volume)</option>
            <option value="studio_la">Studio Los Angeles (Unreal)</option>
            <option value="studio_tokyo">Studio Tokyo (Lookdev)</option>
          </select>
        </div>
      </header>

      {/* Sub-Header Navigation Tabs */}
      <nav className="bg-neutral-900/40 border-b border-neutral-800/60 px-4 py-2 flex items-center gap-1.5 overflow-x-auto shrink-0">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-medium transition-all whitespace-nowrap cursor-pointer ${
                isActive
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20 font-semibold'
                  : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800/50'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
              <span
                className={`text-[9px] font-mono px-1.5 py-0.2 rounded ${
                  isActive ? 'bg-indigo-800/80 text-indigo-100' : 'bg-neutral-800 text-neutral-400'
                }`}
              >
                {tab.badge}
              </span>
            </button>
          );
        })}
      </nav>

      {/* Main Workspace Body */}
      <main className="flex-1 flex overflow-hidden">
        {activeTab === 'viewport' && <StageViewportView />}
        {activeTab === 'narrative' && <NarrativeLoreView />}
        {activeTab === 'collab' && <CollaborationView />}
        {activeTab === 'partner' && <PartnerEnclaveView />}
        {activeTab === 'provenance' && <ProvenanceLedgerView />}
        {activeTab === 'compilation' && <CompilationGridView />}
      </main>
    </div>
  );
}
