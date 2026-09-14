"""MaterialX node graph parser and translation engine bridging film and game shaders."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

try:
    import MaterialX as mx
    HAS_MATERIALX = True
except ImportError:
    HAS_MATERIALX = False


@dataclass
class SurfaceAppearance:
    """Standardized surface appearance parameters from MaterialX."""

    material_name: str
    base: float = 1.0
    base_color: Tuple[float, float, float] = (0.8, 0.8, 0.8)
    roughness: float = 0.2
    metalness: float = 0.0
    specular: float = 1.0
    emission: float = 0.0
    transmission: float = 0.0
    node_graph_xml: str = ""


class MaterialXTranslator:
    """Translates vendor-neutral MaterialX node graphs to Unreal HLSL and Cinematic OSL."""

    def __init__(self, mtlx_search_paths: Optional[list[Path]] = None) -> None:
        self.mtlx_search_paths = mtlx_search_paths or []

    def parse_document(self, mtlx_path: Path) -> SurfaceAppearance:
        """Parse a .mtlx document into a standardized SurfaceAppearance."""
        path = Path(mtlx_path)
        if not path.is_file():
            raise FileNotFoundError(f"MaterialX document not found: {path}")

        raw_xml = path.read_text(encoding="utf-8")

        if HAS_MATERIALX:
            doc = mx.createDocument()
            mx.readFromXmlFile(doc, str(path))

            # Find standard_surface or surface shader nodes
            shaders = doc.getNodes("standard_surface")
            if not shaders:
                shaders = [n for n in doc.getNodes() if "surface" in n.getType()]

            if shaders:
                shader = shaders[0]
                mat_name = shader.getName()

                def get_float(name: str, default: float) -> float:
                    inp = shader.getInput(name)
                    if inp and inp.hasValueString():
                        return float(inp.getValue())
                    return default

                def get_color3(name: str, default: Tuple[float, float, float]) -> Tuple[float, float, float]:
                    inp = shader.getInput(name)
                    if inp and inp.hasValueString():
                        val = inp.getValue()
                        if hasattr(val, "__getitem__"):
                            return (float(val[0]), float(val[1]), float(val[2]))
                        elif hasattr(val, "r") and hasattr(val, "g") and hasattr(val, "b"):
                            return (float(val.r), float(val.g), float(val.b))
                    return default

                base = get_float("base", 1.0)
                base_color = get_color3("base_color", (0.8, 0.8, 0.8))
                roughness = get_float("specular_roughness", 0.2)
                metalness = get_float("metalness", 0.0)
                specular = get_float("specular", 1.0)
                emission = get_float("emission", 0.0)
                transmission = get_float("transmission", 0.0)

                return SurfaceAppearance(
                    material_name=mat_name,
                    base=base,
                    base_color=base_color,
                    roughness=roughness,
                    metalness=metalness,
                    specular=specular,
                    emission=emission,
                    transmission=transmission,
                    node_graph_xml=raw_xml,
                )

        # XML ElementTree Fallback
        root = ET.fromstring(raw_xml)
        shader_elem = root.find(".//standard_surface")
        if shader_elem is None:
            shader_elem = root.find(".//*[@type='surfaceshader']")

        mat_name = shader_elem.attrib.get("name", "standard_surface") if shader_elem is not None else "material"
        base = 1.0
        base_color = (0.8, 0.8, 0.8)
        roughness = 0.2
        metalness = 0.0
        specular = 1.0
        emission = 0.0
        transmission = 0.0

        if shader_elem is not None:
            for inp in shader_elem.findall("input"):
                name = inp.attrib.get("name")
                val_str = inp.attrib.get("value", "")
                if name == "base" and val_str:
                    base = float(val_str)
                elif name == "base_color" and val_str:
                    parts = [float(x.strip()) for x in val_str.split(",")]
                    if len(parts) >= 3:
                        base_color = (parts[0], parts[1], parts[2])
                elif name in ("specular_roughness", "roughness") and val_str:
                    roughness = float(val_str)
                elif name == "metalness" and val_str:
                    metalness = float(val_str)
                elif name == "specular" and val_str:
                    specular = float(val_str)
                elif name == "emission" and val_str:
                    emission = float(val_str)
                elif name == "transmission" and val_str:
                    transmission = float(val_str)

        return SurfaceAppearance(
            material_name=mat_name,
            base=base,
            base_color=base_color,
            roughness=roughness,
            metalness=metalness,
            specular=specular,
            emission=emission,
            transmission=transmission,
            node_graph_xml=raw_xml,
        )

    def export_to_unreal_shader(self, appearance: SurfaceAppearance) -> str:
        """Export MaterialX parameters to an Unreal Engine HLSL shader snippet."""
        r, g, b = appearance.base_color
        return (
            f"// OpenLore MaterialX to Unreal Engine HLSL Translation\n"
            f"// Material: {appearance.material_name}\n\n"
            f"#ifndef OPENLORE_UNREAL_MATERIAL_{appearance.material_name.upper()}\n"
            f"#define OPENLORE_UNREAL_MATERIAL_{appearance.material_name.upper()}\n\n"
            f"struct FOpenLoreMaterialInput {{\n"
            f"    float3 BaseColor;\n"
            f"    float  Metallic;\n"
            f"    float  Roughness;\n"
            f"    float  Specular;\n"
            f"    float3 EmissiveColor;\n"
            f"}};\n\n"
            f"FOpenLoreMaterialInput Get{appearance.material_name}Parameters() {{\n"
            f"    FOpenLoreMaterialInput Mat;\n"
            f"    Mat.BaseColor     = float3({r:.4f}f, {g:.4f}f, {b:.4f}f) * {appearance.base:.4f}f;\n"
            f"    Mat.Metallic      = {appearance.metalness:.4f}f;\n"
            f"    Mat.Roughness     = {appearance.roughness:.4f}f;\n"
            f"    Mat.Specular      = {appearance.specular:.4f}f;\n"
            f"    Mat.EmissiveColor = float3({appearance.emission:.4f}f, {appearance.emission:.4f}f, {appearance.emission:.4f}f);\n"
            f"    return Mat;\n"
            f"}}\n\n"
            f"#endif // OPENLORE_UNREAL_MATERIAL_{appearance.material_name.upper()}\n"
        )

    def export_to_cinematic_osl(self, appearance: SurfaceAppearance) -> str:
        """Export MaterialX parameters to an Open Shading Language (OSL) surface shader."""
        r, g, b = appearance.base_color
        return (
            f"// OpenLore MaterialX to Cinematic OSL Translation\n"
            f"// Material: {appearance.material_name}\n\n"
            f"surface {appearance.material_name}_osl (\n"
            f"    float base = {appearance.base:.4f},\n"
            f"    color base_color = color({r:.4f}, {g:.4f}, {b:.4f}),\n"
            f"    float roughness = {appearance.roughness:.4f},\n"
            f"    float metalness = {appearance.metalness:.4f},\n"
            f"    float specular = {appearance.specular:.4f},\n"
            f"    output closure color Ci = 0\n"
            f") {{\n"
            f"    color diffuse_component = base * base_color * oren_nayar(N, roughness);\n"
            f"    color specular_component = specular * microfacet(\"ggx\", N, roughness, 1.5, 0);\n"
            f"    Ci = mix(diffuse_component, specular_component, metalness);\n"
            f"}}\n"
        )
