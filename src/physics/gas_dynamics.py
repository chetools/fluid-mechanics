"""Calorically perfect gas demonstrations; SI and absolute pressures."""
import math
from src.physics.pipe_network import positive


# Shared by the calculator and the reproducible blocked-outlet worked example.
RELIEF_DEMO_DEFAULTS = dict(
    required_flow=5.0, p0=12e5, t0=333.15, back_pressure=1.013e5,
    gamma=1.4, gas_constant=287.05, discharge_coefficient=0.975,
)


def gas_properties(gamma, gas_constant):
    if not math.isfinite(gamma) or gamma <= 1:
        raise ValueError('gamma must exceed one.')
    positive(gas_constant, 'Gas constant')
    return gamma * gas_constant / (gamma - 1)


def nozzle(p0, t0, back_pressure, area, gamma=1.4, gas_constant=287.05):
    gas_properties(gamma, gas_constant)
    for name, value in [('p0', p0), ('T0', t0), ('back pressure', back_pressure), ('area', area)]:
        positive(value, name)
    critical = (2 / (gamma + 1)) ** (gamma / (gamma - 1))
    ratio = min(1., max(back_pressure / p0, critical))
    mach = math.sqrt(2 / (gamma - 1) * (ratio ** (-(gamma - 1) / gamma) - 1))
    temperature = t0 / (1 + (gamma - 1) * mach**2 / 2)
    pressure = p0 * ratio
    speed = mach * math.sqrt(gamma * gas_constant * temperature)
    return dict(mach=mach, temperature=temperature, pressure=pressure,
                mass_flow=pressure / (gas_constant * temperature) * speed * area,
                critical_ratio=critical, choked=back_pressure / p0 <= critical)


def normal_shock(mach, gamma=1.4):
    gas_properties(gamma, 287.05)
    if not math.isfinite(mach) or mach < 1:
        raise ValueError('Normal shock requires upstream Mach >= 1.')
    m2 = math.sqrt((1 + (gamma - 1) * mach**2 / 2) / (gamma * mach**2 - (gamma - 1) / 2))
    pr = 1 + 2 * gamma / (gamma + 1) * (mach**2 - 1)
    rr = (gamma + 1) * mach**2 / (2 + (gamma - 1) * mach**2)
    p0r = pr * ((1 + (gamma - 1) * m2**2 / 2) / (1 + (gamma - 1) * mach**2 / 2)) ** (gamma / (gamma - 1))
    return dict(mach2=m2, pressure_ratio=pr, density_ratio=rr, temperature_ratio=pr / rr, stagnation_pressure_ratio=p0r)


def gas_machine(t_in, pressure_ratio, efficiency, mode, gamma=1.4, gas_constant=287.05):
    cp = gas_properties(gamma, gas_constant)
    positive(t_in, 'Inlet temperature')
    positive(pressure_ratio, 'Pressure ratio')
    if not 0 < efficiency <= 1:
        raise ValueError('Efficiency must be in (0, 1].')
    if mode not in ('Compressor', 'Turbine') or pressure_ratio < 1:
        raise ValueError('Choose Compressor or Turbine and high/low pressure ratio >= 1.')
    ratio = pressure_ratio if mode == 'Compressor' else 1 / pressure_ratio
    ideal = t_in * ratio ** ((gamma - 1) / gamma)
    actual = t_in + (ideal - t_in) / efficiency if mode == 'Compressor' else t_in + efficiency * (ideal - t_in)
    return dict(ideal_temperature=ideal, outlet_temperature=actual, work_into_fluid=cp * (actual - t_in), cp=cp)


SCHILLER_NAUMANN_RE_MAX = 1000.0


def sphere_drag(reynolds, strict=True):
    """Schiller-Naumann sphere drag coefficient.

    Cd = 24/Re (1 + 0.15 Re^0.687), fitted for Re <= 1000.

    `strict=True` (the default, and what the tests pin) refuses to extrapolate.
    Pass `strict=False` to get the correlation's value anyway: a calculator that
    shows the number together with a warning teaches more than one that only
    raises, because the student can see *how far* the fit has drifted from the
    measured curve before the drag crisis.
    """
    positive(reynolds, 'Reynolds number')
    if reynolds > SCHILLER_NAUMANN_RE_MAX and strict:
        raise ValueError('Schiller–Naumann demonstration limited to Re <= 1000.')
    return 24 / reynolds * (1 + 0.15 * reynolds**0.687)


def critical_pressure_ratio(gamma=1.4):
    """p*/p0 at which a converging passage chokes: (2/(gamma+1))^(gamma/(gamma-1)).

    About 0.528 for a diatomic gas, so a vessel above roughly 1.9 times the
    downstream absolute pressure is already choked. Most relief scenarios start
    well above that, which is why choked flow is the normal case in relief
    sizing rather than a special one.
    """
    if not math.isfinite(gamma) or gamma <= 1:
        raise ValueError('gamma must exceed one.')
    return (2 / (gamma + 1)) ** (gamma / (gamma - 1))


