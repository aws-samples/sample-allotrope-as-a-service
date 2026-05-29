# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import pytest


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------

class TestValidationResult:
    def test_default_is_valid(self, validate_asm_mod):
        result = validate_asm_mod.ValidationResult()
        assert result.is_valid() is True

    def test_add_error_makes_invalid(self, validate_asm_mod):
        result = validate_asm_mod.ValidationResult()
        result.add_error("Something failed")
        assert result.is_valid() is False
        assert len(result.errors) == 1
        assert "ERROR" in result.errors[0]

    def test_warning_alone_stays_valid(self, validate_asm_mod):
        result = validate_asm_mod.ValidationResult()
        result.add_warning("Check this")
        assert result.is_valid() is True
        assert len(result.warnings) == 1
        assert "WARNING" in result.warnings[0]

    def test_info_does_not_affect_validity(self, validate_asm_mod):
        result = validate_asm_mod.ValidationResult()
        result.add_info("Just info")
        assert result.is_valid() is True

    def test_multiple_errors(self, validate_asm_mod):
        result = validate_asm_mod.ValidationResult()
        result.add_error("Error 1")
        result.add_error("Error 2")
        assert len(result.errors) == 2
        assert result.is_valid() is False


# ---------------------------------------------------------------------------
# detect_technique
# ---------------------------------------------------------------------------

class TestDetectTechnique:
    def test_solution_analyzer(self, validate_asm_mod):
        asm = {"solution analyzer aggregate document": {}}
        technique, confidence = validate_asm_mod.detect_technique(asm)
        assert "solution analyzer" in technique
        assert confidence == 100.0

    def test_plate_reader(self, validate_asm_mod):
        asm = {"plate reader aggregate document": {}}
        technique, confidence = validate_asm_mod.detect_technique(asm)
        assert "plate reader" in technique
        assert confidence == 100.0

    def test_cell_counter(self, validate_asm_mod):
        asm = {"cell counting aggregate document": {}}
        technique, confidence = validate_asm_mod.detect_technique(asm)
        assert "cell counting" in technique

    def test_unknown_when_no_aggregate_key(self, validate_asm_mod):
        asm = {"$asm.manifest": "http://example.com", "other key": 1}
        technique, confidence = validate_asm_mod.detect_technique(asm)
        assert technique == "unknown"
        assert confidence == 0.0

    def test_manifest_key_skipped(self, validate_asm_mod):
        asm = {"$asm.manifest": "http://example.com"}
        technique, _ = validate_asm_mod.detect_technique(asm)
        assert technique == "unknown"


# ---------------------------------------------------------------------------
# validate_asm_attributes
# ---------------------------------------------------------------------------

class TestValidateAsmAttributes:
    def test_valid_sample_role_no_warning(self, validate_asm_mod):
        asm = {"doc": {"sample role type": "experiment sample role"}}
        result = validate_asm_mod.ValidationResult()
        validate_asm_mod.validate_asm_attributes(asm, result)
        role_warnings = [w for w in result.warnings if "sample role" in w.lower()]
        assert role_warnings == []

    def test_invalid_sample_role_warning(self, validate_asm_mod):
        asm = {"doc": {"sample role type": "invented-role-type"}}
        result = validate_asm_mod.ValidationResult()
        validate_asm_mod.validate_asm_attributes(asm, result)
        assert any("sample role" in w.lower() for w in result.warnings)

    def test_valid_container_no_warning(self, validate_asm_mod):
        asm = {"doc": {"container type": "well plate"}}
        result = validate_asm_mod.ValidationResult()
        validate_asm_mod.validate_asm_attributes(asm, result)
        container_warnings = [w for w in result.warnings if "container" in w.lower()]
        assert container_warnings == []

    def test_invalid_container_warning(self, validate_asm_mod):
        asm = {"doc": {"container type": "unknown-container-type"}}
        result = validate_asm_mod.ValidationResult()
        validate_asm_mod.validate_asm_attributes(asm, result)
        assert any("container" in w.lower() for w in result.warnings)

    def test_units_counted_in_metrics(self, validate_asm_mod):
        asm = {
            "m1": {"unit": "mmHg"},
            "m2": {"unit": "pH"},
            "m3": {"unit": "mmHg"},  # duplicate
        }
        result = validate_asm_mod.ValidationResult()
        validate_asm_mod.validate_asm_attributes(asm, result)
        assert result.metrics.get("unique_units", 0) > 0


# ---------------------------------------------------------------------------
# validate_supplementary
# ---------------------------------------------------------------------------

