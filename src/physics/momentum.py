"""Control-volume (integral) momentum balances and their classical applications.

Every result in this module comes from one statement -- the Reynolds transport
theorem applied to linear momentum on a fixed control volume:

    sum F  =  d/dt integral_CV rho u dV  +  integral_CS rho u (u . n) dA

and, for steady one-dimensional inlets and outlets,

    sum F  =  sum_out beta mdot u  -  sum_in beta mdot u.

The forces on the left are surface forces (pressure over the control surface,
plus whatever the walls or a support must supply) and body forces (weight).
Gauge pressure is used throughout: a uniform atmosphere contributes nothing to
a closed surface integral, so working in gauge deletes it exactly rather than
approximately.

The reason this balance earns its own chapter is that it needs **no model of
the interior**. A sudden expansion, a hydraulic jump and a rocket chamber are
all violently dissipative, and none of them can be treated with Bernoulli --
but momentum only counts what crosses the boundary, so it does not care.
Energy, by contrast, is *not* conserved in those devices, which is exactly why
combining the two balances measures the loss (see `sudden_expansion` and
`hydraulic_jump`).

Conventions
-----------
* All quantities SI. Angles are given in degrees at the API boundary and
  converted immediately.
* Pressures are gauge (Pa) unless the name says otherwise.
* A reported "force on the device" is the force the fluid exerts on the solid;
  the force the solid exerts on the fluid, which is what appears in the
  balance, is its negative. Mixing those two is the commonest sign error here.
* beta is the momentum-flux correction factor for a non-uniform profile,
  beta = (1/(A u_bar^2)) integral u^2 dA. It is 4/3 for a laminar pipe parabola
  and about 1.02 in turbulent pipe flow; src.physics.turbulence.
  pipe_kinetic_correction computes both from the profiles chapter 4 plots.
  Functions here assume beta = 1 (uniform inlet and outlet) and say so.

Model limits: steady flow, constant density, one-dimensional inlets and
outlets, and gravity as the only body force. Wall shear over the short control
volumes used here is neglected, which is stated at each call site.
"""

import math
from typing import Dict

G = 9.81
G0 = 9.80665  # standard gravity, used only to convert to specific impulse


# --------------------------------------------------------------------------
# 1. Jets: the simplest place where the momentum flux is the whole answer
# --------------------------------------------------------------------------
def jet_on_vane(
    rho: float,
    area: float,
    jet_speed: float,
    vane_speed: float = 0.0,
    deflection_deg: float = 180.0,
    series: bool = True,
) -> Dict[str, float]:
    """Force, power and efficiency for a jet deflected by a vane.

    The control volume moves with the vane, so in its frame the flow is steady
    and the relative speed is w = V - U at both entry and exit (no friction, no
    elevation change along the blade, and the free jet stays at atmospheric
    pressure, so no pressure force appears on the control surface).

    ``series`` distinguishes the two mass flows that are constantly confused:

    * ``series=True`` -- a wheel of buckets, so every vane is replaced as it
      moves away and the machine intercepts the whole jet, mdot = rho A V.
      This is the Pelton case.
    * ``series=False`` -- one isolated vane running away from the nozzle, which
      catches only mdot = rho A (V - U).

    ``deflection_deg`` is the angle through which the *relative* velocity is
    turned: 180 degrees reverses it (maximum force), 90 degrees turns it
    sideways, 0 degrees is no vane at all and gives no force.
    """
    v, u = float(jet_speed), float(vane_speed)
    w = v - u
    theta = math.radians(float(deflection_deg))
    mdot_jet = rho * area * v
    mdot = mdot_jet if series else rho * area * max(w, 0.0)
    fx = mdot * w * (1.0 - math.cos(theta))
    fy = -mdot * w * math.sin(theta)
    power = fx * u
    jet_power = 0.5 * mdot_jet * v**2
    return {
        "relative_speed": w,
        "mass_flow": mdot,
        "jet_mass_flow": mdot_jet,
        "force_x": fx,
        "force_y": fy,
        "force": math.hypot(fx, fy),
        "power": power,
        "jet_power": jet_power,
        "efficiency": power / jet_power if jet_power > 0 else 0.0,
        # Series wheel, 180 deg: eta = 4 U (V-U) / V^2, maximised at U = V/2.
        # A single vane instead maximises power at U = V/3.
        "optimum_vane_speed": 0.5 * v if series else v / 3.0,
    }


