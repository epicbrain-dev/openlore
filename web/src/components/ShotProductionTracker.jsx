import React, { useState } from 'react';
import {
  Film,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Play,
  User,
  Layers,
  ArrowUpRight,
  Filter,
  Eye,
  Server,
  Sparkles,
} from 'lucide-react';

export default function ShotProductionTracker({ onSelectShot, activeShotCode = 'SQ042_SH0020' }) {
  const [filterStatus, setFilterStatus] = useState('ALL');

  const shots = [
    {
      code: 'SQ042_SH0010',
      description: 'Ornithopter aerial approach over shield wall',
      dept: 'Layout / Anim',
      artist: 'Elena Rostova',
      frames: '1001 - 1085',
      totalFrames: 85,
      version: 'v018',
      status: 'APPROVED',
      casHash: '8b7f14e2c...',
      stageUri: 'openlore://stages/sq042_sh0010_hero.usda',
    },
    {
      code: 'SQ042_SH0020',
      description: 'Sandworm seismic breach under hero harvester',
      dept: 'CFX / Lookdev',
      artist: 'Marcus Vance',
      frames: '1001 - 1150',
      totalFrames: 150,
      version: 'v014',
      status: 'IN_PROGRESS',
      casHash: '9a4f21e87...',
      stageUri: 'openlore://stages/sq042_sh0020_hero.usda',
    },
    {
      code: 'SQ042_SH0030',
      description: 'Harvester crew evacuation and tow cable snap',
      dept: 'Lighting / Karma',
      artist: 'Sarah Chen',
      frames: '1001 - 1120',
      totalFrames: 120,
      version: 'v012',
      status: 'IN_REVIEW',
      casHash: '7c3d19b4a...',
      stageUri: 'openlore://stages/sq042_sh0030_hero.usda',
    },
    {
      code: 'SQ042_SH0040',
      description: 'Hero close-up looking through storm visor',
      dept: 'Character FX',
      artist: 'Kenji Sato',
      frames: '1001 - 1060',
      totalFrames: 60,
      version: 'v009',
      status: 'PENDING_CLIENT',
      casHash: '4e2a89f1d...',
      stageUri: 'openlore://stages/sq042_sh0040_hero.usda',
    },
    {
      code: 'SQ042_SH0050',
      description: 'Secondary blast wave engulfing spice refinery',
      dept: 'Crowd / FX',
      artist: 'Maya TD Team',
      frames: '1001 - 1200',
      totalFrames: 200,
      version: 'v004',
      status: 'QUARANTINED',
      casHash: '1a9e84d2c...',
      stageUri: 'openlore://stages/sq042_sh0050_hero.usda',
    },
  ];

  const filteredShots = filterStatus === 'ALL'
    ? shots
    : shots.filter((s) => s.status === filterStatus);

  const getStatusBadge = (status) => {
    switch (status) {
      case 'APPROVED':
        return (
          <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-500/40">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" /> FINAL APPROVED
          </span>
        );
      case 'IN_PROGRESS':
        return (
          <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-indigo-950 text-indigo-300 border border-indigo-500/40">
            <Clock className="w-3 h-3 text-indigo-400" /> IN PROGRESS
          </span>
        );
      case 'IN_REVIEW':
        return (
          <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-950 text-amber-300 border border-amber-500/40">
            <Eye className="w-3 h-3 text-amber-400" /> SUPERVISOR REVIEW
          </span>
        );
      case 'PENDING_CLIENT':
        return (
          <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-sky-950 text-sky-300 border border-sky-500/40">
            <Clock className="w-3 h-3 text-sky-400" /> CLIENT REVIEW
          </span>
        );
      case 'QUARANTINED':
        return (
          <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-rose-950 text-rose-300 border border-rose-500/40">
            <AlertTriangle className="w-3 h-3 text-rose-400" /> QUARANTINE (LINT)
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="flex-1 flex flex-col p-4 overflow-y-auto bg-neutral-950 text-neutral-100 font-sans">
      {/* Producer Summary Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-neutral-900/80 p-4 rounded-xl border border-neutral-800 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <Film className="w-5 h-5 text-amber-400" />
            <h2 className="text-base font-bold text-white tracking-tight">
              Sequence Production Tracker: SQ042
            </h2>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-neutral-800 text-neutral-300">
              Dune: Part Two
            </span>
          </div>
          <p className="text-xs text-neutral-400 mt-1">
            Production deliverable status, OpenUSD stage snapshots, and artist review ledger.
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1 bg-neutral-950 p-1 rounded-lg border border-neutral-800 text-xs font-mono">
          <Filter className="w-3.5 h-3.5 text-neutral-500 ml-1 mr-0.5" />
          {['ALL', 'IN_PROGRESS', 'IN_REVIEW', 'APPROVED'].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`px-2 py-1 rounded transition-colors cursor-pointer ${
                filterStatus === st
                  ? 'bg-neutral-800 text-white font-semibold shadow-sm'
                  : 'text-neutral-400 hover:text-neutral-200'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Production Shot Table */}
      <div className="bg-neutral-900/60 rounded-xl border border-neutral-800 overflow-hidden shadow-xl">
        <table className="w-full text-left border-collapse text-xs font-mono">
          <thead>
            <tr className="bg-neutral-950/80 border-b border-neutral-800 text-neutral-400 text-[11px] uppercase tracking-wider">
              <th className="py-3 px-4">Shot Code</th>
              <th className="py-3 px-4">Description</th>
              <th className="py-3 px-4">Dept / Lead</th>
              <th className="py-3 px-4">Frame Range</th>
              <th className="py-3 px-4">Version / CAS</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-800/60">
            {filteredShots.map((shot) => {
              const isActive = activeShotCode === shot.code;
              return (
                <tr
                  key={shot.code}
                  className={`transition-colors hover:bg-neutral-800/40 ${
                    isActive ? 'bg-indigo-950/20' : ''
                  }`}
                >
                  {/* Shot Code */}
                  <td className="py-3 px-4 font-bold text-white flex items-center gap-2">
                    {isActive && <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />}
                    <span>{shot.code}</span>
                  </td>

                  {/* Description */}
                  <td className="py-3 px-4 text-neutral-300 font-sans text-xs max-w-xs truncate">
                    {shot.description}
                  </td>

                  {/* Dept / Artist */}
                  <td className="py-3 px-4">
                    <div className="text-neutral-200 font-medium flex items-center gap-1.5">
                      <User className="w-3 h-3 text-neutral-500" />
                      {shot.artist}
                    </div>
                    <div className="text-[10px] text-neutral-500">{shot.dept}</div>
                  </td>

                  {/* Frame Range */}
                  <td className="py-3 px-4">
                    <div className="text-amber-300 font-semibold">{shot.frames}</div>
                    <div className="text-[10px] text-neutral-500">({shot.totalFrames} frames)</div>
                  </td>

                  {/* Version & CAS */}
                  <td className="py-3 px-4">
                    <div className="text-indigo-300 font-semibold">{shot.version}</div>
                    <div className="text-[10px] text-neutral-500 truncate max-w-[90px]" title={shot.casHash}>
                      {shot.casHash}
                    </div>
                  </td>

                  {/* Status Badge */}
                  <td className="py-3 px-4">
                    {getStatusBadge(shot.status)}
                  </td>

                  {/* Actions */}
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => onSelectShot && onSelectShot(shot.code)}
                      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-medium transition-all cursor-pointer ${
                        isActive
                          ? 'bg-amber-500 text-neutral-950 font-bold shadow-sm'
                          : 'bg-neutral-800 hover:bg-neutral-700 text-neutral-200 hover:text-white'
                      }`}
                    >
                      <Play className="w-3 h-3 fill-current" />
                      <span>{isActive ? 'Loaded' : 'Load Shot'}</span>
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Sequence Statistics Footer */}
      <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
        <div className="bg-neutral-900/60 p-3 rounded-lg border border-neutral-800">
          <div className="text-neutral-500 text-[10px]">TOTAL SEQUENCE SHOTS</div>
          <div className="text-lg font-bold text-white mt-0.5">5 Shots</div>
        </div>
        <div className="bg-neutral-900/60 p-3 rounded-lg border border-neutral-800">
          <div className="text-neutral-500 text-[10px]">TOTAL RENDER FRAMES</div>
          <div className="text-lg font-bold text-amber-300 mt-0.5">615 Frames</div>
        </div>
        <div className="bg-neutral-900/60 p-3 rounded-lg border border-neutral-800">
          <div className="text-neutral-500 text-[10px]">APPROVAL PROGRESS</div>
          <div className="text-lg font-bold text-emerald-400 mt-0.5">60% Complete</div>
        </div>
        <div className="bg-neutral-900/60 p-3 rounded-lg border border-neutral-800">
          <div className="text-neutral-500 text-[10px]">RENDER ENGINE</div>
          <div className="text-lg font-bold text-sky-300 mt-0.5">Houdini Karma XPU</div>
        </div>
      </div>
    </div>
  );
}
