import React, { useState, useRef } from 'react';
import StageViewportView from './views/StageViewportView';
import AnimationScenegraphView from './views/AnimationScenegraphView';
import NarrativeLoreView from './views/NarrativeLoreView';
import CollaborationView from './views/CollaborationView';
import PartnerEnclaveView from './views/PartnerEnclaveView';
import ProvenanceLedgerView from './views/ProvenanceLedgerView';
import CompilationGridView from './views/CompilationGridView';
import LookdevShadingView from './views/LookdevShadingView';
import VFXTransportTimeline from './components/VFXTransportTimeline';
import ShotProductionTracker from './components/ShotProductionTracker';

import {
  Box,
  Film,
  Layers,
  GitBranch,
  ShieldCheck,
  Package,
  HardDrive,
  Radio,
  Server,
  FolderOpen,
  Monitor,
  CheckCircle2,
  Tv,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  Check,
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('staging');
  const [activeStudio, setActiveStudio] = useState('studio_london');
  const [selectedStage, setSelectedStage] = useState('openlore://stages/sq042_sh0020_hero.usda');
  const [activeShot, setActiveShot] = useState('SQ042_SH0020');
  const [currentFrame, setCurrentFrame] = useState(1001);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showMoreMenu, setShowMoreMenu] = useState(false);
  const navRef = useRef(null);
  const menuRef = useRef(null);

  const scrollNav = (direction) => {
    if (!navRef.current) return;
    navRef.current.scrollBy({ left: direction * 200, behavior: 'smooth' });
  };

  const isDesktop = typeof window !== 'undefined' && Boolean(window.openloreDesktop?.isDesktop);
  const isMacDesktop = isDesktop && window.openloreDesktop?.platform === 'darwin';

  React.useEffect(() => {
    if (!window.openloreDesktop?.onStageOpened) return;
    const unsubStage = window.openloreDesktop.onStageOpened((path) => {
      setSelectedStage(path);
      setActiveTab('staging');
    });
    return unsubStage;
  }, []);

  const handleOpenStage = async () => {
    if (!window.openloreDesktop?.openFileDialog) return;
    try {
      const res = await window.openloreDesktop.openFileDialog({
        title: 'Open OpenUSD Stage',
        filters: [
          { name: 'USD Files (*.usda, *.usdc, *.usd)', extensions: ['usda', 'usdc', 'usd'] },
          { name: 'All Files', extensions: ['*'] },
        ],
      });
      if (!res.canceled && res.filePaths?.[0]) {
        setSelectedStage(res.filePaths[0]);
      }
    } catch (e) {
      console.error('Failed to open stage dialog:', e);
    }
  };

  const handleSelectShot = (shotCode) => {
    setActiveShot(shotCode);
    setSelectedStage(`openlore://stages/${shotCode.toLowerCase()}_hero.usda`);
    setActiveTab('staging');
  };

  const tabs = [
    { id: 'staging', label: '3D Layout & Staging', icon: Box, badge: 'USD 24.11', shortcut: '1' },
    { id: 'anim', label: 'Animation & Scenegraph', icon: Film, badge: '24 FPS', shortcut: '2' },
    { id: 'shots', label: 'Shot Review', icon: Layers, badge: 'ShotGrid', shortcut: '3' },
    { id: 'lookdev', label: 'Lookdev & Shading', icon: Sparkles, badge: 'MaterialX', shortcut: '4' },
    { id: 'collab', label: 'Multi-Studio Sync', icon: Radio, badge: 'CRDT', shortcut: '5' },
    { id: 'farm', label: 'Render Farm & Grid', icon: Package, badge: 'Deadline', shortcut: '6' },
    { id: 'lore', label: 'Narrative Multiverse', icon: GitBranch, badge: 'SHACL', shortcut: '7' },
    { id: 'ledger', label: 'Provenance Ledger', icon: ShieldCheck, badge: 'BLAKE3', shortcut: '8' },
    { id: 'partner', label: 'Partner Enclave', icon: HardDrive, badge: 'Cleanroom', shortcut: '9' },
  ];

  // Auto-scroll active tab into view whenever activeTab changes
  React.useEffect(() => {
    const el = document.getElementById(`nav-tab-${activeTab}`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    }
  }, [activeTab]);

  // Keyboard shortcuts Alt+1 through Alt+9 for instant workspace switching
  React.useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.altKey && !e.ctrlKey && !e.metaKey && e.key >= '1' && e.key <= '9') {
        const idx = parseInt(e.key, 10) - 1;
        if (tabs[idx]) {
          e.preventDefault();
          setActiveTab(tabs[idx].id);
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Close Workspaces menu when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setShowMoreMenu(false);
      }
    };
    if (showMoreMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showMoreMenu]);

  const showTransport = activeTab === 'staging' || activeTab === 'anim';

  return (
    <div className="flex flex-col h-screen w-screen bg-neutral-950 text-neutral-100 overflow-hidden font-sans select-none min-h-0 min-w-0">
      {/* Top VFX Production Pipeline Bar */}
      <header
        className={`h-12 sm:h-14 bg-neutral-900/95 backdrop-blur-md border-b border-neutral-800 px-3 flex items-center justify-between z-30 shrink-0 min-w-0 gap-2 ${
          isMacDesktop ? 'pl-20 app-drag' : ''
        }`}
        style={{ WebkitAppRegion: isMacDesktop ? 'drag' : undefined }}
      >
        {/* Left: Studio Brand & Pipeline Context Breadcrumb */}
        <div
          className="flex items-center gap-2 sm:gap-3 min-w-0 app-no-drag"
          style={{ WebkitAppRegion: 'no-drag' }}
        >
          <div className="flex items-center gap-2 pr-2 sm:pr-3 border-r border-neutral-800 shrink-0">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-amber-500 via-indigo-600 to-purple-600 p-0.5 flex items-center justify-center shadow-md shrink-0">
              <div className="w-full h-full bg-neutral-950 rounded-[6px] flex items-center justify-center">
                <span className="text-sm">🌌</span>
              </div>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-xs tracking-tight text-white">OpenLore</span>
              <span className="text-[10px] text-amber-400 font-mono font-medium px-1 rounded bg-amber-950/60 border border-amber-500/30 hidden sm:inline">
                STUDIO
              </span>
            </div>
          </div>

          {/* VFX Shot Context Breadcrumb */}
          <div className="hidden md:flex items-center gap-1.5 text-xs font-mono min-w-0 truncate">
            <span className="text-neutral-500 hidden 2xl:inline">SHOW:</span>
            <span className="text-neutral-300 font-semibold hidden 2xl:inline">DUNE-PART-TWO</span>
            <ChevronRight className="w-3 h-3 text-neutral-600 hidden 2xl:inline" />
            <span className="text-neutral-500 hidden xl:inline">SEQ:</span>
            <span className="text-neutral-300 font-semibold hidden xl:inline">SQ042</span>
            <ChevronRight className="w-3 h-3 text-neutral-600 hidden xl:inline" />
            <span className="text-neutral-500">SHOT:</span>
            <span className="text-amber-300 font-bold bg-neutral-900 px-1.5 py-0.5 rounded border border-neutral-800 shrink-0">
              {activeShot}
            </span>
            <ChevronRight className="w-3 h-3 text-neutral-600 hidden lg:inline" />
            <span className="text-indigo-400 text-[11px] font-semibold hidden lg:inline truncate">ANIMATION</span>
          </div>
        </div>

        {/* Center: Live DCC Bridges Status */}
        <div
          className="hidden xl:flex items-center gap-2 bg-neutral-950 px-2.5 py-1 rounded border border-neutral-800 text-[11px] font-mono shrink-0 app-no-drag"
          style={{ WebkitAppRegion: 'no-drag' }}
        >
          <div className="flex items-center gap-1.5 text-neutral-300">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span>MAYA</span>
          </div>
          <span className="text-neutral-700">&bull;</span>
          <div className="flex items-center gap-1.5 text-neutral-300">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span>HOUDINI</span>
          </div>
          <span className="text-neutral-700">&bull;</span>
          <div className="flex items-center gap-1.5 text-neutral-300">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
            <span>UE5 LIVELINK</span>
          </div>
          <span className="text-neutral-700">&bull;</span>
          <div className="flex items-center gap-1.5 text-neutral-400">
            <span className="w-1.5 h-1.5 rounded-full bg-neutral-600" />
            <span>BLENDER</span>
          </div>
        </div>

        {/* Right: Color Management & Native Desktop Actions */}
        <div
          className="flex items-center gap-1.5 sm:gap-2 shrink-0 app-no-drag"
          style={{ WebkitAppRegion: 'no-drag' }}
        >
          {/* OCIO Tag */}
          <div className="hidden sm:flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-neutral-950 border border-neutral-800 text-neutral-300 shrink-0">
            <span className="text-neutral-500">OCIO:</span>
            <span className="text-sky-300 font-semibold">ACEScg</span>
          </div>

          {/* Desktop Native Open Stage Button */}
          {isDesktop && (
            <button
              onClick={handleOpenStage}
              className="flex items-center gap-1.5 bg-neutral-800 hover:bg-neutral-700 border border-neutral-700 hover:border-amber-500/50 text-neutral-200 hover:text-white px-2 py-1 rounded text-xs font-mono transition-all cursor-pointer shadow-sm shrink-0"
              title="Open OpenUSD Stage file (*.usda, *.usdc, *.usd)"
            >
              <FolderOpen className="w-3.5 h-3.5 text-amber-400" />
              <span className="hidden md:inline">Open Stage...</span>
            </button>
          )}

          {/* Active Node Switcher */}
          <select
            value={activeStudio}
            onChange={(e) => setActiveStudio(e.target.value)}
            className="bg-neutral-950 border border-neutral-800 text-neutral-300 rounded px-2 py-1 text-xs font-mono focus:outline-none focus:border-amber-500 max-w-[130px] sm:max-w-[180px] truncate shrink-0 cursor-pointer"
          >
            <option value="studio_london">Studio London</option>
            <option value="studio_la">Studio LA (Unreal)</option>
            <option value="studio_tokyo">Studio Tokyo</option>
          </select>
        </div>
      </header>

      {/* VFX Workspace Navigation Bar - Scrollable & Never Obscured */}
      <nav
        className="h-10 bg-neutral-900/90 border-b border-neutral-800 px-2 flex items-center justify-between shrink-0 font-mono text-xs z-20 relative select-none app-no-drag"
        style={{ WebkitAppRegion: 'no-drag' }}
        role="tablist"
        aria-label="VFX Workspaces"
      >
        {/* Left Scroll Chevron */}
        <button
          onClick={() => scrollNav(-1)}
          className="p-1.5 rounded text-neutral-400 hover:text-white hover:bg-neutral-800 transition-colors shrink-0 mr-1 cursor-pointer focus:outline-none"
          title="Scroll workspaces left"
          aria-label="Scroll workspaces left"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>

        {/* Scrollable Tabs Track */}
        <div
          ref={navRef}
          className="flex-1 flex items-center gap-1.5 overflow-x-auto no-scrollbar scroll-smooth py-1 px-1 min-w-0"
        >
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                id={`nav-tab-${tab.id}`}
                key={tab.id}
                role="tab"
                aria-selected={isActive}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs transition-all whitespace-nowrap cursor-pointer shrink-0 font-medium ${
                  isActive
                    ? 'bg-neutral-800 text-amber-300 border border-neutral-700 shadow-sm ring-1 ring-amber-500/25'
                    : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800/60 border border-transparent'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-amber-400' : 'text-neutral-400'}`} />
                <span className="font-semibold tracking-tight">{tab.label}</span>
                <span
                  className={`text-[9px] px-1 py-0.2 rounded font-mono ${
                    isActive
                      ? 'bg-amber-950/90 text-amber-200 border border-amber-500/40'
                      : 'bg-neutral-950/80 text-neutral-500 border border-neutral-800/80'
                  }`}
                >
                  {tab.badge}
                </span>
              </button>
            );
          })}
        </div>

        {/* Right Scroll Chevron */}
        <button
          onClick={() => scrollNav(1)}
          className="p-1.5 rounded text-neutral-400 hover:text-white hover:bg-neutral-800 transition-colors shrink-0 ml-1 cursor-pointer focus:outline-none"
          title="Scroll workspaces right"
          aria-label="Scroll workspaces right"
        >
          <ChevronRight className="w-4 h-4" />
        </button>

        {/* Workspaces (9) Dropdown - 100% Accessible on Any Resolution */}
        <div className="relative shrink-0 ml-2 border-l border-neutral-800 pl-2" ref={menuRef}>
          <button
            onClick={() => setShowMoreMenu((prev) => !prev)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs transition-colors cursor-pointer border ${
              showMoreMenu
                ? 'bg-neutral-800 text-amber-300 border-amber-500/50'
                : 'bg-neutral-950 hover:bg-neutral-800 text-neutral-300 border-neutral-800'
            }`}
            title="Access any workspace directly (Alt+1..9)"
          >
            <Layers className="w-3.5 h-3.5 text-amber-400" />
            <span className="hidden sm:inline font-semibold">Workspaces</span>
            <span className="text-[10px] text-neutral-500 font-mono">({tabs.length})</span>
            <ChevronDown
              className={`w-3 h-3 transition-transform ${showMoreMenu ? 'rotate-180 text-amber-400' : 'text-neutral-400'}`}
            />
          </button>

          {/* Floating Workspace Quick Selector Dropdown */}
          {showMoreMenu && (
            <div className="absolute right-0 top-full mt-1.5 w-72 bg-neutral-900 border border-neutral-700 rounded-lg shadow-2xl py-1.5 z-50 overflow-hidden font-sans">
              <div className="px-3 py-1.5 border-b border-neutral-800 flex items-center justify-between text-[11px] text-neutral-400 font-mono">
                <span className="font-semibold text-neutral-200">OPENLORE WORKSPACES</span>
                <span>Alt + [1-9]</span>
              </div>
              <div className="max-h-[380px] overflow-y-auto py-1">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => {
                        setActiveTab(tab.id);
                        setShowMoreMenu(false);
                      }}
                      className={`w-full flex items-center justify-between px-3 py-2 text-xs text-left transition-colors cursor-pointer ${
                        isActive
                          ? 'bg-neutral-800 text-amber-300 font-bold'
                          : 'text-neutral-300 hover:bg-neutral-800/70 hover:text-white'
                      }`}
                    >
                      <div className="flex items-center gap-2.5 min-w-0">
                        <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-amber-400' : 'text-neutral-400'}`} />
                        <span className="truncate">{tab.label}</span>
                      </div>
                      <div className="flex items-center gap-2 shrink-0 ml-2">
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-neutral-950 border border-neutral-800 text-neutral-400 font-mono">
                          {tab.badge}
                        </span>
                        <span className="text-[10px] text-neutral-500 font-mono w-4 text-right">
                          ⌥{tab.shortcut}
                        </span>
                        {isActive && <Check className="w-3.5 h-3.5 text-amber-400 ml-1" />}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </nav>

      {/* Main Workspace Body */}
      <main className="flex-1 flex overflow-hidden min-h-0 min-w-0 w-full">
        {activeTab === 'staging' && (
          <StageViewportView stageUri={selectedStage} currentFrame={currentFrame} />
        )}
        {activeTab === 'anim' && (
          <AnimationScenegraphView
            stageUri={selectedStage}
            currentFrame={currentFrame}
            onFrameChange={setCurrentFrame}
          />
        )}
        {activeTab === 'shots' && (
          <ShotProductionTracker onSelectShot={handleSelectShot} activeShotCode={activeShot} />
        )}
        {activeTab === 'lookdev' && <LookdevShadingView />}
        {activeTab === 'collab' && <CollaborationView />}
        {activeTab === 'farm' && <CompilationGridView />}
        {activeTab === 'lore' && <NarrativeLoreView />}
        {activeTab === 'ledger' && <ProvenanceLedgerView />}
        {activeTab === 'partner' && <PartnerEnclaveView />}
      </main>

      {/* Docked Bottom Transport Timeline for Animators & VFX artists */}
      {showTransport && (
        <VFXTransportTimeline
          startFrame={1001}
          endFrame={1150}
          currentFrame={currentFrame}
          onFrameChange={setCurrentFrame}
          isPlaying={isPlaying}
          onTogglePlay={() => setIsPlaying((p) => !p)}
          fps={24.0}
        />
      )}
    </div>
  );
}
