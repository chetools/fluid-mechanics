"""Rocket nozzle performance and contour geometry, for a calorically perfect gas.

Everything here is the isentropic duct model of `gas_dynamics` pushed to its
design use: the chamber is the stagnation reservoir, the throat chokes, and the
divergent section is sized to set the *exit* state rather than merely to pass
the flow.

Conventions and model limits, stated once because the rest of the module
assumes them:

* All pressures are **absolute** in pascals, temperatures in kelvin, lengths in
  metres, angles in **radians** inside functions and degrees only at the
  boundaries where a caller is explicitly told so.
* Chamber conditions are stagnation conditions: ``p_c`` and ``T_c`` are ``p0``
  and ``T0``. Combustion, finite chamber velocity ("nozzle inlet Mach"),
  boundary layers, heat loss to the wall, chemical recombination in the
  expansion and two-phase (aluminium oxide) flow are all outside the model.
  Real engines report a ``c*`` efficiency of roughly 0.92-0.99 and a nozzle
  efficiency of roughly 0.95-0.99 against exactly these ideal numbers.
* ``gamma`` is constant. Real exhaust ``gamma`` falls through the nozzle as the
  gas cools and its vibrational modes freeze out; design work uses an
  equilibrium or frozen chemistry code (CEA, RPA) and an effective gamma.
* The flow is assumed to be full-flowing and attached. Separation is *predicted*
  by empirical criteria here, never resolved.
* The method-of-characteristics contour is **planar (two-dimensional)**, which
  is the textbook case and the one whose arithmetic can be followed by hand.
  Flight hardware is axisymmetric, whose characteristics carry an extra term.
"""

from __future__ import annotations

import math
from typing import Dict, List, Sequence, Tuple

from src.physics.pipe_network import positive

# Standard gravity, used only to turn an effective exhaust velocity into the
# specific impulse in seconds that the propulsion literature quotes. It is a
# unit conversion, not a local gravity.
G0 = 9.80665


def _check_gamma(gamma: float) -> float:
    gamma = float(gamma)
    if not math.isfinite(gamma) or gamma <= 1.0:
        raise ValueError("gamma must be finite and greater than one.")
    return gamma


# ---------------------------------------------------------------------------
# 1. Isentropic duct relations, in the form nozzle design actually uses
# ---------------------------------------------------------------------------
def area_ratio(mach: float, gamma: float = 1.2) -> float:
    """A/A* from the area-Mach relation of the compressible chapter.

    Identical to the expression derived for a converging-diverging duct; it is
    repeated here because rocket work calls the same number the *expansion
    ratio* epsilon and treats it as the design variable rather than an output.
    """
    gamma = _check_gamma(gamma)
    mach = positive(mach, "Mach number")
    inner = 2 / (gamma + 1) * (1 + (gamma - 1) * mach * mach / 2)
    return inner ** ((gamma + 1) / (2 * (gamma - 1))) / mach


def mach_from_area_ratio(ratio: float, gamma: float = 1.2,
                         supersonic: bool = True) -> float:
    """Invert A/A*. Two roots exist above one; `supersonic` picks the branch.

    The area-Mach relation has a minimum of exactly 1 at M = 1 and rises on both
    sides, so no closed-form inverse exists. Bracket the wanted branch and use a
    scalar root find: this is a single root inside a design calculation, which
    is the shape Brent is for.
    """
    from scipy.optimize import brentq

    gamma = _check_gamma(gamma)
    ratio = float(ratio)
    if not math.isfinite(ratio) or ratio < 1.0:
        raise ValueError("Area ratio A/A* must be at least one.")
    if ratio == 1.0:
        return 1.0

    def residual(mach: float) -> float:
        return area_ratio(mach, gamma) - ratio

    if supersonic:
        low, high = 1.0 + 1e-12, 2.0
        while residual(high) < 0.0:
            high *= 2.0
            if high > 1e4:
                raise ValueError("Could not bracket a supersonic solution.")
        return brentq(residual, low, high, xtol=1e-13, rtol=1e-14)
    return brentq(residual, 1e-9, 1.0, xtol=1e-14, rtol=1e-15)


def pressure_ratio_from_mach(mach: float, gamma: float = 1.2) -> float:
    """p/p0 for isentropic flow: the stagnation relation, inverted for use."""
    gamma = _check_gamma(gamma)
    mach = float(mach)
    if not math.isfinite(mach) or mach < 0:
        raise ValueError("Mach number must be finite and nonnegative.")
    return (1 + (gamma - 1) * mach * mach / 2) ** (-gamma / (gamma - 1))


