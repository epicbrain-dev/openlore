import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { parseUSDA, buildThreeMeshFromUsdPrim, getDemoUSDA } from '../utils/usdParser';
import { getWsUrl } from '../utils/api';
import { Layers, Cpu, Box, Film, Gamepad2, Radio, Activity, Camera } from 'lucide-react';

export default function ThreeViewport({
  rigMode = 'cinematic_cache',
  onPrimSelect,
  selectedPrim = '/World/Characters/HeroArmor',
  currentFrame = 1042,
  shadingMode = 'usd_preview',
  hiddenPrims = {},
  activeTransforms = null,
}) {
  const containerRef = useRef(null);
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const standardGroupRef = useRef(null);
  const usdGroupRef = useRef(null);
  const heroMeshRef = useRef(null);
  const capsuleRef = useRef(null);
  const skeletonRef = useRef(null);
  const reqIdRef = useRef(null);
  const simRef = useRef(null);
  const selectionBoxRef = useRef(null);

  const [wsConnected, setWsConnected] = useState(false);
  const [viewportEngine, setViewportEngine] = useState('usd_wasm'); // 'usd_wasm' | 'standard'
  const [showEngineDetails, setShowEngineDetails] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [telemetry, setTelemetry] = useState({
    subject: 'Camera_StageA',
    pos: { x: 0.0, y: 110.0, z: 400.0 },
    rot: { pitch: 12.4, yaw: -25.0, roll: 0.0 },
    fov: 39.6,
    focalLength: 50.0,
    aperture: 2.8,
    fps: 60,
    packets: 1420,
    active: true,
  });

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
    // STANDARD VIEWPORT GROUP (Procedural Stylized Meshes)
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

    // Soundstage LED Volume Wall
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
    const stagePrims = stage.getAllPrims();
    stagePrims.forEach((prim) => {
      const mesh = buildThreeMeshFromUsdPrim(prim);
      if (mesh) {
        usdGroup.add(mesh);
      }
    });

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

    let hasMoved = false;
    const onMouseDown = (e) => {
      isDragging = true;
      hasMoved = false;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };
    const onMouseMove = (e) => {
      if (!isDragging) return;
      const dx = e.clientX - prevMouseX;
      const dy = e.clientY - prevMouseY;
      if (Math.abs(dx) > 2 || Math.abs(dy) > 2) hasMoved = true;
      azimuth -= dx * 0.008;
      polar = Math.max(0.1, Math.min(Math.PI / 2 - 0.05, polar + dy * 0.008));
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
      updateCameraPos();
    };
    const onMouseUp = (e) => {
      isDragging = false;
      if (!hasMoved && onPrimSelect && container) {
        const rect = container.getBoundingClientRect();
        const mouse = new THREE.Vector2(
          ((e.clientX - rect.left) / rect.width) * 2 - 1,
          -((e.clientY - rect.top) / rect.height) * 2 + 1
        );
        const raycaster = new THREE.Raycaster();
        raycaster.setFromCamera(mouse, camera);
        const hits = raycaster.intersectObjects(usdGroup.children, true);
        if (hits.length > 0) {
          const hitObj = hits[0].object;
          if (hitObj.userData?.primPath) {
            onPrimSelect(hitObj.userData.primPath);
          }
        }
      }
    };
    const onWheel = (e) => {
      e.preventDefault();
      radius = Math.max(2.5, Math.min(18, radius + e.deltaY * 0.008));
      updateCameraPos();
    };

    container.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    container.addEventListener('wheel', onWheel, { passive: false });

    // Responsive Canvas Resizing using ResizeObserver
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
      resizeObserver.disconnect();
      container.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      container.removeEventListener('wheel', onWheel);
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
    };
  }, []);

  // Selection Highlight Outline
  useEffect(() => {
    if (!sceneRef.current || !usdGroupRef.current) return;
    if (selectionBoxRef.current) {
      sceneRef.current.remove(selectionBoxRef.current);
      selectionBoxRef.current.geometry && selectionBoxRef.current.geometry.dispose();
      selectionBoxRef.current = null;
    }

    if (!selectedPrim) return;

    let targetMesh = null;
    usdGroupRef.current.traverse((child) => {
      if (child.isMesh && (child.userData?.primPath === selectedPrim || child.name === selectedPrim)) {
        targetMesh = child;
      }
    });

    if (targetMesh) {
      const box = new THREE.BoxHelper(targetMesh, 0xf59e0b);
      box.material.linewidth = 2;
      sceneRef.current.add(box);
      selectionBoxRef.current = box;
    }
  }, [selectedPrim]);

  // Dynamic Current Frame Procedural Turntable Animation
  useEffect(() => {
    if (!usdGroupRef.current) return;
    const progress = (currentFrame - 1001) / 149; // 0.0 to 1.0
    usdGroupRef.current.rotation.y = progress * Math.PI * 0.4;

    if (selectionBoxRef.current) {
      selectionBoxRef.current.update();
    }
  }, [currentFrame]);

  // Shading Mode Toggles (USD Preview, Wireframe, Clay)
  useEffect(() => {
    if (!usdGroupRef.current) return;
    usdGroupRef.current.traverse((child) => {
      if (child.isMesh) {
        if (shadingMode === 'wireframe') {
          child.material = new THREE.MeshBasicMaterial({ color: 0x38bdf8, wireframe: true });
        } else if (shadingMode === 'clay') {
          child.material = new THREE.MeshStandardMaterial({ color: 0xa1a1aa, roughness: 0.85, metalness: 0.05 });
        } else {
          // Restore original PBR material
          if (child.userData?.origMaterial) {
            child.material = child.userData.origMaterial;
          }
        }
      }
    });
  }, [shadingMode]);

  // Outliner Visibility Sync
  useEffect(() => {
    if (!usdGroupRef.current) return;
    usdGroupRef.current.traverse((child) => {
      if (child.isMesh && child.userData?.primPath) {
        child.visible = !hiddenPrims[child.userData.primPath];
      }
    });
    if (selectionBoxRef.current) {
      selectionBoxRef.current.update();
    }
  }, [hiddenPrims]);

  // Channel Box Active Transforms Manipulation
  useEffect(() => {
    if (!usdGroupRef.current || !selectedPrim || !activeTransforms) return;
    usdGroupRef.current.traverse((child) => {
      if (child.isMesh && (child.userData?.primPath === selectedPrim || child.name === selectedPrim)) {
        child.position.set(activeTransforms.tx, activeTransforms.ty, activeTransforms.tz);
        child.rotation.set(
          (activeTransforms.rx * Math.PI) / 180,
          (activeTransforms.ry * Math.PI) / 180,
          (activeTransforms.rz * Math.PI) / 180
        );
        child.scale.set(activeTransforms.sx, activeTransforms.sy, activeTransforms.sz);
      }
    });
    if (selectionBoxRef.current) {
      selectionBoxRef.current.update();
    }
  }, [activeTransforms, selectedPrim]);

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
    const wsUrl = getWsUrl('/ws/live');
    let ws = null;

    try {
      ws = new WebSocket(wsUrl);
      ws.onopen = () => setWsConnected(true);
      ws.onclose = () => setWsConnected(false);
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'LIVELINK_FRAME') {
            const trans = msg.translation || [0, 0, 0];
            const rot = msg.rotation || [0, 0, 0, 1];
            const cam = msg.camera || {};

            if (cameraRef.current) {
              cameraRef.current.position.x = (trans[0] || 0) * 0.01;
              cameraRef.current.position.y = Math.max(0.5, (trans[2] || 0) * 0.01);
              cameraRef.current.position.z = Math.max(1.0, -(trans[1] || -400) * 0.01);
              cameraRef.current.lookAt(0, 1.1, 0);
            }

            const qx = rot[0] || 0, qy = rot[1] || 0, qz = rot[2] || 0, qw = rot[3] || 1;
            const pitch = Math.asin(Math.max(-1, Math.min(1, 2 * (qw * qy - qz * qx)))) * (180 / Math.PI);
            const yaw = Math.atan2(2 * (qw * qz + qx * qy), 1 - 2 * (qy * qy + qz * qz)) * (180 / Math.PI);
            const roll = Math.atan2(2 * (qw * qx + qy * qz), 1 - 2 * (qx * qx + qy * qy)) * (180 / Math.PI);

            setTelemetry((prev) => ({
              ...prev,
              subject: msg.subject || prev.subject,
              pos: { x: trans[0] || 0, y: trans[1] || 0, z: trans[2] || 0 },
              rot: {
                pitch: isNaN(pitch) ? 0 : pitch,
                yaw: isNaN(yaw) ? 0 : yaw,
                roll: isNaN(roll) ? 0 : roll,
              },
              fov: cam.field_of_view || prev.fov,
              focalLength: cam.focal_length || prev.focalLength,
              aperture: cam.aperture || prev.aperture,
              packets: prev.packets + 1,
              active: true,
            }));
          } else if (msg.type === 'STAGE_MUTATION') {
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

  // Continuous Telemetry Simulator (When active without external source)
  useEffect(() => {
    if (!simulating) {
      if (simRef.current) clearInterval(simRef.current);
      return;
    }

    let t = 0;
    simRef.current = setInterval(() => {
      t += 0.04;
      const x = Math.sin(t * 1.5) * 120.0;
      const y = Math.cos(t * 0.8) * 30.0 - 40.0;
      const z = 380.0 + Math.sin(t * 0.5) * 50.0;
      const pitch = Math.sin(t * 1.2) * 12.0;
      const yaw = Math.cos(t * 0.9) * 25.0;
      const roll = Math.sin(t * 0.6) * 3.5;
      const fov = 39.6 + Math.sin(t * 0.3) * 4.0;

      if (cameraRef.current) {
        cameraRef.current.position.set(x * 0.012, Math.max(1.0, (y + 160) * 0.012), z * 0.011);
        cameraRef.current.lookAt(0, 1.1, 0);
      }

      setTelemetry((prev) => ({
        ...prev,
        pos: { x, y, z },
        rot: { pitch, yaw, roll },
        fov,
        packets: prev.packets + 1,
        active: true,
      }));
    }, 1000 / 60);

    return () => {
      if (simRef.current) clearInterval(simRef.current);
    };
  }, [simulating]);

  return (
    <div className="relative w-full h-full min-h-0 min-w-0 bg-neutral-950 overflow-hidden flex flex-col justify-between select-none">
      {/* 3D WebGL Canvas */}
      <div ref={containerRef} className="absolute inset-0 w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Top-Left Sleek Compact HUD */}
      <div className="absolute top-2.5 left-2.5 flex flex-col gap-1.5 z-10 font-mono text-xs max-w-[calc(100%-20px)] pointer-events-auto">
        <div className="flex items-center gap-1.5 bg-neutral-900/85 backdrop-blur-md px-2.5 py-1 rounded-lg border border-neutral-800 shadow-md">
          <span className={`w-2 h-2 rounded-full shrink-0 ${wsConnected ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
          <button
            onClick={() => setShowEngineDetails((v) => !v)}
            className="flex items-center gap-1 text-neutral-200 hover:text-white font-medium cursor-pointer"
            title="Click to toggle engine details"
          >
            <span className="truncate max-w-[130px] sm:max-w-none">
              {viewportEngine === 'usd_wasm' ? 'USD Hydra WASM' : 'WebGL Standard'}
            </span>
            <span className="text-[10px] text-neutral-500">{showEngineDetails ? '▲' : '▼'}</span>
          </button>
          <span className="text-[10px] bg-neutral-800 text-neutral-400 px-1 py-0.2 rounded font-mono hidden sm:inline">60 FPS</span>
          <span className={`text-[9px] px-1.5 py-0.2 rounded font-mono ${
            wsConnected ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-800' : 'bg-neutral-800 text-neutral-400'
          }`}>
            {wsConnected ? 'WS LIVE' : 'WS OFF'}
          </span>
        </div>

        {/* Collapsible Details Drawer */}
        {showEngineDetails && (
          <div className="flex flex-col gap-1.5 bg-neutral-900/95 backdrop-blur-md p-2 rounded-lg border border-neutral-800 shadow-xl max-w-xs text-[11px]">
            <div className="flex items-center gap-1">
              <button
                onClick={() => setViewportEngine('usd_wasm')}
                className={`flex-1 flex items-center justify-center gap-1 py-1 rounded text-[10px] cursor-pointer transition-all ${
                  viewportEngine === 'usd_wasm' ? 'bg-indigo-600 text-white font-semibold' : 'bg-neutral-800 text-neutral-400 hover:text-neutral-200'
                }`}
              >
                <Cpu className="w-3 h-3" /> USD-WASM
              </button>
              <button
                onClick={() => setViewportEngine('standard')}
                className={`flex-1 flex items-center justify-center gap-1 py-1 rounded text-[10px] cursor-pointer transition-all ${
                  viewportEngine === 'standard' ? 'bg-indigo-600 text-white font-semibold' : 'bg-neutral-800 text-neutral-400 hover:text-neutral-200'
                }`}
              >
                <Layers className="w-3 h-3" /> WebGL
              </button>
            </div>
            <div className="text-[10px] text-neutral-400 flex flex-col gap-0.5 border-t border-neutral-800 pt-1">
              <div className="truncate">Prim: <span className="text-neutral-200 font-semibold">{selectedPrim.split('/').pop()}</span></div>
              <div>Rig: <span className={rigMode === 'cinematic_cache' ? 'text-amber-400' : 'text-emerald-400'}>{rigMode}</span></div>
            </div>
          </div>
        )}
      </div>

      {/* Sleek Bottom Live Link HUD */}
      <div className="absolute bottom-2 inset-x-2 sm:inset-x-3 flex items-center justify-between gap-2 bg-neutral-900/85 backdrop-blur-md px-3 py-1.5 rounded-lg border border-neutral-800/80 shadow-xl z-10 font-mono text-[11px] pointer-events-auto">
        {/* Left: Stream Protocol & Subject */}
        <div className="flex items-center gap-2 min-w-0">
          <span className={`w-2 h-2 rounded-full shrink-0 ${telemetry.active || simulating ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
          <span className="font-bold text-neutral-200 hidden sm:inline">LIVE LINK</span>
          <span className="text-[9px] bg-neutral-800 text-indigo-300 px-1.5 py-0.2 rounded border border-neutral-700 font-mono hidden md:inline">
            UDP:11111
          </span>
          <span className="text-neutral-300 truncate max-w-[120px] sm:max-w-[180px]">
            <strong className="text-white font-medium">{telemetry.subject}</strong>
          </span>
          <span className="text-[9px] bg-emerald-950/80 border border-emerald-700 text-emerald-400 px-1 py-0.2 rounded font-semibold hidden sm:inline">
            {telemetry.fps} FPS
          </span>
        </div>

        {/* Center: Coordinates */}
        <div className="hidden lg:flex items-center gap-2 text-[10px]">
          <span className="text-neutral-500">POS</span>
          <span className="text-neutral-300">
            X:<span className="text-emerald-400 font-semibold">{telemetry.pos.x.toFixed(1)}</span>{' '}
            Y:<span className="text-emerald-400 font-semibold">{telemetry.pos.y.toFixed(1)}</span>{' '}
            Z:<span className="text-emerald-400 font-semibold">{telemetry.pos.z.toFixed(1)}</span>
          </span>
          <span className="text-neutral-700">&bull;</span>
          <span className="text-neutral-500">ROT</span>
          <span className="text-neutral-300">
            P:<span className="text-indigo-400 font-semibold">{telemetry.rot.pitch.toFixed(1)}°</span>{' '}
            Y:<span className="text-indigo-400 font-semibold">{telemetry.rot.yaw.toFixed(1)}°</span>
          </span>
        </div>

        {/* Right: Simulation Toggle */}
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => setSimulating((prev) => !prev)}
            className={`px-2 py-0.5 rounded text-[10px] font-semibold transition-all cursor-pointer border ${
              simulating
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/50'
                : 'bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border-indigo-500/40'
            }`}
            title="Simulate incoming 60 FPS Live Link stream"
          >
            {simulating ? 'Stop Stream' : 'Test Sine'}
          </button>
        </div>
      </div>
    </div>
  );
}
