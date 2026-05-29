# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import pytest


# ---------------------------------------------------------------------------
# is_nova_flex2
# ---------------------------------------------------------------------------

class TestIsNovaFlex2:
    def test_positive_gluc(self, unified_mod):
        content = "Sample ID,Date & Time,pH,Gluc,Lac\nS001,01/01/2024,7.1,4.5,1.2"
        assert unified_mod.is_nova_flex2(content, "results.csv") is True

    def test_positive_lac_only(self, unified_mod):
        content = "Sample ID,Date & Time,pH,Lac\nS001,01/01/2024,7.1,1.2"
        assert unified_mod.is_nova_flex2(content, "results.csv") is True

    def test_positive_gln_only(self, unified_mod):
        content = "Sample ID,pH,Gln\nS001,7.1,2.0"
        assert unified_mod.is_nova_flex2(content, "results.csv") is True

    def test_negative_not_csv(self, unified_mod):
        content = "Sample ID,pH,Gluc\nS001,7.1,4.5"
        assert unified_mod.is_nova_flex2(content, "results.txt") is False

    def test_negative_missing_ph(self, unified_mod):
        content = "Sample ID,Glucose,Lactate\nS001,4.5,1.2"
        assert unified_mod.is_nova_flex2(content, "results.csv") is False

    def test_negative_missing_sample_id(self, unified_mod):
        content = "Name,pH,Gluc\nS001,7.1,4.5"
        assert unified_mod.is_nova_flex2(content, "results.csv") is False

    def test_negative_no_metabolite(self, unified_mod):
        content = "Sample ID,pH,Temperature\nS001,7.1,37.0"
        assert unified_mod.is_nova_flex2(content, "results.csv") is False

    def test_negative_empty_content(self, unified_mod):
        assert unified_mod.is_nova_flex2("", "results.csv") is False

    def test_negative_single_line(self, unified_mod):
        content = "Sample ID,pH,Gluc"
        assert unified_mod.is_nova_flex2(content, "results.csv") is False


# ---------------------------------------------------------------------------
# convert_nova_flex2
# ---------------------------------------------------------------------------

