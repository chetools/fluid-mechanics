import math
import pytest
from src.physics.pipe_network import example_network, solve_network, resolve_pipe, pipe_headloss, flow_from_head, schedule_dimensions
from src.physics.gas_dynamics import nozzle, normal_shock, gas_machine, sphere_drag


def test_manufacturer_bore_and_schedule_effect():
    p40=schedule_dimensions('2','40'); p80=schedule_dimensions('2','80')
    assert p40['diameter_m'] == pytest.approx(.0525018)
    assert p80['diameter_m'] == pytest.approx(.0492506)
    assert p40['od_m'] == p80['od_m']


def test_network_conserves_loop_energy_and_nodal_mass():
    nodes,pipes=example_network(); r=solve_network(nodes,pipes)
    assert r['mass_residual_m3s'] < 1e-9
    assert r['energy_residual_m'] < 1e-8
    assert sum(n['boundary_supply_m3h'] for n in r['nodes']) == pytest.approx(2.)
    p={e['pipe']:e for e in r['pipes']}
    assert p['P2']['headloss_m']+p['P4']['headloss_m'] == pytest.approx(p['P3']['headloss_m'])
    assert p['P1']['flow_m3h'] == pytest.approx(p['P2']['flow_m3h']+p['P3']['flow_m3h'])


def test_head_inversion_matches_hagen_poiseuille_and_reverse_flow():
    _,pipes=example_network(); pipe=resolve_pipe(pipes[0]); pipe['k_minor']=0
    q=1e-7; rho=1000.; mu=.1
    expected=128*mu*pipe['length_m']*q/(rho*9.81*math.pi*pipe['diameter_m']**4)
    assert pipe_headloss(q,pipe,rho,mu)==pytest.approx(expected)
    assert flow_from_head(-expected,pipe,rho,mu)==pytest.approx(-q)
    assert pipe_headloss(0,pipe,rho,mu)==0


def test_identical_parallel_pipes_split_equally_and_reverse():
    nodes,pipes=example_network(); nodes=[nodes[0],nodes[-1]]
    p=pipes[0]; p['to']='Outlet'
    r=solve_network(nodes,[p,dict(p,pipe='Parallel')])
    assert r['pipes'][0]['flow_m3h']==pytest.approx(r['pipes'][1]['flow_m3h'])
    nodes[0]['pressure_kpag']=-50
    r=solve_network(nodes,[p])
    assert r['pipes'][0]['flow_m3h']<0


def test_hydrostatic_elevation_balance_has_zero_flow():
    nodes,pipes=example_network(); nodes=[nodes[0],nodes[-1]]
    nodes[0]['pressure_kpag']=100.; nodes[1]['pressure_kpag']=100.-1000*9.81*8/1000
    pipes[0]['to']='Outlet'
    r=solve_network(nodes,[pipes[0]],rho=1000)
    assert abs(r['pipes'][0]['flow_m3h'])<1e-9


@pytest.mark.parametrize('kind',['unanchored','duplicate','missing_endpoint','negative_length','pressure_demand'])
def test_network_rejects_invalid_inputs(kind):
    n,p=example_network()
    if kind=='unanchored':
        for node in n: node['boundary']='Junction'
    elif kind=='duplicate': n[1]['node']=n[0]['node']
    elif kind=='missing_endpoint': p[0]['to']='Missing'
    elif kind=='negative_length': p[0]['length_m']=-1
    else: n[0]['demand_m3h']=1
    with pytest.raises(ValueError): solve_network(n,p)


def test_choked_nozzle_matches_analytic_mass_flux_and_area_scaling():
    p,t,a=500000.,300.,1e-4
    r=nozzle(p,t,100000,a)
    expected=a*p/math.sqrt(t)*math.sqrt(1.4/287.05)*(2/2.4)**3
    assert r['mass_flow']==pytest.approx(expected)
    assert r['mach']==pytest.approx(1.)
    assert r['temperature']==pytest.approx(250.)
    assert nozzle(p,t,10000,a)['mass_flow']==pytest.approx(expected)
    assert nozzle(p,t,10000,4*a)['mass_flow']==pytest.approx(4*expected)
    assert nozzle(p,t,p,a)['mass_flow']==0
    assert nozzle(p,t,2*p,a)['mass_flow']==0
    assert nozzle(p,t,.9*p,a)['mass_flow']<expected


def test_normal_shock_mach_two_conserves_mass_momentum_energy():
    r=normal_shock(2.)
    assert r['mach2']==pytest.approx(math.sqrt(1/3))
    assert r['pressure_ratio']==pytest.approx(4.5)
    assert r['density_ratio']==pytest.approx(8/3)
    u1=2*math.sqrt(1.4); u2=r['mach2']*math.sqrt(1.4*r['temperature_ratio'])
    assert u1==pytest.approx(r['density_ratio']*u2)
    assert 1+u1*u1==pytest.approx(r['pressure_ratio']+r['density_ratio']*u2*u2)
    assert 3.5+u1*u1/2==pytest.approx(3.5*r['temperature_ratio']+u2*u2/2)
    assert r['stagnation_pressure_ratio']==pytest.approx(.7208738615)
    assert normal_shock(1.)['stagnation_pressure_ratio']==pytest.approx(1.)


