import React, { useState } from 'react';
import {
  Layers,
  Eye,
  EyeOff,
  Search,
  Box,
  Camera,
  Sun,
  Shield,
  FolderTree,
  Lock,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';

export default function USDOutliner({
  prims = [],
  selectedPrimPath = '/World/Characters/HeroArmor',
  onSelectPrim,
  stageUri = 'openlore://stages/hero_scene.usda',
  hiddenPrims: externalHiddenPrims,
  onToggleVisibility,
}) {
  const [filterText, setFilterText] = useState('');
  const [internalHiddenPrims, setInternalHiddenPrims] = useState({});
  const [lockedPrims, setLockedPrims] = useState({});

  const hiddenPrims = externalHiddenPrims !== undefined ? externalHiddenPrims : internalHiddenPrims;

  const toggleVisibility = (path, e) => {
    e.stopPropagation();
    if (onToggleVisibility) {
      onToggleVisibility(path);
    } else {
      setInternalHiddenPrims((prev) => ({ ...prev, [path]: !prev[path] }));
    }
  };

  const toggleLock = (path, e) => {
    e.stopPropagation();
    setLockedPrims((prev) => ({ ...prev, [path]: !prev[path] }));
  };

  const filteredPrims = prims.filter((p) =>
    p.path.toLowerCase().includes(filterText.toLowerCase()) ||
    (p.type && p.type.toLowerCase().includes(filterText.toLowerCase()))
  );

  const getPrimIcon = (type) => {
    const t = (type || '').toLowerCase();
    if (t.includes('camera')) return <Camera className="w-3.5 h-3.5 text-sky-400" />;
    if (t.includes('light')) return <Sun className="w-3.5 h-3.5 text-amber-400" />;
    if (t.includes('mesh')) return <Box className="w-3.5 h-3.5 text-indigo-400" />;
    if (t.includes('skeleton')) return <Shield className="w-3.5 h-3.5 text-purple-400" />;
    return <FolderTree className="w-3.5 h-3.5 text-neutral-400" />;
  };

  return (
    <div className="w-56 md:w-60 lg:w-64 xl:w-72 bg-neutral-900/90 border-r border-neutral-800 flex flex-col shrink-0 h-full overflow-hidden select-none min-w-0">
      {/* Header */}
      <div className="p-2.5 border-b border-neutral-800/80 bg-neutral-950/60 flex flex-col gap-2 shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-neutral-200">
            <Layers className="w-4 h-4 text-indigo-400 shrink-0" />
            <span className="truncate">USD OUTLINER</span>
          </div>
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-neutral-800 text-neutral-400 shrink-0">
            {prims.length} prims
          </span>
        </div>

        {/* Search Bar */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-neutral-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Filter scenegraph..."
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            className="w-full bg-neutral-950 border border-neutral-800 text-neutral-200 text-xs rounded pl-8 pr-2 py-1 font-mono focus:outline-none focus:border-indigo-500 placeholder:text-neutral-600"
          />
        </div>
      </div>

      {/* Prim Tree List */}
      <div className="flex-1 overflow-y-auto p-1.5 flex flex-col gap-0.5 font-mono text-xs min-h-0">
        {filteredPrims.length === 0 ? (
          <div className="text-center text-neutral-500 py-8 text-xs font-mono">
            No matching prims found
          </div>
        ) : (
          filteredPrims.map((prim) => {
            const isSelected = selectedPrimPath === prim.path;
            const isHidden = hiddenPrims[prim.path];
            const isLocked = lockedPrims[prim.path];
            const depth = (prim.path.match(/\//g) || []).length;
            const shortName = prim.path.split('/').pop() || prim.path;

            return (
              <div
                key={prim.path}
                onClick={() => onSelectPrim && onSelectPrim(prim.path)}
                style={{ paddingLeft: `${Math.max(6, depth * 8)}px` }}
                className={`flex items-center justify-between py-1 px-1.5 rounded group cursor-pointer transition-colors min-w-0 ${
                  isSelected
                    ? 'bg-indigo-600/30 text-indigo-100 border border-indigo-500/40 font-semibold shadow-sm'
                    : 'hover:bg-neutral-800/60 text-neutral-300'
                } ${isHidden ? 'opacity-40' : ''}`}
              >
                {/* Left: Type Icon & Prim Name */}
                <div className="flex items-center gap-1.5 min-w-0 truncate mr-1">
                  {getPrimIcon(prim.type)}
                  <span className="truncate" title={prim.path}>
                    {shortName}
                  </span>
                </div>

                {/* Right: Type Tag & Eye Visibility Toggles */}
                <div className="flex items-center gap-1 opacity-60 group-hover:opacity-100 shrink-0">
                  <span className="text-[9px] px-1 py-0.2 rounded bg-neutral-800/80 text-neutral-400 font-normal">
                    {prim.type || 'Xform'}
                  </span>

                  <button
                    onClick={(e) => toggleLock(prim.path, e)}
                    className={`p-0.5 rounded hover:text-white ${isLocked ? 'text-amber-400 opacity-100' : 'text-neutral-500'}`}
                    title={isLocked ? 'Locked' : 'Unlocked'}
                  >
                    <Lock className="w-3 h-3" />
                  </button>

                  <button
                    onClick={(e) => toggleVisibility(prim.path, e)}
                    className={`p-0.5 rounded hover:text-white ${isHidden ? 'text-neutral-600' : 'text-emerald-400'}`}
                    title={isHidden ? 'Hidden' : 'Visible'}
                  >
                    {isHidden ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Outliner Footer */}
      <div className="p-2 border-t border-neutral-800/80 bg-neutral-950/60 text-[10px] font-mono text-neutral-500 truncate">
        Stage: <span className="text-neutral-400">{stageUri.split('/').pop()}</span>
      </div>
    </div>
  );
}