class TestValidateSupplementary:
    def test_hyphenated_field_names_warning(self, validate_asm_mod):
        asm = {"top": 1}
        content_str = '{"sample-identifier": "x"}'
        result = validate_asm_mod.ValidationResult()
        validate_asm_mod.validate_supplementary(asm, content_str, result)
        assert any("hyphenated" in w.lower() for w in result.warnings)

    def test_no_hyphenated_names_no_warning(self, validate_asm_mod):
        asm = {"top": 1}
        content_str = '{"sample identifier": "x"}'
        result = validate_asm_mod.ValidationResult()
        validate_asm_mod.validate_supplementary(asm, content_str, result)
        hyphen_warnings = [w for w in result.warnings if "hyphenated" in w.lower()]
        assert hyphen_warnings == []

    def test_calculated_data_without_traceability_warning(self, validate_asm_mod):
        asm = {}
        content_str = '{"calculated data document": [{}]}'
        result = validate_asm_mod.ValidationResult()
        validate_asm_mod.validate_supplementary(asm, content_str, result)
        assert any("calculated data" in w.lower() for w in result.warnings)

    def test_calculated_data_with_traceability_no_warning(self, validate_asm_mod):
        asm = {}
        content_str = (
            '{"calculated data document": [{}],'
            ' "data source aggregate document": {}}'
        )
        result = validate_asm_mod.ValidationResult()
        validate_asm_mod.validate_supplementary(asm, content_str, result)
        calc_warnings = [w for w in result.warnings if "calculated data" in w.lower()]
        assert calc_warnings == []

    def test_measurement_count_in_metrics(self, validate_asm_mod):
        asm = {}
        content_str = (
            '{"measurement identifier": "uuid-1",'
            ' "measurement identifier": "uuid-2"}'
        )
        result = validate_asm_mod.ValidationResult()
        validate_asm_mod.validate_supplementary(asm, content_str, result)
        # Metric should exist (even if JSON deduplicated keys)
        assert "measurement_count" in result.metrics

    def test_no_measurement_ids_warning(self, validate_asm_mod):
        asm = {}
        content_str = '{"some key": "value"}'
        result = validate_asm_mod.ValidationResult()
        validate_asm_mod.validate_supplementary(asm, content_str, result)
        assert any("measurement identifier" in w.lower() for w in result.warnings)


# ---------------------------------------------------------------------------
# compare_to_reference
# ---------------------------------------------------------------------------

class TestCompareToReference:
    def _make_asm(self, technique_key, measurement_count):
        measurements = [
            {"measurement identifier": f"uuid-{i}"} for i in range(measurement_count)
        ]
        content = json.dumps({"measurement identifier": f"uuid-{i}"} for i in range(measurement_count))
        asm = {technique_key: {}}
        content_str = json.dumps(asm)
        # Inject measurement identifiers into content_str for count detection
        ids = " ".join(
            f'"measurement identifier": "uuid-{i}"' for i in range(measurement_count)
        )
        content_str = "{" + ids + "}"
        return asm, content_str

    def test_same_technique_no_error(self, validate_asm_mod):
        asm = {"solution analyzer aggregate document": {}}
        ref = {"solution analyzer aggregate document": {}}
        result = validate_asm_mod.ValidationResult()
        content_str = '{"measurement identifier": "uuid-1"}'
        ref_content = '{"measurement identifier": "uuid-1"}'
        validate_asm_mod.compare_to_reference(asm, ref, content_str, ref_content, result)
        technique_errors = [e for e in result.errors if "technique" in e.lower()]
        assert technique_errors == []

    def test_different_technique_error(self, validate_asm_mod):
        asm = {"solution analyzer aggregate document": {}}
        ref = {"plate reader aggregate document": {}}
        result = validate_asm_mod.ValidationResult()
        validate_asm_mod.compare_to_reference(asm, ref, "{}", "{}", result)
        assert any("technique" in e.lower() for e in result.errors)

    def test_same_measurement_count_no_error(self, validate_asm_mod):
        asm = ref = {"solution analyzer aggregate document": {}}
        result = validate_asm_mod.ValidationResult()
        content = '{"measurement identifier": "uuid-1"}'
        validate_asm_mod.compare_to_reference(asm, ref, content, content, result)
        count_errors = [e for e in result.errors if "measurement" in e.lower()]
        assert count_errors == []

    def test_fewer_measurements_error(self, validate_asm_mod):
        asm = ref = {"solution analyzer aggregate document": {}}
        result = validate_asm_mod.ValidationResult()
        gen_content = '{"measurement identifier": "uuid-1"}'
        ref_content = (
            '{"measurement identifier": "uuid-1",'
            ' "measurement identifier2": "uuid-2"}'
        )
        # Use regex-friendly content with two actual measurement identifier keys
        ref_content2 = '"measurement identifier": "a" "measurement identifier": "b"'
        gen_content2 = '"measurement identifier": "a"'
        validate_asm_mod.compare_to_reference(asm, ref, gen_content2, ref_content2, result)
        assert any("missing" in e.lower() or "measurement" in e.lower() for e in result.errors)

    def test_extra_measurements_warning(self, validate_asm_mod):
        asm = ref = {"solution analyzer aggregate document": {}}
        result = validate_asm_mod.ValidationResult()
        gen_content = '"measurement identifier": "a" "measurement identifier": "b" "measurement identifier": "c"'
        ref_content = '"measurement identifier": "a"'
        validate_asm_mod.compare_to_reference(asm, ref, gen_content, ref_content, result)
        assert any("extra" in w.lower() or "measurement" in w.lower() for w in result.warnings)
