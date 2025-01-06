import streamlit as st
import yaml
import subprocess
import os
import ast
import pandas as pd
import copy
import base64
import functools  # For partial functions
from pdw_simulator.visualization import create_pdw_visualizer

# Function to add a background image from a local file
def add_bg_from_local(image_file):
    if not os.path.isfile(image_file):
        st.error(f"Background image file '{image_file}' not found. Please ensure it exists in the application directory.")
        return
    with open(image_file, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url(data:image/png;base64,{encoded_string});
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Function to inject custom CSS into the app
def inject_custom_css(css):
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# CSS styles for opaque expander sections
expander_css = '''
/* Opaque background for expander headers */
div[role="group"] > div:first-child {
    background-color: rgba(255, 255, 255, 1) !important;
    border: 1px solid #ccc !important;
    border-radius: 5px !important;
}

/* Opaque background for expander content */
div[role="group"] > div:nth-child(2) {
    background-color: rgba(255, 255, 255, 0.98) !important;
    padding: 10px !important;
}
'''

# CSS styles for navigation buttons with pastel colors
button_css = '''
.stButton > button {
    background-color: #b3cde0;
    color: #000;
    border-radius: 5px;
    padding: 10px 20px;
    font-size: 16px;
    font-weight: bold;
    margin: 5px;
}
.stButton > button:hover {
    background-color: #6497b1;
    color: #fff;
}
'''

# Function to load configuration from 'dataconfig.yaml'
def load_config():
    if os.path.exists('dataconfig.yaml'):
        with open('dataconfig.yaml', 'r') as file:
            config = yaml.safe_load(file)
    else:
        config = {}
    return config

# Function to save configuration to 'dataconfig.yaml'
def save_config(config):
    with open('dataconfig.yaml', 'w') as file:
        yaml.dump(config, file)

# Function to run the simulation by executing 'main.py'
# Function to run the simulation by executing 'main.py'
def run_simulation():
    main_path = os.path.join('src', 'pdw_simulator', 'main.py')
    if os.path.exists(main_path):
        subprocess.run(['python', main_path])
    else:
        st.error(f"main.py not found at {main_path}")

def display_output():
    #This output log file is not needed
    # st.subheader("Simulation Output Log")
    # if os.path.exists('output.txt'):
    #     with open('output.txt', 'r') as f:
    #         output = f.read()
    #     st.text_area("Output.txt", output, height=400)
    # else:
    #     st.error("output.txt not found.")

    st.subheader("PDW Data")
    if os.path.exists('pdw.csv'):
        pd.options.display.float_format = '{:.9e}'.format
        pdw_data = pd.read_csv('pdw.csv')
        
        # Create tabs for different views
        tab1, tab2 = st.tabs(["Visualizations", "Raw Data"])
        
        with tab1:
            # Initialize visualizer if not already created
            viz_container = st.container()
            visualizer = create_pdw_visualizer(viz_container)
            
            # Update and display visualization
            visualizer.update_data(pdw_data)
            visualizer.display(viz_container)
            
            # Add refresh button
            if st.button("Refresh Visualization"):
                visualizer.update_data(pdw_data)
        
        with tab2:
            st.dataframe(pdw_data)
    else:
        st.error("pdw.csv not found.")

# Main function to run the Streamlit app
def main():
    st.set_page_config(page_title="Radar Simulation", layout="wide")

    # Add background image
    add_bg_from_local('utils/background_image.jpg')

    # Inject custom CSS for expanders and buttons
    inject_custom_css(expander_css + button_css)

    st.title("Pulse Descriptor Word Simulator")

    # Initialize session state variables if not already set
    if 'page' not in st.session_state:
        st.session_state.page = 0
        st.session_state.config = load_config()
        st.session_state.num_radars = 0

    # Define navigation callback functions
    def next_page():
        st.session_state.page += 1

    def prev_page():
        st.session_state.page -= 1

    def reset_app():
        st.session_state.page = 0

    # Page 0: Scenario Parameters
    if st.session_state.page == 0:
        st.header("Scenario Parameters")
        # Retrieve existing values or set defaults
        scenario = st.session_state.config.get('scenario', {})
        start_time = st.number_input('Start Time (s)', value=float(scenario.get('start_time', 0.0)), format="%.2f")
        end_time = st.number_input('End Time (s)', value=float(scenario.get('end_time', 10.0)), format="%.2f")
        time_step = st.number_input('Time Step (s)', value=float(scenario.get('time_step', 0.1)), format="%.4f")

        col1, _ = st.columns([1,1])

        # Function to save scenario parameters and navigate to the next page
        def save_scenario_params():
            st.session_state.config['scenario'] = {
                'start_time': start_time,
                'end_time': end_time,
                'time_step': time_step
            }
            next_page()

        # Next button with single-click functionality
        col1.button("Next", on_click=save_scenario_params, key='scenario_next')

    # Page 1: Select Number of Radars
    elif st.session_state.page == 1:
        st.header("Select Number of Radars")
        num_radars = st.number_input('Number of Radars', min_value=1, max_value=10, value=int(st.session_state.num_radars) if st.session_state.num_radars else 2, step=1)

        col1, col2 = st.columns([1,1])

        # Function to save the number of radars and navigate to the next page
        def save_num_radars():
            st.session_state.num_radars = num_radars
            st.session_state.config['radars'] = st.session_state.config.get('radars', [])[:num_radars]
            next_page()

        # Next and Back buttons with single-click functionality
        col1.button("Next", on_click=save_num_radars, key='radar_count_next')
        col2.button("Back", on_click=prev_page, key='radar_count_back')

    # Pages 2 to N: Radar Configuration
    elif st.session_state.page >= 2 and st.session_state.page < st.session_state.num_radars + 2:
        radar_index = st.session_state.page - 2
        radars = st.session_state.config.get('radars', [])
        if len(radars) <= radar_index:
            if radar_index == 0:
                # Initialize the first radar with default values
                radars.append({'name': f'Radar{radar_index + 1}'})
            else:
                # Copy the properties from the first radar
                new_radar = copy.deepcopy(radars[0])
                new_radar['name'] = f'Radar{radar_index + 1}'
                radars.append(new_radar)
            st.session_state.config['radars'] = radars

        radar = radars[radar_index]
        st.header(f"Configure {radar.get('name', f'Radar{radar_index + 1}')}")

        # Basic Information
        with st.expander("Basic Information", expanded=True):
            radar['name'] = st.text_input('Radar Name', value=radar.get('name', f'Radar{radar_index + 1}'))
            radar['power'] = st.number_input("Power (W)", value=float(radar.get('power', 1000.0)), format="%.2f")

        # Movement Parameters
        with st.expander("Movement Parameters", expanded=False):
            start_position_str = st.text_input(
                "Start Position (x, y in meters)",
                value=str(radar.get('start_position', [0, 0]))
            )
            try:
                radar['start_position'] = ast.literal_eval(start_position_str)
            except:
                st.error("Invalid format for Start Position. Please enter a list like [x, y].")

            velocity_str = st.text_input(
                "Velocity (vx, vy in m/s)",
                value=str(radar.get('velocity', [0, 0]))
            )
            try:
                radar['velocity'] = ast.literal_eval(velocity_str)
            except:
                st.error("Invalid format for Velocity. Please enter a list like [vx, vy].")

            radar['start_time'] = st.number_input("Start Time (s)", value=float(radar.get('start_time', 0.0)), format="%.2f")

        # Rotation Parameters
        with st.expander("Rotation Parameters", expanded=False):
            rotation_types = ['constant', 'varying']
            rotation_type_default = radar.get('rotation_type', 'constant')
            if rotation_type_default not in rotation_types:
                rotation_type_default = 'constant'
            radar['rotation_type'] = st.selectbox("Rotation Type", rotation_types, index=rotation_types.index(rotation_type_default))
            radar['rotation_params'] = radar.get('rotation_params', {})
            radar['rotation_params']['t0'] = st.number_input("Rotation t0", value=float(radar['rotation_params'].get('t0', 0.0)), format="%.2f")
            radar['rotation_params']['alpha0'] = st.number_input("Initial Angle (rad)", value=float(radar['rotation_params'].get('alpha0', 0.0)), format="%.2f")
            radar['rotation_params']['T_rot'] = st.number_input("Rotation Period (s)", value=float(radar['rotation_params'].get('T_rot', 2.5)), format="%.2f")
            
            if radar['rotation_type'] == 'varying':
                radar['rotation_params']['A'] = st.number_input("Amplitude A", value=float(radar['rotation_params'].get('A', 0.1)), format="%.2f")
                radar['rotation_params']['s'] = st.number_input("Angular Frequency s", value=float(radar['rotation_params'].get('s', 1.0)), format="%.2f")
                radar['rotation_params']['phi0'] = st.number_input("Start Phase φ₀ (rad)", value=float(radar['rotation_params'].get('phi0', 0.0)), format="%.2f")

        # PRI Parameters
        with st.expander("PRI Parameters", expanded=False):
            pri_types = ['fixed', 'stagger', 'switched', 'jitter']
            pri_type_default = radar.get('pri_type', 'fixed')
            if pri_type_default not in pri_types:
                pri_type_default = 'fixed'
            radar['pri_type'] = st.selectbox("PRI Type", pri_types, index=pri_types.index(pri_type_default))
            radar['pri_params'] = radar.get('pri_params', {})
            if radar['pri_type'] == 'fixed':
                radar['pri_params']['pri'] = st.number_input("PRI (s)", value=float(radar['pri_params'].get('pri', 0.001)), format="%.6f")
            elif radar['pri_type'] == 'stagger':
                pri_pattern_str = st.text_input("PRI Pattern (s)", value=str(radar['pri_params'].get('pri_pattern', [0.001])))
                try:
                    radar['pri_params']['pri_pattern'] = ast.literal_eval(pri_pattern_str)
                except:
                    st.error("Invalid format for PRI Pattern. Please enter a list like [0.001, 0.0012, 0.0011].")
            elif radar['pri_type'] == 'switched':
                pri_pattern_str = st.text_input("PRI Pattern (s)", value=str(radar['pri_params'].get('pri_pattern', [0.001])))
                try:
                    radar['pri_params']['pri_pattern'] = ast.literal_eval(pri_pattern_str)
                except:
                    st.error("Invalid format for PRI Pattern.")
                repetitions_str = st.text_input("Repetitions", value=str(radar['pri_params'].get('repetitions', [1])))
                try:
                    radar['pri_params']['repetitions'] = ast.literal_eval(repetitions_str)
                except:
                    st.error("Invalid format for Repetitions.")
            elif radar['pri_type'] == 'jitter':
                radar['pri_params']['mean_pri'] = st.number_input("Mean PRI (s)", value=float(radar['pri_params'].get('mean_pri', 0.001)), format="%.6f")
                radar['pri_params']['jitter_percentage'] = st.number_input("Jitter Percentage (%)", value=float(radar['pri_params'].get('jitter_percentage', 5.0)), format="%.2f")

        # Frequency Parameters
        with st.expander("Frequency Parameters", expanded=False):
            frequency_types = ['fixed', 'stagger', 'switched', 'jitter']
            frequency_type_default = radar.get('frequency_type', 'fixed')
            if frequency_type_default not in frequency_types:
                frequency_type_default = 'fixed'
            radar['frequency_type'] = st.selectbox("Frequency Type", frequency_types, index=frequency_types.index(frequency_type_default))
            radar['frequency_params'] = radar.get('frequency_params', {})
            if radar['frequency_type'] == 'fixed':
                frequency_default = radar['frequency_params'].get('frequency', 15e9)
                radar['frequency_params']['frequency'] = st.number_input(
                    "Frequency (Hz)", 
                    value=float(frequency_default), format="%.2f"
                )
            elif radar['frequency_type'] == 'stagger':
                freq_pattern_str = st.text_input("Frequency Pattern (Hz)", value=str(radar['frequency_params'].get('frequency_pattern', [15e9])))
                try:
                    radar['frequency_params']['frequency_pattern'] = ast.literal_eval(freq_pattern_str)
                except:
                    st.error("Invalid format for Frequency Pattern. Please enter a list like [15e9, 16e9].")
            elif radar['frequency_type'] == 'switched':
                freq_pattern_str = st.text_input("Frequency Pattern (Hz)", value=str(radar['frequency_params'].get('frequency_pattern', [15e9])))
                try:
                    radar['frequency_params']['frequency_pattern'] = ast.literal_eval(freq_pattern_str)
                except:
                    st.error("Invalid format for Frequency Pattern.")
                repetitions_str = st.text_input("Repetitions", value=str(radar['frequency_params'].get('repetitions', [1])))
                try:
                    radar['frequency_params']['repetitions'] = ast.literal_eval(repetitions_str)
                except:
                    st.error("Invalid format for Repetitions.")
            elif radar['frequency_type'] == 'jitter':
                radar['frequency_params']['mean_frequency'] = st.number_input("Mean Frequency (Hz)", value=float(radar['frequency_params'].get('mean_frequency', 15e9)), format="%.2f")
                radar['frequency_params']['jitter_percentage'] = st.number_input("Jitter Percentage (%)", value=float(radar['frequency_params'].get('jitter_percentage', 5.0)), format="%.2f")

        # Pulse Width Parameters
        with st.expander("Pulse Width Parameters", expanded=False):
            pulse_width_types = ['fixed', 'stagger', 'switched', 'jitter']
            pulse_width_type_default = radar.get('pulse_width_type', 'fixed')
            if pulse_width_type_default not in pulse_width_types:
                pulse_width_type_default = 'fixed'
            radar['pulse_width_type'] = st.selectbox("Pulse Width Type", pulse_width_types, index=pulse_width_types.index(pulse_width_type_default))
            radar['pulse_width_params'] = radar.get('pulse_width_params', {})
            if radar['pulse_width_type'] == 'fixed':
                radar['pulse_width_params']['pulse_width'] = st.number_input("Pulse Width (s)", value=float(radar['pulse_width_params'].get('pulse_width', 1e-6)), format="%.8f")
            elif radar['pulse_width_type'] == 'stagger':
                pw_pattern_str = st.text_input("Pulse Width Pattern (s)", value=str(radar['pulse_width_params'].get('pulse_width_pattern', [1e-6])))
                try:
                    radar['pulse_width_params']['pulse_width_pattern'] = ast.literal_eval(pw_pattern_str)
                except:
                    st.error("Invalid format for Pulse Width Pattern.")
            elif radar['pulse_width_type'] == 'switched':
                pw_pattern_str = st.text_input("Pulse Width Pattern (s)", value=str(radar['pulse_width_params'].get('pulse_width_pattern', [1e-6])))
                try:
                    radar['pulse_width_params']['pulse_width_pattern'] = ast.literal_eval(pw_pattern_str)
                except:
                    st.error("Invalid format for Pulse Width Pattern.")
                repetitions_str = st.text_input("Repetitions", value=str(radar['pulse_width_params'].get('repetitions', [1])))
                try:
                    radar['pulse_width_params']['repetitions'] = ast.literal_eval(repetitions_str)
                except:
                    st.error("Invalid format for Repetitions.")
            elif radar['pulse_width_type'] == 'jitter':
                radar['pulse_width_params']['mean_pulse_width'] = st.number_input("Mean Pulse Width (s)", value=float(radar['pulse_width_params'].get('mean_pulse_width', 1e-6)), format="%.8f")
                radar['pulse_width_params']['jitter_percentage'] = st.number_input("Jitter Percentage (%)", value=float(radar['pulse_width_params'].get('jitter_percentage', 5.0)), format="%.2f")

        # Lobe Pattern Parameters
        with st.expander("Lobe Pattern Parameters", expanded=False):
            radar['lobe_pattern'] = radar.get('lobe_pattern', {})
            radar['lobe_pattern']['type'] = st.selectbox("Lobe Pattern Type", ['Sinc'], index=0)
            radar['lobe_pattern']['main_lobe_opening_angle'] = st.number_input("Main Lobe Opening Angle (deg)", value=float(radar['lobe_pattern'].get('main_lobe_opening_angle', 5.0)), format="%.2f")
            radar['lobe_pattern']['radar_power_at_main_lobe'] = st.number_input("Radar Power at Main Lobe (dB)", value=float(radar['lobe_pattern'].get('radar_power_at_main_lobe', 0.0)), format="%.2f")
            radar['lobe_pattern']['radar_power_at_back_lobe'] = st.number_input("Radar Power at Back Lobe (dB)", value=float(radar['lobe_pattern'].get('radar_power_at_back_lobe', -20.0)), format="%.2f")

        col1, col2 = st.columns([1,1])

        # Function to save radar configuration and navigate to the next page
        def save_radar_config():
            st.session_state.config['radars'][radar_index] = radar
            next_page()

        # Next and Back buttons with single-click functionality
        col1.button("Next", on_click=functools.partial(save_radar_config), key=f'next_button_{st.session_state.page}')
        col2.button("Back", on_click=prev_page, key=f'back_button_{st.session_state.page}')

    
    # Add this in the main() function after the radar configuration pages and before the review page

    elif st.session_state.page == st.session_state.num_radars + 2:
        st.header("Sensor Configuration")
        
        # Add number of sensors selection if not already set
        if 'num_sensors' not in st.session_state:
            st.session_state.num_sensors = len(st.session_state.config.get('sensors', []))
        
        num_sensors = st.number_input('Number of Sensors', min_value=0, max_value=10, value=st.session_state.num_sensors, step=1)
        st.session_state.num_sensors = num_sensors
        
        # Initialize sensors if not present
        if 'sensors' not in st.session_state.config:
            st.session_state.config['sensors'] = []
        
        # Ensure we have the correct number of sensors
        while len(st.session_state.config['sensors']) < num_sensors:
            st.session_state.config['sensors'].append({
                'name': f'Sensor{len(st.session_state.config["sensors"]) + 1}',
                'start_position': [0, 0],
                'velocity': [0, 0],
                'start_time': 0,
                'saturation_level': '-70 dB'
            })
        
        # Configure each sensor
        for idx, sensor in enumerate(st.session_state.config['sensors'][:num_sensors]):
            with st.expander(f"Configure {sensor.get('name', f'Sensor{idx + 1}')}"):
                # Create tabs for different settings
                tabs = st.tabs(["Basic Settings", "Detection Settings", "Error Settings"])
                
                # Basic Settings Tab
                with tabs[0]:
                    st.subheader("Basic Information")
                    sensor['name'] = st.text_input('Sensor Name', value=sensor.get('name', f'Sensor{idx + 1}'), key=f'sensor_name_{idx}')
                    
                    sensor['freq_padding_factor'] = st.number_input(
                        "Frequency Measurement Padding Factor",
                        min_value=1,
                        max_value=16,
                        value=int(sensor.get('freq_padding_factor', 4)),
                        help="Higher values give better frequency resolution but increase computation time",
                        key=f'freq_padding_{idx}'
                    )
                    
                    st.subheader("Position and Movement")
                    start_position_str = st.text_input(
                        "Start Position (x, y in meters)",
                        value=str(sensor.get('start_position', [0, 0])),
                        key=f'start_pos_{idx}'
                    )
                    try:
                        sensor['start_position'] = ast.literal_eval(start_position_str)
                    except:
                        st.error("Invalid format for Start Position. Please enter a list like [x, y]")
                        
                    velocity_str = st.text_input(
                        "Velocity (vx, vy in m/s)",
                        value=str(sensor.get('velocity', [0, 0])),
                        key=f'velocity_{idx}'
                    )
                    try:
                        sensor['velocity'] = ast.literal_eval(velocity_str)
                    except:
                        st.error("Invalid format for Velocity. Please enter a list like [vx, vy]")
                        
                    sensor['start_time'] = st.number_input(
                        "Start Time (s)",
                        value=float(sensor.get('start_time', 0.0)),
                        format="%.2f",
                        key=f'start_time_{idx}'
                    )
                    
                    sensor['saturation_level'] = st.text_input(
                        "Saturation Level (dB)",
                        value=sensor.get('saturation_level', '-70 dB'),
                        key=f'sat_level_{idx}'
                    )
                
                # Detection Settings Tab
                with tabs[1]:
                    st.subheader("Detection Probability Settings")
                    if 'detection_probability' not in sensor:
                        sensor['detection_probability'] = {'level': [], 'probability': []}
                    
                    level_str = st.text_input(
                        "Detection Levels (dB)",
                        value=str(sensor['detection_probability'].get('level', [-80, -90, -95, -100])),
                        key=f'det_level_{idx}'
                    )
                    prob_str = st.text_input(
                        "Detection Probabilities (%)",
                        value=str(sensor['detection_probability'].get('probability', [100, 80, 30, 5])),
                        key=f'det_prob_{idx}'
                    )
                    try:
                        sensor['detection_probability']['level'] = ast.literal_eval(level_str)
                        sensor['detection_probability']['probability'] = ast.literal_eval(prob_str)
                    except:
                        st.error("Invalid format for detection levels or probabilities")
                
                # Error Settings Tab
                with tabs[2]:
                    error_types = ['amplitude', 'toa', 'frequency', 'pulse_width', 'aoa']
                    error_tabs = st.tabs([type.upper() for type in error_types])
                    
                    for i, error_type in enumerate(error_types):
                        with error_tabs[i]:
                            if f'{error_type}_error' not in sensor:
                                sensor[f'{error_type}_error'] = {
                                    'systematic': {'type': 'constant', 'error': '0'},
                                    'arbitrary': {'type': 'gaussian', 'error': '0'}
                                }
                            
                            # Systematic Error
                            st.subheader("Systematic Error")
                            sys_error = sensor[f'{error_type}_error']['systematic']
                            sys_error['type'] = st.selectbox(
                                "Type",
                                ['constant', 'linear'],
                                index=0 if sys_error.get('type') == 'constant' else 1,
                                key=f'sys_{error_type}_type_{idx}'
                            )
                            
                            sys_error['error'] = st.text_input(
                                "Error Value",
                                value=sys_error.get('error', '0'),
                                key=f'sys_{error_type}_error_{idx}'
                            )
                            
                            if sys_error['type'] == 'linear':
                                sys_error['rate'] = st.text_input(
                                    "Error Rate",
                                    value=sys_error.get('rate', '0'),
                                    key=f'sys_{error_type}_rate_{idx}'
                                )
                            
                            # Arbitrary Error
                            st.subheader("Arbitrary Error")
                            arb_error = sensor[f'{error_type}_error']['arbitrary']
                            arb_error['type'] = st.selectbox(
                                "Type",
                                ['gaussian', 'uniform'],
                                index=0 if arb_error.get('type') == 'gaussian' else 1,
                                key=f'arb_{error_type}_type_{idx}'
                            )
                            
                            arb_error['error'] = st.text_input(
                                "Error Value",
                                value=arb_error.get('error', '0'),
                                key=f'arb_{error_type}_error_{idx}'
                            )
        
        col1, col2 = st.columns([1,1])
        
        # Function to save sensor configuration and move to review page
        def save_sensor_config():
            st.session_state.config['sensors'] = st.session_state.config['sensors'][:num_sensors]
            next_page()
        
        # Next and Back buttons
        col1.button("Next", on_click=save_sensor_config, key='sensor_next')
        col2.button("Back", on_click=prev_page, key='sensor_back')

# Update the page numbers for review and simulation pages accordingly


        #HERE
        # Review Configuration Page
    elif st.session_state.page == st.session_state.num_radars + 3:
        st.header("Review Configuration")

        st.subheader("Scenario Configuration")
        st.write(f"**Start Time:** {st.session_state.config['scenario']['start_time']}")
        st.write(f"**End Time:** {st.session_state.config['scenario']['end_time']}")
        st.write(f"**Time Step:** {st.session_state.config['scenario']['time_step']}")

        st.subheader("Radar Configurations")
        for idx, radar in enumerate(st.session_state.config['radars']):
            st.write(f"### Radar {idx + 1}: {radar['name']}")
            st.json(radar)  # Display radar configuration in JSON format for clarity

        st.subheader("Sensor Configurations")
        for idx, sensor in enumerate(st.session_state.config['sensors']):
            st.write(f"### Sensor {idx + 1}: {sensor['name']}")
            st.json(sensor)

        col1, col2 = st.columns([1,1])

        # Function to run the simulation and navigate to the next page
        def run_simulation_and_next():
            # Save the updated config
            save_config(st.session_state.config)
            # Run the simulation
            run_simulation()
            next_page()

        # Run Simulation and Back buttons with single-click functionality
        col1.button("Run Simulation", on_click=run_simulation_and_next, key='run_simulation')
        col2.button("Back", on_click=prev_page, key='review_back')

    # Simulation Output Page
    elif st.session_state.page == st.session_state.num_radars + 4:
        st.header("Simulation Output")
        display_output()

        col1, col2 = st.columns([1,1])
        col1.button("Back", on_click=prev_page, key='output_back')
        col2.button("Restart", on_click=reset_app, key='restart')

    # Option to restart the app at any time
    st.sidebar.button("Restart", on_click=reset_app, key='sidebar_restart')
    # Sidebar References button
    def go_to_references():
        st.session_state.page = st.session_state.num_radars + 5

    st.sidebar.button("References", on_click=go_to_references, key='sidebar_references',use_container_width=False)

    # References Page
    if st.session_state.page == st.session_state.num_radars + 5:
        st.header("References")
        st.latex(r"""
\begin{aligned}
&\textbf{Reference 1:} \\
&\text{Opland, E. J. (2013). Clustering Evaluation for Deinterleaving. FFI-rapport 2013/00567.}
\end{aligned}
""")
        col1, col2 = st.columns([1,1])
        col1.button("Back", on_click=prev_page, key='references_back')
        col2.button("Restart", on_click=reset_app, key='references_restart')





if __name__ == "__main__":
    main()
