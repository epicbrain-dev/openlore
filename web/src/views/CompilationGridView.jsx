import React, { useState } from 'react';
import { Play, CheckCircle2, Clock, Layers, Package, Film, Gamepad2, Database, Download } from 'lucide-react';

export default function CompilationGridView() {
  const [selectedTargets, setSelectedTargets] = useState({
    unreal: true,
    unity: true,
    cinematic_cache: true,
  });

  const [activeWorkflow, setActiveWorkflow] = useState(null);
  const [catalogBuilds, setCatalogBuilds] = useState([
    {
      id: 'cat-a8f9c1b2',
      stage_uri: 'openlore://stages/hero_scene.usda',
      build_type: 'game_package_unreal',
      artifact_file: 'HeroAsset_unreal.pak',
      cas_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
      registered_at: '2026-09-14 09:20:15 UTC',
    },
    {
      id: 'cat-d4e5f6a7',
      stage_uri: 'openlore://stages/hero_scene.usda',
      build_type: 'game_package_unity',
      artifact_file: 'HeroAsset_unity.unitypackage',
      cas_hash: '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8',
      registered_at: '2026-09-14 09:20:25 UTC',
    },
    {
      id: 'cat-1a2b3c4d',
      stage_uri: 'openlore://stages/hero_scene.usda',
      build_type: 'cinematic_point_cache',
      artifact_file: 'shot_hero_intro_pointcache.usda',
      cas_hash: '4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a',
      registered_at: '2026-09-14 09:20:35 UTC',
    },
  ]);

  const handleDispatch = async () => {
    setActiveWorkflow({
      id: `workflow-${Math.random().toString(16).slice(2, 10)}`,
      status: 'RUNNING',
      stage: 'openlore://stages/hero_scene.usda',
      steps: [
        { name: 'validate_stage', status: 'COMPLETED' },
        { name: 'compile_unreal_package', status: 'RUNNING' },
        { name: 'compile_unity_package', status: 'PENDING' },
        { name: 'bake_shot_point_cache', status: 'PENDING' },
        { name: 'register_production_catalog', status: 'PENDING' },
      ],
    });

    try {
      const targets = [];
      if (selectedTargets.unreal) targets.push('unreal');
      if (selectedTargets.unity) targets.push('unity');
      if (selectedTargets.cinematic_cache) targets.push('cinematic-cache');
      await fetch('/api/compile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          stage_uri: 'openlore://stages/hero_scene.usda',
          targets: targets.length > 0 ? targets : ['unreal'],
        }),
      });
    } catch (e) {
      console.error('Compilation error:', e);
    }

    setTimeout(() => {
      setActiveWorkflow((prev) => ({
        ...prev,
        status: 'COMPLETED',
        steps: prev.steps.map((s) => ({ ...s, status: 'COMPLETED' })),
      }));

      const newId = `cat-${Math.random().toString(16).slice(2, 10)}`;
      setCatalogBuilds((prev) => [
        {
          id: newId,
          stage_uri: 'openlore://stages/hero_scene.usda',
          build_type: selectedTargets.unreal ? 'game_package_unreal' : selectedTargets.unity ? 'game_package_unity' : 'cinematic_point_cache',
          artifact_file: selectedTargets.unreal ? 'hero_scene_v2_unreal.pak' : selectedTargets.unity ? 'hero_scene_v2_unity.unitypackage' : 'hero_scene_v2_cache.usda',
          cas_hash: '8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4',
          registered_at: new Date().toISOString().replace('T', ' ').slice(0, 19) + ' UTC',
        },
        ...prev,
      ]);
    }, 1200);
  };

  const downloadManifest = (build) => {
    const manifestData = {
      catalog_id: build.id,
      stage_uri: build.stage_uri,
      build_type: build.build_type,
      artifact_file: build.artifact_file,
      cas_hash: build.cas_hash,
      registered_at: build.registered_at,
      provenance: {
        schema_version: '1.0.0',
        format: 'OpenUSD 24.08',
        compiler: 'OpenLore Temporal Worker Grid',
        engine_target: build.build_type.includes('unreal')
          ? 'Unreal Engine 5.4+ (Nanite/Lumen)'
          : build.build_type.includes('unity')
          ? 'Unity 6000.0+ (URP/HDRP)'
          : 'Cinematic USD Point Cache (24 FPS)',
      },
      status: 'APPROVED_FOR_RELEASE',
    };

    const blob = new Blob([JSON.stringify(manifestData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${build.artifact_file}.manifest.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const downloadFullCatalog = () => {
    const catalogData = {
      version: '1.0.0',
      stage_uri: 'openlore://stages/hero_scene.usda',
      total_builds: catalogBuilds.length,
      exported_at: new Date().toISOString(),
      builds: catalogBuilds,
    };
    const blob = new Blob([JSON.stringify(catalogData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'openlore_production_catalog.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex-1 p-6 overflow-y-auto max-w-7xl mx-auto w-full space-y-6">
      {/* Header Banner */}
      <div className="flex items-center justify-between bg-neutral-900/60 p-4 rounded-xl border border-neutral-800">
        <div>
          <h2 className="text-base font-semibold text-neutral-100">Automated Downstream Compilation Grid</h2>
          <p className="text-xs text-neutral-400 mt-1">
            Temporal activity orchestration and Kubernetes Argo Workflow DAGs compiling real-time engine packages and cinematic point caches.
          </p>
        </div>
      </div>

      {/* Grid Submitter & Pipeline Tracker */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Compilation Target Config */}
        <div className="bg-neutral-900/60 p-5 rounded-xl border border-neutral-800 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-300 flex items-center gap-2">
            <Package className="w-4 h-4 text-indigo-400" /> Dispatch Workflow to Container Pool
          </h3>

          <div className="space-y-3 font-mono text-xs">
            <label className="flex items-center justify-between p-3 bg-neutral-950 rounded-lg border border-neutral-800 cursor-pointer hover:border-neutral-700">
              <div className="flex items-center gap-2.5">
                <Gamepad2 className="w-4 h-4 text-indigo-400" />
                <div>
                  <div className="text-neutral-200 font-semibold">Unreal Engine 5.4 Package (.pak)</div>
                  <div className="text-[10px] text-neutral-500">Includes PCD3D_SM6 shaders & PhysicsAsset</div>
                </div>
              </div>
              <input
                type="checkbox"
                checked={selectedTargets.unreal}
                onChange={(e) => setSelectedTargets({ ...selectedTargets, unreal: e.target.checked })}
                className="accent-indigo-500 w-4 h-4"
              />
            </label>

            <label className="flex items-center justify-between p-3 bg-neutral-950 rounded-lg border border-neutral-800 cursor-pointer hover:border-neutral-700">
              <div className="flex items-center gap-2.5">
                <Package className="w-4 h-4 text-purple-400" />
                <div>
                  <div className="text-neutral-200 font-semibold">Unity 6000.0 Package (.unitypackage)</div>
                  <div className="text-[10px] text-neutral-500">URP/HDRP prefabs, materials & scenes</div>
                </div>
              </div>
              <input
                type="checkbox"
                checked={selectedTargets.unity}
                onChange={(e) => setSelectedTargets({ ...selectedTargets, unity: e.target.checked })}
                className="accent-indigo-500 w-4 h-4"
              />
            </label>

            <label className="flex items-center justify-between p-3 bg-neutral-950 rounded-lg border border-neutral-800 cursor-pointer hover:border-neutral-700">
              <div className="flex items-center gap-2.5">
                <Film className="w-4 h-4 text-amber-400" />
                <div>
                  <div className="text-neutral-200 font-semibold">Offline Shot Point Cache (24 FPS .usdc)</div>
                  <div className="text-[10px] text-neutral-500">Time-sampled geometry deformation cache</div>
                </div>
              </div>
              <input
                type="checkbox"
                checked={selectedTargets.cinematic_cache}
                onChange={(e) => setSelectedTargets({ ...selectedTargets, cinematic_cache: e.target.checked })}
                className="accent-indigo-500 w-4 h-4"
              />
            </label>
          </div>

          <button
            onClick={handleDispatch}
            className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-semibold text-xs flex items-center justify-center gap-2 shadow-lg transition-all cursor-pointer"
          >
            <Play className="w-4 h-4 fill-white" /> Dispatch Compilation Pipeline (Temporal / Argo)
          </button>
        </div>

        {/* Live Pipeline Steps Activity Tracker */}
        <div className="bg-neutral-900/60 p-5 rounded-xl border border-neutral-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-300 flex items-center gap-2">
              <Layers className="w-4 h-4 text-emerald-400" /> Live Activity Pipeline Tracker
            </h3>
            {activeWorkflow && (
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                activeWorkflow.status === 'COMPLETED'
                  ? 'bg-emerald-950 border-emerald-800 text-emerald-300'
                  : 'bg-indigo-950 border-indigo-800 text-indigo-300 animate-pulse'
              }`}>
                {activeWorkflow.status}
              </span>
            )}
          </div>

          {activeWorkflow ? (
            <div className="space-y-2 font-mono text-xs">
              {activeWorkflow.steps.map((step) => (
                <div key={step.name} className="p-2.5 bg-neutral-950 rounded-lg border border-neutral-800 flex items-center justify-between">
                  <span className="text-neutral-300">{step.name}</span>
                  <span className={`text-[10px] px-2 py-0.5 rounded ${
                    step.status === 'COMPLETED'
                      ? 'text-emerald-400 bg-emerald-950/60 border border-emerald-800'
                      : step.status === 'RUNNING'
                      ? 'text-amber-400 bg-amber-950/60 border border-amber-800 animate-pulse'
                      : 'text-neutral-500 bg-neutral-900'
                  }`}>
                    {step.status}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center text-xs font-mono text-neutral-500 border border-dashed border-neutral-800 rounded-lg">
              No active compilation workflow running. Click dispatch to launch.
            </div>
          )}
        </div>
      </div>

      {/* Central Production Catalog */}
      <div className="bg-neutral-900/60 p-5 rounded-xl border border-neutral-800">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-300 flex items-center gap-2">
            <Database className="w-4 h-4 text-indigo-400" /> Central Production Catalog Ledger ({catalogBuilds.length})
          </h3>
          <button
            onClick={downloadFullCatalog}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-neutral-800 hover:bg-neutral-700 text-indigo-300 hover:text-indigo-200 rounded-lg border border-neutral-700 hover:border-indigo-500/50 transition-colors cursor-pointer shadow-sm w-fit"
            title="Download full catalog as JSON manifest"
          >
            <Download className="w-3.5 h-3.5 text-indigo-400" />
            <span>Download Full Catalog Manifest</span>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="border-b border-neutral-800 text-neutral-400">
                <th className="pb-2">Catalog ID</th>
                <th className="pb-2">Target Build Type</th>
                <th className="pb-2">Artifact Filename</th>
                <th className="pb-2">CAS Hash (BLAKE3)</th>
                <th className="pb-2">Registered Timestamp</th>
                <th className="pb-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-800/60">
              {catalogBuilds.map((b) => (
                <tr key={b.id} className="hover:bg-neutral-950/40">
                  <td className="py-2.5 text-neutral-400">{b.id}</td>
                  <td className="py-2.5">
                    <span className="text-[11px] font-semibold text-indigo-300 bg-indigo-950/50 px-2 py-0.5 rounded border border-indigo-900/60">
                      {b.build_type}
                    </span>
                  </td>
                  <td className="py-2.5 text-neutral-200 font-medium">{b.artifact_file}</td>
                  <td className="py-2.5 text-neutral-400">{b.cas_hash.slice(0, 16)}...</td>
                  <td className="py-2.5 text-neutral-500">{b.registered_at}</td>
                  <td className="py-2.5 text-right">
                    <button
                      onClick={() => downloadManifest(b)}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-medium bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 hover:text-indigo-100 rounded border border-indigo-500/40 hover:border-indigo-500/80 transition-colors cursor-pointer"
                      title={`Download manifest for ${b.artifact_file}`}
                    >
                      <Download className="w-3 h-3 text-indigo-400" />
                      <span>Download Manifest</span>
                    </button>
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