class TestConvertNovaFlex2:
    def setup_method(self):
        """Reset function attributes before each test."""
        pass

    def _set_file_attrs(self, mod, file_name="test.csv", unc_path=""):
        mod.convert_nova_flex2._file_name = file_name
        mod.convert_nova_flex2._unc_path = unc_path

    def test_empty_rows_returns_error(self, unified_mod, nova_flex2_csv):
        self._set_file_attrs(unified_mod)
        # Header only, no data
        header = nova_flex2_csv.split("\n")[0]
        result = unified_mod.convert_nova_flex2(header + "\n")
        assert result["success"] is False

    def test_basic_structure(self, unified_mod, nova_flex2_csv):
        self._set_file_attrs(unified_mod)
        result = unified_mod.convert_nova_flex2(nova_flex2_csv)
        assert result["success"] is True
        asm = result["asm_output"]
        assert "$asm.manifest" in asm
        assert "solution analyzer aggregate document" in asm

    def test_manifest_url(self, unified_mod, nova_flex2_csv):
        self._set_file_attrs(unified_mod)
        result = unified_mod.convert_nova_flex2(nova_flex2_csv)
        assert result["success"] is True
        manifest = result["asm_output"]["$asm.manifest"]
        assert "solution-analyzer" in manifest

    def test_blood_gas_measurement(self, unified_mod, nova_flex2_csv):
        self._set_file_attrs(unified_mod)
        result = unified_mod.convert_nova_flex2(nova_flex2_csv)
        assert result["success"] is True
        measurements = (
            result["asm_output"]
            ["solution analyzer aggregate document"]
            ["solution analyzer document"][0]
            ["measurement aggregate document"]
            ["measurement document"]
        )
        # Blood gas measurement should contain pO2
        gas_measurements = [m for m in measurements if "pO2" in m]
        assert len(gas_measurements) >= 1
        gas = gas_measurements[0]
        assert gas["pO2"]["unit"] == "mmHg"
        assert gas["pCO2"]["unit"] == "mmHg"

    def test_ph_measurement(self, unified_mod, nova_flex2_csv):
        self._set_file_attrs(unified_mod)
        result = unified_mod.convert_nova_flex2(nova_flex2_csv)
        measurements = (
            result["asm_output"]
            ["solution analyzer aggregate document"]
            ["solution analyzer document"][0]
            ["measurement aggregate document"]
            ["measurement document"]
        )
        ph_measurements = [m for m in measurements if "pH" in m]
        assert len(ph_measurements) >= 1
        assert ph_measurements[0]["pH"]["unit"] == "pH"

    def test_osmolality_measurement(self, unified_mod, nova_flex2_csv):
        self._set_file_attrs(unified_mod)
        result = unified_mod.convert_nova_flex2(nova_flex2_csv)
        measurements = (
            result["asm_output"]
            ["solution analyzer aggregate document"]
            ["solution analyzer document"][0]
            ["measurement aggregate document"]
            ["measurement document"]
        )
        osm_measurements = [m for m in measurements if "osmolality" in m]
        assert len(osm_measurements) >= 1
        assert osm_measurements[0]["osmolality"]["unit"] == "mosm/kg"

    def test_metabolites_present(self, unified_mod, nova_flex2_csv):
        self._set_file_attrs(unified_mod)
        result = unified_mod.convert_nova_flex2(nova_flex2_csv)
        measurements = (
            result["asm_output"]
            ["solution analyzer aggregate document"]
            ["solution analyzer document"][0]
            ["measurement aggregate document"]
            ["measurement document"]
        )
        metabolite_measurements = [m for m in measurements if "analyte aggregate document" in m]
        assert len(metabolite_measurements) >= 1
        analytes = metabolite_measurements[0]["analyte aggregate document"]["analyte document"]
        analyte_names = [a["analyte name"] for a in analytes]
        assert "glucose" in analyte_names
        assert "lactate" in analyte_names

    def test_calculated_data_with_traceability(self, unified_mod, nova_flex2_csv):
        self._set_file_attrs(unified_mod)
        result = unified_mod.convert_nova_flex2(nova_flex2_csv)
        meas_agg = (
            result["asm_output"]
            ["solution analyzer aggregate document"]
            ["solution analyzer document"][0]
            ["measurement aggregate document"]
        )
        assert "calculated data aggregate document" in meas_agg
        calc = meas_agg["calculated data aggregate document"]
        assert "calculated data document" in calc
        assert "data source aggregate document" in calc

    def test_custom_info_present(self, unified_mod, nova_flex2_csv):
        self._set_file_attrs(unified_mod)
        result = unified_mod.convert_nova_flex2(nova_flex2_csv)
        meas_agg = (
            result["asm_output"]
            ["solution analyzer aggregate document"]
            ["solution analyzer document"][0]
            ["measurement aggregate document"]
        )
        assert "custom information aggregate document" in meas_agg

    def test_field_mapping_populated(self, unified_mod, nova_flex2_csv):
        self._set_file_attrs(unified_mod)
        result = unified_mod.convert_nova_flex2(nova_flex2_csv)
        assert result["success"] is True
        mapping = result["field_mapping"]
        assert isinstance(mapping, list)
        assert len(mapping) > 0
        # Each entry should have source_field and asm_field
        assert all("source_field" in m for m in mapping)
        assert all("asm_field" in m for m in mapping)

    def test_sample_identifier_propagated(self, unified_mod, nova_flex2_csv):
        self._set_file_attrs(unified_mod)
        result = unified_mod.convert_nova_flex2(nova_flex2_csv)
        measurements = (
            result["asm_output"]
            ["solution analyzer aggregate document"]
            ["solution analyzer document"][0]
            ["measurement aggregate document"]
            ["measurement document"]
        )
        # Every measurement should have a sample document
        for m in measurements:
            assert "sample document" in m
            assert m["sample document"]["sample identifier"] == "S001"

    def test_device_system_document(self, unified_mod, nova_flex2_csv):
        self._set_file_attrs(unified_mod)
        result = unified_mod.convert_nova_flex2(nova_flex2_csv)
        agg = result["asm_output"]["solution analyzer aggregate document"]
        assert "device system document" in agg
        assert agg["device system document"]["product manufacturer"] == "nova biomedical"

    def test_analyst_from_operator_column(self, unified_mod, nova_flex2_csv):
        self._set_file_attrs(unified_mod)
        result = unified_mod.convert_nova_flex2(nova_flex2_csv)
        doc = (
            result["asm_output"]
            ["solution analyzer aggregate document"]
            ["solution analyzer document"][0]
        )
        assert doc["analyst"] == "JSmith"


# ---------------------------------------------------------------------------
# error_response
# ---------------------------------------------------------------------------

class TestErrorResponse:
    def test_status_code_preserved(self, unified_mod):
        resp = unified_mod.error_response(400, "Bad request")
        assert resp["statusCode"] == 400

    def test_cors_header(self, unified_mod):
        resp = unified_mod.error_response(500, "Error")
        assert resp["headers"]["Access-Control-Allow-Origin"] == "*"

    def test_body_has_error_and_timestamp(self, unified_mod):
        resp = unified_mod.error_response(404, "Not found")
        body = json.loads(resp["body"])
        assert body["error"] == "Not found"
        assert "timestamp" in body

    def test_various_status_codes(self, unified_mod):
        for code in (400, 403, 404, 500):
            resp = unified_mod.error_response(code, "msg")
            assert resp["statusCode"] == code
