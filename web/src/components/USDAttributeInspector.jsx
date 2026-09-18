import React, { useState } from 'react';
import {
  Sliders,
  Box,
  Film,
  Gamepad2,
  Cpu,
  ShieldCheck,
  FileCode,
  Sparkles,
  Layers,
  Palette,
} from 'lucide-react';

export default function USDAttributeInspector({
  primPath = '/World/Characters/HeroArmor',
  primType = 'Mesh',
  rigMode = 'cinematic_cache',
  onRigModeChange,
  transforms: externalTransforms,
  onTransformChange: externalOnTransformChange,
}) {
  const [modelLod, setModelLod] = useState('LOD0_Hero');
  const [displayColor, setDisplayColor] = useState('ACEScg_Default');
  const [internalTransforms, setInternalTransforms] = useState({
    tx: 0.0,
    ty: 1.25,
    tz: -3.4,
    rx: 0.0,
    ry: 24.5,
    rz: 0.0,
    sx: 1.0,
    sy: 1.0,
    sz: 1.0,
  });

  const transforms = externalTransforms || internalTransforms;

  const handleTransformChange = (key, val) => {
    const num = parseFloat(val);
    const updatedVal = isNaN(num) ? 0.0 : num;
    if (externalOnTransformChange) {
      externalOnTransformChange(key, updatedVal);
    } else {
      setInternalTransforms((prev) => ({ ...prev, [key]: updatedVal }));
    }
  };

  const shortName = primPath.split('/').pop() || primPath;

  return (
    <div className="w-64 lg:w-72 xl:w-80 bg-neutral-900/90 border-l border-neutral-800 flex flex-col shrink-0 h-full overflow-y-auto select-none font-mono text-xs min-w-0">
      {/* Header */}
      <div className="p-2.5 border-b border-neutral-800/80 bg-neutral-950/60 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <Sliders className="w-4 h-4 text-amber-400 shrink-0" />
          <h3 className="font-bold text-neutral-200 uppercase tracking-wider truncate">
            USD ATTRIBUTES
          </h3>
        </div>
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-950/80 border border-amber-500/40 text-amber-300 shrink-0">
          CHANNEL BOX
        </span>
      </div>

      {/* Prim Header Summary */}
      <div className="p-3 border-b border-neutral-800/60 bg-neutral-900/40 flex flex-col gap-1">
        <div className="flex items-center justify-between">
          <span className="text-neutral-400 text-[11px]">Selected Prim:</span>
          <span className="px-1.5 py-0.5 rounded bg-neutral-800 text-neutral-300 text-[10px] font-semibold">
            {primType || 'UsdGeomMesh'}
          </span>
        </div>
        <div className="font-bold text-neutral-100 truncate text-[12px]" title={primPath}>
          {shortName}
        </div>
        <div className="text-[10px] text-neutral-500 truncate" title={primPath}>
          {primPath}
        </div>
      </div>

      <div className="p-3 flex flex-col gap-4">
        {/* Section 1: Transform Matrix (Channel Box) */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between text-[11px] font-semibold text-neutral-300 border-b border-neutral-800/80 pb-1">
            <span>TRANSFORM MATRIX</span>
            <span className="text-[9px] text-neutral-500">World Space</span>
          </div>

          {/* Translate X, Y, Z */}
          <div className="flex items-center gap-1">
            <span className="w-8 text-[10px] text-neutral-400">Trans</span>
            <div className="flex-1 grid grid-cols-3 gap-1">
              <div className="flex items-center bg-neutral-950 border border-neutral-800 rounded px-1.5 py-0.5">
                <span className="text-[9px] text-rose-400 font-bold mr-1">X</span>
                <input
                  type="number"
                  step="0.1"
                  value={transforms.tx}
                  onChange={(e) => handleTransformChange('tx', e.target.value)}
                  className="w-full bg-transparent text-[11px] text-neutral-200 focus:outline-none"
                />
              </div>
              <div className="flex items-center bg-neutral-950 border border-neutral-800 rounded px-1.5 py-0.5">
                <span className="text-[9px] text-emerald-400 font-bold mr-1">Y</span>
                <input
                  type="number"
                  step="0.1"
                  value={transforms.ty}
                  onChange={(e) => handleTransformChange('ty', e.target.value)}
                  className="w-full bg-transparent text-[11px] text-neutral-200 focus:outline-none"
                />
              </div>
              <div className="flex items-center bg-neutral-950 border border-neutral-800 rounded px-1.5 py-0.5">
                <span className="text-[9px] text-sky-400 font-bold mr-1">Z</span>
                <input
                  type="number"
                  step="0.1"
                  value={transforms.tz}
                  onChange={(e) => handleTransformChange('tz', e.target.value)}
                  className="w-full bg-transparent text-[11px] text-neutral-200 focus:outline-none"
                />
              </div>
            </div>
          </div>

          {/* Rotate X, Y, Z */}
          <div className="flex items-center gap-1">
            <span className="w-8 text-[10px] text-neutral-400">Rot</span>
            <div className="flex-1 grid grid-cols-3 gap-1">
              <div className="flex items-center bg-neutral-950 border border-neutral-800 rounded px-1.5 py-0.5">
                <span className="text-[9px] text-rose-400 font-bold mr-1">X</span>
                <input
                  type="number"
                  step="1.0"
                  value={transforms.rx}
                  onChange={(e) => handleTransformChange('rx', e.target.value)}
                  className="w-full bg-transparent text-[11px] text-neutral-200 focus:outline-none"
                />
              </div>
              <div className="flex items-center bg-neutral-950 border border-neutral-800 rounded px-1.5 py-0.5">
                <span className="text-[9px] text-emerald-400 font-bold mr-1">Y</span>
                <input
                  type="number"
                  step="1.0"
                  value={transforms.ry}
                  onChange={(e) => handleTransformChange('ry', e.target.value)}
                  className="w-full bg-transparent text-[11px] text-neutral-200 focus:outline-none"
                />
              </div>
              <div className="flex items-center bg-neutral-950 border border-neutral-800 rounded px-1.5 py-0.5">
                <span className="text-[9px] text-sky-400 font-bold mr-1">Z</span>
                <input
                  type="number"
                  step="1.0"
                  value={transforms.rz}
                  onChange={(e) => handleTransformChange('rz', e.target.value)}
                  className="w-full bg-transparent text-[11px] text-neutral-200 focus:outline-none"
                />
              </div>
            </div>
          </div>

          {/* Scale X, Y, Z */}
          <div className="flex items-center gap-1">
            <span className="w-8 text-[10px] text-neutral-400">Scale</span>
            <div className="flex-1 grid grid-cols-3 gap-1">
              <div className="flex items-center bg-neutral-950 border border-neutral-800 rounded px-1.5 py-0.5">
                <span className="text-[9px] text-rose-400 font-bold mr-1">X</span>
                <input
                  type="number"
                  step="0.05"
                  value={transforms.sx}
                  onChange={(e) => handleTransformChange('sx', e.target.value)}
                  className="w-full bg-transparent text-[11px] text-neutral-200 focus:outline-none"
                />
              </div>
              <div className="flex items-center bg-neutral-950 border border-neutral-800 rounded px-1.5 py-0.5">
                <span className="text-[9px] text-emerald-400 font-bold mr-1">Y</span>
                <input
                  type="number"
                  step="0.05"
                  value={transforms.sy}
                  onChange={(e) => handleTransformChange('sy', e.target.value)}
                  className="w-full bg-transparent text-[11px] text-neutral-200 focus:outline-none"
                />
              </div>
              <div className="flex items-center bg-neutral-950 border border-neutral-800 rounded px-1.5 py-0.5">
                <span className="text-[9px] text-sky-400 font-bold mr-1">Z</span>
                <input
                  type="number"
                  step="0.05"
                  value={transforms.sz}
                  onChange={(e) => handleTransformChange('sz', e.target.value)}
                  className="w-full bg-transparent text-[11px] text-neutral-200 focus:outline-none"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: OpenUSD VariantSets */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between text-[11px] font-semibold text-neutral-300 border-b border-neutral-800/80 pb-1">
            <span>VARIANT SETS</span>
            <span className="text-[9px] text-indigo-400 font-mono">OpenUSD 24.11</span>
          </div>

          {/* rigMode Variant */}
          <div className="flex flex-col gap-1">
            <span className="text-[10px] text-neutral-400">VariantSet: rigMode</span>
            <div className="grid grid-cols-2 gap-1 bg-neutral-950 p-1 rounded border border-neutral-800">
              <button
                onClick={() => onRigModeChange && onRigModeChange('cinematic_cache')}
                className={`flex items-center justify-center gap-1 py-1 rounded text-[10px] font-semibold transition-all cursor-pointer ${
                  rigMode === 'cinematic_cache'
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm'
                    : 'text-neutral-400 hover:text-neutral-200'
                }`}
              >
                <Film className="w-3 h-3" />
                cinematic
              </button>
              <button
                onClick={() => onRigModeChange && onRigModeChange('game_collision')}
                className={`flex items-center justify-center gap-1 py-1 rounded text-[10px] font-semibold transition-all cursor-pointer ${
                  rigMode === 'game_collision'
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm'
                    : 'text-neutral-400 hover:text-neutral-200'
                }`}
              >
                <Gamepad2 className="w-3 h-3" />
                collision
              </button>
            </div>
          </div>

          {/* model_lod Variant */}
          <div className="flex flex-col gap-1">
            <span className="text-[10px] text-neutral-400">VariantSet: model_lod</span>
            <select
              value={modelLod}
              onChange={(e) => setModelLod(e.target.value)}
              className="bg-neutral-950 border border-neutral-800 text-neutral-200 rounded px-2 py-1 text-[11px] focus:outline-none focus:border-indigo-500"
            >
              <option value="LOD0_Hero">LOD0_Hero (84,200 polys)</option>
              <option value="LOD1_Crowd">LOD1_Crowd (12,400 polys)</option>
              <option value="LOD2_Proxy">LOD2_Proxy (1,800 bounding)</option>
            </select>
          </div>
        </div>

        {/* Section 3: MaterialX Shader Bindings */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between text-[11px] font-semibold text-neutral-300 border-b border-neutral-800/80 pb-1">
            <span className="flex items-center gap-1">
              <Palette className="w-3.5 h-3.5 text-purple-400" />
              MATERIALX BINDINGS
            </span>
            <span className="text-[9px] text-emerald-400">ACEScg PBR</span>
          </div>

          <div className="bg-neutral-950/70 p-2 rounded border border-neutral-800/80 flex flex-col gap-1.5">
            <div className="flex items-center justify-between">
              <span className="text-neutral-400 text-[10px]">Surface Shader:</span>
              <span className="text-purple-300 text-[10px] font-semibold truncate max-w-[140px]">
                ND_openlore_pbr
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-neutral-400 text-[10px]">Base Color:</span>
              <span className="text-neutral-300 text-[10px] font-mono">#b8860b (Gold)</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-neutral-400 text-[10px]">Metallic / Roughness:</span>
              <span className="text-neutral-300 text-[10px] font-mono">0.85 / 0.22</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-neutral-400 text-[10px]">Normal Map:</span>
              <span className="text-emerald-400 text-[10px] font-mono">tex_normal_4k.exr</span>
            </div>
          </div>
        </div>

        {/* Section 4: OpenLore Provenance & OPA Licensing */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between text-[11px] font-semibold text-neutral-300 border-b border-neutral-800/80 pb-1">
            <span className="flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-sky-400" />
              PROVENANCE & LICENSING
            </span>
            <span className="text-[9px] px-1 py-0.2 rounded bg-emerald-950 text-emerald-300 border border-emerald-500/40">
              APPROVED
            </span>
          </div>

          <div className="bg-neutral-950/70 p-2 rounded border border-neutral-800/80 flex flex-col gap-1 text-[10px]">
            <div className="flex items-center justify-between">
              <span className="text-neutral-500">BLAKE3 CAS:</span>
              <span className="text-neutral-300 font-mono">9a4f21e87c0...</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-neutral-500">Author:</span>
              <span className="text-neutral-300">Elena Rostova (Lead)</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-neutral-500">Downstream Export:</span>
              <span className="text-emerald-400">UE5 + Maya Authorized</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
