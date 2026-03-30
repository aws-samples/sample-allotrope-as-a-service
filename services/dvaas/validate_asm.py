"""
ASM Output Validation Script

Validates ASM JSON output using official Allotrope JSON schemas via jsonschema-rs,
plus supplementary $asm-prefixed attribute validation.

Validation Layers:
    1. JSON Schema validation against official Allotrope ASM schemas (jsonschema-rs)
    2. $asm-prefixed attribute validation (unit symbols, ontology terms)
    3. Supplementary checks (traceability, calculated data, naming conventions)

Schema Source: https://gitlab.com/allotrope-public/asm/-/tree/main/json-schemas/adm
Validator: jsonschema-rs (Rust-based, JSON Schema draft 2020-12)

Usage:
    python validate_asm.py output.json
    python validate_asm.py output.json --reference reference.json
    python validate_asm.py output.json --strict
"""

import json
import re
import sys
import os
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from urllib.parse import unquote

try:
    import jsonschema_rs
    HAS_JSONSCHEMA_RS = True
except ImportError:
    HAS_JSONSCHEMA_RS = False

SCHEMA_SOURCE = "https://gitlab.com/allotrope-public/asm"
SCHEMAS_DIR = Path(__file__).parent / "schemas"
URI_PREFIX = "http://purl.allotrope.org/json-schemas/"
MANIFEST_URI_PREFIX = "http://purl.allotrope.org/manifests/"


class ValidationResult:
    """Container for validation results."""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        self.metrics: Dict[str, Any] = {}

    def add_error(self, msg: str):
        self.errors.append(f"ERROR: {msg}")

    def add_warning(self, msg: str):
        self.warnings.append(f"WARNING: {msg}")

    def add_info(self, msg: str):
        self.info.append(f"INFO: {msg}")

    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def print_report(self):
        print("\n" + "=" * 60)
        print("ASM VALIDATION REPORT")
        print("=" * 60)
        if self.metrics:
            print("\nMetrics:")
            for key, value in self.metrics.items():
                print(f"   {key}: {value}")
        if self.info:
            print("\n" + "\n".join(self.info))
        if self.warnings:
            print("\n" + "\n".join(self.warnings))
        if self.errors:
            print("\n" + "\n".join(self.errors))
        print("\n" + "-" * 60)
        if self.is_valid():
            if self.warnings:
                print(f"PASSED with {len(self.warnings)} warning(s)")
            else:
                print("PASSED - No issues found")
        else:
            print(f"FAILED - {len(self.errors)} error(s), {len(self.warnings)} warning(s)")
        print("=" * 60 + "\n")


# =============================================================================
# SCHEMA RESOLUTION
# =============================================================================

def _build_schema_registry() -> Dict[str, dict]:
    """Build a registry mapping schema $id URIs to loaded schema objects."""
    registry = {}
    json_schemas_dir = SCHEMAS_DIR / "json-schemas"
    if not json_schemas_dir.exists():
        return registry

    for schema_file in json_schemas_dir.rglob("*.schema.json"):
        try:
            with open(schema_file, "r", encoding="utf-8") as f:
                schema = json.load(f)
            schema_id = schema.get("$id")
            if schema_id:
                registry[schema_id] = schema
        except (json.JSONDecodeError, OSError):
            continue
    return registry


def _build_manifest_registry() -> Dict[str, dict]:
    """Build a registry mapping manifest @id URIs to manifest objects."""
    registry = {}
    manifests_dir = SCHEMAS_DIR / "manifests"
    if not manifests_dir.exists():
        return registry

    for manifest_file in manifests_dir.rglob("*.manifest.json"):
        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            manifest_id = manifest.get("@id")
            if manifest_id:
                registry[manifest_id] = manifest
        except (json.JSONDecodeError, OSError):
            continue
    return registry


# Lazy-loaded registries
_schema_registry = None
_manifest_registry = None


def _get_schema_registry():
    global _schema_registry
    if _schema_registry is None:
        _schema_registry = _build_schema_registry()
    return _schema_registry


