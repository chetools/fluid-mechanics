"""Editable schedule sizing and nodal hydraulic network laboratory."""
import math
import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from src.ui.state import persistent_editor, persistent_input
from src.units import get_fluid_state
from src.physics.pipe_network import SCHEDULES, PIPE_DATA_SOURCE, resolve_pipe, pipe_headloss, example_network, solve_network
from src.physics.pipe_flow import PIPE_ROUGHNESS, friction_factor_churchill
from src.ui.pedagogy import render_prose_and_latex as prose, render_plot
from src.theme import apply_plotly_theme


def render_network_lab():
    st.divider()
    st.markdown('### 2.5 Real pipe sizes · Churchill calculator')
    st.markdown('Nominal pipe size names the pipe; the **inside diameter** determines velocity. Choose a schedule or enter a measured bore. These SI calculators use the sidebar density and viscosity.')
    fluid = get_fluid_state()
    rho, mu = fluid['rho'], fluid['mu']
    c1, c2, c3 = st.columns(3)
    with c1:
        mode = persistent_input(st.selectbox, 'Size definition', ['Schedule', 'Inside diameter'], key='real_size')
        nps = persistent_input(st.selectbox, 'Nominal pipe size [in]', list(SCHEDULES), index=5, disabled=mode!='Schedule', key="pipe_network_lab_nominal_pipe_size_in")
        schedule = persistent_input(st.selectbox, 'Schedule', ['40', '80'], disabled=mode!='Schedule', key="pipe_network_lab_schedule")
        diameter = persistent_input(st.number_input, 'Measured inside diameter [mm]', min_value=1., value=50., disabled=mode!='Inside diameter', key="pipe_network_lab_measured_inside_diameter_mm")
    with c2:
        rough_mode = persistent_input(st.selectbox, 'Roughness definition', ['Material', 'Relative ε/D', 'Absolute ε (mm)'], key="pipe_network_lab_roughness_definition")
        material = persistent_input(st.selectbox, 'Pipe material', list(PIPE_ROUGHNESS), disabled=rough_mode!='Material', key="pipe_network_lab_pipe_material")
        relative = persistent_input(st.number_input, 'Relative roughness ε/D', min_value=0., max_value=.05, value=.001, format='%.5f', disabled=rough_mode!='Relative ε/D', key="pipe_network_lab_relative_roughness_d")
        rough_mm = persistent_input(st.number_input, 'Absolute roughness ε [mm]', min_value=0., value=.045, format='%.4f', disabled=rough_mode!='Absolute ε (mm)', key="pipe_network_lab_absolute_roughness_mm")
    with c3:
        q = persistent_input(st.number_input, 'Flow [m³/h]', min_value=0., value=10., key="pipe_network_lab_flow_m_h")
        length = persistent_input(st.number_input, 'Pipe length [m]', min_value=.01, value=100., key="pipe_network_lab_pipe_length_m")
        k = persistent_input(st.number_input, 'Total minor-loss coefficient K', min_value=0., value=1., key="pipe_network_lab_total_minor_loss_coefficient_k")
    row = dict(size_mode=mode, nps=nps, schedule=schedule, diameter_mm=diameter, roughness_mode=rough_mode, material=material, relative_roughness=relative, roughness_mm=rough_mm, length_m=length, k_minor=k)
    pipe = None
    try:
        pipe = resolve_pipe(row)
        d = pipe['diameter_m']; velocity = q / 3600 / (math.pi * d*d / 4)
        re = rho * velocity * d / mu
        f = friction_factor_churchill(re, pipe['roughness_m'] / d)
        head = pipe_headloss(q / 3600, pipe, rho, mu)
        a, b, c, e = st.columns(4)
        a.metric('Inside diameter', f'{d*1000:.3f} mm')
        b.metric('Reynolds number', f'{re:,.0f}')
        c.metric('Darcy friction factor', f'{f:.5f}' if q else 'Undefined at rest')
        e.metric('Frictional pressure drop', f'{rho*9.81*head/1000:.3f} kPa')
        st.caption(f'Velocity {velocity:.3f} m/s · loss {head:.3f} m · ε/D = {pipe["roughness_m"]/d:.6g}. Only the selected size and roughness definitions are used.')
        if mode == 'Schedule':
            st.caption(f'OD {pipe["od_m"]*1000:.3f} mm − 2 × wall {pipe["wall_m"]*1000:.3f} mm = ID {d*1000:.3f} mm.')
        if 2000 < re < 4000:
            st.warning('Transition is sensitive to inlet disturbances. A smooth correlation is not a guarantee of the actual flow regime.')
    except ValueError as error:
        st.error(str(error))
    with st.expander('Churchill: evaluate each term in order'):
        prose(r'''Start with the actual bore, then velocity and Reynolds number. Churchill returns the **Darcy** factor; the Fanning factor is one quarter of it.
$$u=4Q/(\pi D^2),\quad Re=\rho uD/\mu,\quad r=\varepsilon/D$$
$$A=\left[2.457\ln\left(\frac{1}{(7/Re)^{0.9}+0.27r}\right)\right]^{16},\qquad B=(37530/Re)^{16}$$
$$f_D=8\left[(8/Re)^{12}+(A+B)^{-3/2}\right]^{1/12},\quad f_F=f_D/4$$
$$h_L=(f_D L/D+K)u^2/(2g),\qquad \Delta p_f=\rho gh_L$$
At small Reynolds number this approaches 64/Re. At zero flow the pressure loss is zero although the friction factor is undefined. Elevation and endpoint velocity changes belong in the full energy balance; they are not frictional pressure loss.''')
        if pipe is not None and q and re >= 1:
            ach = (2.457*math.log(1/((7/re)**.9+.27*pipe['roughness_m']/d)))**16
            bch = (37530/re)**16
            st.write(f'Current substitution: A = {ach:.4e}; B = {bch:.4e}; fD = {f:.6f}; fF = {f/4:.6f}.')
    st.caption(f'[Nominal steel-pipe dimensions: Wheatland manufacturer table]({PIPE_DATA_SOURCE}). ID is calculated from nominal OD and wall, not a pressure rating. Corrosion, lining and tolerances change the bore; material roughness values are illustrative estimates.')

    st.markdown('### 2.6 Solve a piping network')
    prose(r'''**Read the example first.** Supply feeds junction A. Flow splits through B and directly to Outlet; B withdraws 2 m³/h. Pipe directions are bookkeeping: a negative result means reverse flow.

**1 · Define nodes.** A Pressure node fixes gauge pressure and elevation; the solver finds its supply or withdrawal. A Junction fixes elevation and external demand; the solver finds pressure. Positive demand is withdrawal, negative demand is injection. A junction without demand has zero net flow.
$$\sum Q_{\mathrm{out},i}-\sum Q_{\mathrm{in},i}+d_i=0$$
**2 · Define edges.** Use piezometric head at junctions. The edge model includes straight-pipe and entered minor losses; it treats each junction as a common hydraulic-head connection.
$$H_i=z_i+\frac{p_i}{\rho g},\quad H_i-H_j=\left(f_D\frac{L}{D}+K\right)\frac{Q_{ij}|Q_{ij}|}{2gA^2}$$
**3 · Iterate unknown heads.** Guess junction heads, invert each monotone pipe relation to obtain signed flows, calculate each junction imbalance, and adjust heads until those residuals vanish. Friction is recomputed at every flow. Summing head differences around a loop gives zero automatically.
**4 · Verify.** Inspect continuity residuals, edge energy residuals and pressure plausibility. Every connected component needs a prescribed-pressure node. This is a steady, single-phase incompressible model with no pump curves or automatic valve logic.''')
    nodes, pipes = example_network()
    st.caption('Edit cells or add/delete rows. Use exact node names in the pipe table. Pressure entries at Junction nodes are ignored; demands at Pressure nodes must be zero. All table units are SI as labeled.')
    node_table = persistent_editor(pd.DataFrame(nodes), key='network_nodes', num_rows='dynamic', hide_index=True, width='stretch', column_config={
        'boundary': st.column_config.SelectboxColumn('Boundary', options=['Pressure','Junction'], required=True),
        'elevation_m':'Elevation [m]', 'pressure_kpag':'Gauge pressure [kPa]', 'demand_m3h':'Demand [m³/h]'})
    pipe_table = persistent_editor(pd.DataFrame(pipes), key='network_pipes', num_rows='dynamic', hide_index=True, width='stretch', column_config={
        'size_mode': st.column_config.SelectboxColumn('Size definition', options=['Schedule','Inside diameter'], required=True),
        'nps': st.column_config.SelectboxColumn('NPS [in]', options=list(SCHEDULES)),
        'schedule': st.column_config.SelectboxColumn('Schedule', options=['40','80']),
        'roughness_mode': st.column_config.SelectboxColumn('Roughness definition', options=['Material','Relative ε/D','Absolute ε (mm)']),
        'material': st.column_config.SelectboxColumn('Material', options=list(PIPE_ROUGHNESS)),
        'diameter_mm':'Inside diameter [mm]', 'length_m':'Length [m]', 'roughness_mm':'ε [mm]', 'relative_roughness':'ε/D', 'k_minor':'Minor K'})
    st.caption('Scroll the pipe table horizontally for size and roughness fields. For each row only the selected definitions are active. New rows need a pipe name, endpoints, positive length and the selected geometry/roughness fields; enter K = 0 if no fittings are modeled.')
    signature = json.dumps([node_table.to_dict('records'), pipe_table.to_dict('records'), rho, mu], sort_keys=True, default=str)
    pressed = st.button('Solve network', type='primary', key='solve_network_button')
    if pressed:
        try:
            result = solve_network(node_table.to_dict('records'), pipe_table.to_dict('records'), rho, mu)
        except (ValueError, KeyError, TypeError, RuntimeError) as error:
            st.session_state.pop('solved_network', None)
            st.error(f'Check network inputs: {error}')
            return
        st.session_state['solved_network'] = (signature, result)
    saved = st.session_state.get('solved_network')
    if saved and saved[0] == signature:
        result = saved[1]
        st.success(f'Solved in {result["iterations"]} iterations. Maximum junction imbalance: {result["mass_residual_m3s"]:.2e} m³/s; maximum pipe head residual: {result["energy_residual_m"]:.2e} m.')
        ns, ps = result['nodes'], result['pipes']
        coords = {n['node']:(i, n['elevation_m']) for i,n in enumerate(ns)}
        fig = go.Figure()
        for i,p in enumerate(ps):
            x0,y0 = coords[p['from']]; x1,y1 = coords[p['to']]
            # Separate parallel edges with a schematic bend.
            xm, ym = (x0+x1)/2, (y0+y1)/2 + (i%3-1)*1.5
            fig.add_trace(go.Scatter(x=[x0,xm,x1], y=[y0,ym,y1], mode='lines+text', text=['',f'{p["pipe"]}: {p["flow_m3h"]:.2f} m³/h<br>ID {p["diameter_mm"]:.1f} mm',''], textposition='top center', line=dict(width=3), name=p['pipe'], hovertemplate=f'{p["from"]} → {p["to"]}<br>Signed flow {p["flow_m3h"]:.3f} m³/h<extra></extra>'))
            if abs(p['flow_m3h']) > 1e-9:
                dx, dy = (x1-xm)*.22, (y1-ym)*.22
                direction = 1 if p['flow_m3h'] > 0 else -1
                fig.add_annotation(x=xm+(x1-xm)*.55+direction*dx/2, y=ym+(y1-ym)*.55+direction*dy/2,
                                   ax=xm+(x1-xm)*.55-direction*dx/2, ay=ym+(y1-ym)*.55-direction*dy/2,
                                   xref='x',yref='y',axref='x',ayref='y',text='',showarrow=True,arrowhead=3,arrowcolor='#e2e8f0')
        fig.add_trace(go.Scatter(x=[coords[n['node']][0] for n in ns], y=[n['elevation_m'] for n in ns], mode='markers+text', text=[f'{n["node"]}<br>{n["pressure_kpag"]:.1f} kPag' for n in ns], textposition='bottom center', marker=dict(size=18,color='#38bdf8'), name='Nodes'))
        fig.update_layout(title='Solved network · signed flows follow the table directions', xaxis_title='Node ordering (schematic, not distance)', yaxis_title='Node elevation [m]', height=480, showlegend=False)
        elevations = [n['elevation_m'] for n in ns]
        padding = max(3., (max(elevations)-min(elevations))*.25)
        fig.update_yaxes(range=[min(elevations)-padding,max(elevations)+padding])
        fig.update_xaxes(range=[-.35,len(ns)-.65])
        apply_plotly_theme(fig); render_plot(fig,'network')
        st.markdown('**Node balances** · positive boundary supply enters the network; negative supply leaves it.')
        st.dataframe(pd.DataFrame(ns), hide_index=True, width='stretch')
        st.markdown('**Pipe results** · signed velocity and head loss follow the from → to convention.')
        st.dataframe(pd.DataFrame(ps), hide_index=True, width='stretch')
        st.download_button('Download pipe results (CSV)', pd.DataFrame(ps).to_csv(index=False), 'network-pipes.csv', 'text/csv')
        st.caption('Results are cleared on input changes; press Solve network again to recompute.')
    st.caption('[Network conservation principles: EPA EPANET](https://www.epa.gov/water-research/epanet). This teaching solver implements its own nodal calculation; it does not run EPANET.')
