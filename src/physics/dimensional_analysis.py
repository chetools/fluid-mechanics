"""Dimensional analysis: Buckingham Π and a linear-algebra construction of Π groups.

SVD is used only to read rank and nullity. The groups shown to students
are a conventional basis obtained by choosing repeating variables and
solving A_rep x = -A_j, then matching the result to named groups
(Re, Eu, ε/D, …). A raw SVD kernel is not Re.
"""

from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.linalg import null_space

DIMENSION_NAMES = ["Mass [M]", "Length [L]", "Time [T]"]

VARIABLE_REGISTRY = {
    "delta_p": {"name": "Pressure Drop (Δp)", "dims": [1, -1, -2], "symbol": "Δp", "unit": "Pa"},
    "u": {"name": "Velocity (u)", "dims": [0, 1, -1], "symbol": "u", "unit": "m/s"},
    "D": {"name": "Pipe Diameter (D)", "dims": [0, 1, 0], "symbol": "D", "unit": "m"},
    "L": {"name": "Pipe Length (L)", "dims": [0, 1, 0], "symbol": "L", "unit": "m"},
    "rho": {"name": "Fluid Density (ρ)", "dims": [1, -3, 0], "symbol": "ρ", "unit": "kg/m³"},
    "mu": {"name": "Dynamic Viscosity (μ)", "dims": [1, -1, -1], "symbol": "μ", "unit": "Pa·s"},
    "eps": {"name": "Wall Roughness (ε)", "dims": [0, 1, 0], "symbol": "ε", "unit": "m"},
    "g": {"name": "Gravity Acceleration (g)", "dims": [0, 1, -2], "symbol": "g", "unit": "m/s²"},
    "Q": {"name": "Volumetric Flow Rate (Q)", "dims": [0, 3, -1], "symbol": "Q", "unit": "m³/s"},
    "P_shaft": {"name": "Impeller / Pump Power (P)", "dims": [1, 2, -3], "symbol": "P", "unit": "W"},
    "N_rot": {"name": "Rotational Speed (N)", "dims": [0, 0, -1], "symbol": "N", "unit": "1/s"},
    "D_imp": {"name": "Impeller Diameter (D_i)", "dims": [0, 1, 0], "symbol": "D_i", "unit": "m"},
    "sigma": {"name": "Surface Tension (σ)", "dims": [1, 0, -2], "symbol": "σ", "unit": "N/m"},
    "F_drag": {"name": "Drag Force (F_D)", "dims": [1, 1, -2], "symbol": "F_D", "unit": "N"},
}

# Preferred repeating variables (must span M, L, T when possible).
_PREFERRED_REPEATING = ("rho", "u", "D", "D_imp", "N_rot", "L")

# Canonical named groups: symbol -> exponent. Matching allows a global scale
# of ±1 (so 1/Re is reported as Re).
# Patterns are the *named* orientation. Matching accepts the inverse and flips.
_CANONICAL_GROUPS = (
    ("Euler number Eu = Δp/(ρ u²)", {"Δp": 1, "ρ": -1, "u": -2}),
    ("Reynolds number Re = ρ u D / μ", {"ρ": 1, "u": 1, "D": 1, "μ": -1}),
    ("Relative roughness ε/D", {"ε": 1, "D": -1}),
    ("Aspect ratio L/D", {"L": 1, "D": -1}),
    ("Power number N_P = P / (ρ N³ D_i⁵)", {"P": 1, "ρ": -1, "N": -3, "D_i": -5}),
    ("Impeller Reynolds Re = ρ N D_i² / μ", {"ρ": 1, "N": 1, "D_i": 2, "μ": -1}),
    ("Froude number Fr = N² D_i / g", {"N": 2, "D_i": 1, "g": -1}),
    ("Drag group C_D ∼ F_D / (ρ u² D²)", {"F_D": 1, "ρ": -1, "u": -2, "D": -2}),
    ("Weber number We = ρ u² D / σ", {"ρ": 1, "u": 2, "D": 1, "σ": -1}),
    ("Reynolds number Re = ρ u D / μ", {"ρ": 1, "u": 1, "D_i": 1, "μ": -1}),
)