def mach_from_pressure_ratio(ratio: float, gamma: float = 1.2) -> float:
    """M from p/p0. Single valued, and the honest way to start a design."""
    gamma = _check_gamma(gamma)
    ratio = float(ratio)
    if not math.isfinite(ratio) or not 0 < ratio <= 1:
        raise ValueError("Pressure ratio p/p0 must lie in (0, 1].")
    return math.sqrt(2 / (gamma - 1) * (ratio ** (-(gamma - 1) / gamma) - 1))


def area_ratio_for_pressure_ratio(ratio: float, gamma: float = 1.2) -> float:
    """The design step: choose the exit pressure, get the expansion ratio.

    Routed through the Mach number rather than through the algebraically
    condensed closed form, because the two-step route is the one the lesson
    derives and cannot silently disagree with `area_ratio`.
    """
    return area_ratio(mach_from_pressure_ratio(ratio, gamma), gamma)


def vandenkerckhove(gamma: float = 1.2) -> float:
    """The choked-flow constant Gamma = sqrt(gamma) (2/(gamma+1))^((g+1)/(2(g-1))).

    It collects every gamma-dependent factor in the choked mass flow, so
    ``mdot = p_c A_t Gamma / sqrt(R T_c)``. Naming it is worth the line: the
    same group reappears in c*, in C_F and in the relief-sizing flux.
    """
    gamma = _check_gamma(gamma)
    return math.sqrt(gamma) * (2 / (gamma + 1)) ** ((gamma + 1) / (2 * (gamma - 1)))


def characteristic_velocity(gamma: float, gas_constant: float,
                            chamber_temperature: float) -> float:
    """c* = p_c A_t / mdot = sqrt(R T_c)/Gamma, in m/s.

    c* measures the **chamber** alone: how much stagnation pressure a given
    throat area and mass flow can hold up, which depends on the propellant and
    the combustion temperature and not at all on what is bolted downstream of
    the throat. Splitting performance into c* (chamber) and C_F (nozzle) is the
    single most useful bookkeeping in the subject, because a test stand can
    measure them separately.
    """
    gamma = _check_gamma(gamma)
    positive(gas_constant, "Gas constant")
    positive(chamber_temperature, "Chamber temperature")
    return math.sqrt(gas_constant * chamber_temperature) / vandenkerckhove(gamma)


def thrust_coefficient(gamma: float, expansion_ratio: float,
                       ambient_over_chamber: float = 0.0) -> Dict[str, float]:
    """C_F = F/(p_c A_t): everything the divergent section contributes.

    The momentum term is fixed once gamma and the expansion ratio are chosen.
    The pressure term is the only place the atmosphere appears, and it is what
    makes one nozzle two different engines at sea level and in vacuum.
    """
    gamma = _check_gamma(gamma)
    expansion_ratio = positive(expansion_ratio, "Expansion ratio")
    if expansion_ratio < 1.0:
        raise ValueError("Expansion ratio must be at least one.")
    ambient_over_chamber = float(ambient_over_chamber)
    if not math.isfinite(ambient_over_chamber) or ambient_over_chamber < 0:
        raise ValueError("Ambient/chamber pressure ratio must be finite and nonnegative.")

    exit_mach = mach_from_area_ratio(expansion_ratio, gamma, supersonic=True)
    pe_over_pc = pressure_ratio_from_mach(exit_mach, gamma)
    momentum = math.sqrt(
        2 * gamma * gamma / (gamma - 1)
        * (2 / (gamma + 1)) ** ((gamma + 1) / (gamma - 1))
        * (1 - pe_over_pc ** ((gamma - 1) / gamma))
    )
    pressure = (pe_over_pc - ambient_over_chamber) * expansion_ratio
    return {
        "exit_mach": exit_mach,
        "exit_pressure_ratio": pe_over_pc,
        "momentum_term": momentum,
        "pressure_term": pressure,
        "thrust_coefficient": momentum + pressure,
        "vacuum_thrust_coefficient": momentum + pe_over_pc * expansion_ratio,
    }


def optimum_expansion_ratio(chamber_pressure: float, ambient_pressure: float,
                            gamma: float = 1.2) -> float:
    """The expansion ratio whose exit pressure exactly matches the ambient.

    This is *the* design condition, and the derivation for it is one line:
    dF/dA_e = (p_e - p_a), so thrust stops rising exactly where p_e = p_a. Below
    it the engine leaves exhaust pressure unused; above it the last strip of
    bell is pushed on from outside harder than from inside.
    """
    positive(chamber_pressure, "Chamber pressure")
    positive(ambient_pressure, "Ambient pressure")
    if ambient_pressure >= chamber_pressure:
        raise ValueError("Ambient pressure must be below chamber pressure.")
    return area_ratio_for_pressure_ratio(ambient_pressure / chamber_pressure, gamma)


