"""Steady incompressible networks: piezometric heads, signed friction losses, continuity.

Friction factors are Fanning f_F throughout; the Darcy-Weisbach head loss uses
f_D = 4 f_F.
"""

import numpy as np
from scipy.optimize import brentq, least_squares

from src.physics.pipe_flow import PIPE_ROUGHNESS, friction_factor_churchill

G = 9.81
PIPE_DATA_SOURCE = "https://www.wheatland.com/wp-content/uploads/2017/12/Standard-Pipe-Brochure-2.pdf"
# NPS: (OD, schedule-40 wall, schedule-80 wall), in inches. Manufacturer
# nominal dimensions, pp. 4–5. Calculate ID = OD - 2t rather than using rounded IDs.
SCHEDULES = {
    "1/2": (.840, .109, .147), "3/4": (1.050, .113, .154),
    "1": (1.315, .133, .179), "1 1/4": (1.660, .140, .191),
    "1 1/2": (1.900, .145, .200), "2": (2.375, .154, .218),
    "2 1/2": (2.875, .203, .276), "3": (3.500, .216, .300),
    "3 1/2": (4.000, .226, .318), "4": (4.500, .237, .337),
}


def positive(value, name, allow_zero=False):
    value = float(value)
    if not np.isfinite(value) or value < 0 or (value == 0 and not allow_zero):
        raise ValueError(f"{name} must be finite and {'nonnegative' if allow_zero else 'positive'}.")
    return value


def schedule_dimensions(nps, schedule):
    if str(nps) not in SCHEDULES or str(schedule) not in ("40", "80"):
        raise ValueError("Choose a supported NPS (1/2–4) and schedule (40 or 80).")
    od, t40, t80 = SCHEDULES[str(nps)]
    wall = t40 if str(schedule) == "40" else t80
    return {"od_m": od * .0254, "wall_m": wall * .0254, "diameter_m": (od - 2 * wall) * .0254}


def resolve_pipe(row):
    result = dict(row)
    mode = row.get("size_mode", "Inside diameter")
    if mode == "Schedule":
        result.update(schedule_dimensions(row["nps"], row["schedule"]))
    elif mode == "Inside diameter":
        result["diameter_m"] = positive(row["diameter_mm"], "Inside diameter") / 1000
    else:
        raise ValueError("Pipe size mode must be Inside diameter or Schedule.")
    d = result["diameter_m"]
    result["length_m"] = positive(row["length_m"], "Pipe length")
    result["k_minor"] = positive(row.get("k_minor", 0), "Minor-loss K", True)
    mode = row.get("roughness_mode", "Material")
    if mode == "Material":
        if row.get("material") not in PIPE_ROUGHNESS:
            raise ValueError("Choose a known roughness material.")
        rough = PIPE_ROUGHNESS[row["material"]]
    elif mode == "Relative ε/D":
        rough = positive(row["relative_roughness"], "Relative roughness", True) * d
    elif mode == "Absolute ε (mm)":
        rough = positive(row["roughness_mm"], "Roughness", True) / 1000
    else:
        raise ValueError("Unknown roughness mode.")
    if rough / d > .05:
        raise ValueError("This teaching model limits ε/D to 0.05; inspect the pipe dimensions and roughness.")
    result["roughness_m"] = rough
    return result


def pipe_headloss(q, pipe, rho, mu):
    """Signed metres of head lost; exact finite slope at zero flow."""
    d, length = pipe["diameter_m"], pipe["length_m"]
    area = np.pi * d * d / 4
    re = rho * abs(q) * d / (mu * area)
    if re < 1:
        major = 128 * mu * length * q / (rho * G * np.pi * d**4)
    else:
        f_f = friction_factor_churchill(re, pipe["roughness_m"] / d)
        major = 4 * f_f * length / d * q * abs(q) / (2 * G * area**2)
    return major + pipe["k_minor"] * q * abs(q) / (2 * G * area**2)