def build_dimensional_matrix(var_keys: List[str]) -> Tuple[np.ndarray, List[str]]:
    """Build the m x n dimensional matrix A from selected variable keys.

    Rows correspond to base dimensions [M, L, T].
    Columns correspond to physical variables.
    """
    matrix = []
    symbols = []
    for k in var_keys:
        if k in VARIABLE_REGISTRY:
            matrix.append(VARIABLE_REGISTRY[k]["dims"])
            symbols.append(VARIABLE_REGISTRY[k]["symbol"])

    A = np.array(matrix, dtype=float).T
    return A, symbols


def _integerize(vec: np.ndarray, flip_leading: bool = True) -> np.ndarray:
    """Scale a real null-space vector toward small integers when possible."""
    max_val = np.max(np.abs(vec))
    if max_val < 1e-10:
        return np.round(vec, 3)
    vec_norm = vec / max_val
    best_scale = 1.0
    min_err = 1e9
    for scale in range(1, 13):
        test_v = vec_norm * scale
        err = np.max(np.abs(test_v - np.round(test_v)))
        if err < min_err:
            min_err = err
            best_scale = scale
    if min_err < 0.08:
        clean = np.round(vec_norm * best_scale).astype(int)
        if flip_leading:
            nz = np.flatnonzero(clean)
            if len(nz) and clean[nz[0]] < 0:
                clean = -clean
        return clean
    return np.round(vec, 3)


def _formula_from_exponents(symbols: List[str], exponents: np.ndarray) -> str:
    numerator_terms = []
    denominator_terms = []
    for sym, exp in zip(symbols, exponents):
        if abs(exp) < 1e-4:
            continue
        exp_int = int(round(exp)) if np.isclose(exp, round(float(exp))) else exp
        if exp > 0:
            term = f"{sym}^{{{exp_int}}}" if exp_int != 1 else sym
            numerator_terms.append(term)
        else:
            term = f"{sym}^{{{abs(exp_int)}}}" if abs(exp_int) != 1 else sym
            denominator_terms.append(term)
    num_str = " · ".join(numerator_terms) if numerator_terms else "1"
    den_str = " · ".join(denominator_terms) if denominator_terms else "1"
    if den_str == "1":
        return num_str
    return f"\\frac{{{num_str}}}{{{den_str}}}"


def _match_canonical(symbols: List[str], exponents: np.ndarray) -> Tuple[Optional[str], np.ndarray]:
    """If exponents match a named group (or its inverse), return that name and flipped vector."""
    mapping = {s: float(e) for s, e in zip(symbols, exponents) if abs(e) > 1e-8}
    for name, pattern in _CANONICAL_GROUPS:
        if set(pattern.keys()) != set(mapping.keys()):
            continue
        keys = list(pattern.keys())
        if abs(pattern[keys[0]]) < 1e-12:
            continue
        ratio = mapping[keys[0]] / pattern[keys[0]]
        if not np.allclose(
            [mapping[k] for k in keys],
            [ratio * pattern[k] for k in keys],
            atol=1e-6,
        ):
            continue
        vec = np.array(exponents, dtype=float)
        if ratio < 0:
            vec = -vec
        # Do not re-flip a leading-negative D when the canonical form is L/D or ε/D.
        return name, _integerize(vec, flip_leading=False)
    return None, exponents


def _choose_repeating(var_keys: List[str], A: np.ndarray) -> Tuple[List[int], List[int]]:
    """Select a full-rank set of repeating-variable columns."""
    n = A.shape[1]
    k = int(np.linalg.matrix_rank(A))
    chosen: List[int] = []
    preferred_idx = [var_keys.index(name) for name in _PREFERRED_REPEATING if name in var_keys]
    rest = [i for i in range(n) if i not in preferred_idx]
    for idx in preferred_idx + rest:
        trial = chosen + [idx]
        if np.linalg.matrix_rank(A[:, trial]) == len(trial):
            chosen.append(idx)
        if len(chosen) == k:
            break
    remaining = [i for i in range(n) if i not in chosen]
    return chosen, remaining


def _group_dict(symbols: List[str], vec: np.ndarray, raw: np.ndarray, name: Optional[str]) -> Dict:
    return {
        "vector": vec,
        "formula_latex": _formula_from_exponents(symbols, vec),
        "raw_vector": raw,
        "canonical_name": name,
    }