# ---------------------------------------------------------------------------
# 2. Flow separation: an empirical limit on how far over-expansion may go
# ---------------------------------------------------------------------------
SEPARATION_CRITERIA = ("summerfield", "schmucker")


def separation_exit_pressure(ambient_pressure: float, exit_mach: float = 3.0,
                             criterion: str = "summerfield") -> float:
    """Lowest exit pressure a full-flowing nozzle can sustain, in Pa.

    Both criteria below are **correlations of test data**, not results of the
    ideal model, and they disagree with each other by tens of percent. They are
    included because the ideal model has no opinion at all about separation and
    would happily predict a nozzle that in reality tears itself sideways.

    * ``summerfield`` -- separation near ``p_e ~ 0.4 p_a``; the oldest and
      crudest rule, still the one quoted for a first check.
    * ``schmucker`` -- ``p_e/p_a = (1.88 M_e - 1)^(-0.64)``, which recognises
      that a stronger shock is needed to separate a faster boundary layer.

    Side-loads during the transient of start-up and shut-down, when the shock
    system sweeps through the bell, have destroyed real engines; steady-state
    separation is only part of the concern.
    """
    positive(ambient_pressure, "Ambient pressure")
    criterion = str(criterion).lower()
    if criterion not in SEPARATION_CRITERIA:
        raise ValueError(f"Separation criterion must be one of {SEPARATION_CRITERIA}.")
    if criterion == "summerfield":
        return 0.4 * ambient_pressure
    exit_mach = positive(exit_mach, "Exit Mach number")
    if 1.88 * exit_mach - 1 <= 0:
        raise ValueError("Schmucker's correlation needs an exit Mach above 0.53.")
    return ambient_pressure * (1.88 * exit_mach - 1) ** -0.64


# ---------------------------------------------------------------------------
# 3. The whole engine, at one flight condition
# ---------------------------------------------------------------------------
def nozzle_performance(chamber_pressure: float, chamber_temperature: float,
                       expansion_ratio: float, ambient_pressure: float,
                       throat_area: float, gamma: float = 1.2,
                       gas_constant: float = 355.0,
                       separation_criterion: str = "summerfield") -> Dict[str, float]:
    """Thrust, Isp and the expansion regime for one nozzle at one altitude.

    Returns the split that matters for the sea-level/vacuum comparison: the
    momentum thrust, which does not know the altitude, and the pressure thrust,
    which is the only term that does.
    """
    gamma = _check_gamma(gamma)
    positive(chamber_pressure, "Chamber pressure")
    positive(chamber_temperature, "Chamber temperature")
    positive(throat_area, "Throat area")
    positive(gas_constant, "Gas constant")
    ambient_pressure = positive(ambient_pressure, "Ambient pressure", allow_zero=True)
    if expansion_ratio < 1.0:
        raise ValueError("Expansion ratio must be at least one.")

    coefficients = thrust_coefficient(gamma, expansion_ratio,
                                      ambient_pressure / chamber_pressure)
    exit_mach = coefficients["exit_mach"]
    exit_pressure = coefficients["exit_pressure_ratio"] * chamber_pressure
    exit_temperature = chamber_temperature / (1 + (gamma - 1) * exit_mach ** 2 / 2)
    exit_velocity = exit_mach * math.sqrt(gamma * gas_constant * exit_temperature)
    exit_area = expansion_ratio * throat_area

    c_star = characteristic_velocity(gamma, gas_constant, chamber_temperature)
    mass_flow = chamber_pressure * throat_area / c_star
    momentum_thrust = mass_flow * exit_velocity
    pressure_thrust = (exit_pressure - ambient_pressure) * exit_area
    thrust = momentum_thrust + pressure_thrust

    if ambient_pressure <= 0:
        mode, separated = "vacuum (always under-expanded)", False
    elif exit_pressure > 1.05 * ambient_pressure:
        mode, separated = "under-expanded", False
    elif exit_pressure < 0.95 * ambient_pressure:
        mode = "over-expanded"
        separated = exit_pressure < separation_exit_pressure(
            ambient_pressure, exit_mach, separation_criterion)
    else:
        mode, separated = "matched (design point)", False

    return {
        "exit_mach": exit_mach,
        "exit_pressure": exit_pressure,
        "exit_temperature": exit_temperature,
        "exit_velocity": exit_velocity,
        "exit_area": exit_area,
        "throat_area": throat_area,
        "expansion_ratio": expansion_ratio,
        "mass_flow": mass_flow,
        "characteristic_velocity": c_star,
        "thrust_coefficient": coefficients["thrust_coefficient"],
        "vacuum_thrust_coefficient": coefficients["vacuum_thrust_coefficient"],
        "momentum_thrust": momentum_thrust,
        "pressure_thrust": pressure_thrust,
        "thrust": thrust,
        "effective_exhaust_velocity": thrust / mass_flow,
        "specific_impulse": thrust / (mass_flow * G0),
        "ambient_pressure": ambient_pressure,
        "pressure_ratio_exit_ambient": (
            exit_pressure / ambient_pressure if ambient_pressure > 0 else math.inf),
        "mode": mode,
        "separation_predicted": separated,
        "separation_exit_pressure": (
            separation_exit_pressure(ambient_pressure, exit_mach, separation_criterion)
            if ambient_pressure > 0 else 0.0),
    }


