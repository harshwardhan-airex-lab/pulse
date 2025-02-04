import streamlit as st
import yaml
import subprocess
import os
import ast
import pandas as pd
import copy
import functools
import sys

# Import your custom styling from styles.py
from styles import apply_custom_styles

# Set Streamlit page config
st.set_page_config(
    page_title="Pulse Descriptor Word Simulator",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Add PDW simulator directory to Python path
sys.path.append('/mnt/d/zenoxml/pulse/src')
from pdw_simulator.visualization import create_pdw_visualizer


###############################################################################
# 1. SYSTEM CONFIG & PATHS
###############################################################################

def load_system_config():
    """
    Load system config from 'config/systemconfig.yaml'
    containing directories, file naming, etc.
    """
    sys_config_path = os.path.join('config', 'systemconfig.yaml')
    if not os.path.exists(sys_config_path):
        st.error(f"systemconfig.yaml not found at {sys_config_path}")
        return {}
    with open(sys_config_path, 'r') as f:
        return yaml.safe_load(f)

def get_temp_config_path(system_config):
    """
    Compute the path to 'tempconfig.yaml' based on systemconfig.
    """
    temp_dir = system_config.get('directories', {}).get('temp', './temp')
    os.makedirs(temp_dir, exist_ok=True)
    return os.path.join(temp_dir, 'tempconfig.yaml')

###############################################################################
# 2. BASE & TEMP CONFIG LOGIC
###############################################################################

def load_base_config():
    """
    Read 'config/tomlconfig.yaml' if it exists (read-only).
    Return {} if missing.
    """
    base_path = os.path.join('config', 'tomlconfig.yaml')
    if os.path.exists(base_path):
        with open(base_path, 'r') as f:
            return yaml.safe_load(f)
    return {}

def save_temp_config(config, temp_config_path):
    """
    Write config to 'tempconfig.yaml'
    """
    with open(temp_config_path, 'w') as file:
        yaml.dump(config, file)

def load_temp_config(temp_config_path):
    """
    Load config from 'tempconfig.yaml'. Return {} if not found or invalid.
    """
    if os.path.exists(temp_config_path):
        with open(temp_config_path, 'r') as f:
            data = yaml.safe_load(f)
            if data:
                return data
    return {}

###############################################################################
# 3. SIMULATION HELPER
###############################################################################

def find_latest_pdw_file(output_dir):
    """
    Find the newest PDW CSV file in output_dir
    """
    if not os.path.exists(output_dir):
        return None
    pdw_files = [
        f for f in os.listdir(output_dir)
        if f.startswith('pdw_') and f.endswith('.csv')
    ]
    if not pdw_files:
        return None
    return max(pdw_files, key=lambda x: os.path.getctime(os.path.join(output_dir, x)))

def run_simulation(system_config):
    """
    Execute 'main.py' → run the simulator → returns path to newest PDW CSV
    """
    pdw_data_dir = system_config['files']['pdw_data']['directory']
    if not os.path.exists(pdw_data_dir):
        os.makedirs(pdw_data_dir, exist_ok=True)

    main_path = os.path.join('src', 'pdw_simulator', 'main.py')
    if not os.path.exists(main_path):
        st.error(f"main.py not found at {main_path}")
        return None

    try:
        result = subprocess.run(['python', main_path],
                                capture_output=True, 
                                text=True)
        if result.returncode != 0:
            st.error(f"Simulation failed: {result.stderr}")
            return None
        
        latest_file = find_latest_pdw_file(pdw_data_dir)
        if latest_file:
            return os.path.join(pdw_data_dir, latest_file)
    except Exception as e:
        st.error(f"Error running simulation: {str(e)}")
        return None

    return None

def display_output(system_config):
    """
    Display the newest PDW CSV data in tabs (Visualizations & Raw Data).
    """
    st.subheader("PDW Data")
    pdw_data_dir = system_config['files']['pdw_data']['directory']
    if not os.path.exists(pdw_data_dir):
        os.makedirs(pdw_data_dir, exist_ok=True)
    
    latest_file = find_latest_pdw_file(pdw_data_dir)
    pdw_path = os.path.join(pdw_data_dir, latest_file) if latest_file else None
    
    if pdw_path and os.path.exists(pdw_path):
        try:
            pd.options.display.float_format = '{:.9e}'.format
            pdw_data = pd.read_csv(pdw_path)
            
            tab1, tab2 = st.tabs(["Visualizations", "Raw Data"])
            with tab1:
                viz_container = st.container()
                visualizer = create_pdw_visualizer(viz_container)
                visualizer.update_data(pdw_data)
                visualizer.display(viz_container)
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.button("Refresh Visualization", key="refresh_vis_btn",
                              on_click=lambda: visualizer.update_data(pdw_data))
                with col2:
                    csv_data = pdw_data.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download PDW Data",
                        data=csv_data,
                        file_name=os.path.basename(pdw_path),
                        mime='text/csv',
                        key="download_pdw_btn"
                    )
            
            with tab2:
                st.dataframe(pdw_data)
                st.text(f"Current file: {os.path.basename(pdw_path)}")
                
            # Show metadata if present
            metadata_path = pdw_path.replace('.csv', '_metadata.csv')
            if os.path.exists(metadata_path):
                with st.expander("Show Metadata"):
                    metadata = pd.read_csv(metadata_path)
                    st.dataframe(metadata)
                    
        except Exception as e:
            st.error(f"Error reading PDW data: {str(e)}")
            if st.button("Run New Simulation", key="run_sim_after_error"):
                new_file = run_simulation(system_config)
                if new_file:
                    st.experimental_rerun()
    else:
        st.info("No PDW data found. Running new simulation...")
        new_file = run_simulation(system_config)
        if new_file:
            st.experimental_rerun()