# --------------------------------------------------------------------------
# 2. Bends and reducers: the force an anchor block has to hold
# --------------------------------------------------------------------------
def bend_force(
    rho: float,
    d1: float,
    d2: float,
    flow_rate: float,
    p1_gauge: float,
    angle_deg: float,
    loss_k: float = 0.0,
) -> Dict[str, float]:
    """Anchor force on a reducing bend lying in a horizontal plane.

    The outlet points along (cos t, sin t) with t measured from the inlet
    direction, so t = 0 is a straight reducer and t = 180 degrees is a return
    bend.

    p2 comes from the mechanical energy balance with a minor loss charged on
    the inlet velocity head, ``loss_k * rho u1^2 / 2``; set loss_k = 0 for the
    ideal (Bernoulli) estimate. The weight of the fitting and of the water
    inside it acts out of this plane and is not included.

    Returns the force **the fluid exerts on the bend**, which is what the bolts
    and the thrust block have to carry.
    """
    a1 = math.pi * d1**2 / 4.0
    a2 = math.pi * d2**2 / 4.0
    u1 = flow_rate / a1
    u2 = flow_rate / a2
    mdot = rho * flow_rate
    p2 = p1_gauge + 0.5 * rho * (u1**2 - u2**2) - loss_k * 0.5 * rho * u1**2
    t = math.radians(float(angle_deg))
    fx = (p1_gauge * a1 + mdot * u1) - (p2 * a2 + mdot * u2) * math.cos(t)
    fy = -(p2 * a2 + mdot * u2) * math.sin(t)
    return {
        "area_in": a1,
        "area_out": a2,
        "u_in": u1,
        "u_out": u2,
        "mass_flow": mdot,
        "p2_gauge": p2,
        "force_x": fx,
        "force_y": fy,
        "force": math.hypot(fx, fy),
        "direction_deg": math.degrees(math.atan2(fy, fx)),
        "pressure_part": math.hypot(
            p1_gauge * a1 - p2 * a2 * math.cos(t), -p2 * a2 * math.sin(t)
        ),
        "momentum_part": math.hypot(
            mdot * u1 - mdot * u2 * math.cos(t), -mdot * u2 * math.sin(t)
        ),
    }


# --------------------------------------------------------------------------
# 3. Sudden expansion: momentum gives the pressure rise, energy gives the loss
# --------------------------------------------------------------------------
def sudden_expansion(
    rho: float, d1: float, d2: float, u1: float, p1_gauge: float = 0.0
) -> Dict[str, float]:
    """Borda-Carnot expansion: pressure recovery, loss, and force on the step.

    The key modelling assumption is that the separated corner eddy is nearly
    stagnant, so the pressure over the annular step face is p1 rather than
    anything the jet does. Chapter 2 derives the head loss from this; here the
    same balance is also read for the *pressure rise* and for the force the
    fluid puts on the step, which is what a real flange feels.

    ``ideal_pressure_rise`` is what Bernoulli would have predicted; the gap
    between the two is exactly rho g h_L, so the pair measures the loss rather
    than offering two competing formulas.
    """
    a1 = math.pi * d1**2 / 4.0
    a2 = math.pi * d2**2 / 4.0
    if a2 <= a1:
        raise ValueError("a sudden expansion needs d2 > d1")
    u2 = u1 * a1 / a2
    dp = rho * u2 * (u1 - u2)  # momentum: p2 > p1, the flow decelerates
    ideal_dp = 0.5 * rho * (u1**2 - u2**2)
    head_loss = (u1 - u2) ** 2 / (2.0 * G)
    return {
        "area_in": a1,
        "area_out": a2,
        "u_out": u2,
        "area_ratio": a1 / a2,
        "pressure_rise": dp,
        "ideal_pressure_rise": ideal_dp,
        "pressure_defect": ideal_dp - dp,  # equals rho g h_L exactly
        "head_loss": head_loss,
        "loss_coefficient": (1.0 - a1 / a2) ** 2,
        "dissipated_power": rho * u1 * a1 * G * head_loss,
        "p2_gauge": p1_gauge + dp,
        # Step force assumed to act at p1 over the annulus; positive downstream.
        "step_force": p1_gauge * (a2 - a1),
        "pressure_recovery_fraction": dp / ideal_dp if ideal_dp > 0 else 0.0,
    }