def test_machine_efficiency_changes_work_and_temperature_correctly():
    c=gas_machine(300,4,.8,'Compressor'); ci=gas_machine(300,4,1,'Compressor')
    t=gas_machine(300,4,.8,'Turbine'); ti=gas_machine(300,4,1,'Turbine')
    assert c['outlet_temperature']>ci['outlet_temperature']>300
    assert 300>t['outlet_temperature']>ti['outlet_temperature']
    assert ci['work_into_fluid']/c['work_into_fluid']==pytest.approx(.8)
    assert t['work_into_fluid']/ti['work_into_fluid']==pytest.approx(.8)
    assert gas_machine(300,1,.8,'Turbine')['work_into_fluid']==0


def test_sphere_drag_recovers_creeping_limit():
    assert sphere_drag(1e-8)*1e-8==pytest.approx(24,rel=1e-5)
    with pytest.raises(ValueError): sphere_drag(1e5)


# --- choked flow in pressure-relief sizing ---------------------------------

def test_critical_pressure_ratio_matches_the_textbook_value():
    from src.physics.gas_dynamics import critical_pressure_ratio
    assert critical_pressure_ratio(1.4) == pytest.approx(0.5283, abs=1e-4)
    # A vessel above about 1.9x the downstream absolute pressure is choked.
    assert 1 / critical_pressure_ratio(1.4) == pytest.approx(1.893, abs=1e-3)


def test_choked_flux_is_independent_of_back_pressure():
    """The defining property, and the one relief sizing depends on."""
    from src.physics.gas_dynamics import relief_sizing
    low = relief_sizing(5.0, p0=12e5, t0=333.15, back_pressure=1.0e5)
    lower = relief_sizing(5.0, p0=12e5, t0=333.15, back_pressure=0.2e5)
    assert low['choked'] and lower['choked']
    assert low['mass_flux'] == pytest.approx(lower['mass_flux'])
    assert low['area'] == pytest.approx(lower['area'])


def test_choked_flux_scales_with_pressure_and_inverse_root_temperature():
    from src.physics.gas_dynamics import choked_mass_flux
    base = choked_mass_flux(10e5, 300.0)
    assert choked_mass_flux(20e5, 300.0) == pytest.approx(2 * base)
    assert choked_mass_flux(10e5, 1200.0) == pytest.approx(base / 2)


def test_hot_relief_needs_more_area():
    """G ~ 1/sqrt(T0): the same hole passes less mass when the gas is hot."""
    from src.physics.gas_dynamics import relief_sizing
    cold = relief_sizing(5.0, p0=12e5, t0=300.0, back_pressure=1.0e5)
    hot = relief_sizing(5.0, p0=12e5, t0=900.0, back_pressure=1.0e5)
    assert hot['area'] > cold['area']
    assert hot['area'] / cold['area'] == pytest.approx(math.sqrt(3.0), rel=1e-9)


def test_high_back_pressure_unchokes_and_costs_capacity():
    from src.physics.gas_dynamics import relief_sizing
    result = relief_sizing(5.0, p0=12e5, t0=333.15, back_pressure=9.0e5)
    assert not result['choked']
    assert result['back_pressure_ratio'] > result['critical_ratio']
    assert 0 < result['capacity_loss_vs_choked'] < 1
    assert result['mass_flux'] < result['choked_mass_flux']


def test_capacity_curve_is_flat_below_the_critical_ratio():
    from src.physics.gas_dynamics import relief_capacity_curve
    curve = relief_capacity_curve(12e5, 333.15)
    choked = [f for r, f in zip(curve['ratio'], curve['mass_flux'])
              if r <= curve['critical_ratio']]
    assert len(choked) > 10
    assert max(choked) == pytest.approx(min(choked))
    assert max(choked) == pytest.approx(curve['choked_mass_flux'])
    # And it falls away above the critical ratio.
    assert curve['mass_flux'][-1] < curve['choked_mass_flux']


def test_area_is_inversely_proportional_to_discharge_coefficient():
    from src.physics.gas_dynamics import relief_sizing
    valve = relief_sizing(5.0, p0=12e5, t0=333.15, back_pressure=1e5,
                          discharge_coefficient=0.975)
    disc = relief_sizing(5.0, p0=12e5, t0=333.15, back_pressure=1e5,
                         discharge_coefficient=0.62)
    assert disc['area'] / valve['area'] == pytest.approx(0.975 / 0.62)


@pytest.mark.parametrize("kwargs", [
    dict(required_flow=0.0, p0=12e5, t0=300.0, back_pressure=1e5),
    dict(required_flow=5.0, p0=0.0, t0=300.0, back_pressure=1e5),
    dict(required_flow=5.0, p0=12e5, t0=-5.0, back_pressure=1e5),
])
def test_invalid_relief_inputs_rejected(kwargs):
    from src.physics.gas_dynamics import relief_sizing
    with pytest.raises(ValueError):
        relief_sizing(**kwargs)
