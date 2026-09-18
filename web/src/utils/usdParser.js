/**
 * OpenUSD WebAssembly / Universal USDA Parser & Geometry Synthesizer.
 * Parses OpenUSD ASCII (.usda) stages and converts USD Prims into Three.js BufferGeometries.
 */
import * as THREE from 'three';

export class UsdStage {
  constructor(metadata = {}) {
    this.metadata = metadata;
    this.rootPrims = [];
    this.primMap = new Map(); // path -> prim
  }

  addPrim(prim) {
    this.primMap.set(prim.path, prim);
    if (!prim.parentPath || prim.parentPath === '/') {
      this.rootPrims.push(prim);
    } else {
      const parent = this.primMap.get(prim.parentPath);
      if (parent) {
        parent.children.push(prim);
      } else {
        this.rootPrims.push(prim);
      }
    }
  }

  getPrim(path) {
    return this.primMap.get(path);
  }

  getAllPrims() {
    return Array.from(this.primMap.values());
  }
}

export class UsdPrim {
  constructor(name, type, path, parentPath = null) {
    this.name = name;
    this.type = type; // 'Xform', 'Mesh', 'Camera', 'Scope', etc.
    this.path = path;
    this.parentPath = parentPath;
    this.attributes = {};
    this.children = [];
  }
}

/**
 * Parse raw USDA string into UsdStage data structure.
 */
export function parseUSDA(usdaText) {
  const stage = new UsdStage();
  const lines = usdaText.split('\n');

  // Parse stage header metadata
  const upAxisMatch = usdaText.match(/upAxis\s*=\s*"([^"]+)"/);
  if (upAxisMatch) stage.metadata.upAxis = upAxisMatch[1];

  const defaultPrimMatch = usdaText.match(/defaultPrim\s*=\s*"([^"]+)"/);
  if (defaultPrimMatch) stage.metadata.defaultPrim = defaultPrimMatch[1];

  const primStack = []; // Stack of active parent paths
  let currentPrim = null;

  // Regex helpers
  const defPrimRegex = /^\s*def\s+([A-Za-z0-9_]+)\s+"([^"]+)"/;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line || line.startsWith('#') || line.startsWith('//')) continue;

    // Detect prim start
    const defMatch = line.match(defPrimRegex);
    if (defMatch) {
      const type = defMatch[1];
      const name = defMatch[2];
      const parentPath = primStack.length > 0 ? primStack[primStack.length - 1] : '';
      const path = `${parentPath}/${name}`;

      currentPrim = new UsdPrim(name, type, path, parentPath || '/');
      stage.addPrim(currentPrim);
      primStack.push(path);
      continue;
    }

    // Detect scope close
    if (line === '}' || line.startsWith('}')) {
      primStack.pop();
      currentPrim = primStack.length > 0 ? stage.getPrim(primStack[primStack.length - 1]) : null;
      continue;
    }

    // Parse attributes inside current prim
    if (currentPrim) {
      const eqIdx = line.indexOf('=');
      if (eqIdx !== -1) {
        const attrDecl = line.slice(0, eqIdx).trim();
        let valPart = line.slice(eqIdx + 1).trim();

        // If array value, accumulate across lines until closing bracket ']'
        if (valPart.startsWith('[') || valPart.includes('[')) {
          while (!valPart.includes(']') && i + 1 < lines.length) {
            i++;
            valPart += ' ' + lines[i].trim();
          }
        }

        // points attribute
        if (attrDecl.includes('points')) {
          currentPrim.attributes.points = parseVector3List(valPart);
        }
        // faceVertexIndices
        else if (attrDecl.includes('faceVertexIndices')) {
          currentPrim.attributes.faceVertexIndices = parseIntList(valPart);
        }
        // faceVertexCounts
        else if (attrDecl.includes('faceVertexCounts')) {
          currentPrim.attributes.faceVertexCounts = parseIntList(valPart);
        }
        // displayColor
        else if (attrDecl.includes('displayColor')) {
          const colors = parseVector3List(valPart);
          if (colors.length > 0) {
            currentPrim.attributes.displayColor = colors[0];
          }
        }
        // extent
        else if (attrDecl.includes('extent')) {
          currentPrim.attributes.extent = parseVector3List(valPart);
        }
        // translate / transform
        else if (attrDecl.includes('xformOp:translate')) {
          const match = valPart.match(/\(([^)]+)\)/);
          if (match) {
            const parts = match[1].split(',').map(n => parseFloat(n.trim()));
            if (parts.length >= 3) {
              currentPrim.attributes.translate = parts;
            }
          }
        }
      }
    }
  }

  return stage;
}

function parseVector3List(text) {
  const vectors = [];
  const matches = text.matchAll(/\(\s*([-\d.eE]+)\s*,\s*([-\d.eE]+)\s*,\s*([-\d.eE]+)\s*\)/g);
  for (const m of matches) {
    vectors.push([parseFloat(m[1]), parseFloat(m[2]), parseFloat(m[3])]);
  }
  return vectors;
}

function parseIntList(text) {
  return text
    .replace(/\[|\]/g, ' ')
    .split(',')
    .map(s => parseInt(s.trim(), 10))
    .filter(n => !isNaN(n));
}

/**
 * Convert a parsed USD Mesh Prim into a Three.js BufferGeometry mesh.
 */