# --------------------------------------------------------------------------
# 4. Hydraulic jump: the free-surface shock
# --------------------------------------------------------------------------
def momentum_function(depth: float, unit_discharge: float) -> float:
    """M = q^2/(g y) + y^2/2 per unit width, in m^2.

    Momentum flux plus hydrostatic pressure force, both divided by rho g and
    taken per unit width. Across a jump this quantity is conserved while
    specific energy is not.
    """
    return unit_discharge**2 / (G * depth) + depth**2 / 2.0


def specific_energy(depth: float, unit_discharge: float) -> float:
    """E = y + q^2/(2 g y^2), in m."""
    return depth + unit_discharge**2 / (2.0 * G * depth**2)


def hydraulic_jump(y1: float, unit_discharge: float) -> Dict[str, float]:
    """Conjugate depth and energy loss of a jump in a wide rectangular channel.

    Solving M(y1) = M(y2) for the other root gives the Belanger equation

        y2/y1 = 0.5 (sqrt(1 + 8 Fr1^2) - 1),

    after which the dissipation follows from the energy balance that the
    momentum solution never enforced. A jump exists only if the approach flow
    is supercritical; Fr1 <= 1 is reported with ``exists = False`` rather than
    silently returning the trivial root.
    """
    q = float(unit_discharge)
    u1 = q / y1
    fr1 = u1 / math.sqrt(G * y1)
    y2 = 0.5 * y1 * (math.sqrt(1.0 + 8.0 * fr1**2) - 1.0)
    u2 = q / y2
    e1 = specific_energy(y1, q)
    e2 = specific_energy(y2, q)
    loss = (y2 - y1) ** 3 / (4.0 * y1 * y2)
    if fr1 <= 1.0:
        kind = "no jump: the approach flow is already subcritical"
    elif fr1 < 1.7:
        kind = "undular jump (a train of surface waves, little dissipation)"
    elif fr1 < 2.5:
        kind = "weak jump"
    elif fr1 < 4.5:
        kind = "oscillating jump (avoid: it sends waves downstream)"
    elif fr1 < 9.0:
        kind = "steady jump (the design range for stilling basins)"
    else:
        kind = "strong jump (very effective, but rough and erosive)"
    return {
        "y1": y1,
        "y2": y2,
        "u1": u1,
        "u2": u2,
        "froude_1": fr1,
        "froude_2": u2 / math.sqrt(G * y2),
        "critical_depth": (q**2 / G) ** (1.0 / 3.0),
        "energy_1": e1,
        "energy_2": e2,
        "energy_loss": loss,
        "energy_loss_from_difference": e1 - e2,
        "loss_fraction": loss / e1 if e1 > 0 else 0.0,
        "momentum_1": momentum_function(y1, q),
        "momentum_2": momentum_function(y2, q),
        "exists": fr1 > 1.0,
        "kind": kind,
    }


# --------------------------------------------------------------------------
# 5. Weirs and gates: measuring flow by controlling the geometry
# --------------------------------------------------------------------------
def rehbock_cd(head: float, crest_height: float) -> float:
    """Rehbock's discharge coefficient for a sharp-crested rectangular weir.

    Cd = 0.611 + 0.075 H/P. Valid for H/P up to about 5 with a fully ventilated
    nappe; it is a fit to measurements, not a derived constant.
    """
    return 0.611 + 0.075 * float(head) / float(crest_height)


