import React, { useState, useEffect, useRef } from 'react';
import * as THREE from 'three';
import {
  Palette,
  Sun,
  Sliders,
  RotateCw,
  Eye,
  Sparkles,
  Layers,
  Tv,
  CheckCircle2,
  RefreshCw,
} from 'lucide-react';

export default function LookdevShadingView() {
  const containerRef = useRef(null);
  const sceneRef = useRef(null);
  const meshRef = useRef(null);
  const keyLightRef = useRef(null);
  const fillLightRef = useRef(null);
  const rimLightRef = useRef(null);

  // MaterialX parameters
  const [baseColor, setBaseColor] = useState('#d4af37'); // Metallic Gold
  const [metallic, setMetallic] = useState(0.85);
  const [roughness, setRoughness] = useState(0.25);
  const [normalScale, setNormalScale] = useState(1.0);
  const [clearcoat, setClearcoat] = useState(0.5);

  // Lighting & Rig presets
  const [lightingPreset, setLightingPreset] = useState('studio'); // 'studio' | 'sunset' | 'led_volume' | 'rim'
  const [colorLut, setColorLut] = useState('ACEScg');
  const [autoRotate, setAutoRotate] = useState(true);
  const [turntableSpeed, setTurntableSpeed] = useState(1.0);

  // Initialize Three.js MaterialX Lookdev Stage
  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;
    const width = container.clientWidth || 800;
    const height = container.clientHeight || 500;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0e0e11);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 100);
    camera.position.set(0, 1.2, 4.5);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // Subtle Lookdev Ground Pedestal
    const pedestalGeo = new THREE.CylinderGeometry(1.6, 1.8, 0.15, 64);
    const pedestalMat = new THREE.MeshStandardMaterial({
      color: 0x1f1f23,
      roughness: 0.8,
      metalness: 0.2,
    });
    const pedestal = new THREE.Mesh(pedestalGeo, pedestalMat);
    pedestal.position.y = -0.75;
    pedestal.receiveShadow = true;
    scene.add(pedestal);

    // Hero Shader Lookdev Asset (Torus Knot + Sphere combination)
    const assetGeo = new THREE.TorusKnotGeometry(0.7, 0.22, 128, 32);
    const assetMat = new THREE.MeshPhysicalMaterial({
      color: new THREE.Color(baseColor),
      metalness: metallic,
      roughness: roughness,
      clearcoat: clearcoat,
      clearcoatRoughness: 0.1,
    });
    const heroAsset = new THREE.Mesh(assetGeo, assetMat);
    heroAsset.position.y = 0.25;
    heroAsset.castShadow = true;
    heroAsset.receiveShadow = true;
    scene.add(heroAsset);
    meshRef.current = heroAsset;

    // Three-point Studio Lighting Rig
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.2);
    scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0xfff5e6, 2.5);
    keyLight.position.set(3, 4, 3);
    keyLight.castShadow = true;
    scene.add(keyLight);
    keyLightRef.current = keyLight;

    const fillLight = new THREE.DirectionalLight(0xe0f2fe, 1.2);
    fillLight.position.set(-3, 2, 2);
    scene.add(fillLight);
    fillLightRef.current = fillLight;

    const rimLight = new THREE.DirectionalLight(0xfae8ff, 3.0);
    rimLight.position.set(0, 3, -4);
    scene.add(rimLight);
    rimLightRef.current = rimLight;

    // Turntable animation loop
    let reqId;
    const animate = () => {
      reqId = requestAnimationFrame(animate);
      if (heroAsset && autoRotate) {
        heroAsset.rotation.y += 0.008 * turntableSpeed;
      }
      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      if (!container || !camera || !renderer) return;
      const w = container.clientWidth || 800;
      const h = container.clientHeight || 500;
      if (w > 0 && h > 0) {
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
      }
    };
    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(container);
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(reqId);
      resizeObserver.disconnect();
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
    };
  }, []);

  // Update Material parameters in real time
  useEffect(() => {
    if (!meshRef.current) return;
    const mat = meshRef.current.material;
    mat.color.set(baseColor);
    mat.metalness = metallic;
    mat.roughness = roughness;
    mat.clearcoat = clearcoat;
    mat.needsUpdate = true;
  }, [baseColor, metallic, roughness, clearcoat]);

  // Update Lighting Presets
  useEffect(() => {
    if (!keyLightRef.current || !fillLightRef.current || !rimLightRef.current) return;
    if (lightingPreset === 'studio') {
      keyLightRef.current.color.set(0xfff5e6);
      keyLightRef.current.intensity = 2.5;
      fillLightRef.current.color.set(0xe0f2fe);
      fillLightRef.current.intensity = 1.2;
      rimLightRef.current.color.set(0xffffff);
      rimLightRef.current.intensity = 3.0;
    } else if (lightingPreset === 'sunset') {
      keyLightRef.current.color.set(0xff7733);
      keyLightRef.current.intensity = 3.5;
      fillLightRef.current.color.set(0x4a154b);
      fillLightRef.current.intensity = 1.8;
      rimLightRef.current.color.set(0xffaa44);
      rimLightRef.current.intensity = 4.0;
    } else if (lightingPreset === 'led_volume') {
      keyLightRef.current.color.set(0x06b6d4);
      keyLightRef.current.intensity = 2.8;
      fillLightRef.current.color.set(0xa855f7);
      fillLightRef.current.intensity = 2.0;
      rimLightRef.current.color.set(0xec4899);
      rimLightRef.current.intensity = 3.5;
    } else if (lightingPreset === 'rim') {
      keyLightRef.current.color.set(0xffffff);
      keyLightRef.current.intensity = 0.5;
      fillLightRef.current.color.set(0x222222);
      fillLightRef.current.intensity = 0.2;
      rimLightRef.current.color.set(0x38bdf8);
      rimLightRef.current.intensity = 6.0;
    }
  }, [lightingPreset]);

  return (
    <div className="flex-1 flex overflow-hidden h-full bg-neutral-950 font-sans select-none">
      {/* 3D Turntable Viewport */}
      <div className="flex-1 flex flex-col min-w-0 h-full relative">
        {/* Floating Top HUD */}
        <div className="h-10 bg-neutral-900/80 backdrop-blur-md border-b border-neutral-800 px-3 flex items-center justify-between z-10 font-mono text-xs">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5 text-white font-bold">
              <Palette className="w-3.5 h-3.5 text-purple-400" />
              MATERIALX LOOKDEV STAGE
            </span>
            <span className="text-neutral-500 text-[11px]">&bull;</span>
            <span className="text-neutral-400 text-[11px]">ND_openlore_pbr_surface</span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-neutral-950 text-indigo-300 border border-indigo-500/30">
              OCIO: {colorLut}
            </span>
            <button
              onClick={() => setAutoRotate((r) => !r)}
              className={`flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono transition-colors cursor-pointer ${
                autoRotate
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                  : 'bg-neutral-900 text-neutral-400 border border-neutral-800'
              }`}
            >
              <RotateCw className={`w-3 h-3 ${autoRotate ? 'animate-spin' : ''}`} />
              Turntable
            </button>
          </div>
        </div>

        {/* 3D Canvas */}
        <div ref={containerRef} className="flex-1 min-h-0 w-full relative" />
      </div>

      {/* Right Shading & Lighting Control Panel */}
      <div className="w-64 lg:w-72 xl:w-80 bg-neutral-900/90 border-l border-neutral-800 flex flex-col shrink-0 h-full overflow-y-auto font-mono text-xs p-3 gap-4 min-w-0">
        {/* Section 1: Lighting Environment Presets */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between text-[11px] font-semibold text-neutral-300 border-b border-neutral-800 pb-1">
            <span className="flex items-center gap-1">
              <Sun className="w-3.5 h-3.5 text-amber-400" />
              LIGHTING RIG PRESET
            </span>
          </div>

          <div className="grid grid-cols-2 gap-1.5">
            {[
              { id: 'studio', label: 'Studio Neutral (5600K)' },
              { id: 'sunset', label: 'Golden Sunset (3200K)' },
              { id: 'led_volume', label: 'Cyberpunk LED Volume' },
              { id: 'rim', label: 'Dramatic Rim Light' },
            ].map((preset) => (
              <button
                key={preset.id}
                onClick={() => setLightingPreset(preset.id)}
                className={`p-2 rounded border text-left transition-all cursor-pointer ${
                  lightingPreset === preset.id
                    ? 'bg-amber-500/10 text-amber-300 border-amber-500/50 font-bold'
                    : 'bg-neutral-950/60 text-neutral-400 border-neutral-800 hover:bg-neutral-800'
                }`}
              >
                <div className="text-[11px]">{preset.label}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Section 2: MaterialX Shader Controls */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between text-[11px] font-semibold text-neutral-300 border-b border-neutral-800 pb-1">
            <span className="flex items-center gap-1">
              <Sliders className="w-3.5 h-3.5 text-purple-400" />
              MATERIALX PBR SHADER
            </span>
          </div>

          {/* Base Color Presets */}
          <div className="flex flex-col gap-1.5">
            <span className="text-[10px] text-neutral-400">Base Color / Albedo:</span>
            <div className="flex items-center gap-2">
              <input
                type="color"
                value={baseColor}
                onChange={(e) => setBaseColor(e.target.value)}
                className="w-8 h-8 rounded border border-neutral-700 bg-transparent cursor-pointer"
              />
              <div className="flex items-center gap-1 flex-1">
                {[
                  { name: 'Gold', val: '#d4af37' },
                  { name: 'Chrome', val: '#e5e7eb' },
                  { name: 'Sand', val: '#c2b280' },
                  { name: 'Carbon', val: '#1c1917' },
                ].map((c) => (
                  <button
                    key={c.name}
                    onClick={() => setBaseColor(c.val)}
                    style={{ backgroundColor: c.val }}
                    className="w-6 h-6 rounded-full border border-neutral-700 hover:scale-110 transition-transform cursor-pointer"
                    title={c.name}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Metallic Slider */}
          <div className="flex flex-col gap-1">
            <div className="flex justify-between text-[10px]">
              <span className="text-neutral-400">Metallic</span>
              <span className="text-amber-300 font-bold">{metallic.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.02"
              value={metallic}
              onChange={(e) => setMetallic(parseFloat(e.target.value))}
              className="accent-amber-500 cursor-pointer"
            />
          </div>

          {/* Roughness Slider */}
          <div className="flex flex-col gap-1">
            <div className="flex justify-between text-[10px]">
              <span className="text-neutral-400">Roughness</span>
              <span className="text-amber-300 font-bold">{roughness.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.02"
              value={roughness}
              onChange={(e) => setRoughness(parseFloat(e.target.value))}
              className="accent-amber-500 cursor-pointer"
            />
          </div>

          {/* Clearcoat Slider */}
          <div className="flex flex-col gap-1">
            <div className="flex justify-between text-[10px]">
              <span className="text-neutral-400">Clearcoat / Gloss</span>
              <span className="text-amber-300 font-bold">{clearcoat.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={clearcoat}
              onChange={(e) => setClearcoat(parseFloat(e.target.value))}
              className="accent-amber-500 cursor-pointer"
            />
          </div>
        </div>

        {/* Section 3: Color Management / OCIO LUT */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between text-[11px] font-semibold text-neutral-300 border-b border-neutral-800 pb-1">
            <span className="flex items-center gap-1">
              <Tv className="w-3.5 h-3.5 text-sky-400" />
              OCIO COLOR DISPLAY
            </span>
          </div>

          <select
            value={colorLut}
            onChange={(e) => setColorLut(e.target.value)}
            className="bg-neutral-950 border border-neutral-800 text-neutral-200 rounded px-2.5 py-1.5 text-xs font-mono focus:outline-none focus:border-amber-500"
          >
            <option value="ACEScg">ACEScg (Scene-Linear HDR)</option>
            <option value="Rec.709">Rec.709 (sRGB Broadcast)</option>
            <option value="DCI-P3">DCI-P3 (Theatrical Cinema)</option>
            <option value="Raw">Raw (Unprocessed Linear)</option>
          </select>
        </div>
      </div>
    </div>
  );
}
