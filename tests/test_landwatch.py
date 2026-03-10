"""LandWatch Kenya — test suite."""
from __future__ import annotations
import pandas as pd
import pytest
from pathlib import Path

DATA = Path(__file__).parent.parent / "data"


class TestViolationsData:
    def _df(self): return pd.read_csv(DATA / "encroachments" / "documented_violations.csv")

    def test_load(self):
        df = self._df()
        assert len(df) >= 10

    def test_required_columns(self):
        df = self._df()
        required = {
            "id", "river", "basin", "city", "zone", "lat", "lon",
            "setback_m", "structure_type", "severity", "status",
            "policy_ref", "source", "verified",
        }
        assert required.issubset(df.columns)

    def test_all_confirmed(self):
        df = self._df()
        bad = df[df["verified"] != "confirmed"]
        assert len(bad) == 0, f"Unverified: {bad['id'].tolist()}"

    def test_no_duplicate_ids(self):
        df = self._df()
        assert df["id"].is_unique

    def test_severity_values(self):
        df = self._df()
        valid = {"Critical", "High", "Medium", "Low"}
        assert set(df["severity"].unique()).issubset(valid)

    def test_status_values(self):
        df = self._df()
        valid = {"Active", "Resolved", "Pending"}
        assert set(df["status"].unique()).issubset(valid)

    def test_lat_lon_kenya(self):
        df = self._df()
        assert df["lat"].between(-5.0, 5.0).all(), "Latitudes outside Kenya"
        assert df["lon"].between(33.8, 42.0).all(), "Longitudes outside Kenya"

    def test_setback_valid(self):
        df = self._df()
        # Water Act 2016 s.72 minimum is 30m
        assert (df["setback_m"] >= 30).all(), "Setback cannot be less than 30m"

    def test_policy_ref_present(self):
        df = self._df()
        assert df["policy_ref"].notna().all()
        assert (df["policy_ref"].str.len() > 10).all()

    def test_critical_cases_exist(self):
        df = self._df()
        assert (df["severity"] == "Critical").sum() >= 3

    def test_nairobi_coverage(self):
        df = self._df()
        nairobi = df[df["city"] == "Nairobi"]
        assert len(nairobi) >= 4, "Nairobi should have ≥4 documented violations"

    def test_multi_city_coverage(self):
        df = self._df()
        assert df["city"].nunique() >= 4


class TestRiversData:
    def _df(self): return pd.read_csv(DATA / "rivers" / "rivers_reference.csv")

    def test_load(self):
        df = self._df()
        assert len(df) >= 8

    def test_required_columns(self):
        df = self._df()
        required = {"river", "basin", "total_length_km", "urban_length_km",
                    "setback_m", "primary_threat", "enforcement_body", "source"}
        assert required.issubset(df.columns)

    def test_urban_le_total(self):
        df = self._df()
        assert (df["urban_length_km"] <= df["total_length_km"]).all()

    def test_setback_water_act_minimum(self):
        df = self._df()
        assert (df["setback_m"] >= 30).all()

    def test_basin_variety(self):
        df = self._df()
        assert df["basin"].nunique() >= 3


def test_app_compiles():
    import py_compile
    py_compile.compile(str(Path(__file__).parent.parent / "app.py"), doraise=True)
