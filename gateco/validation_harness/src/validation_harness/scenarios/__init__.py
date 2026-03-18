"""Scenario modules — importing this package triggers registration of all scenarios."""

from validation_harness.scenarios import (  # noqa: F401
    s00_health,
    s01_auth,
    s02_connector_lifecycle,
    s03_connector_config,
    s04_ingest_single,
    s05_ingest_batch,
    s06_retroactive_register,
    s07_data_catalog,
    s08_policy_lifecycle,
    s09_retrieval_allowed,
    s10_retrieval_denied,
    s11_retrieval_partial,
    s12_metadata_resolution,
    s13_simulator,
    s14_audit,
    s15_coverage_readiness,
    s16_dashboard,
    s17_billing_readonly,
)