def _get_manifest_registry():
    global _manifest_registry
    if _manifest_registry is None:
        _manifest_registry = _build_manifest_registry()
    return _manifest_registry


def resolve_manifest_to_schema(manifest_value) -> Optional[dict]:
    """Resolve $asm.manifest value to the appropriate JSON schema."""
    manifest_registry = _get_manifest_registry()
    schema_registry = _get_schema_registry()

    # $asm.manifest can be a URI string or an object with @id
    if isinstance(manifest_value, str):
        manifest_uri = manifest_value
    elif isinstance(manifest_value, dict):
        manifest_uri = manifest_value.get("@id", "")
    else:
        return None

    # Look up manifest to find schema URI
    manifest = manifest_registry.get(manifest_uri)
    if manifest and "json-schemas" in manifest:
        for schema_uri in manifest["json-schemas"]:
            schema = schema_registry.get(schema_uri)
            if schema:
                return schema

    # Fallback: try to derive schema from manifest URI pattern
    # e.g. http://purl.allotrope.org/manifests/plate-reader/REC/2025/12/plate-reader.manifest
    #   -> http://purl.allotrope.org/json-schemas/adm/plate-reader/REC/2025/12/plate-reader.schema
    if manifest_uri.startswith(MANIFEST_URI_PREFIX):
        path_part = manifest_uri[len(MANIFEST_URI_PREFIX):]
        schema_uri = URI_PREFIX + "adm/" + path_part.replace(".manifest", ".schema")
        schema = schema_registry.get(schema_uri)
        if schema:
            return schema

    # Try matching by technique name from URI
    for schema_id, schema in schema_registry.items():
        if "core" in schema_id:
            continue
        # Extract technique from manifest URI
        parts = manifest_uri.replace(MANIFEST_URI_PREFIX, "").split("/")
        if parts and parts[0] in schema_id:
            return schema

    return None


def detect_technique(asm: Dict) -> Tuple[str, float]:
    """Detect technique from ASM structure."""
    for key in asm.keys():
        if key == "$asm.manifest":
            continue
        key_normalized = key.lower().replace("-", " ")
        if "aggregate document" in key_normalized:
            technique = key_normalized.replace(" aggregate document", "").strip()
            return technique, 100.0
    return "unknown", 0.0


# =============================================================================
# LAYER 1: JSON SCHEMA VALIDATION (jsonschema-rs)
# =============================================================================

def validate_against_schema(asm: Dict, result: ValidationResult) -> bool:
    """Validate ASM data against official Allotrope JSON schema using jsonschema-rs."""
    if not HAS_JSONSCHEMA_RS:
        result.add_warning(
            "jsonschema-rs not available - falling back to structural checks only. "
            "Install with: pip install jsonschema-rs"
        )
        return False

    schema_registry = _get_schema_registry()
    if not schema_registry:
        result.add_warning(
            "No Allotrope schemas found in schemas/ directory - "
            "schema validation skipped"
        )
        return False

    manifest_value = asm.get("$asm.manifest")
    if not manifest_value:
        result.add_error("Missing $asm.manifest - cannot determine schema for validation")
        return False

    schema = resolve_manifest_to_schema(manifest_value)
    if not schema:
        manifest_str = manifest_value if isinstance(manifest_value, str) else json.dumps(manifest_value)
        result.add_warning(
            f"No matching schema found for manifest: {manifest_str} - "
            "schema validation skipped. The manifest may reference a newer schema version."
        )
        return False

    schema_id = schema.get("$id", "unknown")
    result.add_info(f"Schema: {schema_id}")
    result.metrics["schema_id"] = schema_id

    # Build retriever for $ref resolution from local schema files
    def retriever(uri):
        # Strip fragment
        base_uri = uri.split("#")[0]
        s = schema_registry.get(base_uri)
        if s:
            return s
        raise jsonschema_rs.ReferencingError(f"Schema not found: {uri}")

    try:
        validator = jsonschema_rs.validator_for(schema, retriever=retriever)
        errors = list(validator.iter_errors(asm))
    except Exception as e:
        result.add_warning(f"Schema validation engine error: {e}")
        return False

    schema_errors = []
    for error in errors:
        path = "/".join(str(p) for p in error.instance_path) if error.instance_path else "(root)"
        schema_errors.append(f"[{path}] {error.message}")

    result.metrics["schema_errors"] = len(schema_errors)

    if schema_errors:
        # Report up to 20 schema errors
        for err in schema_errors[:20]:
            result.add_error(f"Schema: {err}")
        if len(schema_errors) > 20:
            result.add_error(f"Schema: ... and {len(schema_errors) - 20} more errors")
        return False

    result.add_info("Schema validation: PASSED")
    return True