def flow_from_head(dh, pipe, rho, mu):
    if dh == 0:
        return 0.0
    target = abs(dh)
    upper = max(1e-10, np.pi * pipe["diameter_m"]**2 / 4 * np.sqrt(2 * G * target))
    for _ in range(80):
        if pipe_headloss(upper, pipe, rho, mu) >= target:
            break
        upper *= 2
    else:
        raise ValueError("Could not bracket a pipe flow. Check head and dimensions.")
    q = brentq(lambda q: pipe_headloss(q, pipe, rho, mu) - target, 0, upper, xtol=1e-14)
    return np.copysign(q, dh)


def solve_network(nodes, pipes, rho=998.2, mu=.001002):
    """Solve each anchored connected component; reject inconsistent input.

    Junction demand is m³/h, positive out of the network. Boundary pressures
    are kPa gauge using a common reference. No gas density changes or pumps.
    """
    rho, mu = positive(rho, "Density"), positive(mu, "Viscosity")
    if not 2 <= len(nodes) <= 40 or not 1 <= len(pipes) <= 80:
        raise ValueError("Enter 2–40 nodes and 1–80 pipes.")
    nodes = [dict(n) for n in nodes]
    names = [str(n["node"]).strip() for n in nodes]
    if any(not n or n.lower() in ("nan", "none") for n in names) or len(set(names)) != len(names):
        raise ValueError("Node names must be nonempty and unique.")
    index = {name: i for i, name in enumerate(names)}
    heads = np.zeros(len(nodes))
    demands = np.zeros(len(nodes))
    known, unknown = [], []
    for i, node in enumerate(nodes):
        node["node"] = names[i]
        z = float(node["elevation_m"])
        demand = float(node.get("demand_m3h", 0))
        if not np.isfinite([z, demand]).all():
            raise ValueError("Elevations and demands must be finite.")
        demands[i] = demand / 3600
        if node["boundary"] == "Pressure":
            pressure = float(node["pressure_kpag"])
            if not np.isfinite(pressure):
                raise ValueError("Each pressure boundary requires a finite gauge pressure.")
            if demand != 0:
                raise ValueError("A pressure boundary's exchange is solved; set its demand to zero.")
            heads[i] = z + pressure * 1000 / (rho * G)
            known.append(i)
        elif node["boundary"] == "Junction":
            unknown.append(i)
        else:
            raise ValueError("Node type must be Junction or Pressure.")
    resolved = [resolve_pipe(p) for p in pipes]
    labels = [str(p["pipe"]).strip() for p in resolved]
    if len(set(labels)) != len(labels) or any(not n or n.lower() in ("nan", "none") for n in labels):
        raise ValueError("Pipe names must be nonempty and unique.")
    incidence = np.zeros((len(nodes), len(pipes)))  # +out, -in
    adjacency = [set() for _ in nodes]
    edges = []
    for k, pipe in enumerate(resolved):
        start, end = str(pipe["from"]).strip(), str(pipe["to"]).strip()
        if start not in index or end not in index or start == end:
            raise ValueError(f"Pipe {labels[k]} must connect two different existing nodes.")
        i, j = index[start], index[end]
        pipe.update({"pipe": labels[k], "from": start, "to": end})
        edges.append((i, j))
        incidence[i, k], incidence[j, k] = 1, -1
        adjacency[i].add(j)
        adjacency[j].add(i)
    unseen = set(range(len(nodes)))
    while unseen:
        stack, component = [next(iter(unseen))], set()
        while stack:
            i = stack.pop()
            if i in component:
                continue
            component.add(i)
            stack.extend(adjacency[i] - component)
        anchors = sorted(component & set(known))
        if not anchors:
            raise ValueError("Every connected component needs a prescribed-pressure boundary.")
        if any(not adjacency[i] for i in component):
            raise ValueError("Remove isolated nodes or connect them with a pipe.")
        for i in component - set(known):
            heads[i] = np.mean(heads[anchors])
        unseen -= component

    def evaluate(h):
        state = heads.copy()
        state[unknown] = h
        q = np.array([flow_from_head(state[i] - state[j], p, rho, mu)
                      for (i, j), p in zip(edges, resolved)])
        return q, incidence @ q + demands

    scale = max(1e-4, float(np.sum(np.abs(demands))))
    iterations = 0
    if unknown:
        fit = least_squares(lambda h: evaluate(h)[1][unknown] / scale, heads[unknown],
                            xtol=1e-11, ftol=1e-11, gtol=1e-11, max_nfev=500, x_scale="jac")
        heads[unknown] = fit.x
        iterations = fit.nfev
        if not fit.success:
            raise ValueError("Network iteration did not converge; inspect the boundary conditions and demands.")
    q, balances = evaluate(heads[unknown])
    residual = float(np.max(np.abs(balances[unknown]))) if unknown else 0.0
    if residual > 1e-8:
        raise ValueError(f"Continuity tolerance not met: residual {residual:.3g} m³/s.")
    node_results = []
    for i, n in enumerate(nodes):
        node_results.append({"node": names[i], "boundary": n["boundary"], "elevation_m": float(n["elevation_m"]),
            "head_m": heads[i], "pressure_kpag": rho * G * (heads[i] - float(n["elevation_m"])) / 1000,
            "demand_m3h": demands[i] * 3600, "net_pipe_out_m3h": (incidence @ q)[i] * 3600,
            "boundary_supply_m3h": balances[i] * 3600 if i in known else 0,
            "continuity_residual_m3h": balances[i] * 3600 if i in unknown else 0})
    pipe_results = []
    for k, (p, (i, j)) in enumerate(zip(resolved, edges)):
        area = np.pi * p["diameter_m"]**2 / 4
        re = rho * abs(q[k]) * p["diameter_m"] / (mu * area)
        loss = pipe_headloss(q[k], p, rho, mu)
        pipe_results.append({"pipe": p["pipe"], "from": p["from"], "to": p["to"],
            "diameter_mm": p["diameter_m"] * 1000, "roughness_mm": p["roughness_m"] * 1000,
            "relative_roughness": p["roughness_m"] / p["diameter_m"], "flow_m3h": q[k] * 3600,
            "velocity_ms": q[k] / area, "reynolds": re,
            "f_fanning": friction_factor_churchill(re, p["roughness_m"] / p["diameter_m"]),
            "f_darcy": 4 * friction_factor_churchill(re, p["roughness_m"] / p["diameter_m"]),
            "headloss_m": loss, "energy_residual_m": heads[i] - heads[j] - loss})
    return {"nodes": node_results, "pipes": pipe_results, "iterations": iterations,
            "mass_residual_m3s": residual,
            "energy_residual_m": max(abs(p["energy_residual_m"]) for p in pipe_results)}


def example_network():
    nodes = [
        dict(node="Supply", boundary="Pressure", elevation_m=0., pressure_kpag=300., demand_m3h=0.),
        dict(node="A", boundary="Junction", elevation_m=5., pressure_kpag=0., demand_m3h=0.),
        dict(node="B", boundary="Junction", elevation_m=12., pressure_kpag=0., demand_m3h=2.),
        dict(node="Outlet", boundary="Pressure", elevation_m=8., pressure_kpag=50., demand_m3h=0.),
    ]
    pipes = []
    for label, start, end, length, nps in [
        ("P1", "Supply", "A", 100., "3"), ("P2", "A", "B", 65., "2"),
        ("P3", "A", "Outlet", 90., "2"), ("P4", "B", "Outlet", 75., "1 1/2")]:
        pipes.append(dict(pipe=label, **{"from": start, "to": end}, length_m=length,
            size_mode="Schedule", diameter_mm=50., nps=nps, schedule="40", roughness_mode="Material",
            material="Commercial Steel / Wrought Iron", relative_roughness=.001, roughness_mm=.045, k_minor=1.))
    return nodes, pipes