def rectangular_weir(
    head: float, width: float, crest_height: float = 0.5, cd: float = None
) -> Dict[str, float]:
    """Sharp-crested rectangular weir: Q = (2/3) Cd b sqrt(2g) H^(3/2).

    The 2/3 and the 3/2 power come from integrating the free-jet speed
    sqrt(2 g h) over the depth of the nappe; Cd absorbs contraction, viscosity,
    surface tension and the approach velocity head, none of which that
    integration knows about.
    """
    cd = rehbock_cd(head, crest_height) if cd is None else float(cd)
    ideal = (2.0 / 3.0) * width * math.sqrt(2.0 * G) * head**1.5
    return {
        "discharge": cd * ideal,
        "ideal_discharge": ideal,
        "cd": cd,
        "sensitivity": 1.5,  # dQ/Q = 1.5 dH/H
        "head": head,
    }


def v_notch_weir(
    head: float, notch_angle_deg: float = 90.0, cd: float = 0.58
) -> Dict[str, float]:
    """Triangular weir: Q = (8/15) Cd tan(t/2) sqrt(2g) H^(5/2).

    The extra power of H over the rectangular weir is purely geometric: the
    flow width itself grows with the head, so a V-notch keeps its resolution at
    small flows, which is why it is the standard low-flow gauge.
    """
    t = math.radians(float(notch_angle_deg))
    q = (8.0 / 15.0) * cd * math.tan(t / 2.0) * math.sqrt(2.0 * G) * head**2.5
    return {"discharge": q, "cd": cd, "sensitivity": 2.5, "head": head}


def broad_crested_weir(head: float, width: float, cd: float = 0.85) -> Dict[str, float]:
    """Broad-crested weir: Q = Cd b sqrt(g) (2H/3)^(3/2).

    Here the physics is chapter 2's critical depth rather than a free jet: the
    crest forces Fr = 1, so y_c = 2H/3 and q = sqrt(g) y_c^(3/2). Cd (about
    0.85 to 0.95) corrects for the boundary layer on the crest and for
    streamlines that are not quite parallel.
    """
    yc = 2.0 * head / 3.0
    q = cd * width * math.sqrt(G) * yc**1.5
    return {
        "discharge": q,
        "critical_depth": yc,
        "cd": cd,
        "sensitivity": 1.5,
        "head": head,
    }


def sluice_gate(
    y1: float, opening: float, cc: float = 0.61, rho: float = 1000.0
) -> Dict[str, float]:
    """Free discharge under a vertical sluice gate, per unit width.

    The vena contracta downstream sits at y2 = Cc a. Energy between the
    upstream pool and the contracted jet (both parallel flow, so hydrostatic,
    and the reach is short enough to lose little) gives

        q = y1 y2 sqrt(2 g / (y1 + y2)),

    and momentum on the same control volume then gives the force on the gate,
    which is markedly **less** than the hydrostatic thrust the same pool would
    put on a solid wall, because the flow carries momentum away downstream.
    """
    y2 = cc * opening
    if y2 >= y1:
        raise ValueError("the contracted depth must be below the upstream depth")
    q = y1 * y2 * math.sqrt(2.0 * G / (y1 + y2))
    u1, u2 = q / y1, q / y2
    hydrostatic = 0.5 * rho * G * y1**2
    gate_force = 0.5 * rho * G * (y1**2 - y2**2) - rho * q * (u2 - u1)
    return {
        "y2": y2,
        "unit_discharge": q,
        "u1": u1,
        "u2": u2,
        "froude_1": u1 / math.sqrt(G * y1),
        "froude_2": u2 / math.sqrt(G * y2),
        "gate_force_per_width": gate_force,
        "hydrostatic_force_per_width": hydrostatic,
        "force_ratio": gate_force / hydrostatic,
        "contraction_coefficient": cc,
    }