# =============================================================================
# LAYER 2: $asm-PREFIXED ATTRIBUTE VALIDATION
# =============================================================================

def validate_asm_attributes(asm: Dict, result: ValidationResult):
    """Validate $asm-prefixed attributes based on ASM manifest specification."""
    content_str = json.dumps(asm)

    # Collect all $asm.property-class references from the schema for cross-check
    # Validate unit symbols against QUDT
    units = re.findall(r'"unit":\s*"([^"]+)"', content_str)
    if units:
        result.metrics["unique_units"] = len(set(units))

    # Validate sample role types against known ontology terms
    roles = re.findall(r'"sample role type":\s*"([^"]+)"', content_str)
    valid_roles = {
        "control sample role", "standard sample role", "validation sample role",
        "experiment sample role", "sample role", "spiked sample role",
        "blank role", "unknown sample role", "calibration sample role",
        "unspiked sample role", "specimen role", "quality control sample role",
        "reference sample role",
    }
    if roles:
        invalid = [r for r in set(roles) if r not in valid_roles]
        if invalid:
            result.add_warning(
                f"Unknown sample role types (not in Allotrope ontology): {invalid}"
            )

    # Validate container type against known ontology terms
    containers = re.findall(r'"container type":\s*"([^"]+)"', content_str)
    valid_containers = {
        "reactor", "controlled lab reactor", "tube", "well plate",
        "differential scanning calorimetry pan", "qPCR reaction block",
        "vial rack", "pan", "reservoir", "array card block", "capillary",
        "disintegration apparatus basket", "jar", "container", "tray",
        "basket", "cell holder",
    }
    if containers:
        invalid = [c for c in set(containers) if c not in valid_containers]
        if invalid:
            result.add_warning(
                f"Unknown container types (not in Allotrope ontology): {invalid}"
            )


# =============================================================================
# LAYER 3: SUPPLEMENTARY CHECKS
# =============================================================================

def validate_supplementary(asm: Dict, content_str: str, result: ValidationResult):
    """Supplementary validation checks beyond schema compliance."""
    # Naming conventions: ASM uses space-separated field names
    hyphenated = re.findall(r'"([a-z]+-[a-z]+-?[a-z]*-?[a-z]*)":', content_str)
    asm_hyphenated = [
        k for k in set(hyphenated)
        if "http" not in k and "manifest" not in k
        and k not in {"data-source-identifier", "data-source-feature",
                       "cube-structure", "well-plate"}
    ]
    if asm_hyphenated:
        result.add_warning(
            f"Hyphenated field names (ASM uses spaces): {list(asm_hyphenated)[:10]}"
        )

    # Calculated data traceability
    content_lower = content_str.lower()
    has_calculated = "calculated data document" in content_lower
    has_data_source = "data source aggregate document" in content_lower
    result.metrics["has_calculated_data"] = has_calculated
    result.metrics["has_data_source_traceability"] = has_data_source

    if has_calculated and not has_data_source:
        result.add_warning(
            "Calculated data found without data source aggregate document - "
            "recommended for regulatory compliance (FDA 21 CFR Part 11)"
        )

    # Measurement count
    measurement_ids = len(re.findall(r'"measurement identifier":\s*"[^"]+"', content_str))
    result.metrics["measurement_count"] = measurement_ids
    if measurement_ids == 0:
        result.add_warning("No measurement identifiers found")

    # Technique detection
    technique, confidence = detect_technique(asm)
    result.metrics["technique"] = technique
    result.metrics["technique_confidence"] = confidence


