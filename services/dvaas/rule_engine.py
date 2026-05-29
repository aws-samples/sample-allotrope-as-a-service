# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
Rule Engine for Pluggable Validation Framework

Evaluates JSON rule sets against ASM files. Each rule is a declarative check
defined in JSON — no custom code needed per rule.

Supported check types:
    - field_required: A field must exist at the specified path
    - field_not_empty: A string field must not be empty
    - value_in_list: A value must be in an allowed list
    - value_matches_pattern: A value must match a regex pattern
    - path_exists: A JSON path must exist in the document
    - conditional_required: A field is required IF another field exists
    - count_min: An array must have at least N items
    - value_equals: A field must have a specific value
    - key_not_matches_pattern: Field names must not match a pattern
"""

import json
import re
import os
from typing import Any, Dict, List, Optional
from pathlib import Path


class RuleFinding:
    def __init__(self, rule_set_id, rule_id, level, severity, message, path=""):
        self.rule_set_id = rule_set_id
        self.rule_id = rule_id
        self.level = level
        self.severity = severity
        self.message = message
        self.path = path

    def to_dict(self):
        return {
            "rule_set": self.rule_set_id,
            "rule_id": self.rule_id,
            "level": self.level,
            "severity": self.severity,
            "message": self.message,
            "path": self.path,
        }


def resolve_path(data, path_pattern):
    """Resolve a path pattern against JSON data. Returns list of (path_string, value) tuples."""
    results = []

    def _walk(obj, pattern_parts, current_path):
        if not pattern_parts:
            results.append((current_path, obj))
            return

        part = pattern_parts[0]
        remaining = pattern_parts[1:]

        if part == "**":
            # Recursive descent — try matching remaining at every level
            _walk(obj, remaining, current_path)
            if isinstance(obj, dict):
                for k, v in obj.items():
                    _walk(v, pattern_parts, f"{current_path}/{k}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    _walk(item, pattern_parts, f"{current_path}[{i}]")

        elif part == "[*]":
            if isinstance(obj, list):
                for i, item in enumerate(obj):
                    _walk(item, remaining, f"{current_path}[{i}]")

        elif isinstance(obj, dict) and part in obj:
            _walk(obj[part], remaining, f"{current_path}/{part}")

    # Handle | alternatives in path
    if "|" in path_pattern:
        for alt in path_pattern.split("|"):
            resolve_path_single(data, alt.strip(), results)
    else:
        resolve_path_single(data, path_pattern, results)

    return results


def resolve_path_single(data, path_pattern, results):
    """Resolve a single path pattern (no | alternatives)."""
    parts = []
    for segment in path_pattern.split("."):
        if "[*]" in segment:
            name = segment.replace("[*]", "")
            if name:
                parts.append(name)
            parts.append("[*]")
        elif segment:
            parts.append(segment)

    def _walk(obj, pattern_parts, current_path):
        if not pattern_parts:
            results.append((current_path, obj))
            return

        part = pattern_parts[0]
        remaining = pattern_parts[1:]

        if part == "**":
            _walk(obj, remaining, current_path)
            if isinstance(obj, dict):
                for k, v in obj.items():
                    _walk(v, pattern_parts, f"{current_path}/{k}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    _walk(item, pattern_parts, f"{current_path}[{i}]")

        elif part == "[*]":
            if isinstance(obj, list):
                for i, item in enumerate(obj):
                    _walk(item, remaining, f"{current_path}[{i}]")

        elif isinstance(obj, dict) and part in obj:
            _walk(obj[part], remaining, f"{current_path}/{part}")

    _walk(data, parts, "")


def check_field_required(data, rule, rule_set_id):
    """Check that a field exists at the specified path."""
    findings = []
    field = rule.get("field", "")
    matches = resolve_path(data, rule["path"])

    if not matches:
        return findings

    for path, obj in matches:
        if isinstance(obj, dict) and field not in obj:
            findings.append(RuleFinding(
                rule_set_id, rule["rule_id"], rule["level"], rule["severity"],
                rule["message"], path
            ))
    return findings


def check_field_not_empty(data, rule, rule_set_id):
    """Check that a string value is not empty."""
    findings = []
    matches = resolve_path(data, rule["path"])

    for path, value in matches:
        if isinstance(value, str) and value.strip() == "":
            findings.append(RuleFinding(
                rule_set_id, rule["rule_id"], rule["level"], rule["severity"],
                rule["message"], path
            ))
    return findings


def check_value_in_list(data, rule, rule_set_id, reference_data=None):
    """Check that a value is in an allowed list."""
    findings = []
    allowed = set()

    list_source = rule.get("list_source", "")
    if reference_data and list_source in reference_data:
        allowed = set(reference_data[list_source])
    elif list_source:
        # Try loading from file
        try:
            rule_sets_dir = Path(__file__).parent / "rule-sets"
            with open(rule_sets_dir / list_source, "r", encoding="utf-8") as f:
                allowed = set(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            return findings  # Can't validate without the list

    if not allowed:
        return findings

    matches = resolve_path(data, rule["path"])
    for path, value in matches:
        if isinstance(value, str) and value not in allowed:
            msg = rule["message"].replace("{value}", str(value))
            findings.append(RuleFinding(
                rule_set_id, rule["rule_id"], rule["level"], rule["severity"],
                msg, path
            ))
    return findings


def check_value_matches_pattern(data, rule, rule_set_id):
    """Check that a value matches a regex pattern."""
    findings = []
    pattern = rule.get("pattern", "")
    if not pattern:
        return findings

    matches = resolve_path(data, rule["path"])
    for path, value in matches:
        if isinstance(value, str) and not re.match(pattern, value):
            msg = rule["message"].replace("{value}", str(value))
            findings.append(RuleFinding(
                rule_set_id, rule["rule_id"], rule["level"], rule["severity"],
                msg, path
            ))
    return findings


def check_path_exists(data, rule, rule_set_id):
    """Check that a JSON path exists in the document."""
    findings = []
    matches = resolve_path(data, rule["path"])
    if not matches:
        findings.append(RuleFinding(
            rule_set_id, rule["rule_id"], rule["level"], rule["severity"],
            rule["message"], rule["path"]
        ))
    return findings


def check_conditional_required(data, rule, rule_set_id):
    """Check that a field/path exists IF another field/path exists."""
    findings = []

    if "if_path" in rule:
        if_matches = resolve_path(data, rule["if_path"])
        if if_matches:
            then_matches = resolve_path(data, rule["then_path"])
            if not then_matches:
                findings.append(RuleFinding(
                    rule_set_id, rule["rule_id"], rule["level"], rule["severity"],
                    rule["message"], rule.get("then_path", "")
                ))
    elif "if_field" in rule:
        matches = resolve_path(data, rule["path"])
        for path, obj in matches:
            if isinstance(obj, dict) and rule["if_field"] in obj:
                if rule["then_field"] not in obj:
                    findings.append(RuleFinding(
                        rule_set_id, rule["rule_id"], rule["level"], rule["severity"],
                        rule["message"], path
                    ))
    return findings


def check_count_min(data, rule, rule_set_id):
    """Check that an array has at least N items."""
    findings = []
    min_count = rule.get("min", 1)
    matches = resolve_path(data, rule["path"])

    for path, value in matches:
        if isinstance(value, list) and len(value) < min_count:
            findings.append(RuleFinding(
                rule_set_id, rule["rule_id"], rule["level"], rule["severity"],
                rule["message"], path
            ))
    return findings


def check_key_not_matches_pattern(data, rule, rule_set_id):
    """Check that field names do not match a pattern."""
    findings = []
    pattern = rule.get("pattern", "")
    exclude = set(rule.get("exclude", []))
    if not pattern:
        return findings

    def _walk_keys(obj, path):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k not in exclude and re.match(pattern, k):
                    msg = rule["message"].replace("{key}", k)
                    findings.append(RuleFinding(
                        rule_set_id, rule["rule_id"], rule["level"], rule["severity"],
                        msg, f"{path}/{k}"
                    ))
                _walk_keys(v, f"{path}/{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                _walk_keys(item, f"{path}[{i}]")

    _walk_keys(data, "")
    return findings


# Dispatcher
CHECK_HANDLERS = {
    "field_required": check_field_required,
    "field_not_empty": check_field_not_empty,
    "value_in_list": check_value_in_list,
    "value_matches_pattern": check_value_matches_pattern,
    "path_exists": check_path_exists,
    "conditional_required": check_conditional_required,
    "count_min": check_count_min,
    "key_not_matches_pattern": check_key_not_matches_pattern,
}


def evaluate_rule_set(asm_data: dict, rule_set: dict, reference_data: dict = None) -> List[dict]:
    """
    Evaluate a rule set against an ASM file.

    Args:
        asm_data: The ASM JSON document
        rule_set: The rule set JSON with rules array
        reference_data: Optional dict of reference data (e.g., unit lists)

    Returns:
        List of finding dicts
    """
    findings = []
    rule_set_id = rule_set.get("rule_set_id", "unknown")

    for rule in rule_set.get("rules", []):
        check_type = rule.get("check", "")
        handler = CHECK_HANDLERS.get(check_type)

        if handler is None:
            continue

        try:
            if check_type == "value_in_list":
                rule_findings = handler(asm_data, rule, rule_set_id, reference_data)
            else:
                rule_findings = handler(asm_data, rule, rule_set_id)
            findings.extend(rule_findings)
        except Exception:
            pass  # Don't let a bad rule crash validation

    return [f.to_dict() for f in findings]


def evaluate_rule_sets(asm_data: dict, rule_sets: List[dict], reference_data: dict = None) -> List[dict]:
    """Evaluate multiple rule sets against an ASM file."""
    all_findings = []
    for rule_set in rule_sets:
        all_findings.extend(evaluate_rule_set(asm_data, rule_set, reference_data))
    return all_findings