def compute_null_space_pi_groups(var_keys: List[str]) -> Dict:
    """Solve for dimensionless Π groups.

    Rank and nullity come from SVD. The displayed basis is constructed by
    the repeating-variable method (linear solve), then named when it
    matches Re, Eu, ε/D, L/D, N_P, Fr, C_D, or We.
    """
    A, symbols = build_dimensional_matrix(var_keys)
    n_vars = len(symbols)
    rank_A = int(np.linalg.matrix_rank(A))
    nullity = n_vars - rank_A

    ns = null_space(A) if n_vars else np.zeros((0, 0))
    svd_groups = []
    if ns.size:
        for col_idx in range(ns.shape[1]):
            raw = ns[:, col_idx]
            clean = _integerize(raw)
            svd_groups.append(_group_dict(symbols, clean, raw, None))

    repeating_idx, remaining_idx = _choose_repeating(var_keys, A) if n_vars else ([], [])
    pi_groups = []
    for j in remaining_idx:
        A_rep = A[:, repeating_idx]
        rhs = -A[:, j]
        x, _, _, _ = np.linalg.lstsq(A_rep, rhs, rcond=None)
        vec = np.zeros(n_vars, dtype=float)
        vec[j] = 1.0
        for xi, ri in zip(x, repeating_idx):
            vec[ri] = xi
        if np.max(np.abs(A @ vec)) > 1e-6:
            continue
        clean = _integerize(vec)
        name, named_vec = _match_canonical(symbols, clean)
        if name is not None:
            clean = named_vec
        pi_groups.append(_group_dict(symbols, clean, vec, name))

    # Fall back to SVD basis if the repeating-variable solve produced nothing.
    if not pi_groups:
        pi_groups = svd_groups

    rotation = rotate_svd_to_named(A, ns, pi_groups, symbols) if ns.size and pi_groups else None

    return {
        "A": A,
        "symbols": symbols,
        "n_vars": n_vars,
        "rank": rank_A,
        "nullity": nullity,
        "pi_groups": pi_groups,
        "svd_groups": svd_groups,
        "svd_basis": ns,
        "rotation": rotation,
        "repeating_symbols": [symbols[i] for i in repeating_idx],
        "var_keys": list(var_keys),
    }


def rotate_svd_to_named(
    A: np.ndarray,
    svd_basis: np.ndarray,
    named_groups: List[Dict],
    symbols: List[str],
) -> Optional[Dict]:
    """Least-squares rotation that takes the orthonormal SVD kernel onto named Π groups.

    If N is n×p (SVD null-space) and C is n×p (integer named groups),
    R = argmin || N R − C ||  so each standard group is a mix of SVD columns.
    """
    if svd_basis is None or svd_basis.size == 0 or not named_groups:
        return None
    C = np.column_stack([np.array(g["vector"], dtype=float) for g in named_groups])
    if C.shape[0] != svd_basis.shape[0] or C.shape[1] != svd_basis.shape[1]:
        return None
    R, residuals, rank, _ = np.linalg.lstsq(svd_basis, C, rcond=None)
    rotated = svd_basis @ R
    recon_err = float(np.linalg.norm(rotated - C) / max(np.linalg.norm(C), 1e-12))
    mixes = []
    for j, g in enumerate(named_groups):
        coeff = R[:, j]
        parts = []
        for i, c in enumerate(coeff):
            if abs(c) < 0.03:
                continue
            parts.append(f"{c:+.2f} N_{i+1}")
        mixes.append(
            {
                "name": g.get("canonical_name") or f"Π_{j+1}",
                "formula_latex": g["formula_latex"],
                "coefficients": coeff,
                "mix": " ".join(parts) if parts else "0",
            }
        )
    return {
        "R": R,
        "rotated": rotated,
        "C": C,
        "reconstruction_error": recon_err,
        "mixes": mixes,
        "rank": int(rank),
        "residual_norm": float(np.sqrt(np.sum(residuals))) if len(residuals) else recon_err,
    }


def get_cheme_preset(preset_name: str) -> List[str]:
    """Return standard sets of variables for classic Chemical Engineering problems."""
    presets = {
        "Pipe Flow Pressure Drop": ["delta_p", "D", "L", "u", "rho", "mu", "eps"],
        "Stirred Tank Mixing Power": ["P_shaft", "D_imp", "N_rot", "rho", "mu", "g"],
        "Submerged Body Drag": ["F_drag", "u", "D", "rho", "mu"],
        "Capillary Rise / Atomization": ["delta_p", "D", "u", "rho", "mu", "sigma"],
    }
    return presets.get(preset_name, ["delta_p", "D", "L", "u", "rho", "mu", "eps"])