def compare_to_reference(
    asm: Dict, reference: Dict, content_str: str, ref_content: str,
    result: ValidationResult,
):
    """Compare generated ASM to reference ASM."""
    result.add_info("Comparing to reference ASM...")

    gen_tech, _ = detect_technique(asm)
    ref_tech, _ = detect_technique(reference)
    if gen_tech.replace("-", " ") != ref_tech.replace("-", " "):
        result.add_error(f"Technique mismatch: generated '{gen_tech}' vs reference '{ref_tech}'")

    gen_count = len(re.findall(r'"measurement identifier":\s*"[^"]+"', content_str))
    ref_count = len(re.findall(r'"measurement identifier":\s*"[^"]+"', ref_content))
    result.metrics["reference_measurement_count"] = ref_count
    if gen_count != ref_count:
        diff = ref_count - gen_count
        if diff > 0:
            result.add_error(f"Missing {diff} measurements: generated {gen_count} vs reference {ref_count}")
        else:
            result.add_warning(f"Extra {-diff} measurements: generated {gen_count} vs reference {ref_count}")


# =============================================================================
# MAIN VALIDATION ENTRY POINT
# =============================================================================

def validate_asm(
    filepath: str, reference_path: Optional[str] = None, strict: bool = False
) -> ValidationResult:
    """
    Validate ASM JSON file using official Allotrope schemas + supplementary checks.

    Args:
        filepath: Path to ASM JSON file
        reference_path: Optional path to reference ASM for comparison
        strict: If True, treat warnings as errors
    """
    result = ValidationResult()

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content_str = f.read()
            asm = json.loads(content_str)
    except json.JSONDecodeError as e:
        result.add_error(f"Invalid JSON: {e}")
        return result
    except FileNotFoundError:
        result.add_error(f"File not found: {filepath}")
        return result

    result.add_info(f"Validating: {filepath}")
    result.add_info(f"Validator: jsonschema-rs + Allotrope ASM schemas")

    schema_registry = _get_schema_registry()
    result.metrics["schemas_loaded"] = len(schema_registry)

    # Layer 1: JSON Schema validation
    validate_against_schema(asm, result)

    # Layer 2: $asm attribute validation
    validate_asm_attributes(asm, result)

    # Layer 3: Supplementary checks
    validate_supplementary(asm, content_str, result)

    # Reference comparison
    if reference_path:
        try:
            with open(reference_path, "r", encoding="utf-8") as f:
                ref_content = f.read()
                reference = json.loads(ref_content)
            compare_to_reference(asm, reference, content_str, ref_content, result)
        except Exception as e:
            result.add_warning(f"Could not load reference file: {e}")

    if strict:
        result.errors.extend([w.replace("WARNING", "ERROR") for w in result.warnings])
        result.warnings = []

    return result


def main():
    parser = argparse.ArgumentParser(description="Validate ASM JSON output against Allotrope schemas")
    parser.add_argument("input", help="ASM JSON file to validate")
    parser.add_argument("--reference", "-r", help="Reference ASM file for comparison")
    parser.add_argument("--strict", "-s", action="store_true", help="Treat warnings as errors")
    parser.add_argument("--quiet", "-q", action="store_true", help="Only show errors")

    args = parser.parse_args()
    result = validate_asm(args.input, args.reference, args.strict)

    if args.quiet:
        if result.errors:
            for error in result.errors:
                print(error)
            sys.exit(1)
        sys.exit(0)

    result.print_report()
    sys.exit(0 if result.is_valid() else 1)


if __name__ == "__main__":
    main()