# ---------------------------------------------------------------------------
# 4. Where the atmosphere goes, so "sea level versus vacuum" has a middle
# ---------------------------------------------------------------------------
# US Standard Atmosphere 1976, geopotential layers to 71 km. Base pressures are
# the published layer values; recomputing them by chaining the barometric
# formula from sea level reproduces them, which the tests check.
_ATMOSPHERE_LAYERS: Tuple[Tuple[float, float, float, float], ...] = (
    # base geopotential height [m], base T [K], lapse rate [K/m], base p [Pa]
    (0.0, 288.15, -0.0065, 101325.0),
    (11000.0, 216.65, 0.0, 22632.06),
    (20000.0, 216.65, 0.001, 5474.889),
    (32000.0, 228.65, 0.0028, 868.0187),
    (47000.0, 270.65, 0.0, 110.9063),
    (51000.0, 270.65, -0.0028, 66.93887),
    (71000.0, 214.65, -0.002, 3.956420),
)
_AIR_R = 287.0528


def standard_atmosphere_pressure(altitude: float) -> float:
    """Ambient pressure [Pa] at a geopotential altitude [m], US Standard 1976.

    Only the pressure is returned, because that is the only atmospheric
    property a thrust calculation needs: the nozzle's own gas is the propellant,
    not the air. Above 71 km the last layer is extrapolated and the answer is
    small enough that vacuum performance is the honest description.
    """
    altitude = float(altitude)
    if not math.isfinite(altitude) or altitude < 0:
        raise ValueError("Altitude must be finite and nonnegative.")
    base_h, base_t, lapse, base_p = _ATMOSPHERE_LAYERS[0]
    for layer in _ATMOSPHERE_LAYERS:
        if altitude >= layer[0]:
            base_h, base_t, lapse, base_p = layer
        else:
            break
    delta = altitude - base_h
    if lapse == 0.0:
        return base_p * math.exp(-G0 * delta / (_AIR_R * base_t))
    temperature = base_t + lapse * delta
    return base_p * (temperature / base_t) ** (-G0 / (_AIR_R * lapse))


def altitude_sweep(chamber_pressure: float, chamber_temperature: float,
                   expansion_ratio: float, throat_area: float,
                   gamma: float = 1.2, gas_constant: float = 355.0,
                   altitudes: Sequence[float] = None) -> Dict[str, List[float]]:
    """Thrust, Isp and expansion regime of one fixed nozzle from pad to vacuum.

    Nothing about the engine changes along this sweep. Only ``p_a`` does, and
    the whole climb in thrust is the pressure term ``(p_e - p_a) A_e`` losing
    its subtrahend.
    """
    if altitudes is None:
        altitudes = [i * 1000.0 for i in range(0, 81)]
    rows = {key: [] for key in
            ("altitude", "ambient_pressure", "thrust", "specific_impulse",
             "momentum_thrust", "pressure_thrust", "separation_predicted")}
    for altitude in altitudes:
        ambient = standard_atmosphere_pressure(altitude)
        result = nozzle_performance(chamber_pressure, chamber_temperature,
                                    expansion_ratio, ambient, throat_area,
                                    gamma, gas_constant)
        rows["altitude"].append(float(altitude))
        rows["ambient_pressure"].append(ambient)
        for key in ("thrust", "specific_impulse", "momentum_thrust",
                    "pressure_thrust", "separation_predicted"):
            rows[key].append(result[key])
    return rows


# ---------------------------------------------------------------------------
# 5. Prandtl-Meyer: how much a supersonic stream may turn
# ---------------------------------------------------------------------------
def prandtl_meyer(mach: float, gamma: float = 1.2) -> float:
    """nu(M) in radians: the turn a sonic stream needs to reach Mach M.

    Read backwards, it is the design tool: a nozzle wall that turns the flow
    away from the axis by nu(M_e)/2 and then turns it back is exactly enough to
    produce M_e, which is where the minimum-length contour comes from.
    """
    gamma = _check_gamma(gamma)
    mach = float(mach)
    if not math.isfinite(mach) or mach < 1.0:
        raise ValueError("Prandtl-Meyer angle is defined for M >= 1.")
    if mach == 1.0:
        return 0.0
    root = math.sqrt(mach * mach - 1)
    factor = math.sqrt((gamma + 1) / (gamma - 1))
    return factor * math.atan(root / factor) - math.atan(root)


