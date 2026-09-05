"""Calorically perfect gas demonstrations; SI and absolute pressures."""
import math
from src.physics.pipe_network import positive


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
