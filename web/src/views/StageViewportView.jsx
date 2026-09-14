import React, { useState } from 'react';
import ThreeViewport from '../components/ThreeViewport';
import { Layers, Box, Film, Gamepad2, Eye, ShieldCheck, Database } from 'lucide-react';

export default function StageViewportView({ stages = [] }) {
  const [rigMode, setRigMode] = useState('cinematic_cache');
  const [selectedPrim, setSelectedPrim] = useState('/World/Characters/Hero');

  const primHierarchy = [
    { path: '/World', type: 'Xform', children: 2 },
    { path: '/World/Characters', type: 'Scope', children: 1 },
    { path: '/World/Characters/Hero', type: 'UsdGeom.Mesh', custom: 'DynamicRig', variant: rigMode },
    { path: '/World/Characters/Hero/CollisionCapsule', type: 'UsdGeom.Capsule', custom: 'Physics' },
    { path: '/World/Environment', type: 'Xform', children: 1 },
    { path: '/World/Environment/Soundstage', type: 'UsdGeom.Mesh', custom: 'LED Volume' },
  ];

  return (
    <div className="flex-1 flex gap-4 p-4 overflow-hidden h-[calc(100vh-72px)]">
      {/* Left 3D Viewport Panel */}
      <div className="flex-1 flex flex-col gap-3 min-w-0">
        <div className="flex items-center justify-between bg-neutral-900/60 p-3 rounded-xl border border-neutral-800">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg border border-indigo-500/20">
              <Box className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-neutral-100">Live Stage Composition Viewport</h2>
              <p className="text-xs text-neutral-400 font-mono">openlore://stages/hero_scene.usda</p>
            </div>
          </div>

          {/* Dynamic Dual-Rig Variant Switcher */}
          <div className="flex items-center gap-1 bg-neutral-950 p-1 rounded-lg border border-neutral-800">
            <span className="text-[11px] font-mono text-neutral-400 px-2">VariantSet: rigMode</span>
            <button
              onClick={() => setRigMode('cinematic_cache')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                rigMode === 'cinematic_cache'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm'
                  : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800/60'
              }`}
            >
              <Film className="w-3.5 h-3.5" />
              cinematic_cache
            </button>
            <button
              onClick={() => setRigMode('game_collision')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                rigMode === 'game_collision'
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm'
                  : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800/60'
              }`}
            >
              <Gamepad2 className="w-3.5 h-3.5" />
              game_collision
            </button>
          </div>
        </div>

        {/* 3D Canvas */}
        <div className="flex-1 min-h-0">
          <ThreeViewport rigMode={rigMode} selectedPrim={selectedPrim} onPrimSelect={setSelectedPrim} />
        </div>
      </div>

      {/* Right Scene Hierarchy & Metadata Inspector */}
      <div className="w-80 flex flex-col gap-4 bg-neutral-900/60 p-4 rounded-xl border border-neutral-800 overflow-y-auto">
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Layers className="w-4 h-4 text-indigo-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-300">Prim Hierarchy</h3>
          </div>
          <div className="flex flex-col gap-1">
            {primHierarchy.map((prim) => {
              const isSelected = selectedPrim === prim.path;
              return (
                <button
                  key={prim.path}
                  onClick={() => setSelectedPrim(prim.path)}
                  className={`text-left px-3 py-2 rounded-lg text-xs font-mono transition-all flex items-center justify-between ${
                    isSelected
                      ? 'bg-indigo-600/20 border border-indigo-500/50 text-indigo-200'
                      : 'bg-neutral-950/40 hover:bg-neutral-800/60 text-neutral-300 border border-neutral-800/50'
                  }`}
                >
                  <span className="truncate">{prim.path}</span>
                  <span className="text-[10px] text-neutral-500 bg-neutral-900 px-1.5 py-0.5 rounded ml-2 whitespace-nowrap">
                    {prim.type}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Prim Metadata Inspector */}
        <div className="pt-3 border-t border-neutral-800">
          <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-300 mb-2">Selected Prim Details</h3>
          <div className="bg-neutral-950 p-3 rounded-lg border border-neutral-800/80 text-xs font-mono space-y-2">
            <div>
              <div className="text-[10px] text-neutral-500">Prim Path</div>
              <div className="text-neutral-200 truncate">{selectedPrim}</div>
            </div>
            <div>
              <div className="text-[10px] text-neutral-500">Type</div>
              <div className="text-neutral-300">UsdGeom.Mesh (Polygonal)</div>
            </div>
            <div>
              <div className="text-[10px] text-neutral-500">CAS Binding (BLAKE3)</div>
              <div className="text-indigo-400 text-[11px] truncate">9f86d081884c7d659a2feaa0c55ad015...</div>
            </div>
            <div>
              <div className="text-[10px] text-neutral-500">Active Rig Mode</div>
              <div className={`font-semibold ${rigMode === 'cinematic_cache' ? 'text-amber-400' : 'text-emerald-400'}`}>
                {rigMode}
              </div>
            </div>
            <div>
              <div className="text-[10px] text-neutral-500">MaterialX Graph</div>
              <div className="text-neutral-300">SR_robot_armor.mtlx</div>
            </div>
          </div>
        </div>

        {/* Sublayers Stack */}
        <div className="pt-3 border-t border-neutral-800">
          <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-300 mb-2 flex items-center justify-between">
            <span>Sublayer Stack</span>
            <span className="text-[10px] text-neutral-500 font-normal font-mono">L.I.F.O. Priority</span>
          </h3>
          <div className="space-y-1.5 text-xs font-mono">
            <div className="bg-neutral-950 p-2 rounded border border-neutral-800/70 text-neutral-300">
              <span className="text-indigo-400">0:</span> ./quarantine/promoted_prop.usda
            </div>
            <div className="bg-neutral-950 p-2 rounded border border-neutral-800/70 text-neutral-300">
              <span className="text-indigo-400">1:</span> ./stages/lighting_set.usda
            </div>
            <div className="bg-neutral-950 p-2 rounded border border-neutral-800/70 text-neutral-300">
              <span className="text-indigo-400">2:</span> ./stages/character_base.usda
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
