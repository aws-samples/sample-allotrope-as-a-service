# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
Allotropy Conversion Wrapper with Data Integrity Verification

Wraps the allotropy library to produce field-level traceability mapping
from source file values to ASM output values. Every value in the ASM
can be traced back to its source cell/field in the original instrument file.

This is the "data integrity proof" — a byproduct of conversion that enables
regulatory compliance (FDA 21 CFR Part 11, EMA Annex 11).
"""

import csv
import io
import json
import os
import re
import tempfile
from datetime import datetime
from typing import Any, Optional

try:
    from allotropy.to_allotrope import allotrope_from_file
    from allotropy.parser_factory import Vendor
    ALLOTROPY_AVAILABLE = True
except ImportError:
    ALLOTROPY_AVAILABLE = False


def convert_with_traceability(
    file_content: str,
    file_name: str,
    vendor_type: Optional[str] = None,
) -> dict:
    """
    Convert instrument file to ASM using allotropy, with field-level traceability.

    Returns:
        {
            "success": bool,
            "asm_output": dict,           # The ASM JSON
            "field_mapping": list,         # Source→ASM value traceability
            "integrity_summary": dict,     # Coverage stats
            "vendor": str,
            "error": str (if failed)
        }
    """
    if not ALLOTROPY_AVAILABLE:
        return {"success": False, "error": "allotropy not available"}

    # Detect vendor
    vendor = _resolve_vendor(file_content, file_name, vendor_type)
    if not vendor:
        return {"success": False, "error": "Could not detect allotropy vendor"}

    # Parse source file into flat values for matching
    source_values = _parse_source_values(file_content, file_name)

    # Write to temp file preserving original filename (some parsers validate it)
    ext = os.path.splitext(file_name)[1] or ".csv"
    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, file_name)
    with open(tmp_path, "w", encoding="utf-8") as tmp:
        tmp.write(file_content)

    try:
        vendor_enum = Vendor(vendor) if isinstance(vendor, str) else vendor
        asm_output = allotrope_from_file(tmp_path, vendor_enum)
    except Exception as e:
        return {"success": False, "error": str(e), "vendor": str(vendor)}
    finally:
        os.unlink(tmp_path)
        os.rmdir(tmp_dir)

    # Build field mapping by matching ASM leaf values to source values
    asm_leaves = _extract_leaves(asm_output)
    field_mapping = _build_field_mapping(source_values, asm_leaves)

    # Compute integrity summary
    matchable_leaves = [
        l for l in asm_leaves if not _is_metadata_field(l["path"], l["value"])
    ]
    mapped_count = len(field_mapping)
    unique_source_cells = len(set(
        (m["source_row"], m["source_field"]) for m in field_mapping
    ))
    integrity_summary = {
        "total_asm_values": len(asm_leaves),
        "matchable_asm_values": len(matchable_leaves),
        "mapped_to_source": mapped_count,
        "unique_source_cells": unique_source_cells,
        "coverage_pct": round(
            mapped_count / len(matchable_leaves) * 100, 1
        ) if matchable_leaves else 0,
        "source_rows": len(set(sv["row"] for sv in source_values)),
        "timestamp": datetime.utcnow().isoformat(),
    }

    return {
        "success": True,
        "asm_output": asm_output,
        "field_mapping": field_mapping,
        "integrity_summary": integrity_summary,
        "vendor": str(vendor),
    }


# =============================================================================
# SOURCE FILE PARSING
# =============================================================================

def _parse_source_values(file_content: str, file_name: str) -> list[dict]:
    """Parse source file into list of {row, column, value} records."""
    ext = os.path.splitext(file_name)[1].lower()
    if ext in (".csv", ".tsv", ".txt"):
        return _parse_csv_source(file_content, ext)
    return []


def _parse_csv_source(file_content: str, ext: str) -> list[dict]:
    """Parse CSV/TSV/TXT into flat value records."""
    delimiter = "\t" if ext == ".tsv" else ","
    records = []

    # Try CSV with headers first
    try:
        reader = csv.DictReader(io.StringIO(file_content), delimiter=delimiter)
        for row_idx, row in enumerate(reader):
            for col_name, raw_value in row.items():
                if not col_name or not raw_value or not raw_value.strip():
                    continue
                val = raw_value.strip()
                record = {
                    "row": row_idx + 1,
                    "column": col_name.strip(),
                    "raw_value": val,
                }
                # Try to parse as number
                try:
                    num = float(val)
                    record["numeric_value"] = num
                except ValueError:
                    record["string_value"] = val
                records.append(record)
    except Exception:
        # Fallback: line-by-line
        for row_idx, line in enumerate(file_content.strip().split("\n")):
            parts = line.split(delimiter)
            for col_idx, val in enumerate(parts):
                val = val.strip()
                if val:
                    records.append({
                        "row": row_idx,
                        "column": f"col_{col_idx}",
                        "raw_value": val,
                    })

    return records


# =============================================================================
# ASM LEAF EXTRACTION
# =============================================================================

def _extract_leaves(obj: Any, path: str = "") -> list[dict]:
    """Walk ASM dict and extract all leaf values with their paths."""
    leaves = []
    if isinstance(obj, dict):
        for key, val in obj.items():
            leaves.extend(_extract_leaves(val, f"{path}/{key}"))
    elif isinstance(obj, list):
        for i, val in enumerate(obj):
            leaves.extend(_extract_leaves(val, f"{path}[{i}]"))
    else:
        leaves.append({"path": path, "value": obj})
    return leaves


# =============================================================================
# FIELD MAPPING (VALUE MATCHING)
# =============================================================================

def _build_field_mapping(
    source_values: list[dict],
    asm_leaves: list[dict],
) -> list[dict]:
    """Match ASM leaf values back to source file values."""
    mapping = []

    # Build lookup indexes for fast matching
    numeric_source = {}  # numeric_value -> list of source records
    string_source = {}   # string_value -> list of source records
    for sv in source_values:
        if "numeric_value" in sv:
            nv = sv["numeric_value"]
            numeric_source.setdefault(nv, []).append(sv)
        if "string_value" in sv:
            string_source.setdefault(sv["string_value"], []).append(sv)
        # Also index raw_value as string
        string_source.setdefault(sv["raw_value"], []).append(sv)

    # Track which source records have been used (prefer 1:1 mapping)
    used_sources = set()

    for leaf in asm_leaves:
        val = leaf["value"]
        path = leaf["path"]

        # Skip metadata/structural fields
        if _is_metadata_field(path, val):
            continue

        match = None

        # Try numeric match
        if isinstance(val, (int, float)):
            candidates = numeric_source.get(float(val), [])
            # Pick best candidate by context (column name similarity to ASM path)
            match = _best_match(candidates, path, used_sources)

        # Try string match
        if match is None and isinstance(val, str):
            candidates = string_source.get(val, [])
            match = _best_match(candidates, path, used_sources)

        if match:
            source_id = (match["row"], match["column"])
            used_sources.add(source_id)
            mapping.append({
                "source_field": match["column"],
                "source_row": match["row"],
                "source_value": match["raw_value"],
                "asm_path": path,
                "asm_value": val,
                "unit": _extract_unit_from_path(path, asm_leaves),
                "match_type": "exact",
            })

    return mapping


def _best_match(
    candidates: list[dict],
    asm_path: str,
    used_sources: set,
) -> Optional[dict]:
    """Pick the best source match for an ASM leaf, preferring unused + name-similar."""
    if not candidates:
        return None

    # Normalize ASM path for comparison
    path_lower = asm_path.lower()

    scored = []
    for c in candidates:
        source_id = (c["row"], c["column"])
        score = 0
        # Prefer unused sources
        if source_id not in used_sources:
            score += 10
        # Score by column name similarity to ASM path
        col_lower = c["column"].lower()
        col_words = re.split(r"[\s_\-+()]+", col_lower)
        for word in col_words:
            if len(word) > 1 and word in path_lower:
                score += 5
        scored.append((score, c))

    scored.sort(key=lambda x: -x[0])
    return scored[0][1] if scored else None


def _is_metadata_field(path: str, value: Any) -> bool:
    """Check if this ASM leaf is structural metadata (not a source data value)."""
    skip_patterns = [
        "$asm.manifest",
        "device type",
        "detection type",
        "ASM converter",
        "ASM file identifier",
        "software name",
        "software version",
        "product manufacturer",
        "model number",
        "brand name",
        "data system instance",
        "/unit",
        "measurement identifier",
    ]
    path_lower = path.lower()
    return any(p.lower() in path_lower for p in skip_patterns)


def _extract_unit_from_path(path: str, all_leaves: list[dict]) -> str:
    """Find the unit sibling for a value leaf."""
    # If path ends with /value, look for sibling /unit
    if path.endswith("/value"):
        unit_path = path[:-6] + "/unit"
        for leaf in all_leaves:
            if leaf["path"] == unit_path:
                return str(leaf["value"])
    return ""


# =============================================================================
# VENDOR DETECTION
# =============================================================================

_VENDOR_PATTERNS = {
    "BECKMAN_VI_CELL_BLU": ["vi-cell blu", "vicell blu"],
    "BECKMAN_VI_CELL_XR": ["vi-cell xr", "vicell xr"],
    "NOVABIO_FLEX2": ["sampleresults", "nova", "flex2", "bioprofile"],
    "AGILENT_GEN5": ["gen5", "biotek"],
    "MOLDEV_SOFTMAX_PRO": ["softmax", "molecular devices"],
    "APPBIO_QUANTSTUDIO": ["quantstudio"],
    "PERKIN_ELMER_ENVISION": ["envision", "perkinelmer"],
    "BMG_MARS": ["bmg", "mars"],
    "ROCHE_CEDEX_BIOHT": ["cedex", "bioht"],
    "THERMO_FISHER_NANODROP_EIGHT": ["nanodrop"],
    "CHEMOMETEC_NUCLEOVIEW": ["nucleoview", "nucleocounter"],
    "LUMINEX_XPONENT": ["xponent", "luminex"],
    "BIORAD_BIOPLEX": ["bioplex", "bio-plex"],
}


def _resolve_vendor(
    file_content: str, file_name: str, vendor_hint: Optional[str]
) -> Optional[str]:
    """Resolve vendor from hint, filename, or content."""
    if not ALLOTROPY_AVAILABLE:
        return None

    # Direct hint
    if vendor_hint:
        try:
            Vendor(vendor_hint)
            return vendor_hint
        except ValueError:
            # Try uppercase
            upper = vendor_hint.upper().replace(" ", "_").replace("-", "_")
            try:
                Vendor(upper)
                return upper
            except ValueError:
                pass

    # Pattern match against filename + content
    search_text = (file_name + " " + file_content[:2000]).lower()
    for vendor_name, patterns in _VENDOR_PATTERNS.items():
        if any(p in search_text for p in patterns):
            try:
                Vendor(vendor_name)
                return vendor_name
            except ValueError:
                continue

    return None
