import React, { useState } from 'react';
import ThreeViewport from '../components/ThreeViewport';
import { parseUSDA, getDemoUSDA } from '../utils/usdParser';
import { Layers, Box, Film, Gamepad2, ChevronRight, Eye, Sparkles, Cpu } from 'lucide-react';

export default function StageViewportView({ stages = [] }) {
  const [rigMode, setRigMode] = useState('cinematic_cache');
  const [selectedPrimPath, setSelectedPrimPath] = useState('/World/Characters/HeroArmor');
  const [stage] = useState(() => parseUSDA(getDemoUSDA()));

  const prims = stage.getAllPrims();
  const activePrim = stage.getPrim(selectedPrimPath) || prims[0];

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
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all cursor-pointer ${
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
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all cursor-pointer ${
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
          <ThreeViewport
            rigMode={rigMode}
            selectedPrim={selectedPrimPath}
            onPrimSelect={setSelectedPrimPath}
          />
        </div>
      </div>

      {/* Right: USD Prim Scenegraph Inspector */}
      <div className="w-84 flex flex-col gap-4 bg-neutral-900/80 backdrop-blur-md p-4 rounded-xl border border-neutral-800 overflow-y-auto shadow-xl">
        <div>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-400" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-100">
                USD Prim Scenegraph Inspector
              </h3>
            </div>
            <span className="text-[10px] bg-indigo-950/80 border border-indigo-700 text-indigo-300 px-1.5 py-0.5 rounded font-mono flex items-center gap-1">
              <Cpu className="w-3 h-3" /> WASM AST
            </span>
          </div>

          <p className="text-[11px] text-neutral-400 mb-3">
            Interactive OpenUSD stage hierarchy parsed client-side via WebAssembly.
          </p>

          {/* Hierarchy Scenegraph Tree */}
          <div className="flex flex-col gap-1">
            {prims.map((prim) => {
              const isSelected = selectedPrimPath === prim.path;
              const depth = (prim.path.match(/\//g) || []).length;
              return (
                <button
                  key={prim.path}
                  onClick={() => setSelectedPrimPath(prim.path)}
                  style={{ paddingLeft: `${Math.max(8, depth * 12)}px` }}
                  className={`text-left px-2.5 py-2 rounded-lg text-xs font-mono transition-all flex items-center justify-between cursor-pointer ${
                    isSelected
                      ? 'bg-indigo-600/30 border border-indigo-500/60 text-indigo-200 font-semibold shadow-sm'
                      : 'bg-neutral-950/50 hover:bg-neutral-800/60 text-neutral-300 border border-neutral-800/60'
                  }`}
                >
                  <div className="flex items-center gap-1.5 truncate">
                    <ChevronRight className={`w-3 h-3 shrink-0 ${isSelected ? 'text-indigo-400' : 'text-neutral-500'}`} />
                    <span className="truncate">{prim.name}</span>
                  </div>
                  <span className="text-[10px] text-neutral-400 bg-neutral-900 border border-neutral-800 px-1.5 py-0.5 rounded ml-2 whitespace-nowrap">
                    {prim.type}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Selected Prim Details Inspector */}
        {activePrim && (
          <div className="pt-3 border-t border-neutral-800">
            <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-300 mb-2 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              <span>Selected Prim Attributes</span>
            </h3>
            <div className="bg-neutral-950 p-3 rounded-lg border border-neutral-800/80 text-xs font-mono space-y-2.5">
              <div>
                <div className="text-[10px] text-neutral-500">Prim Path</div>
                <div className="text-indigo-300 font-semibold truncate">{activePrim.path}</div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <div className="text-[10px] text-neutral-500">Type</div>
                  <div className="text-neutral-200 font-medium">{activePrim.type}</div>
                </div>
                <div>
                  <div className="text-[10px] text-neutral-500">Rig Variant</div>
                  <div className={rigMode === 'cinematic_cache' ? 'text-amber-400 font-bold' : 'text-emerald-400 font-bold'}>
                    {rigMode}
                  </div>
                </div>
              </div>

              {activePrim.type === 'Mesh' ? (
                <div className="grid grid-cols-2 gap-2 pt-1 border-t border-neutral-900">
                  <div>
                    <div className="text-[10px] text-neutral-500">Vertices (points)</div>
                    <div className="text-emerald-400 font-bold">{activePrim.attributes.points?.length || 0}</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-neutral-500">Face Indices</div>
                    <div className="text-emerald-400 font-bold">{activePrim.attributes.faceVertexIndices?.length || 0}</div>
                  </div>
                </div>
              ) : (
                <div className="pt-1 border-t border-neutral-900">
                  <div className="text-[10px] text-neutral-500">Scenegraph Role</div>
                  <div className="text-xs text-neutral-300 font-medium">
                    {activePrim.type === 'Camera'
                      ? 'Virtual CineCamera Prim (Live Link Stream Target)'
                      : `Transform Grouping (${activePrim.children?.length || 0} sub-prims)`}
                  </div>
                </div>
              )}

              {activePrim.attributes.displayColor && (
                <div className="pt-1 border-t border-neutral-900 flex items-center justify-between">
                  <span className="text-[10px] text-neutral-500">displayColor</span>
                  <div className="flex items-center gap-2">
                    <span
                      className="w-3.5 h-3.5 rounded-full inline-block border border-neutral-600 shadow-sm"
                      style={{
                        backgroundColor: `rgb(${Math.round(activePrim.attributes.displayColor[0] * 255)}, ${Math.round(activePrim.attributes.displayColor[1] * 255)}, ${Math.round(activePrim.attributes.displayColor[2] * 255)})`
                      }}
                    />
                    <span className="text-[10px] text-neutral-400">
                      [{activePrim.attributes.displayColor.map(n => n.toFixed(2)).join(', ')}]
                    </span>
                  </div>
                </div>
              )}

              {activePrim.attributes.extent && (
                <div className="pt-1 border-t border-neutral-900">
                  <div className="text-[10px] text-neutral-500">Bounding Extent</div>
                  <div className="text-[10px] text-neutral-400 truncate">
                    min: ({activePrim.attributes.extent[0]?.join(', ')}) max: ({activePrim.attributes.extent[1]?.join(', ')})
                  </div>
                </div>
              )}

              <div className="pt-1 border-t border-neutral-900">
                <div className="text-[10px] text-neutral-500">CAS Hash (BLAKE3)</div>
                <div className="text-indigo-400 text-[10px] truncate">9f86d081884c7d659a2feaa0c55ad015...</div>
              </div>
            </div>
          </div>
        )}

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