def mach_from_prandtl_meyer(nu: float, gamma: float = 1.2) -> float:
    """Invert nu(M). Monotonic in M, so a bracketed root find is exact enough."""
    from scipy.optimize import brentq

    gamma = _check_gamma(gamma)
    nu = float(nu)
    if not math.isfinite(nu) or nu < 0:
        raise ValueError("Prandtl-Meyer angle must be finite and nonnegative.")
    if nu == 0.0:
        return 1.0
    nu_max = (math.sqrt((gamma + 1) / (gamma - 1)) - 1) * math.pi / 2
    if nu >= nu_max:
        raise ValueError(
            f"nu = {nu:.4f} rad is at or beyond the vacuum limit {nu_max:.4f} rad "
            "for this gamma; no finite Mach number reaches it.")
    return brentq(lambda m: prandtl_meyer(m, gamma) - nu, 1.0 + 1e-12, 1e4,
                  xtol=1e-13, rtol=1e-14)


def mach_angle(mach: float) -> float:
    """mu = asin(1/M), the angle a weak disturbance makes with the stream."""
    mach = float(mach)
    if not math.isfinite(mach) or mach < 1.0:
        raise ValueError("Mach angle is defined for M >= 1.")
    return math.asin(1.0 / mach)


# ---------------------------------------------------------------------------
# 6. Method of characteristics: the contour, computed rather than sketched
# ---------------------------------------------------------------------------
def _intersect(point_a: Tuple[float, float], slope_a: float,
               point_b: Tuple[float, float], slope_b: float) -> Tuple[float, float]:
    """Intersection of two lines given as point-and-slope."""
    if abs(slope_a - slope_b) < 1e-14:
        raise ValueError("Characteristics are parallel; refine the mesh.")
    x = ((point_b[1] - point_a[1]) + slope_a * point_a[0] - slope_b * point_b[0]) \
        / (slope_a - slope_b)
    return x, point_a[1] + slope_a * (x - point_a[0])