def choked_mass_flux(p0, t0, gamma=1.4, gas_constant=287.05):
    """Mass flow per unit throat area when choked, kg/(s.m^2).

        G = p0 sqrt(gamma/(R T0)) (2/(gamma+1))^((gamma+1)/(2(gamma-1)))

    Note what is absent: the downstream pressure. Once choked, the throat has no
    way of learning what is downstream, because the information would have to
    travel upstream against a flow already moving at the speed of sound. The
    capacity of a relief device is therefore fixed by its upstream stagnation
    state and its throat area alone.

    Two design consequences follow directly from the formula:
    G scales with p0, so capacity rises as the vessel pressure rises; and G goes
    as 1/sqrt(T0), so a hot relief case passes *less* mass through the same hole.
    """
    positive(p0, 'Upstream stagnation pressure')
    positive(t0, 'Upstream stagnation temperature')
    gas_properties(gamma, gas_constant)
    return p0 * math.sqrt(gamma / (gas_constant * t0)) * (
        (2 / (gamma + 1)) ** ((gamma + 1) / (2 * (gamma - 1)))
    )


def relief_sizing(required_flow, p0, t0, back_pressure, gamma=1.4,
                  gas_constant=287.05, discharge_coefficient=0.975):
    """Throat area for a gas relief device, and whether it is choked.

    `discharge_coefficient` is the device's effective coefficient (API 520 K_d;
    about 0.975 for a nozzle-type safety relief valve, about 0.62 for a
    rupture disc treated as an orifice).

    Model limits, and they matter: single-phase, ideal, non-reacting gas with
    constant gamma; no inlet line pressure loss; no valve-lift dynamics. This
    does **not** cover flashing or two-phase relief, which needs the omega
    method or HEM and can require an order of magnitude more area. It also does
    not check the 3% inlet-loss rule or the built-up backpressure limits that
    decide whether a conventional spring valve will chatter.
    """
    positive(required_flow, 'Required relief rate')
    positive(back_pressure, 'Back pressure')
    positive(p0, 'Upstream stagnation pressure')
    if not math.isfinite(discharge_coefficient) or not 0 < discharge_coefficient <= 1:
        raise ValueError('Discharge coefficient must be finite and in (0, 1].')
    if back_pressure >= p0:
        raise ValueError('Back pressure must be below the upstream stagnation pressure.')
    critical = critical_pressure_ratio(gamma)
    flux = choked_mass_flux(p0, t0, gamma, gas_constant)
    ratio = back_pressure / p0
    choked = ratio <= critical

    if choked:
        effective_flux = flux
    else:
        # Subcritical: the throat now does feel the downstream pressure.
        mach = math.sqrt(2 / (gamma - 1) * (ratio ** (-(gamma - 1) / gamma) - 1))
        temperature = t0 / (1 + (gamma - 1) * mach ** 2 / 2)
        density = back_pressure / (gas_constant * temperature)
        effective_flux = density * mach * math.sqrt(gamma * gas_constant * temperature)

    area = required_flow / (discharge_coefficient * effective_flux)
    return {
        'required_flow': required_flow,
        'area': area,
        'diameter': math.sqrt(4 * area / math.pi),
        'mass_flux': effective_flux,
        'choked_mass_flux': flux,
        'choked': choked,
        'critical_ratio': critical,
        'back_pressure_ratio': ratio,
        'capacity_loss_vs_choked': 1 - effective_flux / flux,
        'discharge_coefficient': discharge_coefficient,
        'p0': p0, 't0': t0, 'back_pressure': back_pressure,
    }


def relief_capacity_curve(p0, t0, gamma=1.4, gas_constant=287.05, n_points=120):
    """Mass flux against back-pressure ratio: the plateau that defines choking.

    The flat left-hand portion is the entire point. Lowering the downstream
    pressure below the critical ratio buys no extra flow, so a relief device
    cannot be made to pass more by venting it somewhere lower.
    """
    critical = critical_pressure_ratio(gamma)
    flux = choked_mass_flux(p0, t0, gamma, gas_constant)
    ratios = [0.02 + (0.98 - 0.02) * index / (n_points - 1) for index in range(n_points)]
    fluxes = []
    for ratio in ratios:
        if ratio <= critical:
            fluxes.append(flux)
        else:
            mach = math.sqrt(2 / (gamma - 1) * (ratio ** (-(gamma - 1) / gamma) - 1))
            temperature = t0 / (1 + (gamma - 1) * mach ** 2 / 2)
            density = ratio * p0 / (gas_constant * temperature)
            fluxes.append(density * mach * math.sqrt(gamma * gas_constant * temperature))
    return {
        'ratio': ratios,
        'mass_flux': fluxes,
        'critical_ratio': critical,
        'choked_mass_flux': flux,
        'p0': p0,
        't0': t0,
    }
