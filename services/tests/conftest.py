# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import importlib
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from moto import mock_aws

SERVICES_DIR = Path(__file__).resolve().parent.parent
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


# ---------------------------------------------------------------------------
# Stubs for Lambda runtime deps not installed in the test venv
# ---------------------------------------------------------------------------

# allotropy is a heavy Lambda layer dep not needed for unit tests.
# Inject a MagicMock so its import at module level doesn't fail.
for _mod in ("allotropy", "allotropy.parser_factory",
             "allotropy.allotrope", "allotropy.to_allotrope"):
    sys.modules.setdefault(_mod, MagicMock())


# ---------------------------------------------------------------------------
# Module loader
# ---------------------------------------------------------------------------

def _load_lambda_module(service_name, module_name="lambda_function"):
    """Load a Lambda module from its service directory.

    All five services have a lambda_function.py, so we must flush sys.modules
    and temporarily adjust sys.path per service to avoid name collisions.
    """
    service_dir = str(SERVICES_DIR / service_name)
    sys.modules.pop(module_name, None)
    sys.path.insert(0, service_dir)
    try:
        mod = importlib.import_module(module_name)
    finally:
        sys.path.remove(service_dir)
        sys.modules.pop(module_name, None)
    return mod


# ---------------------------------------------------------------------------
# Lambda module fixtures (session-scoped; AWS calls are mocked via moto)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
@mock_aws
def unified_mod():
    """unified-converter/lambda_function.py loaded inside a moto context."""
    os.environ.setdefault("CONVERTER_REGISTRY_TABLE", "mock-registry")
    os.environ.setdefault("CUSTOM_CONVERTER_ENDPOINT", "http://mock")
    os.environ.setdefault("MULTI_INSTRUMENT_ENDPOINT", "http://mock")
    os.environ.setdefault("ATAAS_ENDPOINT", "http://mock")
    os.environ.setdefault("ASM_FILES_BUCKET", "mock-bucket")
    os.environ.setdefault("CONVERSION_HISTORY_TABLE", "mock-history")
    return _load_lambda_module("unified-converter")


@pytest.fixture(scope="session")
@mock_aws
def custom_mod():
    """custom-converter/lambda_function.py loaded inside a moto context."""
    os.environ.setdefault("CONVERTER_REGISTRY_TABLE", "mock-registry")
    os.environ.setdefault("CONVERTERS_BUCKET", "mock-converters")
    os.environ["ZERO_PERMISSION_ROLE_ARN"] = ""   # disable STS assumption in tests
    return _load_lambda_module("custom-converter")


@pytest.fixture(scope="session")
@mock_aws
def multi_mod():
    """multi-instrument/lambda_function.py loaded inside a moto context."""
    return _load_lambda_module("multi-instrument")


# ---------------------------------------------------------------------------
# Pure-logic module fixtures (no AWS at all)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def rule_engine():
    """dvaas/rule_engine.py — pure logic, no AWS."""
    service_dir = str(SERVICES_DIR / "dvaas")
    sys.modules.pop("rule_engine", None)
    sys.path.insert(0, service_dir)
    try:
        mod = importlib.import_module("rule_engine")
    finally:
        sys.path.remove(service_dir)
        sys.modules.pop("rule_engine", None)
    return mod


@pytest.fixture(scope="session")
def validate_asm_mod():
    """dvaas/validate_asm.py."""
    # jsonschema_rs is an optional Lambda layer dep; stub it so the module loads.
    sys.modules.setdefault("jsonschema_rs", MagicMock())
    service_dir = str(SERVICES_DIR / "dvaas")
    sys.modules.pop("validate_asm", None)
    sys.path.insert(0, service_dir)
    try:
        mod = importlib.import_module("validate_asm")
    finally:
        sys.path.remove(service_dir)
        sys.modules.pop("validate_asm", None)
    return mod


# ---------------------------------------------------------------------------
# Data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def nova_flex2_csv():
    return (FIXTURES_DIR / "nova_flex2_sample.csv").read_text()


@pytest.fixture(scope="session")
def sample_valid_asm():
    return json.loads((FIXTURES_DIR / "sample_asm_valid.json").read_text())


@pytest.fixture(scope="session")
def sample_rule_set():
    return json.loads((FIXTURES_DIR / "sample_rule_set.json").read_text())


@pytest.fixture(scope="session")
def cell_counter_csv():
    return (SERVICES_DIR.parent / "example" / "chememotec_nc_view_example.csv").read_text()