def moc_minimum_length_nozzle(exit_mach: float, gamma: float = 1.2,
                              n_characteristics: int = 12,
                              throat_half_height: float = 1.0) -> Dict:
    """Planar minimum-length nozzle by the method of characteristics.

    The construction, in the order the code performs it:

    1. The exit Mach number fixes the total turning available,
       ``nu(M_e)``. A sharp-cornered (minimum-length) nozzle spends half of it
       expanding and recovers the other half straightening, so the wall's
       maximum angle is ``theta_max = nu(M_e)/2``.
    2. That corner turn is discretised into ``n`` waves of ``d_theta =
       theta_max/n``. Wave ``i`` leaves the corner having turned the flow to
       ``theta_i = i d_theta``, and since the expansion starts sonic,
       ``nu_i = theta_i`` there.
    3. Along a C- characteristic ``K_- = theta + nu`` is constant; along a C+,
       ``K_+ = theta - nu``. So each wave carries ``K_- = 2 theta_i`` downstream
       unchanged, and every mesh point's state is the intersection of one of
       each.
    4. On the axis symmetry forces ``theta = 0``, which reflects each C- into a
       C+ carrying ``K_+ = -2 theta_i``.
    5. At the wall the contour is *chosen* so that the arriving wave is not
       reflected: the wall simply turns to the local flow angle. That is the
       cancellation that ends the expansion, and it is why the last wall point
       has ``theta = 0`` and ``nu = nu(M_e)`` -- axial flow at the design Mach.

    Because every point's ``(theta, nu)`` is fixed by steps 3-5 before any
    geometry is drawn, the state field is exact and only the *positions* carry
    the discretisation error of averaging characteristic slopes between points.
    Increasing ``n_characteristics`` therefore converges the wall shape, not the
    exit Mach number, which is imposed.

    Returns a dict with the wall contour, the interior mesh, the wave segments
    for drawing, and the achieved area ratio ``y_exit/y_throat`` -- which should
    approach the planar ``A/A*`` of the design Mach number, and is the honest
    check that the construction worked.
    """
    gamma = _check_gamma(gamma)
    exit_mach = float(exit_mach)
    if not math.isfinite(exit_mach) or exit_mach <= 1.0:
        raise ValueError("A diverging nozzle needs a design exit Mach above one.")
    n = int(n_characteristics)
    if n < 2:
        raise ValueError("Use at least two characteristics.")
    throat_half_height = positive(throat_half_height, "Throat half-height")

    nu_exit = prandtl_meyer(exit_mach, gamma)
    theta_max = nu_exit / 2
    d_theta = theta_max / n

    def state(theta: float, nu: float) -> Dict[str, float]:
        mach = mach_from_prandtl_meyer(nu, gamma)
        return {"theta": theta, "nu": nu, "mach": mach, "mu": mach_angle(mach)}

    # The n waves as they leave the sharp corner: theta_i = nu_i = i d_theta.
    corner = (0.0, throat_half_height)
    corner_states = [state(i * d_theta, i * d_theta) for i in range(1, n + 1)]

    rows: List[List[Dict[str, float]]] = []
    wall: List[Dict[str, float]] = [
        {"x": 0.0, "y": throat_half_height, "theta": theta_max,
         "nu": theta_max, "mach": mach_from_prandtl_meyer(theta_max, gamma)}
    ]
    waves: List[List[Tuple[float, float]]] = []

    for k in range(1, n + 1):
        row: List[Dict[str, float]] = []
        # Axis point of row k: theta = 0, so nu = K_- = 2 theta_k.
        axis = state(0.0, 2 * k * d_theta)
        if k == 1:
            source, source_state = corner, corner_states[0]
        else:
            previous = rows[k - 2][1]
            source = (previous["x"], previous["y"])
            source_state = previous
        slope = math.tan(
            0.5 * ((source_state["theta"] - source_state["mu"])
                   + (axis["theta"] - axis["mu"])))
        x_axis = source[0] - source[1] / slope
        axis.update({"x": x_axis, "y": 0.0})
        row.append(axis)
        waves.append([source, (x_axis, 0.0)])

        # Interior points: the C+ reflected off the axis crossing waves k+1..n.
        for j in range(1, n - k + 1):
            here = state(j * d_theta, (2 * k + j) * d_theta)
            left = row[j - 1]
            slope_plus = math.tan(
                0.5 * ((left["theta"] + left["mu"]) + (here["theta"] + here["mu"])))
            if k == 1:
                down, down_state = corner, corner_states[j]
            else:
                previous = rows[k - 2][j + 1]
                down = (previous["x"], previous["y"])
                down_state = previous
            slope_minus = math.tan(
                0.5 * ((down_state["theta"] - down_state["mu"])
                       + (here["theta"] - here["mu"])))
            x, y = _intersect((left["x"], left["y"]), slope_plus, down, slope_minus)
            here.update({"x": x, "y": y})
            row.append(here)
            waves.append([(left["x"], left["y"]), (x, y)])
            waves.append([down, (x, y)])

        # Wall point: the contour turns to the arriving flow angle, cancelling
        # the wave instead of reflecting it.
        last = row[-1]
        wall_state = {"theta": last["theta"], "nu": last["nu"], "mach": last["mach"]}
        previous_wall = wall[-1]
        wall_slope = math.tan(0.5 * (previous_wall["theta"] + wall_state["theta"]))
        slope_plus = math.tan(
            0.5 * ((last["theta"] + last["mu"])
                   + (wall_state["theta"] + mach_angle(wall_state["mach"]))))
        x, y = _intersect((previous_wall["x"], previous_wall["y"]), wall_slope,
                          (last["x"], last["y"]), slope_plus)
        wall_state.update({"x": x, "y": y})
        wall.append(wall_state)
        waves.append([(last["x"], last["y"]), (x, y)])
        rows.append(row)

    achieved = wall[-1]["y"] / throat_half_height
    return {
        "wall": wall,
        "rows": rows,
        "waves": waves,
        "theta_max": theta_max,
        "nu_exit": nu_exit,
        "design_mach": exit_mach,
        "d_theta": d_theta,
        "length": wall[-1]["x"],
        "exit_half_height": wall[-1]["y"],
        "achieved_area_ratio": achieved,
        "ideal_area_ratio": area_ratio(exit_mach, gamma),
        "area_ratio_error": achieved / area_ratio(exit_mach, gamma) - 1.0,
    }


