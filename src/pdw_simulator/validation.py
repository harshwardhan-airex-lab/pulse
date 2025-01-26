from typing import List, Dict, Any
from pdw_simulator.scenario_geometry_functions import get_unit_registry
import numpy as np

# Get the unit registry from scenario_geometry_functions
ureg = get_unit_registry()

class PDWValidator:
    """Validator class for PDW simulation parameters"""
    
    def __init__(self):
        # Define constants
        self.FREQ_MIN = 0.5 * ureg.GHz
        self.FREQ_MAX = 40 * ureg.GHz
        self.FREQ_ACCURACY = 0.01  # 1%
        self.FREQ_MIN_SEPARATION = 4 * ureg.MHz
        
        self.AMPLITUDE_MIN = -65 * ureg.dBm
        self.AMPLITUDE_MAX = 0 * ureg.dBm
        
        self.AOA_MIN = 0 * ureg.degree
        self.AOA_MAX = 360 * ureg.degree
        self.AOA_ACCURACY = 2 * ureg.degree
        
        self.ELEVATION_MIN = -45 * ureg.degree
        self.ELEVATION_MAX = 45 * ureg.degree
        
        self.PW_MIN = 100 * ureg.microsecond
        self.PW_MAX = 500 * ureg.microsecond
        self.PW_ACCURACY = 25 * ureg.nanosecond
        
        self.MAX_RADARS = 32

    def validate_scenario_config(self, scenario_config: Dict[str, Any]) -> List[str]:
        """Validate basic scenario parameters"""
        errors = []
        
        # Validate time parameters exist
        required_params = ['start_time', 'end_time', 'time_step']
        for param in required_params:
            if param not in scenario_config:
                errors.append(f"Missing required parameter: {param}")
        
        # Validate time logic if parameters exist
        if all(param in scenario_config for param in required_params):
            if scenario_config['end_time'] <= scenario_config['start_time']:
                errors.append("end_time must be greater than start_time")
            if scenario_config['time_step'] <= 0:
                errors.append("time_step must be greater than 0")
                
        return errors

    def validate_full_config(self, config: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate complete configuration including radars and sensors"""
        errors = {
            'scenario': [],
            'frequency': [],
            'amplitude': [],
            'aoa': [],
            'elevation': [],
            'pulse_width': [],
            'radar_count': [],
            'frequency_separation': []
        }
        
        # Validate scenario section
        if 'scenario' in config:
            scenario_errors = self.validate_scenario_config(config['scenario'])
            if scenario_errors:
                errors['scenario'].extend(scenario_errors)
        
        # Validate radar count
        if len(config.get('radars', [])) > self.MAX_RADARS:
            errors['radar_count'].append(f'Maximum {self.MAX_RADARS} radars allowed')

        # Collect frequencies for separation validation
        frequencies = []
        
        # Validate each radar
        for idx, radar in enumerate(config.get('radars', [])):
            # Validate frequency
            if 'frequency_params' in radar:
                freq = radar['frequency_params'].get('frequency')
                if freq:
                    if not self.validate_frequency(freq):
                        errors['frequency'].append(
                            f'Radar {idx}: Frequency {freq} Hz outside allowed range'
                        )
                    frequencies.append(freq)

            # Validate pulse width
            if 'pulse_width_params' in radar:
                pw = radar['pulse_width_params'].get('pulse_width')
                if pw and not self.validate_pulse_width(pw):
                    errors['pulse_width'].append(
                        f'Radar {idx}: Pulse width {pw} s outside allowed range'
                    )

        # Validate frequency separation
        if frequencies and not self.validate_frequency_separation(frequencies):
            errors['frequency_separation'].append(
                'Minimum frequency separation requirement not met'
            )

        return {k: v for k, v in errors.items() if v}

    # Keep all your existing validation methods
    def validate_frequency(self, frequency: float, unit: str = 'Hz') -> bool:
        freq = frequency * ureg(unit)
        return self.FREQ_MIN <= freq <= self.FREQ_MAX

    def validate_frequency_separation(self, frequencies: List[float], unit: str = 'Hz') -> bool:
        freqs = sorted([f * ureg(unit) for f in frequencies])
        for i in range(len(freqs) - 1):
            if (freqs[i+1] - freqs[i]) < self.FREQ_MIN_SEPARATION:
                return False
        return True

    def validate_amplitude(self, amplitude: float, unit: str = 'dBm') -> bool:
        amp = amplitude * ureg(unit)
        return self.AMPLITUDE_MIN <= amp <= self.AMPLITUDE_MAX

    def validate_aoa(self, angle: float, unit: str = 'degree') -> bool:
        aoa = angle * ureg(unit)
        return self.AOA_MIN <= aoa <= self.AOA_MAX

    def validate_elevation(self, angle: float, unit: str = 'degree') -> bool:
        elev = angle * ureg(unit)
        return self.ELEVATION_MIN <= elev <= self.ELEVATION_MAX

    def validate_pulse_width(self, width: float, unit: str = 'second') -> bool:
        pw = width * ureg(unit)
        return self.PW_MIN <= pw <= self.PW_MAX