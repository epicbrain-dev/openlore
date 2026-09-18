import React, { useState, useEffect, useRef } from 'react';
import * as THREE from 'three';
import {
  Film,
  Activity,
  Sliders,
  Play,
  Pause,
  Layers,
  Sparkles,
  Zap,
  ChevronRight,
  Eye,
  EyeOff,
  Lock,
  RotateCw,
  RefreshCw,
  CheckCircle2,
  GitCommit,
  Radio,
} from 'lucide-react';

export default function AnimationScenegraphView({
  stageUri = 'openlore://stages/hero_scene.usda',
  currentFrame = 1042,
  onFrameChange,
}) {
  // Animation Mode: 'graph_editor' | 'dope_sheet' | 'pose_library'
  const [editorMode, setEditorMode] = useState('graph_editor');
  const [activeTake, setActiveTake] = useState('take_02_dodge');
  const [ghostingEnabled, setGhostingEnabled] = useState(true);
  const [motionTrails, setMotionTrails] = useState(true);
  const [tangentMode, setTangentMode] = useState('bezier'); // 'bezier' | 'linear' | 'step' | 'flat'
  const [selectedChannel, setSelectedChannel] = useState('HeroArmor.translateX');
  const [selectedKeyIndex, setSelectedKeyIndex] = useState(2); // Key at 1045

  // Rig Controls State
  const [armIkFk, setArmIkFk] = useState(85); // 85% IK
  const [legIkFk, setLegIkFk] = useState(100); // 100% IK
  const [squashStretch, setSquashStretch] = useState(1.05);

  // Active Animated Channels & Keyframe Data
  const [channels, setChannels] = useState([
    {
      id: 'HeroArmor.translateX',
      name: 'Translate X',
      color: '#f43f5e', // Rose
      visible: true,
      keys: [
        { frame: 1001, value: 0.0, inTan: 0, outTan: 0.5 },
        { frame: 1024, value: 1.8, inTan: -0.8, outTan: 0.8 },
        { frame: 1045, value: -1.2, inTan: 1.2, outTan: -1.0 },
        { frame: 1080, value: 2.4, inTan: -0.5, outTan: 0.5 },
        { frame: 1120, value: 0.4, inTan: 0.8, outTan: -0.2 },
        { frame: 1150, value: 0.0, inTan: -0.2, outTan: 0.0 },
      ],
    },
    {
      id: 'HeroArmor.translateY',
      name: 'Translate Y',
      color: '#10b981', // Emerald
      visible: true,
      keys: [
        { frame: 1001, value: 1.1, inTan: 0, outTan: 0 },
        { frame: 1024, value: 1.45, inTan: 0.2, outTan: -0.2 },
        { frame: 1045, value: 0.85, inTan: -0.4, outTan: 0.4 },
        { frame: 1080, value: 1.7, inTan: 0.6, outTan: -0.6 },
        { frame: 1120, value: 1.15, inTan: -0.2, outTan: 0.1 },
        { frame: 1150, value: 1.1, inTan: 0, outTan: 0 },
      ],
    },
    {
      id: 'HeroArmor.translateZ',
      name: 'Translate Z',
      color: '#0ea5e9', // Sky
      visible: true,
      keys: [
        { frame: 1001, value: 0.0, inTan: 0, outTan: -0.5 },
        { frame: 1024, value: -1.5, inTan: 0.5, outTan: -0.8 },
        { frame: 1045, value: -3.4, inTan: 0.9, outTan: -0.2 },
        { frame: 1080, value: -1.8, inTan: 0.2, outTan: 0.8 },
        { frame: 1120, value: -0.5, inTan: -0.6, outTan: 0.3 },
        { frame: 1150, value: 0.0, inTan: -0.2, outTan: 0 },
      ],
    },
    {
      id: 'HeroArmor.rotateY',
      name: 'Rotate Y',
      color: '#f59e0b', // Amber
      visible: true,
      keys: [
        { frame: 1001, value: 0.0, inTan: 0, outTan: 15 },
        { frame: 1024, value: 45.0, inTan: -10, outTan: -20 },
        { frame: 1045, value: 24.5, inTan: 12, outTan: -12 },
        { frame: 1080, value: -30.0, inTan: 18, outTan: 10 },
        { frame: 1120, value: 10.0, inTan: -15, outTan: -5 },
        { frame: 1150, value: 0.0, inTan: 5, outTan: 0 },
      ],
    },
    {
      id: 'Spine.rotateX',
      name: 'Spine Bend X',
      color: '#a855f7', // Purple
      visible: false,
      keys: [
        { frame: 1001, value: 5.0, inTan: 0, outTan: 0 },
        { frame: 1045, value: -15.0, inTan: 5, outTan: -5 },
        { frame: 1150, value: 5.0, inTan: 0, outTan: 0 },
      ],
    },
  ]);

  // Performance Takes Library
  const takes = [
    {
      id: 'take_01_idle',
      name: 'Take 01: Combat Idle Stance',
      range: '1001 - 1040',
      duration: '1.6s',
      fps: 24,
      status: 'APPROVED',
      animator: 'Elena Rostova',
    },
    {
      id: 'take_02_dodge',
      name: 'Take 02: Sandworm Evasive Dodge',
      range: '1041 - 1085',
      duration: '1.8s',
      fps: 24,
      status: 'IN_PROGRESS',
      animator: 'Marcus Vance',
    },
    {
      id: 'take_03_strike',
      name: 'Take 03: Crysknife Counter-Strike',
      range: '1086 - 1130',
      duration: '1.8s',
      fps: 24,
      status: 'NEEDS_REVIEW',
      animator: 'Kenji Sato',
    },
    {
      id: 'take_04_recovery',
      name: 'Take 04: Tactical Landing Recovery',
      range: '1131 - 1150',
      duration: '0.8s',
      fps: 24,
      status: 'APPROVED',
      animator: 'Elena Rostova',
    },
  ];

  // 3D Three.js Animation Canvas
  const canvasContainerRef = useRef(null);
  const characterGroupRef = useRef(null);
  const skeletonRef = useRef(null);
  const motionTrailRef = useRef(null);

  useEffect(() => {
    if (!canvasContainerRef.current) return;
    const container = canvasContainerRef.current;
    const width = container.clientWidth || 600;
    const height = container.clientHeight || 340;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x09090c);

    const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 100);
    camera.position.set(0, 1.8, 5.0);
    camera.lookAt(0, 1.1, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // Animation Grid Floor with Distance Ticks
    const grid = new THREE.GridHelper(10, 20, 0x6366f1, 0x27272a);
    grid.position.y = 0;
    scene.add(grid);

    // Lights
    const ambient = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambient);

    const keyLight = new THREE.DirectionalLight(0xa5b4fc, 2.5);
    keyLight.position.set(4, 6, 5);
    keyLight.castShadow = true;
    scene.add(keyLight);

    const rimLight = new THREE.DirectionalLight(0x38bdf8, 2.0);
    rimLight.position.set(-4, 3, -4);
    scene.add(rimLight);

    // Character Rig & Skeleton Group
    const charGroup = new THREE.Group();
    characterGroupRef.current = charGroup;
    scene.add(charGroup);

    // Hero Armor Mesh
    const armorMat = new THREE.MeshStandardMaterial({
      color: 0x475569,
      metalness: 0.8,
      roughness: 0.25,
    });
    const torsoGeo = new THREE.CylinderGeometry(0.45, 0.35, 1.5, 16);
    const torso = new THREE.Mesh(torsoGeo, armorMat);
    torso.position.y = 1.1;
    charGroup.add(torso);

    const headGeo = new THREE.SphereGeometry(0.28, 16, 16);
    const head = new THREE.Mesh(headGeo, armorMat);
    head.position.y = 1.05;
    torso.add(head);

    // Skeleton Bone Lines (Golden joints & cyan bone sticks)
    const skelGroup = new THREE.Group();
    skeletonRef.current = skelGroup;
    scene.add(skelGroup);

    const jointMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b });
    const boneMat = new THREE.LineBasicMaterial({ color: 0x06b6d4, linewidth: 2 });

    const jointPositions = [
      [0, 0.2, 0],   // Root
      [0, 1.0, 0],   // Spine
      [0, 1.7, 0],   // Chest
      [0, 2.1, 0],   // Head
      [-0.6, 1.6, 0],// Left Shoulder
      [-1.1, 1.0, 0],// Left Elbow
      [-1.3, 0.5, 0],// Left Hand
      [0.6, 1.6, 0], // Right Shoulder
      [1.1, 1.0, 0], // Right Elbow
      [1.3, 0.5, 0], // Right Hand
      [-0.4, 0.6, 0],// Left Hip
      [-0.4, 0.1, 0],// Left Foot
      [0.4, 0.6, 0], // Right Hip
      [0.4, 0.1, 0], // Right Foot
    ];

    jointPositions.forEach((pos) => {
      const jointMesh = new THREE.Mesh(new THREE.SphereGeometry(0.06, 8, 8), jointMat);
      jointMesh.position.set(pos[0], pos[1], pos[2]);
      skelGroup.add(jointMesh);
    });

    // Bone connections
    const bonePairs = [
      [0, 1], [1, 2], [2, 3],
      [2, 4], [4, 5], [5, 6],
      [2, 7], [7, 8], [8, 9],
      [0, 10], [10, 11],
      [0, 12], [12, 13],
    ];

    const bonePoints = [];
    bonePairs.forEach(([i1, i2]) => {
      bonePoints.push(new THREE.Vector3(...jointPositions[i1]));
      bonePoints.push(new THREE.Vector3(...jointPositions[i2]));
    });
    const boneGeo = new THREE.BufferGeometry().setFromPoints(bonePoints);
    const boneLines = new THREE.LineSegments(boneGeo, boneMat);
    skelGroup.add(boneLines);

    // Motion Trail Arc
    const trailCurve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(-1.4, 0.4, 0.2),
      new THREE.Vector3(-1.0, 1.3, 0.6),
      new THREE.Vector3(0.0, 1.8, 0.9),
      new THREE.Vector3(1.2, 1.2, 0.4),
      new THREE.Vector3(1.4, 0.5, -0.1),
    ]);
    const trailGeo = new THREE.BufferGeometry().setFromPoints(trailCurve.getPoints(50));
    const trailMat = new THREE.LineBasicMaterial({ color: 0xec4899, transparent: true, opacity: 0.8 });
    const trailLine = new THREE.Line(trailGeo, trailMat);
    motionTrailRef.current = trailLine;
    scene.add(trailLine);

    // Ghosting Onion Skins (Past in Cyan, Future in Magenta)
    const ghostMatPast = new THREE.MeshBasicMaterial({ color: 0x06b6d4, wireframe: true, transparent: true, opacity: 0.35 });
    const ghostMatFuture = new THREE.MeshBasicMaterial({ color: 0xec4899, wireframe: true, transparent: true, opacity: 0.35 });

    const pastGhost = new THREE.Mesh(torsoGeo, ghostMatPast);
    pastGhost.position.set(-0.35, 1.05, -0.2);
    pastGhost.rotation.y = -0.2;
    scene.add(pastGhost);

    const futureGhost = new THREE.Mesh(torsoGeo, ghostMatFuture);
    futureGhost.position.set(0.35, 1.15, 0.2);
    futureGhost.rotation.y = 0.2;
    scene.add(futureGhost);

    // Resize handling with ResizeObserver
    const handleResize = () => {
      if (!container || !camera || !renderer) return;
      const w = container.clientWidth || 600;
      const h = container.clientHeight || 340;
      if (w > 0 && h > 0) {
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
      }
    };
    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(container);

    // Orbit Drag Controls
    let isDragging = false;
    let prevX = 0;
    let prevY = 0;
    let lon = 0;
    let lat = 15;

    const onMouseDown = (e) => {
      isDragging = true;
      prevX = e.clientX;
      prevY = e.clientY;
    };
    const onMouseMove = (e) => {
      if (!isDragging) return;
      const dx = e.clientX - prevX;
      const dy = e.clientY - prevY;
      prevX = e.clientX;
      prevY = e.clientY;
      lon -= dx * 0.4;
      lat = Math.max(-20, Math.min(80, lat + dy * 0.4));
      const phi = THREE.MathUtils.degToRad(90 - lat);
      const theta = THREE.MathUtils.degToRad(lon);
      camera.position.x = 5.0 * Math.sin(phi) * Math.sin(theta);
      camera.position.y = 5.0 * Math.cos(phi) + 0.5;
      camera.position.z = 5.0 * Math.sin(phi) * Math.cos(theta);
      camera.lookAt(0, 1.1, 0);
    };
    const onMouseUp = () => { isDragging = false; };
    container.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);

    let reqId;
    const animate = () => {
      reqId = requestAnimationFrame(animate);
      if (pastGhost) pastGhost.visible = ghostingEnabled;
      if (futureGhost) futureGhost.visible = ghostingEnabled;
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(reqId);
      resizeObserver.disconnect();
      container.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      renderer.dispose();
    };
  }, [ghostingEnabled]);

  // Update animated pose based on currentFrame, squashStretch, and channels
  useEffect(() => {
    if (!characterGroupRef.current || !skeletonRef.current) return;
    const norm = (currentFrame - 1001) / (1150 - 1001);
    const sway = Math.sin(norm * Math.PI * 4) * 0.4;
    const bob = Math.cos(norm * Math.PI * 4) * 0.08;

    characterGroupRef.current.position.x = sway;
    characterGroupRef.current.position.y = bob;
    characterGroupRef.current.rotation.y = sway * 0.6;
    characterGroupRef.current.scale.set(
      1 / Math.sqrt(squashStretch),
      squashStretch,
      1 / Math.sqrt(squashStretch)
    );

    skeletonRef.current.position.x = sway;
    skeletonRef.current.position.y = bob;
    skeletonRef.current.rotation.y = sway * 0.6;
    skeletonRef.current.scale.set(
      1 / Math.sqrt(squashStretch),
      squashStretch,
      1 / Math.sqrt(squashStretch)
    );

    if (motionTrailRef.current) {
      motionTrailRef.current.visible = motionTrails;
    }
  }, [currentFrame, motionTrails, squashStretch]);

  // Graph Editor Coordinate Calculations
  const startF = 1001;
  const endF = 1150;
  const totalF = endF - startF;
  const graphWidth = 700;
  const graphHeight = 220;

  const frameToX = (f) => ((f - startF) / totalF) * (graphWidth - 80) + 50;
  const valToY = (v, min = -4, max = 50) => {
    const norm = (v - min) / (max - min);
    return (1 - norm) * (graphHeight - 50) + 20;
  };

  const activeChannelData = channels.find((c) => c.id === selectedChannel) || channels[0];

  return (
    <div className="flex-1 flex flex-col h-full bg-neutral-950 font-mono text-xs overflow-hidden select-none min-h-0 min-w-0">
      {/* Top Animation Toolbar */}
      <div className="h-10 bg-neutral-900/90 border-b border-neutral-800 px-3 flex items-center justify-between shrink-0 z-10 min-w-0 gap-2">
        {/* Left: Active Take & Clip Selector */}
        <div className="flex items-center gap-2 min-w-0">
          <Film className="w-4 h-4 text-amber-400 shrink-0" />
          <span className="text-neutral-400 font-bold hidden sm:inline shrink-0">TAKE:</span>
          <select
            value={activeTake}
            onChange={(e) => setActiveTake(e.target.value)}
            className="bg-neutral-950 border border-neutral-800 text-amber-300 font-bold px-2 py-1 rounded text-xs focus:outline-none focus:border-amber-500 max-w-[180px] sm:max-w-[240px] truncate shrink-0"
          >
            {takes.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name} ({t.range})
              </option>
            ))}
          </select>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-neutral-800 text-neutral-400 hidden md:inline shrink-0">
            24 FPS
          </span>
        </div>

        {/* Center: Editor Mode Switches (Graph Editor vs Dope Sheet) */}
        <div className="flex items-center gap-1 bg-neutral-950 p-0.5 rounded border border-neutral-800 shrink-0">
          <button
            onClick={() => setEditorMode('graph_editor')}
            className={`px-2.5 py-1 rounded text-[11px] font-semibold cursor-pointer transition-all ${
              editorMode === 'graph_editor'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-neutral-400 hover:text-neutral-200'
            }`}
          >
            Graph Editor
          </button>
          <button
            onClick={() => setEditorMode('dope_sheet')}
            className={`px-2.5 py-1 rounded text-[11px] font-semibold cursor-pointer transition-all ${
              editorMode === 'dope_sheet'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-neutral-400 hover:text-neutral-200'
            }`}
          >
            Dope Sheet
          </button>
          <button
            onClick={() => setEditorMode('pose_library')}
            className={`px-2.5 py-1 rounded text-[11px] font-semibold cursor-pointer transition-all hidden sm:inline ${
              editorMode === 'pose_library'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-neutral-400 hover:text-neutral-200'
            }`}
          >
            Pose Takes
          </button>
        </div>

        {/* Right: Onion Skinning & Motion Trail Toggles */}
        <div className="flex items-center gap-1.5 shrink-0">
          <button
            onClick={() => setGhostingEnabled((v) => !v)}
            className={`flex items-center gap-1 px-2 py-1 rounded text-[10px] border cursor-pointer transition-all ${
              ghostingEnabled
                ? 'bg-cyan-950/80 text-cyan-300 border-cyan-700'
                : 'bg-neutral-950 text-neutral-500 border-neutral-800'
            }`}
            title="Toggle Onion Skinning / Ghosting"
          >
            <Sparkles className="w-3 h-3" />
            <span className="hidden sm:inline">Ghosting</span>
          </button>

          <button
            onClick={() => setMotionTrails((v) => !v)}
            className={`flex items-center gap-1 px-2 py-1 rounded text-[10px] border cursor-pointer transition-all ${
              motionTrails
                ? 'bg-pink-950/80 text-pink-300 border-pink-700'
                : 'bg-neutral-950 text-neutral-500 border-neutral-800'
            }`}
            title="Toggle Motion Arc Trails"
          >
            <Activity className="w-3 h-3" />
            <span className="hidden sm:inline">Trails</span>
          </button>
        </div>
      </div>

      {/* Main Animation Split Area */}
      <div className="flex-1 flex overflow-hidden min-h-0 min-w-0">
        {/* Left / Center Stack: 3D Viewport on Top, Curve Editor on Bottom */}
        <div className="flex-1 flex flex-col min-h-0 min-w-0 border-r border-neutral-800">
          {/* Top Half: 3D Character & Skeleton Viewport */}
          <div className="flex-1 relative min-h-[180px] overflow-hidden bg-neutral-950">
            <div ref={canvasContainerRef} className="absolute inset-0 w-full h-full cursor-grab active:cursor-grabbing" />

            {/* Viewport Floating Overlay Tag */}
            <div className="absolute top-2.5 left-2.5 flex items-center gap-2 bg-neutral-900/85 backdrop-blur-md px-2.5 py-1 rounded border border-neutral-800 text-[10px] text-neutral-300 pointer-events-none">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="font-bold text-white">SKELETON POSE VIEW</span>
              <span className="text-neutral-500">&bull;</span>
              <span>Frame: <strong className="text-amber-300">{currentFrame}</strong></span>
              <span className="text-neutral-500">&bull;</span>
              <span>Take: <strong className="text-indigo-300">{activeTake}</strong></span>
            </div>

            <div className="absolute bottom-2 right-2 text-[9px] text-neutral-500 bg-neutral-950/80 px-2 py-0.5 rounded border border-neutral-800 pointer-events-none">
              Orbit: <span className="text-neutral-300">Drag LMB</span> | Pan: <span className="text-neutral-300">MMB</span>
            </div>
          </div>

          {/* Bottom Half: Interactive Graph Editor & Animation Curves */}
          <div className="h-60 sm:h-64 border-t border-neutral-800 flex flex-col bg-neutral-900/95 min-h-0 shrink-0">
            {/* Graph Header: Channel Selection & Tangent Tools */}
            <div className="h-8 bg-neutral-950 px-3 border-b border-neutral-800 flex items-center justify-between text-[11px] shrink-0">
              <div className="flex items-center gap-3">
                <span className="font-bold text-neutral-300 flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-indigo-400" />
                  {editorMode === 'graph_editor' ? 'GRAPH EDITOR (BÉZIER CURVES)' : 'DOPE SHEET TIMELINE'}
                </span>
                <span className="text-neutral-600 hidden sm:inline">&bull;</span>
                <span className="text-neutral-400 hidden sm:inline">
                  Active Channel: <strong style={{ color: activeChannelData.color }}>{activeChannelData.name}</strong>
                </span>
              </div>

              {/* Tangent Mode Selectors */}
              {editorMode === 'graph_editor' && (
                <div className="flex items-center gap-1">
                  <span className="text-[10px] text-neutral-500 hidden md:inline">Tangents:</span>
                  {[
                    { id: 'bezier', label: 'Bézier Smooth' },
                    { id: 'linear', label: 'Linear' },
                    { id: 'step', label: 'Step' },
                  ].map((t) => (
                    <button
                      key={t.id}
                      onClick={() => setTangentMode(t.id)}
                      className={`px-1.5 py-0.5 rounded text-[10px] cursor-pointer transition-colors ${
                        tangentMode === t.id
                          ? 'bg-neutral-800 text-amber-300 font-bold border border-neutral-700'
                          : 'text-neutral-500 hover:text-neutral-300'
                      }`}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Graph Content Area: Channel List on Left, SVG Curve Canvas on Right */}
            <div className="flex-1 flex overflow-hidden min-h-0">
              {/* Channels Sidebar */}
              <div className="w-48 bg-neutral-950/90 border-r border-neutral-800 overflow-y-auto p-1 flex flex-col gap-0.5 shrink-0">
                <div className="text-[10px] text-neutral-500 font-semibold px-2 py-1">CHANNELS</div>
                {channels.map((ch) => {
                  const isSel = ch.id === selectedChannel;
                  return (
                    <div
                      key={ch.id}
                      onClick={() => setSelectedChannel(ch.id)}
                      className={`flex items-center justify-between px-2 py-1 rounded cursor-pointer transition-colors ${
                        isSel
                          ? 'bg-neutral-800 text-white font-semibold shadow-sm'
                          : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-900'
                      }`}
                    >
                      <div className="flex items-center gap-1.5 truncate">
                        <span className="w-2.5 h-2.5 rounded-sm shrink-0" style={{ backgroundColor: ch.color }} />
                        <span className="truncate text-[11px]">{ch.name}</span>
                      </div>
                      <span className="text-[9px] text-neutral-600 font-mono">{ch.keys.length} keys</span>
                    </div>
                  );
                })}
              </div>

              {/* Curve Canvas */}
              <div className="flex-1 bg-neutral-950 relative overflow-hidden flex items-center justify-center">
                {editorMode === 'graph_editor' ? (
                  <svg
                    viewBox={`0 0 ${graphWidth} ${graphHeight}`}
                    className="w-full h-full cursor-crosshair"
                    onClick={(e) => {
                      if (!onFrameChange) return;
                      const rect = e.currentTarget.getBoundingClientRect();
                      const clickX = e.clientX - rect.left;
                      const ratio = Math.max(0, Math.min(1, clickX / rect.width));
                      const clickedFrame = Math.round(startF + ratio * totalF);
                      onFrameChange(clickedFrame);
                    }}
                  >
                    {/* Horizontal Grid lines */}
                    {[0.2, 0.4, 0.6, 0.8].map((ratio) => (
                      <line
                        key={ratio}
                        x1="40"
                        y1={graphHeight * ratio}
                        x2={graphWidth - 20}
                        y2={graphHeight * ratio}
                        stroke="#27272a"
                        strokeDasharray="4 4"
                      />
                    ))}

                    {/* Vertical Frame Grid Lines */}
                    {[1001, 1024, 1045, 1080, 1120, 1150].map((f) => {
                      const x = frameToX(f);
                      return (
                        <g key={f}>
                          <line x1={x} y1="15" x2={x} y2={graphHeight - 20} stroke="#27272a" />
                          <text x={x} y={graphHeight - 6} fill="#71717a" fontSize="9" textAnchor="middle">
                            {f}
                          </text>
                        </g>
                      );
                    })}

                    {/* Render Curve for selected channel */}
                    {activeChannelData && (() => {
                      const minV = Math.min(...activeChannelData.keys.map((k) => k.value)) - 2;
                      const maxV = Math.max(...activeChannelData.keys.map((k) => k.value)) + 2;

                      // Build SVG Cubic Bézier path
                      let pathD = '';
                      activeChannelData.keys.forEach((key, idx) => {
                        const x = frameToX(key.frame);
                        const y = valToY(key.value, minV, maxV);
                        if (idx === 0) {
                          pathD += `M ${x} ${y} `;
                        } else {
                          const prevKey = activeChannelData.keys[idx - 1];
                          const prevX = frameToX(prevKey.frame);
                          const prevY = valToY(prevKey.value, minV, maxV);
                          const cp1x = prevX + (x - prevX) * 0.5;
                          const cp1y = prevY + (prevKey.outTan || 0) * 8;
                          const cp2x = x - (x - prevX) * 0.5;
                          const cp2y = y - (key.inTan || 0) * 8;
                          if (tangentMode === 'linear') {
                            pathD += `L ${x} ${y} `;
                          } else if (tangentMode === 'step') {
                            pathD += `H ${x} V ${y} `;
                          } else {
                            pathD += `C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${x} ${y} `;
                          }
                        }
                      });

                      return (
                        <g>
                          {/* Smooth Glow Curve */}
                          <path
                            d={pathD}
                            fill="none"
                            stroke={activeChannelData.color}
                            strokeWidth="2.5"
                            strokeLinecap="round"
                            opacity="0.9"
                          />

                          {/* Keyframe Points & Tangent Handles */}
                          {activeChannelData.keys.map((key, kIdx) => {
                            const kx = frameToX(key.frame);
                            const ky = valToY(key.value, minV, maxV);
                            const isSelected = selectedKeyIndex === kIdx;

                            return (
                              <g
                                key={key.frame}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setSelectedKeyIndex(kIdx);
                                  if (onFrameChange) onFrameChange(key.frame);
                                }}
                                className="cursor-pointer"
                              >
                                {isSelected && (
                                  <circle
                                    cx={kx}
                                    cy={ky}
                                    r="8"
                                    fill="none"
                                    stroke="#f59e0b"
                                    strokeWidth="1.5"
                                    opacity="0.8"
                                  />
                                )}
                                <circle
                                  cx={kx}
                                  cy={ky}
                                  r="4"
                                  fill={isSelected ? '#f59e0b' : activeChannelData.color}
                                  stroke="#09090b"
                                  strokeWidth="1.5"
                                />
                                <text x={kx} y={ky - 8} fill="#d4d4d8" fontSize="8" textAnchor="middle">
                                  {key.value.toFixed(1)}
                                </text>
                              </g>
                            );
                          })}
                        </g>
                      );
                    })()}

                    {/* Active Playhead Frame Line */}
                    {(() => {
                      const px = frameToX(currentFrame);
                      return (
                        <g>
                          <line x1={px} y1="10" x2={px} y2={graphHeight - 15} stroke="#f59e0b" strokeWidth="1.5" />
                          <polygon
                            points={`${px - 4},10 ${px + 4},10 ${px},16`}
                            fill="#f59e0b"
                          />
                        </g>
                      );
                    })()}
                  </svg>
                ) : editorMode === 'pose_library' ? (
                  /* Pose Library Cards View */
                  <div className="w-full h-full p-3 grid grid-cols-2 md:grid-cols-4 gap-2.5 overflow-y-auto">
                    {[
                      { id: 'idle', name: 'Combat Idle', frame: 1001, desc: 'Neutral ready stance with balanced center of gravity' },
                      { id: 'dodge', name: 'Sandworm Dodge', frame: 1045, desc: 'Rapid evasive low crouch with dynamic torque' },
                      { id: 'strike', name: 'Crysknife Strike', frame: 1080, desc: 'High-impact thrust pose with clavicle extension' },
                      { id: 'recovery', name: 'Tactical Landing', frame: 1130, desc: '3-point ground impact shock absorption' },
                    ].map((p) => (
                      <div
                        key={p.id}
                        className="bg-neutral-900 border border-neutral-800 hover:border-indigo-500/60 p-2.5 rounded-lg flex flex-col justify-between transition-all group"
                      >
                        <div>
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-white text-[11px] group-hover:text-indigo-300 transition-colors">
                              {p.name}
                            </span>
                            <span className="text-[9px] bg-neutral-800 text-amber-400 px-1.5 py-0.2 rounded">
                              F{p.frame}
                            </span>
                          </div>
                          <p className="text-[10px] text-neutral-400 mt-1 leading-tight">{p.desc}</p>
                        </div>
                        <button
                          onClick={() => {
                            if (onFrameChange) onFrameChange(p.frame);
                          }}
                          className="mt-2.5 py-1 px-2 rounded bg-neutral-800 hover:bg-indigo-600 text-neutral-200 hover:text-white font-semibold text-[10px] transition-colors cursor-pointer text-center"
                        >
                          Apply Pose to Rig
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  /* Dope Sheet Timeline Block View */
                  <div className="w-full h-full p-3 flex flex-col gap-2 overflow-y-auto">
                    {channels.map((ch) => (
                      <div key={ch.id} className="flex items-center gap-2 h-7 bg-neutral-900/80 px-2 rounded border border-neutral-800">
                        <span className="w-24 text-[11px] truncate" style={{ color: ch.color }}>{ch.name}</span>
                        <div className="flex-1 relative h-4 bg-neutral-950 rounded overflow-hidden">
                          {ch.keys.map((k) => {
                            const ratio = (k.frame - startF) / totalF;
                            return (
                              <div
                                key={k.frame}
                                style={{ left: `calc(${ratio * 100}% - 4px)` }}
                                onClick={() => onFrameChange && onFrameChange(k.frame)}
                                className="absolute top-1 w-2 h-2 bg-amber-400 rotate-45 cursor-pointer hover:scale-125"
                                title={`Key at frame ${k.frame}: ${k.value}`}
                              />
                            );
                          })}
                          <div
                            style={{ left: `${((currentFrame - startF) / totalF) * 100}%` }}
                            className="absolute top-0 bottom-0 w-0.5 bg-amber-400 pointer-events-none"
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Right Panel: Rig & Posing Inspector */}
        <div className="w-64 lg:w-72 xl:w-80 bg-neutral-900/90 border-l border-neutral-800 flex flex-col shrink-0 h-full overflow-y-auto p-3 gap-4 font-mono text-xs select-none min-w-0">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-neutral-800 pb-2">
            <div className="flex items-center gap-1.5 font-bold text-neutral-200">
              <Sliders className="w-4 h-4 text-indigo-400" />
              <span>RIG & POSE CONTROLS</span>
            </div>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-700">
              FK/IK
            </span>
          </div>

          {/* Section 1: Active Keyframe Channel Inspector */}
          <div className="flex flex-col gap-2 bg-neutral-950 p-2.5 rounded-lg border border-neutral-800">
            <div className="text-neutral-400 font-bold text-[11px] flex items-center justify-between">
              <span>ACTIVE KEYFRAME</span>
              <span className="text-amber-400">Frame {currentFrame}</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div>
                <span className="text-neutral-500">Channel:</span>
                <div className="font-semibold text-neutral-200 truncate">{activeChannelData.name}</div>
              </div>
              <div>
                <span className="text-neutral-500">Value:</span>
                <input
                  type="number"
                  step="0.1"
                  value={activeChannelData.keys[selectedKeyIndex]?.value ?? 0}
                  onChange={(e) => {
                    const val = parseFloat(e.target.value) || 0;
                    setChannels((prev) =>
                      prev.map((c) => {
                        if (c.id !== selectedChannel) return c;
                        const newKeys = [...c.keys];
                        if (newKeys[selectedKeyIndex]) {
                          newKeys[selectedKeyIndex] = { ...newKeys[selectedKeyIndex], value: val };
                        }
                        return { ...c, keys: newKeys };
                      })
                    );
                  }}
                  className="w-full bg-neutral-900 border border-neutral-800 text-amber-300 font-bold px-1.5 py-0.5 rounded focus:outline-none focus:border-amber-500 text-xs"
                />
              </div>
            </div>
            <div className="flex items-center gap-1.5 mt-1">
              <button
                onClick={() => {
                  setChannels((prev) =>
                    prev.map((c) => {
                      if (c.id !== selectedChannel) return c;
                      const existing = c.keys.find((k) => k.frame === currentFrame);
                      if (existing) return c;
                      const newKeys = [...c.keys, { frame: currentFrame, value: 1.0, inTan: 0, outTan: 0 }].sort(
                        (a, b) => a.frame - b.frame
                      );
                      return { ...c, keys: newKeys };
                    })
                  );
                }}
                className="flex-1 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-[10px] cursor-pointer text-center"
              >
                + Set Key [S]
              </button>
              <button
                onClick={() => {
                  setChannels((prev) =>
                    prev.map((c) => {
                      if (c.id !== selectedChannel) return c;
                      return { ...c, keys: c.keys.filter((k) => k.frame !== currentFrame) };
                    })
                  );
                }}
                className="flex-1 py-1 rounded bg-neutral-800 hover:bg-neutral-700 text-neutral-300 font-semibold text-[10px] cursor-pointer text-center"
              >
                Delete Key
              </button>
            </div>
          </div>

          {/* Section 2: Rig Solvers (FK / IK) */}
          <div className="flex flex-col gap-3">
            <div className="text-[11px] font-bold text-neutral-300 border-b border-neutral-800 pb-1">
              INVERSE KINEMATICS (IK/FK)
            </div>

            <div className="flex flex-col gap-1">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-neutral-400">Arm Limbs:</span>
                <span className="text-sky-400 font-semibold">{armIkFk}% IK</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={armIkFk}
                onChange={(e) => setArmIkFk(parseInt(e.target.value, 10))}
                className="w-full accent-indigo-500 cursor-pointer"
              />
            </div>

            <div className="flex flex-col gap-1">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-neutral-400">Leg Limbs:</span>
                <span className="text-emerald-400 font-semibold">{legIkFk}% IK</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={legIkFk}
                onChange={(e) => setLegIkFk(parseInt(e.target.value, 10))}
                className="w-full accent-emerald-500 cursor-pointer"
              />
            </div>

            <div className="flex flex-col gap-1">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-neutral-400">Squash & Stretch:</span>
                <span className="text-amber-400 font-semibold">{squashStretch.toFixed(2)}x</span>
              </div>
              <input
                type="range"
                min="80"
                max="140"
                value={Math.round(squashStretch * 100)}
                onChange={(e) => setSquashStretch(parseInt(e.target.value, 10) / 100)}
                className="w-full accent-amber-500 cursor-pointer"
              />
            </div>
          </div>

          {/* Section 3: Joint Hierarchy */}
          <div className="flex flex-col gap-2">
            <div className="text-[11px] font-bold text-neutral-300 border-b border-neutral-800 pb-1">
              SKELETON BONE CHAIN
            </div>
            <div className="bg-neutral-950 p-2 rounded border border-neutral-800 flex flex-col gap-1 text-[11px]">
              {[
                { name: 'Root_Hips', depth: 0, channel: 'HeroArmor.translateX' },
                { name: 'Spine_01', depth: 1, channel: 'Spine.rotateX' },
                { name: 'Chest_Torso', depth: 2, channel: 'HeroArmor.translateY' },
                { name: 'Head_Neck', depth: 3, channel: 'HeroArmor.rotateY' },
                { name: 'Arm_IK_Left', depth: 3, channel: 'HeroArmor.translateZ' },
                { name: 'Arm_IK_Right', depth: 3, channel: 'HeroArmor.translateX' },
                { name: 'Leg_IK_Left', depth: 1, channel: 'HeroArmor.translateY' },
                { name: 'Leg_IK_Right', depth: 1, channel: 'HeroArmor.translateZ' },
              ].map((j) => (
                <div
                  key={j.name}
                  onClick={() => setSelectedChannel(j.channel)}
                  style={{ paddingLeft: `${j.depth * 10}px` }}
                  className={`flex items-center justify-between py-1 px-1.5 rounded cursor-pointer transition-colors ${
                    selectedChannel === j.channel ? 'bg-indigo-950 text-indigo-200 border border-indigo-700' : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-900'
                  }`}
                >
                  <span className="truncate">🦴 {j.name}</span>
                  <span className="text-[9px] text-emerald-400">Selected</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