# ---------------------------------------------------------------------------
# 7. Practical contours: the cone that is easy and the bell that is used
# ---------------------------------------------------------------------------
def conical_nozzle(expansion_ratio: float, throat_radius: float = 1.0,
                   half_angle_deg: float = 15.0,
                   n_points: int = 60) -> Dict:
    """A straight-walled cone, and the price of its non-axial exhaust.

    A cone's exhaust leaves on a spread of directions. Averaging the axial
    component of momentum over a uniform flow through a spherical cap gives the
    divergence efficiency ``lambda = (1 + cos alpha)/2`` -- 0.983 at the
    traditional 15 degrees, which is 1.7% of thrust thrown sideways. That number
    is the entire reason bells exist.
    """
    expansion_ratio = positive(expansion_ratio, "Expansion ratio")
    throat_radius = positive(throat_radius, "Throat radius")
    half_angle = math.radians(positive(half_angle_deg, "Cone half-angle"))
    if not 0 < half_angle < math.pi / 2:
        raise ValueError("Cone half-angle must lie strictly between 0 and 90 degrees.")
    exit_radius = throat_radius * math.sqrt(expansion_ratio)
    length = (exit_radius - throat_radius) / math.tan(half_angle)
    xs = [length * i / (n_points - 1) for i in range(n_points)]
    return {
        "x": xs,
        "r": [throat_radius + x * math.tan(half_angle) for x in xs],
        "length": length,
        "exit_radius": exit_radius,
        "half_angle_deg": half_angle_deg,
        "divergence_efficiency": (1 + math.cos(half_angle)) / 2,
    }


