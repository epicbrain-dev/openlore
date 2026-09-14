import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

export default function ThreeViewport({ rigMode = 'cinematic_cache', onPrimSelect, selectedPrim }) {
  const containerRef = useRef(null);
  const sceneRef = useRef(null);
  const heroMeshRef = useRef(null);
  const capsuleRef = useRef(null);
  const skeletonRef = useRef(null);
  const reqIdRef = useRef(null);

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

    // 2. Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // 3. Grid & Lighting
    const grid = new THREE.GridHelper(12, 24, 0x4f46e5, 0x262626);
    grid.position.y = -0.01;
    scene.add(grid);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0x818cf8, 2.5);
    dirLight.position.set(5, 10, 7);
    dirLight.castShadow = true;
    scene.add(dirLight);

    const rimLight = new THREE.DirectionalLight(0x38bdf8, 1.5);
    rimLight.position.set(-5, 4, -5);
    scene.add(rimLight);

    // 4. Hero Mesh (Character Armor Model)
    const bodyGeo = new THREE.CylinderGeometry(0.5, 0.35, 1.6, 16);
    const armorMat = new THREE.MeshStandardMaterial({
      color: 0x475569,
      metalness: 0.85,
      roughness: 0.25,
      wireframe: false,
    });
    const heroMesh = new THREE.Mesh(bodyGeo, armorMat);
    heroMesh.position.y = 1.1;
    heroMesh.castShadow = true;
    scene.add(heroMesh);
    heroMeshRef.current = heroMesh;

    // Head
    const headGeo = new THREE.SphereGeometry(0.3, 16, 16);
    const headMat = new THREE.MeshStandardMaterial({ color: 0x64748b, metalness: 0.9, roughness: 0.2 });
    const headMesh = new THREE.Mesh(headGeo, headMat);
    headMesh.position.y = 1.1;
    heroMesh.add(headMesh);

    // Shoulder Pauldrons
    const pauldronGeo = new THREE.BoxGeometry(0.35, 0.2, 0.4);
    const leftP = new THREE.Mesh(pauldronGeo, armorMat);
    leftP.position.set(-0.65, 0.65, 0);
    heroMesh.add(leftP);
    const rightP = leftP.clone();
    rightP.position.x = 0.65;
    heroMesh.add(rightP);

    // 5. Interactive Collision Capsule (for game_collision rigMode)
    const capGeo = new THREE.CapsuleGeometry(0.65, 1.6, 8, 16);
    const capMat = new THREE.MeshBasicMaterial({
      color: 0x22c55e,
      wireframe: true,
      transparent: true,
      opacity: 0.7,
    });
    const capsule = new THREE.Mesh(capGeo, capMat);
    capsule.position.y = 1.1;
    capsule.visible = false;
    scene.add(capsule);
    capsuleRef.current = capsule;

    // 6. UsdSkel Skeleton Bones visualizer
    const skelGroup = new THREE.Group();
    const boneMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b, wireframe: true });
    const rootBone = new THREE.Mesh(new THREE.SphereGeometry(0.1, 8, 8), boneMat);
    rootBone.position.y = 0.2;
    skelGroup.add(rootBone);
    const spineBone = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 1.2), boneMat);
    spineBone.position.y = 0.9;
    skelGroup.add(spineBone);
    skelGroup.visible = false;
    scene.add(skelGroup);
    skeletonRef.current = skelGroup;

    // 7. Virtual Production LED Volume Wall (Curved Soundstage)
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
    scene.add(ledWall);

    // Mouse Drag Controls
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

    // Handle Window Resize
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

      // Subtle breathing point-cache deformation simulation in cinematic mode
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

  // Update rigMode visual state
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

  return (
    <div className="relative w-full h-full min-h-[440px] bg-neutral-950 rounded-xl overflow-hidden border border-neutral-800">
      <div ref={containerRef} className="w-full h-full cursor-grab active:cursor-grabbing" />
      
      {/* 3D Viewport HUD Overlay */}
      <div className="absolute top-4 left-4 flex flex-col gap-2 pointer-events-none">
        <div className="flex items-center gap-2 bg-neutral-900/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-neutral-700/60 shadow-lg">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="text-xs font-mono font-medium text-neutral-200">OpenUSD Live Viewport</span>
          <span className="text-[10px] bg-neutral-800 text-neutral-400 px-1.5 py-0.5 rounded font-mono">60 FPS</span>
        </div>
        <div className="bg-neutral-900/80 backdrop-blur-md px-3 py-2 rounded-lg border border-neutral-700/60 text-[11px] font-mono text-neutral-400 flex flex-col gap-1">
          <div>Stage: <span className="text-indigo-300">openlore://stages/hero_scene.usda</span></div>
          <div>Active Prim: <span className="text-neutral-200 font-semibold">{selectedPrim || '/World/Characters/Hero'}</span></div>
          <div>Rig Variant: <span className={rigMode === 'cinematic_cache' ? 'text-amber-400 font-bold' : 'text-emerald-400 font-bold'}>{rigMode}</span></div>
        </div>
      </div>

      <div className="absolute bottom-4 right-4 bg-neutral-900/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-neutral-700/60 text-[10px] text-neutral-400 font-mono pointer-events-none">
        Orbit: Left Click + Drag | Zoom: Scroll
      </div>
    </div>
  );
}
