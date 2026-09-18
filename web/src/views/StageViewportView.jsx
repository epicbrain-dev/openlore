import React, { useState } from 'react';
import ThreeViewport from '../components/ThreeViewport';
import USDOutliner from '../components/USDOutliner';
import USDAttributeInspector from '../components/USDAttributeInspector';
import { parseUSDA, getDemoUSDA } from '../utils/usdParser';
import {
  Layers,
  Sliders,
  Camera,
  Maximize2,
  Minimize2,
  Tv,
  Film,
  Sparkles,
  Eye,
} from 'lucide-react';

export default function StageViewportView({
  stageUri = 'openlore://stages/hero_scene.usda',
  currentFrame = 1042,
}) {
  const [rigMode, setRigMode] = useState('cinematic_cache');
  const [selectedPrimPath, setSelectedPrimPath] = useState('/World/Characters/HeroArmor');
  const [showOutliner, setShowOutliner] = useState(true);
  const [showInspector, setShowInspector] = useState(true);
  const [shadingMode, setShadingMode] = useState('usd_preview'); // 'usd_preview' | 'wireframe' | 'clay'
  const [hiddenPrims, setHiddenPrims] = useState({});
  const [transforms, setTransforms] = useState({
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
  const [stage] = useState(() => parseUSDA(getDemoUSDA()));

  const handleToggleVisibility = (path) => {
    setHiddenPrims((prev) => ({ ...prev, [path]: !prev[path] }));
  };

  const handleTransformChange = (key, val) => {
    setTransforms((prev) => ({ ...prev, [key]: val }));
  };

  const prims = stage.getAllPrims();
  const activePrim = stage.getPrim(selectedPrimPath) || prims[0];

  return (
    <div className="flex-1 flex overflow-hidden h-full bg-neutral-950 font-sans">
      {/* Left: USD Scenegraph Outliner */}
      {showOutliner && (
        <USDOutliner
          prims={prims}
          selectedPrimPath={selectedPrimPath}
          onSelectPrim={setSelectedPrimPath}
          stageUri={stageUri}
          hiddenPrims={hiddenPrims}
          onToggleVisibility={handleToggleVisibility}
        />
      )}

      {/* Center: 3D Viewport with DCC HUD Overlays */}
      <div className="flex-1 flex flex-col min-w-0 h-full relative overflow-hidden bg-neutral-950">
        {/* Top Viewport Floating HUD Header */}
        <div className="h-10 bg-neutral-900/80 backdrop-blur-md border-b border-neutral-800/80 px-3 flex items-center justify-between z-10 shrink-0 font-mono text-xs min-w-0">
          {/* Left: Camera & Lens Info */}
          <div className="flex items-center gap-2 sm:gap-3 min-w-0">
            <button
              onClick={() => setShowOutliner((v) => !v)}
              className={`p-1 rounded text-xs transition-colors cursor-pointer shrink-0 ${
                showOutliner ? 'text-indigo-400 bg-neutral-800' : 'text-neutral-500 hover:text-neutral-300'
              }`}
              title={showOutliner ? 'Hide Outliner' : 'Show Outliner'}
            >
              <Layers className="w-3.5 h-3.5" />
            </button>

            <div className="flex items-center gap-1.5 text-neutral-300 min-w-0 truncate">
              <Camera className="w-3.5 h-3.5 text-sky-400 shrink-0" />
              <span className="font-semibold text-white truncate">RenderCam_50mm</span>
              <span className="text-neutral-500 text-[11px] hidden sm:inline shrink-0">(f/2.8 • 50mm)</span>
            </div>

            <div className="hidden xl:flex items-center gap-1.5 text-neutral-400 text-[11px] shrink-0">
              <span className="text-neutral-700">&bull;</span>
              <Tv className="w-3.5 h-3.5 text-emerald-400" />
              <span>4096 × 1714 (Scope)</span>
            </div>
          </div>

          {/* Center: Shading Mode Toggles */}
          <div className="flex items-center gap-0.5 bg-neutral-950 p-0.5 rounded border border-neutral-800 text-[10px] shrink-0">
            {[
              { id: 'usd_preview', label: 'USD Shaded' },
              { id: 'wireframe', label: 'Wireframe' },
              { id: 'clay', label: 'Clay' },
            ].map((m) => (
              <button
                key={m.id}
                onClick={() => setShadingMode(m.id)}
                className={`px-1.5 sm:px-2 py-0.5 rounded transition-colors cursor-pointer ${
                  shadingMode === m.id
                    ? 'bg-neutral-800 text-amber-300 font-semibold shadow-sm'
                    : 'text-neutral-400 hover:text-neutral-200'
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>

          {/* Right: Color Management & Inspector Toggle */}
          <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-neutral-950 text-indigo-300 border border-indigo-500/30 hidden sm:inline">
              ACEScg
            </span>

            <button
              onClick={() => setShowInspector((v) => !v)}
              className={`p-1 rounded text-xs transition-colors cursor-pointer ${
                showInspector ? 'text-amber-400 bg-neutral-800' : 'text-neutral-500 hover:text-neutral-300'
              }`}
              title={showInspector ? 'Hide Inspector' : 'Show Inspector'}
            >
              <Sliders className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* 3D Canvas Canvas */}
        <div className="flex-1 relative min-h-0 min-w-0 w-full overflow-hidden">
          <ThreeViewport
            rigMode={rigMode}
            selectedPrim={selectedPrimPath}
            onPrimSelect={setSelectedPrimPath}
            currentFrame={currentFrame}
            shadingMode={shadingMode}
            hiddenPrims={hiddenPrims}
            activeTransforms={transforms}
          />

          <div className="absolute bottom-2 right-2 sm:bottom-3 sm:right-3 pointer-events-none text-[9px] sm:text-[10px] font-mono text-neutral-400 bg-neutral-950/80 px-2 py-0.5 rounded border border-neutral-800/80 backdrop-blur-sm hidden sm:block">
            Tumble: <span className="text-neutral-200">LMB</span> | Pan: <span className="text-neutral-200">MMB</span> | Zoom: <span className="text-neutral-200">Wheel</span>
          </div>
        </div>
      </div>

      {/* Right: USD Attribute Inspector */}
      {showInspector && (
        <USDAttributeInspector
          primPath={selectedPrimPath}
          primType={activePrim ? activePrim.type : 'Mesh'}
          rigMode={rigMode}
          onRigModeChange={setRigMode}
          transforms={transforms}
          onTransformChange={handleTransformChange}
        />
      )}
    </div>
  );
}
