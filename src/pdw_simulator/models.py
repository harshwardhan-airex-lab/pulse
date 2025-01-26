import numpy as np
from pdw_simulator.scenario_geometry_functions import calculate_trajectory, get_unit_registry
from pdw_simulator.radar_properties import *
from pdw_simulator.sensor_properties import *

#For Validating the data
from pdw_simulator.validation import PDWValidator

class Scenario:
    def __init__(self, config):
        
        #Initialise the validator
        self.validator=PDWValidator()
        
        ## Validate Configuration before proceeding
        validation_errors = self.validator.validate_scenario(config)
        if validation_errors:
            raise ValueError(f"Scenario validation failed: {validation_errors}")
        
        
        self.start_time = config['start_time'] * ureg.second
        self.end_time = config['end_time'] * ureg.second
        self.time_step = config['time_step'] * ureg.second
        self.current_time = self.start_time
        self.radars = []
        self.sensors = []

    def update(self):
        self.current_time += self.time_step
        for radar in self.radars:
            radar.update_position(self.current_time)
        for sensor in self.sensors:
            sensor.update_position(self.current_time)
    
    def add_radar(self, radar_config):
        # Validate before adding new radar
        if len(self.radars) >= self.validator.MAX_RADARS:
            raise ValueError(f"Cannot add more than {self.validator.MAX_RADARS} radars")
            
        # Validate frequency separation with existing radars
        if 'frequency_params' in radar_config:
            new_freq = radar_config['frequency_params'].get('frequency')
            if new_freq:
                existing_freqs = [r.frequency_params.get('frequency') 
                                for r in self.radars 
                                if hasattr(r, 'frequency_params')]
                existing_freqs.append(new_freq)
                if not self.validator.validate_frequency_separation(existing_freqs):
                    raise ValueError("New radar frequency violates minimum separation requirement")

        # Create and add radar if validation passes
        radar = Radar(radar_config)
        self.radars.append(radar)
        return radar

