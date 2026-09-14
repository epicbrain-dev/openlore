import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { parseUSDA, buildThreeMeshFromUsdPrim, getDemoUSDA } from '../utils/usdParser';
import { Layers, Box, Cpu, ChevronRight, ChevronDown, CheckCircle, Eye } from 'lucide-react';

export default function ThreeViewport({ rigMode = 'cinematic_cache', onPrimSelect, selectedPrim }) {
  const containerRef = useRef(null);
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const standardGroupRef = useRef(null);
  const usdGroupRef = useRef(null);
  const heroMeshRef = useRef(null);
  const capsuleRef = useRef(null);
  const skeletonRef = useRef(null);
  const reqIdRef = useRef(null);

  const [wsConnected, setWsConnected] = useState(false);
  const [viewportEngine, setViewportEngine] = useState('usd_wasm'); // 'standard' | 'usd_wasm'
  const [parsedStage, setParsedStage] = useState(null);
  const [activeUsdPrim, setActiveUsdPrim] = useState(null);
  const [showInspector, setShowInspector] = useState(true);

  // Initialize Three.js Scene and USD Parser
  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;
    const width = container.clientWidth || 800;
    const height = container.clientHeight || 500;

    // 1. Scene & Camera
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0a0c);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(4, 3, 6);
    camera.lookAt(0, 1, 0);
    cameraRef.current = camera;

    // 2. Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // 3. Grid & Lighting
    const grid = new THREE.GridHelper(14, 28, 0x4f46e5, 0x262626);
    grid.position.y = -0.01;
    scene.add(grid);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0x818cf8, 2.5);
    dirLight.position.set(5, 10, 7);
    dirLight.castShadow = true;
    scene.add(dirLight);

    const rimLight = new THREE.DirectionalLight(0x38bdf8, 1.8);
    rimLight.position.set(-5, 4, -5);
    scene.add(rimLight);

    // -------------------------------------------------------------
    // STANDARD VIEWPORT GROUP (Stylized Procedural Meshes)
    // -------------------------------------------------------------
    const standardGroup = new THREE.Group();
    standardGroupRef.current = standardGroup;
    scene.add(standardGroup);

    // Hero Character Armor Model
    const bodyGeo = new THREE.CylinderGeometry(0.5, 0.35, 1.6, 16);
    const armorMat = new THREE.MeshStandardMaterial({
      color: 0x475569,
      metalness: 0.85,
      roughness: 0.25,
    });
    const heroMesh = new THREE.Mesh(bodyGeo, armorMat);
    heroMesh.position.y = 1.1;
    heroMesh.castShadow = true;
    standardGroup.add(heroMesh);
    heroMeshRef.current = heroMesh;

    // Head
    const headGeo = new THREE.SphereGeometry(0.3, 16, 16);
    const headMat = new THREE.MeshStandardMaterial({ color: 0x64748b, metalness: 0.9, roughness: 0.2 });
    const headMesh = new THREE.Mesh(headGeo, headMat);
    headMesh.position.y = 1.1;
    heroMesh.add(headMesh);

    // Pauldrons
    const pauldronGeo = new THREE.BoxGeometry(0.35, 0.2, 0.4);
    const leftP = new THREE.Mesh(pauldronGeo, armorMat);
    leftP.position.set(-0.65, 0.65, 0);
    heroMesh.add(leftP);
    const rightP = leftP.clone();
    rightP.position.x = 0.65;
    heroMesh.add(rightP);

    // Collision Capsule
    const capGeo = new THREE.CapsuleGeometry(0.65, 1.6, 8, 16);
    const capMat = new THREE.MeshBasicMaterial({ color: 0x22c55e, wireframe: true, transparent: true, opacity: 0.7 });
    const capsule = new THREE.Mesh(capGeo, capMat);
    capsule.position.y = 1.1;
    capsule.visible = false;
    standardGroup.add(capsule);
    capsuleRef.current = capsule;

    // Skeleton Bones
    const skelGroup = new THREE.Group();
    const boneMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b, wireframe: true });
    const rootBone = new THREE.Mesh(new THREE.SphereGeometry(0.1, 8, 8), boneMat);
    rootBone.position.y = 0.2;
    skelGroup.add(rootBone);
    const spineBone = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 1.2), boneMat);
    spineBone.position.y = 0.9;
    skelGroup.add(spineBone);
    skelGroup.visible = false;
    standardGroup.add(skelGroup);
    skeletonRef.current = skelGroup;

    // Virtual Production LED Volume Wall
    const ledCurveGeo = new THREE.CylinderGeometry(8, 8, 4, 32, 1, true, -Math.PI * 0.35, Math.PI * 0.7);
    const ledMat = new THREE.MeshBasicMaterial({
      color: 0x1e1b4b,
      wireframe: true,
      transparent: true,
      opacity: 0.3,
      side: THREE.BackSide,
    });
    const ledWall = new THREE.Mesh(ledCurveGeo, ledMat);
    ledWall.position.set(0, 2, 0);
    standardGroup.add(ledWall);

    // -------------------------------------------------------------
    // USD-WASM HYDRA GROUP (Native USDA Parsed Geometry)
    // -------------------------------------------------------------
    const usdGroup = new THREE.Group();
    usdGroupRef.current = usdGroup;
    scene.add(usdGroup);

    // Parse and populate USD Stage
    const stage = parseUSDA(getDemoUSDA());
    setParsedStage(stage);

    const stagePrims = stage.getAllPrims();
    stagePrims.forEach((prim) => {
      const mesh = buildThreeMeshFromUsdPrim(prim);
      if (mesh) {
        usdGroup.add(mesh);
      }
    });

    if (stagePrims.length > 0) {
      setActiveUsdPrim(stagePrims[0]);
    }

    // Mouse Drag & Orbit Controls
    let isDragging = false;
    let prevMouseX = 0;
    let prevMouseY = 0;
    let azimuth = 0.6;
    let polar = 0.4;
    let radius = 7;

    const updateCameraPos = () => {
      camera.position.x = radius * Math.sin(azimuth) * Math.cos(polar);
      camera.position.y = Math.max(0.5, radius * Math.sin(polar) + 1);
      camera.position.z = radius * Math.cos(azimuth) * Math.cos(polar);
      camera.lookAt(0, 1.1, 0);
    };
    updateCameraPos();

    const onMouseDown = (e) => {
      isDragging = true;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };
    const onMouseMove = (e) => {
      if (!isDragging) return;
      const dx = e.clientX - prevMouseX;
      const dy = e.clientY - prevMouseY;
      azimuth -= dx * 0.008;
      polar = Math.max(0.1, Math.min(Math.PI / 2 - 0.05, polar + dy * 0.008));
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
      updateCameraPos();
    };
    const onMouseUp = () => { isDragging = false; };
    const onWheel = (e) => {
      e.preventDefault();
      radius = Math.max(2.5, Math.min(18, radius + e.deltaY * 0.008));
      updateCameraPos();
    };

    container.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    container.addEventListener('wheel', onWheel, { passive: false });

    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    // Animation Loop
    let clock = new THREE.Clock();
    const animate = () => {
      reqIdRef.current = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      if (heroMeshRef.current) {
        heroMeshRef.current.position.y = 1.1 + Math.sin(elapsed * 2.0) * 0.02;
        heroMeshRef.current.rotation.y = Math.sin(elapsed * 0.4) * 0.05;
      }

      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(reqIdRef.current);
      container.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      container.removeEventListener('wheel', onWheel);
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
    };
  }, []);

  // Toggle Viewport Engine Visibility
  useEffect(() => {
    if (standardGroupRef.current && usdGroupRef.current) {
      if (viewportEngine === 'usd_wasm') {
        usdGroupRef.current.visible = true;
        standardGroupRef.current.visible = false;
      } else {
        usdGroupRef.current.visible = false;
        standardGroupRef.current.visible = true;
      }
    }
  }, [viewportEngine]);

  // Rig Mode Visuals (Standard Mode)
  useEffect(() => {
    if (capsuleRef.current && skeletonRef.current && heroMeshRef.current) {
      if (rigMode === 'game_collision') {
        capsuleRef.current.visible = true;
        skeletonRef.current.visible = true;
        heroMeshRef.current.material.wireframe = true;
        heroMeshRef.current.material.opacity = 0.5;
      } else {
        capsuleRef.current.visible = false;
        skeletonRef.current.visible = false;
        heroMeshRef.current.material.wireframe = false;
        heroMeshRef.current.material.opacity = 1.0;
      }
    }
  }, [rigMode]);

  // WebSocket Telemetry Hook
  useEffect(() => {
    const isHttps = window.location.protocol === 'https:';
    const wsProto = isHttps ? 'wss:' : 'ws:';
    const wsUrl = `${wsProto}//${window.location.host}/ws/live`;
    let ws = null;

    try {
      ws = new WebSocket(wsUrl);
      ws.onopen = () => setWsConnected(true);
      ws.onclose = () => setWsConnected(false);
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'STAGE_MUTATION') {
            if ((msg.prim_path === '/World/Camera' || msg.prim_path === '/World/CineCamera') && cameraRef.current) {
              const val = msg.value;
              if (Array.isArray(val) && val.length >= 3) {
                cameraRef.current.position.x = val[0] * 0.1;
                cameraRef.current.position.y = Math.max(0.5, val[1] * 0.1);
                cameraRef.current.position.z = val[2] * 0.1 + 4.0;
                cameraRef.current.lookAt(0, 1.1, 0);
              }
            } else if (msg.prim_path === '/World/Hero' && heroMeshRef.current) {
              const val = msg.value;
              if (Array.isArray(val) && val.length >= 3) {
                heroMeshRef.current.position.set(val[0], val[1], val[2]);
              }
            }
          }
        } catch (e) {
          // ignore
        }
      };
    } catch (err) {
      setWsConnected(false);
    }

    return () => {
      if (ws) ws.close();
    };
  }, []);

  const handlePrimClick = (prim) => {
    setActiveUsdPrim(prim);
    if (onPrimSelect) onPrimSelect(prim.path);
  };

  return (
    <div className="relative w-full h-full min-h-[460px] bg-neutral-950 rounded-xl overflow-hidden border border-neutral-800 flex">
      {/* 3D WebGL Canvas */}
      <div className="flex-1 relative h-full">
        <div ref={containerRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

        {/* Viewport HUD Overlay */}
        <div className="absolute top-4 left-4 flex flex-col gap-2 pointer-events-none">
          <div className="flex items-center gap-2 bg-neutral-900/85 backdrop-blur-md px-3 py-1.5 rounded-lg border border-neutral-700/60 shadow-lg pointer-events-auto">
            <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`}></span>
            <span className="text-xs font-mono font-medium text-neutral-200">
              {viewportEngine === 'usd_wasm' ? 'USD-WASM Hydra Viewer' : 'WebGL Standard Viewport'}
            </span>
            <span className="text-[10px] bg-neutral-800 text-neutral-400 px-1.5 py-0.5 rounded font-mono">60 FPS</span>
            <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
              wsConnected ? 'bg-emerald-950/80 border border-emerald-700 text-emerald-300' : 'bg-neutral-800 text-neutral-400'
            }`}>
              {wsConnected ? '⚡ WS LIVE' : 'WS OFFLINE'}
            </span>
          </div>

          {/* Engine Mode Selector */}
          <div className="flex items-center gap-1 bg-neutral-900/85 backdrop-blur-md p-1 rounded-lg border border-neutral-700/60 pointer-events-auto shadow-md">
            <button
              onClick={() => setViewportEngine('usd_wasm')}
              className={`flex items-center gap-1 px-2 py-1 rounded text-[11px] font-mono cursor-pointer transition-all ${
                viewportEngine === 'usd_wasm'
                  ? 'bg-indigo-600 text-white font-semibold shadow-sm'
                  : 'text-neutral-400 hover:text-neutral-200'
              }`}
            >
              <Cpu className="w-3.5 h-3.5" /> USD-WASM
            </button>
            <button
              onClick={() => setViewportEngine('standard')}
              className={`flex items-center gap-1 px-2 py-1 rounded text-[11px] font-mono cursor-pointer transition-all ${
                viewportEngine === 'standard'
                  ? 'bg-indigo-600 text-white font-semibold shadow-sm'
                  : 'text-neutral-400 hover:text-neutral-200'
              }`}
            >
              <Layers className="w-3.5 h-3.5" /> WebGL Standard
            </button>
          </div>

          <div className="bg-neutral-900/85 backdrop-blur-md px-3 py-2 rounded-lg border border-neutral-700/60 text-[11px] font-mono text-neutral-400 flex flex-col gap-1">
            <div>Stage: <span className="text-indigo-300">openlore://stages/hero_scene.usda</span></div>
            <div>Active Prim: <span className="text-neutral-200 font-semibold">{activeUsdPrim ? activeUsdPrim.path : selectedPrim || '/World/Characters/Hero'}</span></div>
            <div>Rig Variant: <span className={rigMode === 'cinematic_cache' ? 'text-amber-400 font-bold' : 'text-emerald-400 font-bold'}>{rigMode}</span></div>
          </div>
        </div>

        <div className="absolute bottom-4 right-4 bg-neutral-900/85 backdrop-blur-md px-3 py-1.5 rounded-lg border border-neutral-700/60 text-[10px] text-neutral-400 font-mono pointer-events-none">
          Orbit: Left Click + Drag | Zoom: Scroll
        </div>
      </div>

      {/* USD Prim Scenegraph Inspector (Docked Right) */}
      {viewportEngine === 'usd_wasm' && (
        <div className="w-72 bg-neutral-900/90 backdrop-blur-md border-l border-neutral-800 flex flex-col z-10">
          <div className="p-3 border-b border-neutral-800 flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-bold text-neutral-200">
              <Box className="w-4 h-4 text-indigo-400" />
              <span>USD Prim Hierarchy</span>
            </div>
            <span className="text-[10px] bg-indigo-950/80 border border-indigo-700 text-indigo-300 px-1.5 py-0.5 rounded font-mono">
              WASM AST
            </span>
          </div>

          {/* Hierarchy Tree */}
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {parsedStage && parsedStage.getAllPrims().map((prim) => {
              const isSelected = activeUsdPrim && activeUsdPrim.path === prim.path;
              const depth = (prim.path.match(/\//g) || []).length;
              return (
                <button
                  key={prim.path}
                  onClick={() => handlePrimClick(prim)}
                  style={{ paddingLeft: `${Math.max(8, depth * 14)}px` }}
                  className={`w-full flex items-center gap-2 py-1.5 pr-2 rounded text-left text-xs font-mono transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-indigo-600/30 border border-indigo-500/50 text-indigo-200 font-medium'
                      : 'text-neutral-400 hover:bg-neutral-800/60 hover:text-neutral-200'
                  }`}
                >
                  <ChevronRight className="w-3 h-3 text-neutral-500 shrink-0" />
                  <span className="truncate">{prim.name}</span>
                  <span className="ml-auto text-[10px] text-neutral-500 uppercase px-1 rounded bg-neutral-950/60">
                    {prim.type}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Selected Prim Inspector */}
          {activeUsdPrim && (
            <div className="p-3 border-t border-neutral-800 bg-neutral-950/70 text-xs font-mono space-y-2">
              <div className="font-bold text-neutral-200 truncate">{activeUsdPrim.name}</div>
              <div className="text-[11px] text-neutral-400 truncate">Path: <span className="text-neutral-300">{activeUsdPrim.path}</span></div>
              <div className="text-[11px] text-neutral-400">Type: <span className="text-indigo-400">{activeUsdPrim.type}</span></div>
              
              {activeUsdPrim.attributes.points && (
                <div className="text-[11px] text-neutral-400">
                  Vertices: <span className="text-emerald-400">{activeUsdPrim.attributes.points.length}</span>
                </div>
              )}
              {activeUsdPrim.attributes.faceVertexIndices && (
                <div className="text-[11px] text-neutral-400">
                  Indices: <span className="text-emerald-400">{activeUsdPrim.attributes.faceVertexIndices.length}</span>
                </div>
              )}
              {activeUsdPrim.attributes.displayColor && (
                <div className="flex items-center gap-1.5 text-[11px] text-neutral-400">
                  DisplayColor:
                  <span
                    className="w-3 h-3 rounded-full inline-block border border-neutral-600"
                    style={{
                      backgroundColor: `rgb(${Math.round(activeUsdPrim.attributes.displayColor[0] * 255)}, ${Math.round(activeUsdPrim.attributes.displayColor[1] * 255)}, ${Math.round(activeUsdPrim.attributes.displayColor[2] * 255)})`
                    }}
                  />
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