def bell_contour(expansion_ratio: float, throat_radius: float = 1.0,
                 initial_angle_deg: float = 22.0, exit_angle_deg: float = 11.0,
                 length_fraction: float = 0.8,
                 reference_half_angle_deg: float = 15.0,
                 n_points: int = 80) -> Dict:
    """Rao's parabolic-approximation bell: arcs, then one quadratic curve.

    The construction is fully determined by five numbers and is drawn here
    exactly, with nothing interpolated from a chart:

    1. ``L = f * (R_t(sqrt(eps) - 1)/tan(15 deg))`` -- the bell's axial length as
       a stated fraction of the 15-degree cone of the same expansion ratio. An
       "80% bell" means ``f = 0.8``.
    2. A circular arc of radius ``1.5 R_t`` shapes the converging side of the
       throat, and one of radius ``0.382 R_t`` the diverging side. Both radii
       are conventional workshop values, chosen small enough to turn the flow
       quickly and large enough not to separate; they are not derived here.
    3. The downstream arc is swept from the throat to the initial wall angle
       ``theta_n``, giving the attachment point N.
    4. A quadratic Bezier runs from N to the exit point E, its control point at
       the intersection of the tangent at N (slope ``tan theta_n``) with the
       tangent at E (slope ``tan theta_e``). A quadratic Bezier *is* a parabola,
       which is what "parabolic approximation" means.

    ``theta_n`` and ``theta_e`` come from Rao's optimisation charts and are
    inputs here rather than outputs, because reproducing that optimisation needs
    an axisymmetric method-of-characteristics solve with a control-surface
    variational condition. What this function guarantees is that the contour it
    returns is tangent-continuous and hits the requested area ratio exactly.
    """
    expansion_ratio = positive(expansion_ratio, "Expansion ratio")
    if expansion_ratio < 1.0:
        raise ValueError("Expansion ratio must be at least one.")
    throat_radius = positive(throat_radius, "Throat radius")
    theta_n = math.radians(positive(initial_angle_deg, "Initial wall angle"))
    theta_e = math.radians(positive(exit_angle_deg, "Exit wall angle"))
    if theta_e >= theta_n:
        raise ValueError("A bell turns back toward the axis: theta_e must be below theta_n.")
    length_fraction = positive(length_fraction, "Length fraction")
    reference = math.radians(positive(reference_half_angle_deg, "Reference cone half-angle"))

    exit_radius = throat_radius * math.sqrt(expansion_ratio)
    cone_length = (exit_radius - throat_radius) / math.tan(reference)
    length = length_fraction * cone_length

    # Diverging throat arc, radius 0.382 R_t, centred at (0, R_t + 0.382 R_t).
    arc_radius = 0.382 * throat_radius
    centre_y = throat_radius + arc_radius
    n_arc = max(8, n_points // 4)
    arc_x, arc_r = [], []
    for i in range(n_arc + 1):
        angle = theta_n * i / n_arc          # swept from the throat
        arc_x.append(arc_radius * math.sin(angle))
        arc_r.append(centre_y - arc_radius * math.cos(angle))
    start = (arc_x[-1], arc_r[-1])
    end = (length, exit_radius)
    if end[0] <= start[0]:
        raise ValueError("Requested bell is shorter than its own throat arc; "
                         "raise the length fraction or lower the initial angle.")

    # Bezier control point: where the two tangents meet.
    m_n, m_e = math.tan(theta_n), math.tan(theta_e)
    cx = ((end[1] - start[1]) + m_n * start[0] - m_e * end[0]) / (m_n - m_e)
    cy = start[1] + m_n * (cx - start[0])

    n_bell = n_points - n_arc
    xs, rs = list(arc_x), list(arc_r)
    for i in range(1, n_bell + 1):
        t = i / n_bell
        one = 1 - t
        xs.append(one * one * start[0] + 2 * one * t * cx + t * t * end[0])
        rs.append(one * one * start[1] + 2 * one * t * cy + t * t * end[1])
    return {
        "x": xs,
        "r": rs,
        "length": length,
        "cone_length": cone_length,
        "length_fraction": length_fraction,
        "exit_radius": exit_radius,
        "attachment_point": start,
        "control_point": (cx, cy),
        "initial_angle_deg": initial_angle_deg,
        "exit_angle_deg": exit_angle_deg,
        "throat_arc_radius": arc_radius,
    }


def converging_contour(throat_radius: float = 1.0, chamber_radius: float = 3.0,
                       half_angle_deg: float = 30.0, n_points: int = 40) -> Dict:
    """The subsonic side: a conical taper closed by a 1.5 R_t throat arc.

    Its shape barely affects performance, because subsonic flow is forgiving and
    the mass flow is set by the throat area alone. It affects *packaging* and
    the chamber's contraction ratio, and it must not be so steep that the flow
    separates before it reaches the throat.
    """
    throat_radius = positive(throat_radius, "Throat radius")
    chamber_radius = positive(chamber_radius, "Chamber radius")
    if chamber_radius <= throat_radius:
        raise ValueError("The chamber must be wider than the throat.")
    half_angle = math.radians(positive(half_angle_deg, "Converging half-angle"))
    arc_radius = 1.5 * throat_radius
    centre_y = throat_radius + arc_radius

    n_arc = max(8, n_points // 2)
    arc_x, arc_r = [], []
    for i in range(n_arc + 1):
        angle = half_angle * (1 - i / n_arc)
        arc_x.append(-arc_radius * math.sin(angle))
        arc_r.append(centre_y - arc_radius * math.cos(angle))
    join = (arc_x[0], arc_r[0])
    run = (chamber_radius - join[1]) / math.tan(half_angle)
    n_line = n_points - n_arc
    xs = [join[0] - run * (1 - i / n_line) for i in range(n_line)]
    rs = [chamber_radius - (chamber_radius - join[1]) * i / n_line for i in range(n_line)]
    return {
        "x": xs + arc_x,
        "r": rs + arc_r,
        "contraction_ratio": (chamber_radius / throat_radius) ** 2,
        "throat_arc_radius": arc_radius,
        "half_angle_deg": half_angle_deg,
    }


def march_along_contour(x: Sequence[float], r: Sequence[float],
                        chamber_pressure: float, chamber_temperature: float,
                        gamma: float = 1.2, gas_constant: float = 355.0,
                        throat_radius: float = None) -> Dict[str, List[float]]:
    """State along a given wall contour, using only the local area.

    Quasi-one-dimensional: each station is assigned the Mach number its own area
    ratio implies, on the supersonic branch downstream of the throat and the
    subsonic branch upstream. That ignores the flow's two-dimensionality
    entirely -- a real bell has a curved sonic line and radial velocity
    components, which is exactly what the method of characteristics puts back.
    Good enough to show *where* the expansion happens; not a design tool.
    """
    if len(x) != len(r) or len(x) < 2:
        raise ValueError("Contour needs matching x and r arrays of at least two points.")
    throat = positive(throat_radius if throat_radius is not None else min(r),
                      "Throat radius")
    x_throat = list(x)[list(r).index(min(r))] if throat_radius is None else 0.0
    out = {key: [] for key in ("x", "area_ratio", "mach", "pressure",
                               "temperature", "velocity")}
    for xi, ri in zip(x, r):
        ratio = max((ri / throat) ** 2, 1.0)
        mach = mach_from_area_ratio(ratio, gamma, supersonic=xi > x_throat)
        pressure = chamber_pressure * pressure_ratio_from_mach(mach, gamma)
        temperature = chamber_temperature / (1 + (gamma - 1) * mach * mach / 2)
        out["x"].append(float(xi))
        out["area_ratio"].append(ratio)
        out["mach"].append(mach)
        out["pressure"].append(pressure)
        out["temperature"].append(temperature)
        out["velocity"].append(mach * math.sqrt(gamma * gas_constant * temperature))
    return out


# A reproducible worked example: a kerosene/oxygen gas-generator-cycle first
# stage, of the general size of a Merlin-class engine. The propellant numbers
# are representative values for a lesson, not a manufacturer's data sheet.
ROCKET_DEMO_DEFAULTS = dict(
    chamber_pressure=97e5,
    chamber_temperature=3500.0,
    gamma=1.24,
    gas_constant=355.0,
    throat_area=0.0305,
    expansion_ratio=16.0,
)