class Radar:
    def __init__(self, config):
        
        #Initialise Validator
        self.validator=PDWValidator()
        
        #Validate Radar configuration
        self._validate_radar_config(config)
        
        
        self.name = config['name']
        self.start_position = np.array(config['start_position']) * ureg.meter
        self.velocity = np.array(config.get('velocity', [0, 0])) * ureg('meter/second')
        self.start_time = config.get('start_time', 0) * ureg.second
        self.current_time = self.start_time
        
        # Rotation period parameters
        self.rotation_type = config['rotation_type']
        self.rotation_params = config['rotation_params']
        self.rotation_data = None
        self.current_angle = self.rotation_params['alpha0']
        self.current_period = self.rotation_params['T_rot'] * ureg.second
        # self.frequency = config['frequency'] * ureg.hertz
        # self.pulse_width = config['pulse_width'] * ureg.second
        self.power = config['power'] * ureg.watt
        self.trajectory = None
        self.current_position = self.start_position

        ## PRI 
        self.pri_type=config['pri_type']
        self.pri_params=config['pri_params']
        self.pulse_times=None


        ## Frequency 
        self.frequency_type = config['frequency_type']
        self.frequency_params = config['frequency_params']
        self.pulse_width_type = config['pulse_width_type']
        self.pulse_width_params = config['pulse_width_params']
        self.frequencies = None
        self.pulse_widths = None


        #Antenna Lobe pattern
        self.lobe_pattern_type = config['lobe_pattern']['type']
        if self.lobe_pattern_type == 'Sinc':
            self.theta_ml = config['lobe_pattern']['main_lobe_opening_angle'] * ureg.degree
            self.P_ml = config['lobe_pattern']['radar_power_at_main_lobe'] * ureg.dB
            self.P_bl = config['lobe_pattern']['radar_power_at_back_lobe'] * ureg.dB
            
        # Initialize radar parameters with validation
        self._init_rotation(config)
        self._init_frequency(config)
        self._init_pulse_width(config)
        self._init_lobe_pattern(config)
    
    def _validate_radar_config(self, config):
        """Validate all radar configuration parameters"""
        errors = []
        
        # Validate frequency params
        if 'frequency_params' in config:
            freq = config['frequency_params'].get('frequency')
            if freq and not self.validator.validate_frequency(freq):
                errors.append(f"Invalid frequency: {freq}")
                
        # Validate pulse width
        if 'pulse_width_params' in config:
            pw = config['pulse_width_params'].get('pulse_width')
            if pw and not self.validator.validate_pulse_width(pw):
                errors.append(f"Invalid pulse width: {pw}")
                
        if errors:
            raise ValueError(f"Radar configuration validation failed: {errors}")
            
    def _init_frequency(self, config):
        """Initialize frequency parameters with validation"""
        self.frequency_type = config['frequency_type']
        self.frequency_params = config['frequency_params']
        
        # Validate frequency based on type
        if self.frequency_type == 'fixed':
            freq = self.frequency_params['frequency']
            if not self.validator.validate_frequency(freq):
                raise ValueError(f"Invalid fixed frequency: {freq}")
        elif self.frequency_type in ['stagger', 'switched']:
            for freq in self.frequency_params['frequency_pattern']:
                if not self.validator.validate_frequency(freq):
                    raise ValueError(f"Invalid frequency in pattern: {freq}")
                    
    def _init_pulse_width(self, config):
        """Initialize pulse width parameters with validation"""
        self.pulse_width_type = config['pulse_width_type']
        self.pulse_width_params = config['pulse_width_params']
        
        if self.pulse_width_type == 'fixed':
            pw = self.pulse_width_params['pulse_width']
            if not self.validator.validate_pulse_width(pw):
                raise ValueError(f"Invalid pulse width: {pw}")
        elif self.pulse_width_type in ['stagger', 'switched']:
            for pw in self.pulse_width_params['pulse_width_pattern']:
                if not self.validator.validate_pulse_width(pw):
                    raise ValueError(f"Invalid pulse width in pattern: {pw}")

    def get_next_pulse_time(self, current_time):
        """
        Get the next pulse time after the current time.

        :param current_time: Current simulation time
        :return: Next pulse time or None if no more pulses
        """
        if self.pulse_times is None:
            return None
        next_pulse_index = np.searchsorted(self.pulse_times, current_time.magnitude, side='left')
        if next_pulse_index < len(self.pulse_times):
            return self.pulse_times[next_pulse_index] * ureg.second
        return None

    def get_current_frequency(self):
        """
        Get the current frequency of the radar.

        :return: Current frequency
        """
        if self.frequencies is None:
            return None
        # print("Hi Harshwardhan")
        # print(type((self.frequencies[0])))
        # print(self.frequencies[0])
        true_freq=self.frequencies[0].astype(float)
        # return self.frequencies[0] * ureg.Hz
        return true_freq * ureg.Hz

    def get_current_pulse_width(self):
        """
        Get the current pulse width of the radar.

        :return: Current pulse width
        """
        # print(type((self.frequencies[0])))
        # print(self.frequencies[0])
        if self.pulse_widths is None:
            return None
        true_pw=self.pulse_widths[0].astype(float)
        print(true_pw)
        return true_pw * ureg.second
    
    def calculate_power_at_angle(self, theta):
        if self.lobe_pattern_type == 'Sinc':
            return sinc_lobe_pattern(theta, self.theta_ml, self.P_ml, self.P_bl)
        else:
            raise ValueError(f"Unsupported lobe pattern type: {self.lobe_pattern_type}")

    def get_current_angle(self):
        return self.current_angle * ureg.radian

    def get_current_period(self):
        return self.current_period
    
    def calculate_pulse_times(self, end_time):
        if self.pri_type == 'fixed':
            self.pulse_times = fixed_pri(self.start_time.magnitude, end_time.magnitude, self.pri_params['pri'])
        elif self.pri_type == 'stagger':
            self.pulse_times = stagger_pri(self.start_time.magnitude, end_time.magnitude, self.pri_params['pri_pattern'])
        elif self.pri_type == 'switched':
            self.pulse_times = switched_pri(self.start_time.magnitude, end_time.magnitude, 
                                            self.pri_params['pri_pattern'], self.pri_params['repetitions'])
        elif self.pri_type == 'jitter':
            self.pulse_times = jitter_pri(self.start_time.magnitude, end_time.magnitude, 
                                          self.pri_params['mean_pri'], self.pri_params['jitter_percentage'])
        else:
            raise ValueError(f"Invalid PRI type: {self.pri_type}")
        
    def calculate_frequencies(self, end_time):
            if self.frequency_type == 'fixed':
                self.frequencies = fixed_frequency(self.start_time.magnitude, end_time.magnitude, self.frequency_params['frequency'])
            elif self.frequency_type == 'stagger':
                self.frequencies = stagger_frequency(self.start_time.magnitude, end_time.magnitude, self.frequency_params['frequency_pattern'])
            elif self.frequency_type == 'switched':
                self.frequencies = switched_frequency(self.start_time.magnitude, end_time.magnitude, 
                                                    self.frequency_params['frequency_pattern'], self.frequency_params['repetitions'])
            elif self.frequency_type == 'jitter':
                self.frequencies = jitter_frequency(self.start_time.magnitude, end_time.magnitude, 
                                                    self.frequency_params['mean_frequency'], self.frequency_params['jitter_percentage'])
            else:
                raise ValueError(f"Invalid frequency type: {self.frequency_type}")

    def calculate_pulse_widths(self, end_time):
        if self.pulse_width_type == 'fixed':
            self.pulse_widths = fixed_pulse_width(self.start_time.magnitude, end_time.magnitude, self.pulse_width_params['pulse_width'])
        elif self.pulse_width_type == 'stagger':
            self.pulse_widths = stagger_pulse_width(self.start_time.magnitude, end_time.magnitude, self.pulse_width_params['pulse_width_pattern'])
        elif self.pulse_width_type == 'switched':
            self.pulse_widths = switched_pulse_width(self.start_time.magnitude, end_time.magnitude, 
                                                     self.pulse_width_params['pulse_width_pattern'], self.pulse_width_params['repetitions'])
        elif self.pulse_width_type == 'jitter':
            self.pulse_widths = jitter_pulse_width(self.start_time.magnitude, end_time.magnitude, 
                                                   self.pulse_width_params['mean_pulse_width'], self.pulse_width_params['jitter_percentage'])
        else:
            raise ValueError(f"Invalid pulse width type: {self.pulse_width_type}")
        
    def calculate_trajectory(self, end_time, time_step):
        if np.any(self.velocity != 0):
            self.trajectory = calculate_trajectory(
                self.start_position.magnitude, end_time.magnitude, time_step.magnitude,
                self.velocity.magnitude, self.start_time.magnitude)
        else:
            self.trajectory = calculate_trajectory(
                self.start_position.magnitude, end_time.magnitude, time_step.magnitude)
            
        self.calculate_pulse_times(end_time)
        print(f"Initialized {self.name} with {len(self.pulse_times)} pulse times")
        self.calculate_frequencies(end_time)
        self.calculate_pulse_widths(end_time)
        
        # Calculate rotation angles and periods
        self.rotation_data = calculate_rotation_angles(
            self.start_time.magnitude, end_time.magnitude, time_step.magnitude,
            self.rotation_type, self.rotation_params)

    def update_position(self, current_time):
        if self.trajectory is not None:
            idx = np.searchsorted([t[0] for t in self.trajectory], current_time.magnitude)
            if idx < len(self.trajectory):
                self.current_position = np.array([self.trajectory[idx][1], self.trajectory[idx][2]]) * ureg.meter
        
        # Update rotation angle and period
        if self.rotation_data is not None:
            idx = np.searchsorted([t[0] for t in self.rotation_data], current_time.magnitude)
            if idx < len(self.rotation_data):
                self.current_angle = self.rotation_data[idx][1]
                self.current_period = self.rotation_data[idx][2] * ureg.second


    def get_current_angle(self):
        if self.rotation_data is not None:
            idx = np.searchsorted([t[0] for t in self.rotation_data], self.current_time.magnitude)
            if idx < len(self.rotation_data):
                return self.rotation_data[idx][1] * ureg.radian
        return 0 * ureg.radian

    def get_current_period(self):
        if self.rotation_data is not None:
            idx = np.searchsorted([t[0] for t in self.rotation_data], self.current_time.magnitude)
            if idx < len(self.rotation_data):
                return self.rotation_data[idx][2] * ureg.second
        return self.rotation_params['T_rot'] * ureg.second
    
    def update(self, current_time):
        self.current_time = current_time
        self.update_position(current_time)
        self.update_rotation(current_time)

    def update_position(self, current_time):
        if self.trajectory is not None:
            idx = np.searchsorted([t[0] for t in self.trajectory], current_time.magnitude)
            if idx < len(self.trajectory):
                self.current_position = np.array([self.trajectory[idx][1], self.trajectory[idx][2]]) * ureg.meter

    def update_rotation(self, current_time):
        if self.rotation_data is not None:
            idx = np.searchsorted([t[0] for t in self.rotation_data], current_time.magnitude)
            if idx < len(self.rotation_data):
                self.current_angle = self.rotation_data[idx][1]
                self.current_period = self.rotation_data[idx][2] * ureg.second

    def get_current_angle(self):
        return self.current_angle * ureg.radian

    def get_current_period(self):
        return self.current_period