###############################################################################
# 4. MAIN APP
###############################################################################

def main():
    apply_custom_styles()  # Apply your styles from styles.py

    st.title("Pulse Descriptor Word Simulator")

    # 1) Load system config
    system_config = load_system_config()
    temp_config_path = get_temp_config_path(system_config)

    # 2) Load base config from tomlconfig.yaml
    base_config = load_base_config()

    # 3) Initialize session
    if 'page' not in st.session_state:
        st.session_state.page = 0
        
        # Attempt to load existing tempconfig
        existing_temp = load_temp_config(temp_config_path)
        if existing_temp:
            st.session_state.config = existing_temp
        else:
            # If no temp config, use base config
            st.session_state.config = copy.deepcopy(base_config)
        
        st.session_state.num_radars = len(st.session_state.config.get('radars', []))

    # Guarantee exactly 1 sensor
    if 'sensors' not in st.session_state.config:
        st.session_state.config['sensors'] = []
    if len(st.session_state.config['sensors']) < 1:
        st.session_state.config['sensors'] = [{
            'name': 'Sensor1',
            'start_position': [0,0],
            'velocity': [0,0],
            'start_time': 0,
            'saturation_level': '-70 dB',
            'detection_probability': {
                'level': [-80, -85, -90, -95],
                'probability': [100, 85, 60, 30]
            },
            'amplitude_error': {
                'systematic': {'type': 'constant', 'error': '0 dB'},
                'arbitrary': {'type': 'gaussian', 'error': '0.5 dB'}
            },
            'toa_error': {
                'systematic': {'type': 'constant', 'error': '0 s'},
                'arbitrary': {'type': 'gaussian', 'error': '1e-9 s'}
            },
            'frequency_error': {
                'systematic': {'type': 'linear', 'error': '0 Hz', 'rate': '100 Hz/s'},
                'arbitrary': {'type': 'gaussian', 'error': '1e6 Hz'}
            },
            'pulse_width_error': {
                'systematic': {'type': 'constant', 'error': '0 s'},
                'arbitrary': {'type': 'uniform', 'error': '2%'}
            },
            'aoa_error': {
                'systematic': {'type': 'constant', 'error': '0 deg'},
                'arbitrary': {'type': 'gaussian', 'error': '1 deg'}
            },
            'freq_padding_factor': 4
        }]

    # NAV functions
    def next_page():
        st.session_state.page += 1
    def prev_page():
        st.session_state.page -= 1
    def reset_app():
        st.session_state.page = 0

    # -- PAGE 0: Scenario
    if st.session_state.page == 0:
        st.header("Scenario Parameters")

        scenario = st.session_state.config.get('scenario', {})
        start_time = st.number_input('Start Time (s)',
                                     value=float(scenario.get('start_time', 0.0)),
                                     format="%.2f",
                                     key="scenario_start_time")
        end_time = st.number_input('End Time (s)',
                                   value=float(scenario.get('end_time', 10.0)),
                                   format="%.2f",
                                   key="scenario_end_time")
        time_step = st.number_input('Time Step (s)',
                                    value=float(scenario.get('time_step', 0.1)),
                                    format="%.4f",
                                    key="scenario_time_step")
        
        def save_scenario_params():
            st.session_state.config['scenario'] = {
                'start_time': start_time,
                'end_time': end_time,
                'time_step': time_step
            }
            # Write to temp
            save_temp_config(st.session_state.config, temp_config_path)
            next_page()

        col1, col2, col3 = st.columns([1,6,1])
        with col3:
            st.button("Next", on_click=save_scenario_params, key="scenario_next_btn")

    # -- PAGE 1: Number of Radars
    elif st.session_state.page == 1:
        st.header("Select Number of Radars")

        current_num = len(st.session_state.config.get('radars', []))
        num_radars = st.number_input(
            'Number of Radars',
            min_value=1,
            max_value=20,
            value=current_num,
            step=1,
            key="radar_count"
        )

        def set_num_radars():
            """
            1) Load fresh from base_config
            2) Slice to user-specified number
            3) Overwrite st.session_state.config
            4) Save to temp config
            """
            base_conf = load_base_config()
            base_scenario = base_conf.get('scenario', {})
            base_radars = base_conf.get('radars', [])
            base_sensors = base_conf.get('sensors', [])

            slice_count = min(num_radars, len(base_radars))

            new_conf = {}
            new_conf['scenario'] = copy.deepcopy(base_scenario)
            new_conf['radars'] = copy.deepcopy(base_radars[:slice_count])
            if base_sensors:
                new_conf['sensors'] = [base_sensors[0]]
            else:
                new_conf['sensors'] = copy.deepcopy(st.session_state.config['sensors'])

            st.session_state.config = new_conf
            st.session_state.num_radars = num_radars
            save_temp_config(st.session_state.config, temp_config_path)
            next_page()

        col1, col2, col3 = st.columns([1,6,1])
        with col1:
            st.button("Back", on_click=prev_page, key="radar_count_back_btn")
        with col3:
            st.button("Next", on_click=set_num_radars, key="radar_count_next_btn")

    # -- Radar config pages (2..(num_radars+1))
    elif 2 <= st.session_state.page < st.session_state.num_radars + 2:
        radar_index = st.session_state.page - 2
        radars = st.session_state.config.get('radars', [])

        if radar_index >= len(radars):
            st.error("Radar index out of range—please go back.")
        else:
            radar = radars[radar_index]
            st.header(f"Configure {radar.get('name', f'Radar{radar_index + 1}')}")

            # -------------------------------
            # Basic Info
            # -------------------------------
            with st.expander("Basic Information", expanded=True):
                rname = st.text_input(
                    'Radar Name',
                    value=radar.get('name', f'Radar{radar_index+1}'),
                    key=f"radar_name_{radar_index}"
                )
                radar['name'] = rname

                rpower = st.number_input(
                    "Power (W)",
                    value=float(radar.get('power', 1000.0)),
                    format="%.2f",
                    key=f"radar_power_{radar_index}"
                )
                radar['power'] = rpower

            # -------------------------------
            # Movement
            # -------------------------------
            with st.expander("Movement Parameters", expanded=False):
                start_pos_str = st.text_input(
                    "Start Position (x, y in meters)",
                    value=str(radar.get('start_position', [0, 0])),
                    key=f"radar_startpos_str_{radar_index}"
                )
                try:
                    radar['start_position'] = ast.literal_eval(start_pos_str)
                except:
                    st.error("Invalid format for Start Position. e.g. [0, 0]")

                vel_str = st.text_input(
                    "Velocity (vx, vy in m/s)",
                    value=str(radar.get('velocity', [0, 0])),
                    key=f"radar_velocity_str_{radar_index}"
                )
                try:
                    radar['velocity'] = ast.literal_eval(vel_str)
                except:
                    st.error("Invalid format for Velocity. e.g. [0, 0]")

                rstart_time = st.number_input(
                    "Start Time (s)",
                    value=float(radar.get('start_time', 0.0)),
                    format="%.2f",
                    key=f"radar_starttime_{radar_index}"
                )
                radar['start_time'] = rstart_time

            # -------------------------------
            # Rotation
            # -------------------------------
            with st.expander("Rotation Parameters", expanded=False):
                rotation_types = ['constant', 'varying']
                default_rot_type = radar.get('rotation_type', 'constant')
                if default_rot_type not in rotation_types:
                    default_rot_type = 'constant'
                radar['rotation_type'] = st.selectbox(
                    "Rotation Type",
                    rotation_types,
                    index=rotation_types.index(default_rot_type),
                    key=f"radar_rotation_type_{radar_index}"
                )

                rot_params = radar.get('rotation_params', {})
                # Make sure the dict exists
                if not rot_params:
                    rot_params = {}

                rot_params['t0'] = st.number_input(
                    "Rotation t0 (s)",
                    value=float(rot_params.get('t0', 0.0)),
                    format="%.2f",
                    key=f"rot_t0_{radar_index}"
                )
                rot_params['alpha0'] = st.number_input(
                    "Initial Angle alpha0 (deg/rad)",
                    value=float(rot_params.get('alpha0', 0.0)),
                    format="%.2f",
                    key=f"rot_alpha0_{radar_index}"
                )
                rot_params['T_rot'] = st.number_input(
                    "Rotation Period T_rot (s)",
                    value=float(rot_params.get('T_rot', 2.5)),
                    format="%.2f",
                    key=f"rot_T_{radar_index}"
                )

                if radar['rotation_type'] == 'varying':
                    rot_params['A'] = st.number_input(
                        "Amplitude A",
                        value=float(rot_params.get('A', 0.1)),
                        format="%.2f",
                        key=f"rotA_{radar_index}"
                    )
                    rot_params['s'] = st.number_input(
                        "Angular Frequency s (rad/s)",
                        value=float(rot_params.get('s', 1.0)),
                        format="%.2f",
                        key=f"rot_s_{radar_index}"
                    )
                    rot_params['phi0'] = st.number_input(
                        "Start Phase phi0 (deg/rad)",
                        value=float(rot_params.get('phi0', 0.0)),
                        format="%.2f",
                        key=f"rot_phi0_{radar_index}"
                    )

                radar['rotation_params'] = rot_params

            # -------------------------------
            # PRI
            # -------------------------------
            with st.expander("PRI Parameters", expanded=False):
                pri_types = ['fixed', 'stagger', 'switched', 'jitter']
                default_pri_type = radar.get('pri_type', 'fixed')
                if default_pri_type not in pri_types:
                    default_pri_type = 'fixed'
                radar['pri_type'] = st.selectbox(
                    "PRI Type",
                    pri_types,
                    index=pri_types.index(default_pri_type),
                    key=f"radar_pri_type_{radar_index}"
                )

                pri_params = radar.get('pri_params', {})
                if radar['pri_type'] == 'fixed':
                    pri_params['pri'] = st.number_input(
                        "PRI (s)",
                        value=float(pri_params.get('pri', 0.001)),
                        format="%.6f",
                        key=f"radar_pri_fixed_{radar_index}"
                    )
                elif radar['pri_type'] == 'stagger':
                    pri_str = st.text_input(
                        "PRI Pattern (list in s)",
                        value=str(pri_params.get('pri_pattern', [0.001])),
                        key=f"radar_pri_stagger_str_{radar_index}"
                    )
                    try:
                        pri_params['pri_pattern'] = ast.literal_eval(pri_str)
                    except:
                        st.error("Invalid format for PRI Pattern, e.g. [0.001, 0.0012]")
                elif radar['pri_type'] == 'switched':
                    pri_str = st.text_input(
                        "PRI Pattern (list in s)",
                        value=str(pri_params.get('pri_pattern', [0.001])),
                        key=f"radar_pri_switched_str_{radar_index}"
                    )
                    try:
                        pri_params['pri_pattern'] = ast.literal_eval(pri_str)
                    except:
                        st.error("Invalid format for PRI Pattern.")
                    rep_str = st.text_input(
                        "Repetitions (list)",
                        value=str(pri_params.get('repetitions', [1])),
                        key=f"radar_pri_switched_reps_{radar_index}"
                    )
                    try:
                        pri_params['repetitions'] = ast.literal_eval(rep_str)
                    except:
                        st.error("Invalid format for repetitions, e.g. [2,3]")
                elif radar['pri_type'] == 'jitter':
                    pri_params['mean_pri'] = st.number_input(
                        "Mean PRI (s)",
                        value=float(pri_params.get('mean_pri', 0.001)),
                        format="%.6f",
                        key=f"radar_pri_jitter_mean_{radar_index}"
                    )
                    pri_params['jitter_percentage'] = st.number_input(
                        "Jitter Percentage (%)",
                        value=float(pri_params.get('jitter_percentage', 5.0)),
                        format="%.2f",
                        key=f"radar_pri_jitter_perc_{radar_index}"
                    )

                radar['pri_params'] = pri_params

            # -------------------------------
            # Frequency
            # -------------------------------
            with st.expander("Frequency Parameters", expanded=False):
                freq_types = ['fixed', 'stagger', 'switched', 'jitter']
                default_freq_type = radar.get('frequency_type', 'fixed')
                if default_freq_type not in freq_types:
                    default_freq_type = 'fixed'
                radar['frequency_type'] = st.selectbox(
                    "Frequency Type",
                    freq_types,
                    index=freq_types.index(default_freq_type),
                    key=f"radar_freq_type_{radar_index}"
                )

                freq_params = radar.get('frequency_params', {})
                if radar['frequency_type'] == 'fixed':
                    freq_val = freq_params.get('frequency', 9.4e9)
                    freq_params['frequency'] = st.number_input(
                        "Frequency (Hz)",
                        value=float(freq_val),
                        format="%.2f",
                        key=f"radar_freq_fixed_{radar_index}"
                    )
                elif radar['frequency_type'] == 'stagger':
                    freq_str = st.text_input(
                        "Frequency Pattern (Hz)",
                        value=str(freq_params.get('frequency_pattern', [9.4e9])),
                        key=f"radar_freq_stagger_str_{radar_index}"
                    )
                    try:
                        freq_params['frequency_pattern'] = ast.literal_eval(freq_str)
                    except:
                        st.error("Invalid freq pattern, e.g. [9.4e9, 9.5e9]")
                elif radar['frequency_type'] == 'switched':
                    freq_str = st.text_input(
                        "Frequency Pattern (Hz)",
                        value=str(freq_params.get('frequency_pattern', [9.4e9])),
                        key=f"radar_freq_switched_str_{radar_index}"
                    )
                    try:
                        freq_params['frequency_pattern'] = ast.literal_eval(freq_str)
                    except:
                        st.error("Invalid freq pattern.")
                    rep_str = st.text_input(
                        "Repetitions (list)",
                        value=str(freq_params.get('repetitions', [1])),
                        key=f"radar_freq_switched_reps_{radar_index}"
                    )
                    try:
                        freq_params['repetitions'] = ast.literal_eval(rep_str)
                    except:
                        st.error("Invalid freq repetitions, e.g. [2,3]")
                elif radar['frequency_type'] == 'jitter':
                    mean_f = freq_params.get('mean_frequency', 9.4e9)
                    freq_params['mean_frequency'] = st.number_input(
                        "Mean Frequency (Hz)",
                        value=float(mean_f),
                        format="%.2f",
                        key=f"radar_freq_jitter_mean_{radar_index}"
                    )
                    freq_params['jitter_percentage'] = st.number_input(
                        "Jitter Percentage (%)",
                        value=float(freq_params.get('jitter_percentage', 5.0)),
                        format="%.2f",
                        key=f"radar_freq_jitter_perc_{radar_index}"
                    )

                radar['frequency_params'] = freq_params

            # -------------------------------
            # Pulse Width
            # -------------------------------
            with st.expander("Pulse Width Parameters", expanded=False):
                pw_types = ['fixed', 'stagger', 'switched', 'jitter']
                default_pw_type = radar.get('pulse_width_type', 'fixed')
                if default_pw_type not in pw_types:
                    default_pw_type = 'fixed'
                radar['pulse_width_type'] = st.selectbox(
                    "Pulse Width Type",
                    pw_types,
                    index=pw_types.index(default_pw_type),
                    key=f"radar_pw_type_{radar_index}"
                )

                pw_params = radar.get('pulse_width_params', {})
                if radar['pulse_width_type'] == 'fixed':
                    pw_params['pulse_width'] = st.number_input(
                        "Pulse Width (s)",
                        value=float(pw_params.get('pulse_width', 1.2e-6)),
                        format="%.8f",
                        key=f"radar_pw_fixed_{radar_index}"
                    )
                elif radar['pulse_width_type'] == 'stagger':
                    pw_str = st.text_input(
                        "Pulse Width Pattern (s)",
                        value=str(pw_params.get('pulse_width_pattern', [1.2e-6])),
                        key=f"radar_pw_stagger_str_{radar_index}"
                    )
                    try:
                        pw_params['pulse_width_pattern'] = ast.literal_eval(pw_str)
                    except:
                        st.error("Invalid PW pattern.")
                elif radar['pulse_width_type'] == 'switched':
                    pw_str = st.text_input(
                        "Pulse Width Pattern (s)",
                        value=str(pw_params.get('pulse_width_pattern', [1.2e-6])),
                        key=f"radar_pw_switched_str_{radar_index}"
                    )
                    try:
                        pw_params['pulse_width_pattern'] = ast.literal_eval(pw_str)
                    except:
                        st.error("Invalid PW pattern.")
                    rep_str = st.text_input(
                        "Repetitions (list)",
                        value=str(pw_params.get('repetitions', [1])),
                        key=f"radar_pw_switched_reps_{radar_index}"
                    )
                    try:
                        pw_params['repetitions'] = ast.literal_eval(rep_str)
                    except:
                        st.error("Invalid PW repetitions.")
                elif radar['pulse_width_type'] == 'jitter':
                    mean_pw = pw_params.get('mean_pulse_width', 1.2e-6)
                    pw_params['mean_pulse_width'] = st.number_input(
                        "Mean Pulse Width (s)",
                        value=float(mean_pw),
                        format="%.8f",
                        key=f"radar_pw_jitter_mean_{radar_index}"
                    )
                    pw_params['jitter_percentage'] = st.number_input(
                        "Jitter Percentage (%)",
                        value=float(pw_params.get('jitter_percentage', 5.0)),
                        format="%.2f",
                        key=f"radar_pw_jitter_perc_{radar_index}"
                    )

                radar['pulse_width_params'] = pw_params

            # -------------------------------
            # Lobe Pattern
            # -------------------------------
            with st.expander("Lobe Pattern Parameters", expanded=False):
                lobe = radar.get('lobe_pattern', {})
                lobe['type'] = st.selectbox(
                    "Lobe Pattern Type",
                    ['Sinc'],
                    index=0,
                    key=f"lobe_pattern_type_{radar_index}"
                )
                lobe['main_lobe_opening_angle'] = st.number_input(
                    "Main Lobe Opening Angle (deg)",
                    value=float(lobe.get('main_lobe_opening_angle', 5.0)),
                    format="%.2f",
                    key=f"lobe_main_angle_{radar_index}"
                )
                lobe['radar_power_at_main_lobe'] = st.number_input(
                    "Radar Power at Main Lobe (dB)",
                    value=float(lobe.get('radar_power_at_main_lobe', 0.0)),
                    format="%.2f",
                    key=f"lobe_main_power_{radar_index}"
                )
                lobe['radar_power_at_back_lobe'] = st.number_input(
                    "Radar Power at Back Lobe (dB)",
                    value=float(lobe.get('radar_power_at_back_lobe', -20.0)),
                    format="%.2f",
                    key=f"lobe_back_power_{radar_index}"
                )
                radar['lobe_pattern'] = lobe

            # Save function
            def save_radar_config():
                st.session_state.config['radars'][radar_index] = radar
                save_temp_config(st.session_state.config, temp_config_path)
                next_page()

            col1, col2 = st.columns([1,1])
            col1.button("Next", on_click=save_radar_config, key=f"radar_{radar_index}_next_btn")
            col2.button("Back", on_click=prev_page, key=f"radar_{radar_index}_back_btn")

    # -- REVIEW PAGE
    elif st.session_state.page == st.session_state.num_radars + 2:
        st.header("Review Configuration")

        scenario_cfg = st.session_state.config.get('scenario', {})
        st.subheader("Scenario Configuration")
        st.json(scenario_cfg)

        st.subheader("Radar Configurations")
        for idx, radar in enumerate(st.session_state.config.get('radars', [])):
            st.write(f"### Radar {idx + 1}: {radar['name']}")
            st.json(radar)

        st.subheader("Sensor Configuration (Single Default Sensor Only)")
        st.json(st.session_state.config['sensors'][0])

        def run_sim_and_go():
            # Save final config
            save_temp_config(st.session_state.config, temp_config_path)
            # Run simulator
            run_simulation(system_config)
            next_page()

        col1, col2 = st.columns([1,1])
        col1.button("Run Simulation", on_click=run_sim_and_go, key="review_run_sim_btn")
        col2.button("Back", on_click=prev_page, key="review_back_btn")

    # -- OUTPUT PAGE
    elif st.session_state.page == st.session_state.num_radars + 3:
        st.header("Simulation Output")
        display_output(system_config)

        col1, col2 = st.columns([1,1])
        col1.button("Back", on_click=prev_page, key="output_back_btn")
        col2.button("Restart", on_click=lambda: [reset_app()], key="output_restart_btn")

    # Sidebar
    st.sidebar.button("Restart", on_click=lambda: reset_app(), key="sidebar_restart_btn")


if __name__ == "__main__":
    main()