export function buildThreeMeshFromUsdPrim(prim) {
  if (prim.type !== 'Mesh' || !prim.attributes.points || prim.attributes.points.length === 0) {
    return null;
  }

  const { points, faceVertexIndices, faceVertexCounts, displayColor, translate } = prim.attributes;
  const geometry = new THREE.BufferGeometry();

  const triIndices = [];
  if (faceVertexCounts && faceVertexCounts.length > 0 && faceVertexIndices && faceVertexIndices.length > 0) {
    let offset = 0;
    for (const count of faceVertexCounts) {
      if (count === 3) {
        triIndices.push(
          faceVertexIndices[offset],
          faceVertexIndices[offset + 1],
          faceVertexIndices[offset + 2]
        );
      } else if (count === 4) {
        // Quad triangulation: (0, 1, 2) and (0, 2, 3)
        triIndices.push(
          faceVertexIndices[offset],
          faceVertexIndices[offset + 1],
          faceVertexIndices[offset + 2],
          faceVertexIndices[offset],
          faceVertexIndices[offset + 2],
          faceVertexIndices[offset + 3]
        );
      } else {
        // Simple fan triangulation for n-gons
        for (let j = 1; j < count - 1; j++) {
          triIndices.push(
            faceVertexIndices[offset],
            faceVertexIndices[offset + j],
            faceVertexIndices[offset + j + 1]
          );
        }
      }
      offset += count;
    }
  }

  // Flatten vertex positions
  const posArray = new Float32Array(points.length * 3);
  for (let i = 0; i < points.length; i++) {
    posArray[i * 3] = points[i][0];
    posArray[i * 3 + 1] = points[i][1];
    posArray[i * 3 + 2] = points[i][2];
  }

  geometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
  if (triIndices.length > 0) {
    geometry.setIndex(triIndices);
  }
  geometry.computeVertexNormals();

  // Material setup
  const color = displayColor
    ? new THREE.Color(displayColor[0], displayColor[1], displayColor[2])
    : new THREE.Color(0x6366f1);

  const material = new THREE.MeshStandardMaterial({
    color: color,
    roughness: 0.35,
    metalness: 0.65,
    side: THREE.DoubleSide,
  });

  const mesh = new THREE.Mesh(geometry, material);
  mesh.name = prim.name;
  mesh.castShadow = true;
  mesh.receiveShadow = true;

  if (translate) {
    mesh.position.set(translate[0], translate[1], translate[2]);
  }

  mesh.userData = {
    primPath: prim.path,
    usdPath: prim.path,
    usdType: prim.type,
    attributes: prim.attributes,
    origMaterial: material,
  };

  return mesh;
}

/**
 * Generate a default demo OpenUSD Stage string.
 */
export function getDemoUSDA() {
  return `#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1.0
    upAxis = "Y"
)

def Xform "World" (
    kind = "group"
)
{
    def Xform "Environment" (
        kind = "group"
    )
    {
        def Mesh "SoundstageFloor"
        {
            float3[] extent = [(-6, 0, -6), (6, 0, 6)]
            int[] faceVertexCounts = [4]
            int[] faceVertexIndices = [0, 1, 2, 3]
            point3f[] points = [(-6, 0, -6), (6, 0, -6), (6, 0, 6), (-6, 0, 6)]
            color3f[] primvars:displayColor = [(0.15, 0.18, 0.25)]
        }
    }

    def Xform "Characters" (
        kind = "group"
    )
    {
        def Mesh "HeroArmor"
        {
            float3[] extent = [(-1, 0, -1), (1, 2, 1)]
            int[] faceVertexCounts = [4, 4, 4, 4, 4, 4]
            int[] faceVertexIndices = [
                0, 1, 2, 3,
                4, 5, 6, 7,
                0, 4, 7, 3,
                1, 5, 6, 2,
                3, 2, 6, 7,
                0, 1, 5, 4
            ]
            point3f[] points = [
                (-0.4, 0.2, -0.3), (0.4, 0.2, -0.3), (0.4, 1.8, -0.3), (-0.4, 1.8, -0.3),
                (-0.4, 0.2, 0.3), (0.4, 0.2, 0.3), (0.4, 1.8, 0.3), (-0.4, 1.8, 0.3)
            ]
            color3f[] primvars:displayColor = [(0.38, 0.45, 0.95)]
            double3 xformOp:translate = (0, 0, 0)
        }

        def Mesh "Pauldrons"
        {
            float3[] extent = [(-0.8, 1.4, -0.25), (0.8, 1.7, 0.25)]
            int[] faceVertexCounts = [4, 4]
            int[] faceVertexIndices = [0, 1, 2, 3, 4, 5, 6, 7]
            point3f[] points = [
                (-0.75, 1.4, -0.2), (-0.45, 1.4, -0.2), (-0.45, 1.7, 0.2), (-0.75, 1.7, 0.2),
                (0.45, 1.4, -0.2), (0.75, 1.4, -0.2), (0.75, 1.7, 0.2), (0.45, 1.7, 0.2)
            ]
            color3f[] primvars:displayColor = [(0.92, 0.65, 0.15)]
        }
    }

    def Camera "CineCamera"
    {
        double3 xformOp:translate = (4, 3, 6)
    }
}
`;
}