class Sensor:
    def __init__(self, config):
        
        #Initialise validator
        self.validator=validator
        
        #Validate Sensor Configuration
        self._validate_radar_config(config)
        
        
        self.name = config['name']
        self.start_position = np.array(config['start_position']) * ureg.meter
        self.velocity = np.array(config.get('velocity', [0, 0])) * ureg('meter/second')
        self.start_time = config.get('start_time', 0) * ureg.second
        self.trajectory = None
        self.current_position = self.start_position
        self.current_time = self.start_time

        # Detection Probability and Saturation Level
        saturation_level_str = config['saturation_level']
        value, unit = saturation_level_str.split()
        self.saturation_level = float(value) * ureg(unit)
        # self.saturation_level = config['saturation_level'] * ureg.dB
        # self.detection_levels = np.array(config['detection_probability']['level']) * ureg.dB
        # self.detection_probabilities = np.array(config['detection_probability']['probability']) / 100
        self.detection_levels = [level * ureg.dB for level in config['detection_probability']['level']]
        self.detection_probabilities = [prob / 100 for prob in config['detection_probability']['probability']]
        self.freq_padding_factor = config.get('freq_padding_factor', 4)
        # Error models
        self.amplitude_error_syst = create_error_model(config['amplitude_error']['systematic'])
        self.amplitude_error_arb = create_error_model(config['amplitude_error']['arbitrary'])
        self.toa_error_syst = create_error_model(config['toa_error']['systematic'])
        self.toa_error_arb = create_error_model(config['toa_error']['arbitrary'])
        self.frequency_error_syst = create_error_model(config['frequency_error']['systematic'])
        self.frequency_error_arb = create_error_model(config['frequency_error']['arbitrary'])
        self.pw_error_syst = create_error_model(config['pulse_width_error']['systematic'])
        self.pw_error_arb = create_error_model(config['pulse_width_error']['arbitrary'])
        self.aoa_error_syst = create_error_model(config['aoa_error']['systematic'])
        self.aoa_error_arb = create_error_model(config['aoa_error']['arbitrary'])
        
        # Validate and set detection parameters
        self._init_detection_params(config)
    
    def _validate_sensor_config(self, config):
        """Validate sensor configuration parameters"""
        errors = []
        
        # Validate amplitude range
        if 'saturation_level' in config:
            sat_level = float(config['saturation_level'].split()[0])
            if not self.validator.validate_amplitude(sat_level):
                errors.append(f"Invalid saturation level: {sat_level}")
                
        if errors:
            raise ValueError(f"Sensor configuration validation failed: {errors}")
            
    def _init_detection_params(self, config):
        """Initialize detection parameters with validation"""
        # Validate detection levels
        for level in config['detection_probability']['level']:
            if not self.validator.validate_amplitude(level):
                raise ValueError(f"Invalid detection level: {level}")
                
        # Set parameters after validation
        self.detection_levels = [level * ureg.dB for level in config['detection_probability']['level']]
        self.detection_probabilities = [prob / 100 for prob in config['detection_probability']['probability']]

    def detect_pulse(self, amplitude):
        return detect_pulse(amplitude, self.detection_levels, self.detection_probabilities, self.saturation_level)

    def measure_amplitude(self, true_amplitude, r, P_theta, t, P0):
        return measure_amplitude(true_amplitude, r, P_theta, t, P0, self.amplitude_error_syst, self.amplitude_error_arb)

    def measure_toa(self, true_toa, r, t):
        return measure_toa(true_toa, r, t, self.toa_error_syst, self.toa_error_arb)

    def measure_frequency(self, true_frequency,t,radar=None):
        return measure_frequency(true_frequency=true_frequency,t=t,current_time=self.current_time,frequency_error_syst=self.frequency_error_syst,frequency_error_arb=self.frequency_error_arb,radar=radar,sensor=self)

    def measure_pulse_width(self, true_pw, t):
        return measure_pulse_width(true_pw, t, self.pw_error_syst, self.pw_error_arb)

    def measure_aoa(self, true_aoa, t):
        return measure_aoa(true_aoa, t, self.aoa_error_syst, self.aoa_error_arb)

    def calculate_trajectory(self, end_time, time_step):
        if np.any(self.velocity != 0):
            self.trajectory = calculate_trajectory(
                self.start_position.magnitude, end_time.magnitude, time_step.magnitude,
                self.velocity.magnitude, self.start_time.magnitude)
        else:
            self.trajectory = calculate_trajectory(
                self.start_position.magnitude, end_time.magnitude, time_step.magnitude)

    def update_position(self, current_time):
        self.current_time = current_time
        if self.trajectory is not None:
            idx = np.searchsorted([t[0] for t in self.trajectory], current_time.magnitude)
            if idx < len(self.trajectory):
                self.current_position = np.array([self.trajectory[idx][1], self.trajectory[idx][2]]) * ureg.meter
