"""Unit tests for Dimensional Analysis Buckingham Pi and Null-Space solver."""

import numpy as np
from src.physics.dimensional_analysis import (
    build_dimensional_matrix,
    compute_null_space_pi_groups,
    get_cheme_preset
)

def test_dimensional_matrix_and_rank():
    """Verify matrix construction and rank-nullity theorem for pipe flow."""
    vars_list = ["delta_p", "D", "L", "u", "rho", "mu", "eps"]
    A, symbols = build_dimensional_matrix(vars_list)
    
    # Rows are [M, L, T], columns are 7 variables
    assert A.shape == (3, 7)
    assert len(symbols) == 7
    
    # Check dimensions of delta_p: [M L^-1 T^-2]
    assert np.allclose(A[:, 0], [1, -1, -2])
    # Check dimensions of velocity u: [M^0 L^1 T^-1]
    assert np.allclose(A[:, 3], [0, 1, -1])
    
    # Rank of A must be 3 (all 3 fundamental dimensions M, L, T are present)
    rank_A = np.linalg.matrix_rank(A)
    assert rank_A == 3

def test_null_space_orthogonality():
    """Verify that every Pi group vector lies strictly in the null space of A: A @ x == 0."""
    res = compute_null_space_pi_groups(["delta_p", "D", "L", "u", "rho", "mu", "eps"])
    A = res["A"]
    
    assert res["n_vars"] == 7
    assert res["rank"] == 3
    assert res["nullity"] == 4  # 7 - 3 = 4 Pi groups
    assert len(res["pi_groups"]) == 4
    
    # For every Pi group vector, A @ raw_vector must be zero
    for pi in res["pi_groups"]:
        v_raw = pi["raw_vector"]
        product = A @ v_raw
        assert np.allclose(product, 0.0, atol=1e-10)

def test_stirred_tank_preset():
    """Verify stirred tank mixing power yields 3 Pi groups (Power, Reynolds, Froude)."""
    preset_vars = get_cheme_preset("Stirred Tank Mixing Power")
    res = compute_null_space_pi_groups(preset_vars)
    
    assert res["n_vars"] == 6
    assert res["rank"] == 3
    assert res["nullity"] == 3


def test_pipe_flow_named_conventional_groups():
    """Repeating-variable basis must recover Eu, Re, ε/D, L/D — not an anonymous SVD mix."""
    res = compute_null_space_pi_groups(get_cheme_preset("Pipe Flow Pressure Drop"))
    names = [g.get("canonical_name") or "" for g in res["pi_groups"]]
    blob = " | ".join(names)
    assert "Euler" in blob
    assert "Reynolds" in blob
    assert "roughness" in blob.lower() or "ε/D" in blob
    assert "Aspect" in blob or "L/D" in blob
    formulas = " | ".join(g["formula_latex"] for g in res["pi_groups"])
    assert r"\frac{L}{D}" in formulas
    assert r"\frac{ε}{D}" in formulas
    re_g = next(g for g in res["pi_groups"] if (g.get("canonical_name") or "").startswith("Reynolds"))
    vec = {s: float(e) for s, e in zip(res["symbols"], re_g["vector"])}
    assert vec["ρ"] > 0 and vec["μ"] < 0
    for g in res["pi_groups"]:
        assert np.allclose(res["A"] @ np.array(g["vector"], dtype=float), 0.0, atol=1e-8)


def test_svd_rotation_recovers_named_pipe_groups():
    res = compute_null_space_pi_groups(get_cheme_preset("Pipe Flow Pressure Drop"))
    rot = res["rotation"]
    assert rot is not None
    assert rot["R"].shape == (4, 4)
    assert rot["reconstruction_error"] < 1e-6
    names = " | ".join(m["name"] for m in rot["mixes"])
    assert "Euler" in names
    assert "Reynolds" in names


def test_stirred_tank_named_groups():
    res = compute_null_space_pi_groups(get_cheme_preset("Stirred Tank Mixing Power"))
    blob = " | ".join(g.get("canonical_name") or "" for g in res["pi_groups"])
    assert "Power" in blob
    assert "Reynolds" in blob
    assert "Froude" in blob
