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
