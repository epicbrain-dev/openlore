import React, { useState } from 'react';
import { apiUrl } from '../utils/api';
import { Wifi, WifiOff, RefreshCw, Cpu, Activity, Send, CheckCircle2, Clock } from 'lucide-react';

export default function CollaborationView() {
  const [isOnline, setIsOnline] = useState(true);
  const [shadowBufferedCount, setShadowBufferedCount] = useState(0);
  const [camX, setCamX] = useState(25.0);
  const [camY, setCamY] = useState(10.0);
  const [camZ, setCamZ] = useState(5.0);

  const [vectorClocks, setVectorClocks] = useState({
    studio_london: 14,
    studio_la: 9,
    studio_tokyo: 6,
  });

  const [auditLog, setAuditLog] = useState([
    { id: 1, studio: 'studio_london', attr: '/World/Camera.xformOp:translate', val: '[25.0, 10.0, 5.0]', status: 'CONVERGED' },
    { id: 2, studio: 'studio_la', attr: '/World/Villain.xformOp:translate', val: '[-50.0, 0.0, 20.0]', status: 'CONVERGED' },
    { id: 3, studio: 'studio_tokyo', attr: '/World/Environment/Lighting.inputs:intensity', val: '2500.0', status: 'CONVERGED' },
  ]);

  const handleToggleOnline = async () => {
    const nextOnline = !isOnline;
    setIsOnline(nextOnline);
    try {
      await fetch(apiUrl('/api/daemon/sever'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sever: !nextOnline }),
      });
    } catch (e) {
      console.error('Sever daemon error:', e);
    }
    if (!isOnline) {
      // Reconnecting -> flush shadow buffer!
      if (shadowBufferedCount > 0) {
        setVectorClocks((prev) => ({ ...prev, studio_london: prev.studio_london + shadowBufferedCount }));
        setShadowBufferedCount(0);
      }
    }
  };

  const handleBroadcastEdit = async () => {
    try {
      await fetch(apiUrl('/api/daemon/edit'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prim_path: '/World/Camera',
          attribute_name: 'xformOp:translate',
          value: [camX, camY, camZ],
        }),
      });
    } catch (e) {
      console.error('Broadcast edit error:', e);
    }

    if (!isOnline) {
      setShadowBufferedCount((prev) => prev + 1);
    } else {
      setVectorClocks((prev) => ({ ...prev, studio_london: prev.studio_london + 1 }));
      setAuditLog((prev) => [
        {
          id: Date.now(),
          studio: 'studio_london',
          attr: '/World/Camera.xformOp:translate',
          val: `[${camX.toFixed(1)}, ${camY.toFixed(1)}, ${camZ.toFixed(1)}]`,
          status: 'CONVERGED',
        },
        ...prev.slice(0, 5),
      ]);
    }
  };

  return (
    <div className="flex-1 p-6 overflow-y-auto max-w-7xl mx-auto w-full space-y-6">
      {/* Header Banner */}
      <div className="flex items-center justify-between bg-neutral-900/60 p-4 rounded-xl border border-neutral-800">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-base font-semibold text-neutral-100">Distributed Multi-Studio Collaboration</h2>
            <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-medium border ${
              isOnline
                ? 'bg-emerald-950/60 border-emerald-700/60 text-emerald-400'
                : 'bg-rose-950/60 border-rose-700/60 text-rose-400 animate-pulse'
            }`}>
              {isOnline ? <Wifi className="w-3.5 h-3.5" /> : <WifiOff className="w-3.5 h-3.5" />}
              {isOnline ? 'ONLINE (Kafka Event Stream Active)' : 'OFFLINE (Shadow Buffering Local Edits)'}
            </div>
          </div>
          <p className="text-xs text-neutral-400 mt-1">
            Deterministic causal conflict resolution via Vector Clocks and Sparse CRDT LWW registers with offline shadow resilience.
          </p>
        </div>

        {/* Network Severance Simulator */}
        <button
          onClick={handleToggleOnline}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold shadow-md transition-all cursor-pointer ${
            isOnline
              ? 'bg-rose-600 hover:bg-rose-500 text-white'
              : 'bg-emerald-600 hover:bg-emerald-500 text-white'
          }`}
        >
          {isOnline ? (
            <>
              <WifiOff className="w-4 h-4" /> Sever Studio Connection
            </>
          ) : (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" /> Restore & Flush Shadow Buffer ({shadowBufferedCount})
            </>
          )}
        </button>
      </div>

      {/* Studios & Vector Clocks Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { id: 'studio_london', name: 'Studio London (LED Volume)', loc: 'London, UK', clock: vectorClocks.studio_london, color: 'text-indigo-400', role: 'Camera Operator' },
          { id: 'studio_la', name: 'Studio Los Angeles (Unreal)', loc: 'Los Angeles, USA', clock: vectorClocks.studio_la, color: 'text-purple-400', role: 'Level Layout TD' },
          { id: 'studio_tokyo', name: 'Studio Tokyo (Lookdev)', loc: 'Tokyo, Japan', clock: vectorClocks.studio_tokyo, color: 'text-sky-400', role: 'Lighting Lead' },
        ].map((s) => (
          <div key={s.id} className="bg-neutral-900/60 p-4 rounded-xl border border-neutral-800">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-neutral-200">{s.name}</span>
              <span className="text-[10px] text-neutral-400 font-mono">{s.loc}</span>
            </div>
            <div className="text-xs text-neutral-400 mb-3">{s.role}</div>
            <div className="bg-neutral-950 p-2.5 rounded-lg border border-neutral-800 flex items-center justify-between text-xs font-mono">
              <span className="text-neutral-400 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-neutral-500" /> Vector Clock:
              </span>
              <span className={`font-bold ${s.color}`}>T={s.clock}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Interactive Transform Broadcasting & Shadow Buffer */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Transform Broadcaster */}
        <div className="bg-neutral-900/60 p-5 rounded-xl border border-neutral-800">
          <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-300 mb-4 flex items-center gap-2">
            <Activity className="w-4 h-4 text-indigo-400" /> Live Scene Transform Broadcaster (CRDT LWW)
          </h3>
          <div className="space-y-4 font-mono text-xs">
            <div>
              <div className="flex justify-between text-neutral-300 mb-1">
                <span>Camera X Translation:</span>
                <span className="text-indigo-400 font-semibold">{camX.toFixed(1)} m</span>
              </div>
              <input
                type="range"
                min="0"
                max="50"
                step="0.5"
                value={camX}
                onChange={(e) => setCamX(parseFloat(e.target.value))}
                className="w-full accent-indigo-500"
              />
            </div>
            <div>
              <div className="flex justify-between text-neutral-300 mb-1">
                <span>Camera Y Translation (Elevation):</span>
                <span className="text-indigo-400 font-semibold">{camY.toFixed(1)} m</span>
              </div>
              <input
                type="range"
                min="0"
                max="30"
                step="0.5"
                value={camY}
                onChange={(e) => setCamY(parseFloat(e.target.value))}
                className="w-full accent-indigo-500"
              />
            </div>
            <div>
              <div className="flex justify-between text-neutral-300 mb-1">
                <span>Camera Z Translation (Depth):</span>
                <span className="text-indigo-400 font-semibold">{camZ.toFixed(1)} m</span>
              </div>
              <input
                type="range"
                min="0"
                max="30"
                step="0.5"
                value={camZ}
                onChange={(e) => setCamZ(parseFloat(e.target.value))}
                className="w-full accent-indigo-500"
              />
            </div>

            <button
              onClick={handleBroadcastEdit}
              className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-semibold flex items-center justify-center gap-2 shadow transition-all cursor-pointer"
            >
              <Send className="w-4 h-4" />
              {isOnline ? 'Record Collaborative Edit (Broadcast over Kafka)' : 'Record Collaborative Edit (Buffer in Shadow Storage)'}
            </button>
          </div>
        </div>

        {/* Shadow Buffer & Causal Audit Stream */}
        <div className="bg-neutral-900/60 p-5 rounded-xl border border-neutral-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-300 flex items-center gap-2">
                <Cpu className="w-4 h-4 text-emerald-400" /> Causal Replication Audit Stream
              </h3>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                shadowBufferedCount > 0 ? 'bg-amber-950/60 border-amber-800 text-amber-300' : 'bg-neutral-950 border-neutral-800 text-neutral-400'
              }`}>
                Shadow Buffered: {shadowBufferedCount}
              </span>
            </div>

            <div className="space-y-2">
              {auditLog.map((log) => (
                <div key={log.id} className="bg-neutral-950 p-2.5 rounded-lg border border-neutral-800/80 text-xs font-mono flex items-center justify-between">
                  <div>
                    <span className="text-indigo-400 font-medium">[{log.studio}]</span>{' '}
                    <span className="text-neutral-300">{log.attr}</span>
                    <div className="text-[11px] text-neutral-500">Value: {log.val}</div>
                  </div>
                  <span className="flex items-center gap-1 text-[10px] text-emerald-400 bg-emerald-950/40 border border-emerald-900 px-2 py-0.5 rounded">
                    <CheckCircle2 className="w-3 h-3" /> {log.status}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-neutral-800 text-[11px] text-neutral-400 font-mono">
            Payload size strictly enforced &lt; 64 KB per mutation to preserve sub-millisecond line speeds.
          </div>
        </div>
      </div>

      {/* Unreal Engine 5 Live Link Virtual Production Bridge Panel */}
      <div className="bg-neutral-900/60 p-5 rounded-xl border border-neutral-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center font-bold text-indigo-400 text-xs">
              UE5
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-semibold text-neutral-200">Unreal Engine 5 Live Link Bridge</h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-700 text-emerald-400">
                  DUPLEX ACTIVE
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-neutral-950 border border-neutral-800 text-neutral-400">
                  UDP 127.0.0.1:11111 @ 60 FPS
                </span>
              </div>
              <p className="text-xs text-neutral-400 mt-0.5">
                Real-time bi-directional telemetry synchronizing OpenUSD CRDT mutations with Unreal Engine Live Link viewports and in-camera VFX tracking.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                // Simulate an inbound camera packet from an on-stage virtual camera tracker
                const newX = parseFloat((Math.random() * 10 + 20).toFixed(1));
                const newY = parseFloat((Math.random() * 5 + 8).toFixed(1));
                const newZ = parseFloat((Math.random() * 2 + 4).toFixed(1));
                setCamX(newX);
                setCamY(newY);
                setCamZ(newZ);
                setVectorClocks((prev) => ({ ...prev, studio_london: prev.studio_london + 1 }));
                setAuditLog((prev) => [
                  {
                    id: Date.now(),
                    studio: 'UE5-VP-STAGE-01',
                    attr: '/World/CineCamera.xformOp:translate',
                    val: `[${newX}, ${newY}, ${newZ}]`,
                    status: 'CONVERGED (INBOUND)',
                  },
                  ...prev.slice(0, 5),
                ]);
              }}
              className="px-3 py-1.5 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 border border-neutral-700 text-xs font-medium rounded-lg flex items-center gap-1.5 transition-all cursor-pointer"
            >
              <Activity className="w-3.5 h-3.5 text-indigo-400" />
              Simulate Inbound UE5 Telemetry
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 border-t border-neutral-800 text-xs">
          {/* Channel 1: CineCamera */}
          <div className="bg-neutral-950 p-3 rounded-lg border border-neutral-800/80 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-neutral-200">/World/CineCamera</span>
              <span className="text-[10px] font-mono text-indigo-400 bg-indigo-950/60 px-1.5 py-0.5 rounded border border-indigo-900">
                Camera Role
              </span>
            </div>
            <div className="text-[11px] text-neutral-400 font-mono">
              Live Link Subject: <span className="text-neutral-200">Camera_StageA</span>
            </div>
            <div className="text-[10px] text-neutral-500 font-mono">
              Coord: Right-Handed (M) &rarr; Left-Handed (CM, Z-Up)
            </div>
          </div>

          {/* Channel 2: Hero Character */}
          <div className="bg-neutral-950 p-3 rounded-lg border border-neutral-800/80 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-neutral-200">/World/Hero</span>
              <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/60 px-1.5 py-0.5 rounded border border-cyan-900">
                Transform Role
              </span>
            </div>
            <div className="text-[11px] text-neutral-400 font-mono">
              Live Link Subject: <span className="text-neutral-200">Hero_Character</span>
            </div>
            <div className="text-[10px] text-neutral-500 font-mono">
              Pose: UsdSkel Dual-Rig Variants
            </div>
          </div>

          {/* Channel 3: Virtual LED Volume */}
          <div className="bg-neutral-950 p-3 rounded-lg border border-neutral-800/80 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-neutral-200">/World/Stage_LED</span>
              <span className="text-[10px] font-mono text-amber-400 bg-amber-950/60 px-1.5 py-0.5 rounded border border-amber-900">
                Stage Bounds
              </span>
            </div>
            <div className="text-[11px] text-neutral-400 font-mono">
              Live Link Subject: <span className="text-neutral-200">LED_Volume</span>
            </div>
            <div className="text-[10px] text-neutral-500 font-mono">
              ICVFX 270&deg; Volume Display Matrix
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between pt-2 border-t border-neutral-800/60 text-[11px] font-mono text-neutral-400">
          <div>Export plugin to project: <code className="text-indigo-300">openlore livelink export-plugin --output-dir ./Plugins/OpenLoreLiveLink</code></div>
          <div className="text-emerald-400 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
            60 FPS Zero-Copy Broadcast Active
          </div>
        </div>
      </div>
    </div>
  );
}