# --------------------------------------------------------------------------
# 6. Variable-mass control volumes: rockets
# --------------------------------------------------------------------------
def rocket_thrust(
    mass_flow: float,
    exhaust_velocity: float,
    exit_pressure: float = 0.0,
    ambient_pressure: float = 0.0,
    exit_area: float = 0.0,
) -> Dict[str, float]:
    """Thrust of a rocket nozzle: F = mdot ve + (pe - pa) Ae.

    The pressure term is not an afterthought: it is the part of the control
    surface integral that fails to cancel against the atmosphere, and it is why
    an engine optimised for sea level is under-expanded in vacuum. The
    *effective* exhaust velocity c = F/mdot lumps both terms together, and it
    is c -- not ve -- that belongs in the rocket equation.
    """
    momentum_thrust = mass_flow * exhaust_velocity
    pressure_thrust = (exit_pressure - ambient_pressure) * exit_area
    thrust = momentum_thrust + pressure_thrust
    c = thrust / mass_flow if mass_flow > 0 else 0.0
    return {
        "thrust": thrust,
        "momentum_thrust": momentum_thrust,
        "pressure_thrust": pressure_thrust,
        "effective_exhaust_velocity": c,
        "specific_impulse": c / G0,
    }


def tsiolkovsky(
    effective_exhaust_velocity: float,
    initial_mass: float,
    final_mass: float,
    burn_time: float = 0.0,
    gravity: float = G0,
    drag_loss: float = 0.0,
) -> Dict[str, float]:
    """Ideal delta-v, and what a vertical climb gives back to gravity.

    dv_ideal = c ln(m0/mf) is the integral of -(c/m) dm with no external force.
    A vertical launch subtracts g t_b (the gravity loss) and whatever drag loss
    the caller supplies, which is why a slowly burning first stage wastes
    delta-v even with a perfect engine.
    """
    ratio = initial_mass / final_mass
    ideal = effective_exhaust_velocity * math.log(ratio)
    gravity_loss = gravity * burn_time
    return {
        "mass_ratio": ratio,
        "propellant_fraction": 1.0 - 1.0 / ratio,
        "delta_v_ideal": ideal,
        "gravity_loss": gravity_loss,
        "drag_loss": drag_loss,
        "delta_v_net": ideal - gravity_loss - drag_loss,
    }


def rocket_mass_ratio_for(delta_v: float, effective_exhaust_velocity: float) -> float:
    """Inverse rocket equation: m0/mf = exp(dv/c).

    Exponential, which is the whole tyranny of it: every extra unit of delta-v
    costs a *multiplicative* amount of propellant.
    """
    return math.exp(delta_v / effective_exhaust_velocity)


# --------------------------------------------------------------------------
# 7. Actuator disc: propellers, rotors and the Betz limit
# --------------------------------------------------------------------------
def actuator_disk(
    rho: float, area: float, free_stream: float, induction: float
) -> Dict[str, float]:
    """Froude momentum theory for a disc that removes axial momentum.

    With induction factor a, the disc sees U(1-a) and the far wake U(1-2a) --
    the classic result that *half* of the total slowdown has already happened
    at the disc itself. Then

        T = 2 rho A U^2 a (1-a),   P = T U (1-a) = 2 rho A U^3 a (1-a)^2,

    so Cp = 4a(1-a)^2 peaks at a = 1/3 with Cp = 16/27: the Betz limit. It is a
    momentum-and-energy result for an ideal unshrouded turbine in an unbounded,
    steady incompressible stream, with no wake swirl or external losses and
    power normalized by the disc area. Ducts and confinement are different models.
    At a = 0.5 the algebraic endpoint has Cp = 0.5 and zero wake speed; finite
    mass flow would require infinite wake area. It is a singular limiting value,
    not a realizable finite wake. High-induction real wakes require corrections.
    """
    a = float(induction)
    u_disk = free_stream * (1.0 - a)
    u_wake = free_stream * (1.0 - 2.0 * a)
    thrust = 2.0 * rho * area * free_stream**2 * a * (1.0 - a)
    power = thrust * u_disk
    available = 0.5 * rho * area * free_stream**3
    return {
        "u_disk": u_disk,
        "u_wake": u_wake,
        "thrust": thrust,
        "power": power,
        "power_coefficient": power / available if available > 0 else 0.0,
        "thrust_coefficient": (
            thrust / (0.5 * rho * area * free_stream**2) if free_stream > 0 else 0.0
        ),
        "available_power": available,
        "betz_limit": 16.0 / 27.0,
        "betz_induction": 1.0 / 3.0,
    }
