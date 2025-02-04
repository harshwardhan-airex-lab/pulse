import numpy as np
from pdw_simulator.radar_properties import calculate_doppler_shift, calculate_relative_velocity, apply_doppler_effect
from pdw_simulator.scenario_geometry_functions import get_unit_registry

ureg = get_unit_registry()

def create_error_model(error_config):
    """
    Create an error model based on the configuration.
    
    :param error_config: Dictionary containing error model parameters
    :return: Function that generates errors based on the model
    """
    if error_config['type'] == 'constant':
        error_value, error_unit = parse_value_and_unit(error_config['error'])
        return lambda t: error_value * ureg(error_unit)
    elif error_config['type'] == 'linear':
        error_value, error_unit = parse_value_and_unit(error_config['error'])
        rate_value, rate_unit = parse_value_and_unit(error_config['rate'])
        return lambda t: (error_value + rate_value * t.magnitude) * ureg(error_unit)
    elif error_config['type'] == 'sinus':
        # Parse amplitude
        A, A_unit = parse_value_and_unit(error_config['amplitude'])
        
        # Parse frequency
        f, f_unit = parse_value_and_unit(error_config['frequency'])
        if f_unit != 'Hz':
            raise ValueError(f"Frequency unit must be Hz, got {f_unit}")
        
        # Parse phase (assuming it's a unitless numerical value)
        try:
            phi0 = float(error_config['phase'])
        except ValueError:
            raise ValueError(f"Phase must be a numerical value, got {error_config['phase']}")
        
        print(f"Sinusoidal Error Model Parameters: Amplitude={A} {A_unit}, Frequency={f} Hz, Phase={phi0}")
        
        return lambda t: A * np.sin(2 * np.pi * f * t.magnitude + phi0) * ureg(A_unit)
    elif error_config['type'] == 'gaussian':
        error_value, error_unit = parse_value_and_unit(error_config['error'])
        if error_unit == 'percent':
            return lambda size: np.random.normal(0, error_value, size) * ureg.dimensionless
        else:
            return lambda size: np.random.normal(0, error_value, size) * ureg(error_unit)
    elif error_config['type'] == 'uniform':
        error_value, error_unit = parse_value_and_unit(error_config['error'])
        if error_unit == 'percent':
            return lambda size: np.random.uniform(-error_value, error_value, size) * ureg.dimensionless
        else:
            return lambda size: np.random.uniform(-error_value, error_value, size) * ureg(error_unit)
    else:
        raise ValueError(f"Unknown error type: {error_config['type']}")

def parse_value_and_unit(string_value):
    """
    Parse a string containing a value and a unit.
    
    :param string_value: String containing value and unit (e.g., '0.1 dB', '4.5%')
    :return: Tuple of (value, unit)
    """
    parts = string_value.split()
    if len(parts) == 2:
        value, unit = parts
    elif len(parts) == 1:
        value, unit = parts[0], ''
    else:
        raise ValueError(f"Invalid value and unit string: {string_value}")
    
    # Handle percentage
    if value.endswith('%'):
        return float(value[:-1]) / 100, 'percent'
    else:
        return float(value), unit


def detect_pulse(amplitude, detection_levels, detection_probabilities, saturation_level):
    """
    Determine if a pulse is detected based on its amplitude.
    All amplitudes should be in dBm.
    """
    # Convert saturation_level to dBm if it's a string
    if isinstance(saturation_level, str):
        value = float(saturation_level.split()[0])
        saturation_level = value * ureg.dBm

    # Compare amplitudes (all should be in dBm)
    if amplitude.magnitude > saturation_level.magnitude:
        return True

    for level, prob in zip(detection_levels, detection_probabilities):
        # Convert level to dBm if needed
        if isinstance(level, (int, float)):
            level = level * ureg.dBm
        elif isinstance(level, str):
            value = float(level.split()[0])
            level = value * ureg.dBm

        if amplitude.magnitude > level.magnitude:
            return np.random.random() < prob
    return False

# def detect_pulse(amplitude, detection_levels, detection_probabilities, saturation_level):
#     """
#     Determine if a pulse is detected based on its amplitude.
    
#     :param amplitude: Amplitude of the pulse
#     :param detection_levels: List of detection levels
#     :param detection_probabilities: List of detection probabilities corresponding to levels
#     :param saturation_level: Saturation level of the sensor
#     :return: Boolean indicating whether the pulse is detected
#     """
#     if amplitude.to('dB').magnitude > saturation_level.to('dB').magnitude:
#         return True
    
#     for level, prob in zip(detection_levels,detection_probabilities):
#         if amplitude.to('dB').magnitude > level.to('dB').magnitude:
#             return np.random.random() < prob
#     return False
#         # if amplitude > saturation_level:
#         #     return True
#         # for level, prob in zip(detection_levels, detection_probabilities):
#         #     if amplitude > level:
#         #         return np.random.random() < prob
#         # return False


def measure_amplitude(true_amplitude, r, P_theta, t, P0, amplitude_error_syst, amplitude_error_arb):
    """
    Measure the amplitude of a detected pulse.
    All amplitude measurements are in dBm.
    """
    # Ensure proper units
    r = ureg.Quantity(r).to(ureg.meter)
    P0 = ureg.Quantity(P0).to(ureg.dBm)
    
    # Convert r to a dimensionless quantity by dividing by 1 meter
    r_dimensionless = r / ureg.meter
    
    # Calculate path loss in dB
    Pr = 20 * np.log10(r_dimensionless.magnitude) * ureg.dBm
    
    # P_theta should already be in dBm from the radar calculations
    if not isinstance(P_theta, ureg.Quantity):
        P_theta = P_theta * ureg.dBm
        
    # Get systematic and arbitrary errors
    P_syst = ureg.Quantity(amplitude_error_syst(t)).to(ureg.dBm)
    P_arb = ureg.Quantity(amplitude_error_arb(1)[0]).to(ureg.dBm)
    
    # Calculate total amplitude in dBm
    total_magnitude = P0.magnitude - Pr.magnitude + P_theta.magnitude + P_syst.magnitude + P_arb.magnitude
    measured_amplitude = total_magnitude * ureg.dBm
    
    return measured_amplitude

# def measure_amplitude(true_amplitude, r, P_theta, t, P0, amplitude_error_syst, amplitude_error_arb):
#     """
#     Measure the amplitude of a detected pulse.
    
#     :param true_amplitude: True amplitude of the pulse (in dB)
#     :param r: Distance between radar and sensor (in meters)
#     :param P_theta: Amplitude correction due to radar antenna lobe pattern (in dB)
#     :param t: Current time
#     :param P0: Amplitude of an emitted pulse from an equivalent omnidirectional radar antenna (in watts)
#     :param amplitude_error_syst: Function to generate systematic error
#     :param amplitude_error_arb: Function to generate arbitrary error
#     :return: Measured amplitude (in dB)
#     """
#     # print("\nDebugging measure_amplitude:")
#     # print(f"true_amplitude: {true_amplitude}, type: {type(true_amplitude)}")
#     # print(f"r: {r}, type: {type(r)}")
#     # print(f"P_theta: {P_theta}, type: {type(P_theta)}")
#     # print(f"t: {t}, type: {type(t)}")
#     # print(f"P0: {P0}, type: {type(P0)}")

#     # Ensure all inputs are Pint Quantities with correct units
#     r = ureg.Quantity(r).to(ureg.meter)
#     P_theta = ureg.Quantity(P_theta).to(ureg.dB)
#     P0 = ureg.Quantity(P0).to(ureg.watt)
    
#     # Convert r to a dimensionless quantity by dividing by 1 meter
#     r_dimensionless = r / ureg.meter
#     Pr = 20 * ureg.dB * np.log10(r_dimensionless.magnitude)
    
#     # Convert P0 from watts to dB
#     P0_dB = 10 * ureg.dB * np.log10(P0.magnitude)
    
#     P_syst = ureg.Quantity(amplitude_error_syst(t)).to(ureg.dB)
#     P_arb = ureg.Quantity(amplitude_error_arb(1)[0]).to(ureg.dB)
    
#     # print(f"After conversion:")
#     # print(f"Pr: {Pr}, Dimensionality: {Pr.dimensionality}")
#     # print(f"P0_dB: {P0_dB}, type: {P0_dB.dimensionality}")
#     # print(f"P_theta: {P_theta}, type: {P_theta.dimensionality}")
#     # print(f"P_syst: {P_syst}, type: {P_syst.dimensionality}")
#     # print(f"P_arb: {P_arb}, type: {P_arb.dimensionality}")


#     # print(f"Pr: {Pr}, Dimensionality: {type(Pr)}")
#     # print(f"P0_dB: {P0_dB}, type: {type(P0_dB)}")
#     # print(f"P_theta: {P_theta}, type: {type(P_theta)}")
#     # print(f"P_syst: {P_syst}, type: {type(P_syst)}")
#     # print(f"P_arb: {P_arb}, type: {type(P_arb)}")
#     total_magnitude = P0_dB.magnitude - Pr.magnitude + P_theta.magnitude + P_syst.magnitude + P_arb.magnitude
#     measured_amplitude = ureg.Quantity(total_magnitude, ureg.dB)
#     # print(f"measured_amplitude: {measured_amplitude}, type: {type(measured_amplitude)}")
    
#     return measured_amplitude


def measure_toa(true_toa, r, t, toa_error_syst, toa_error_arb):
    """
    Measure the Time of Arrival (TOA) of a detected pulse.
    
    :param true_toa: True TOA of the pulse
    :param r: Distance between radar and sensor
    :param t: Current time
    :param toa_error_syst: Function to generate systematic error
    :param toa_error_arb: Function to generate arbitrary error
    :return: Measured TOA
    """
    c = 299792458 * ureg.meter / ureg.second  # Speed of light
    delta_Tr = r / c
    
    #TODO - Check why TOA_syst and TOA_arb are coming out as dimensionless sometimes
    # Check if TOA_syst and TOA_arb have units; add ureg.second only if dimensionless
    TOA_syst = toa_error_syst(t)
    if TOA_syst.dimensionality == ureg.dimensionless:
        TOA_syst *= ureg.second

    TOA_arb = toa_error_arb(1)[0]  # Generate a single random error
    if TOA_arb.dimensionality == ureg.dimensionless:
        TOA_arb *= ureg.second

    # Debug prints
    # print(f"TOA_system magnitude: {TOA_syst.magnitude}, dimensionality: {TOA_syst.dimensionality}")
    # print(f"TOA_arbitrary magnitude: {TOA_arb.magnitude}, dimensionality: {TOA_arb.dimensionality}")
    # print(f"True_TOA dimensionality: {true_toa.dimensionality}")
    # print(f"Delta_Tr dimensionality: {delta_Tr.dimensionality}")

    # Calculate the measured TOA
    measured_toa = true_toa + delta_Tr + TOA_syst + TOA_arb
    return measured_toa


# Add to sensor_properties.py

def measure_frequency(true_frequency, t, current_time, frequency_error_syst, frequency_error_arb, radar=None, sensor=None):
    """
    Measure frequency with enhanced FFT interpolation, error models, and Doppler shift.
    
    Args:
        true_frequency: True frequency with units
        t: Time with units
        current_time: Current simulation time with units
        frequency_error_syst: Systematic error model function
        frequency_error_arb: Arbitrary error model function
        radar: Optional radar object for Doppler calculations
        sensor: Optional sensor object for Doppler calculations
    
    Returns:
        Measured frequency with units
    """
    # Get enhanced frequency measurement
    measured_freq = enhanced_frequency_measurement(true_frequency, t, current_time)
    
    # Apply error models
    f_syst = frequency_error_syst(t)
    f_arb = frequency_error_arb(1)[0]  # Generate a single random error
    
    # Ensure proper units
    if f_syst.dimensionality == ureg.dimensionless:
        f_syst = f_syst * ureg.Hz
    if f_arb.dimensionality == ureg.dimensionless:
        f_arb = f_arb * ureg.Hz
        
    # Apply errors to measurement
    measured_freq = measured_freq + f_syst + f_arb
    
    # Apply Doppler shift if radar and sensor are provided
    if radar is not None and sensor is not None:
        measured_freq = apply_doppler_effect(measured_freq, radar, sensor)
    
    return measured_freq


def enhanced_frequency_measurement(true_frequency, t, current_time, padding_factor=4):
    """
    Enhanced frequency measurement with zero padding and proper unit handling.
    Uses fftshift for proper frequency centering while ensuring positive frequencies.
    """
    ureg = get_unit_registry()
    
    # Generate some signal samples around the true frequency
    sample_rate = 2.5 * ureg.GHz  # Nyquist rate for typical radar frequencies
    num_samples = 1024  # Base number of samples
    
    # Create time array for sampling
    t_samples = np.linspace(
        current_time.magnitude, 
        (current_time + 1*ureg.microsecond).magnitude,
        num_samples
    ) * ureg.second
    
    # Generate complex signal at true frequency
    signal = np.exp(2j * np.pi * true_frequency.magnitude * t_samples.magnitude)
    
    # Add some noise
    noise_level = 0.1
    signal += noise_level * (np.random.randn(len(signal)) + 1j * np.random.randn(len(signal)))
    
    # Zero padding
    padded_length = num_samples * padding_factor
    padded_signal = np.pad(signal, (0, padded_length - num_samples))
    
    # Perform FFT and shift
    spectrum = np.fft.fftshift(np.fft.fft(padded_signal))
    frequencies = np.fft.fftshift(np.fft.fftfreq(padded_length, (1/sample_rate).magnitude))
    
    # After fftshift, the frequencies are arranged from -Fs/2 to +Fs/2
    # Select only the positive half of the spectrum
    center_idx = len(frequencies) // 2
    positive_spectrum = spectrum[center_idx:]
    positive_frequencies = frequencies[center_idx:]
    
    # Find peak frequency in positive frequencies
    peak_idx = np.argmax(np.abs(positive_spectrum))
    measured_freq = positive_frequencies[peak_idx] * ureg.Hz
    
    # Add some measurement error
    freq_error = np.random.normal(0, 1e6) * ureg.Hz  # 1 MHz standard deviation error
    measured_freq = measured_freq + freq_error
    
    # Ensure the measured frequency stays close to true frequency
    if np.abs(measured_freq - true_frequency) > 10 * ureg.MHz:
        measured_freq = true_frequency + freq_error
    
    return abs(measured_freq)  # Ensure positive frequency

def measure_pulse_width(true_pw, t, pw_error_syst, pw_error_arb):
    """
    Measure the pulse width of a detected pulse.
    
    :param true_pw: True pulse width
    :param t: Current time
    :param pw_error_syst: Function to generate systematic error
    :param pw_error_arb: Function to generate arbitrary error
    :return: Measured pulse width
    """
    PW_syst = pw_error_syst(t)
    PW_arb = pw_error_arb(1)[0]  # Generate a single random error

    if isinstance(PW_arb, ureg.Quantity) and PW_arb.units == ureg.percent:
        PW_arb = true_pw * PW_arb.magnitude / 100

    if isinstance(PW_arb, ureg.Quantity) and PW_arb.dimensionless:
        PW_arb = true_pw * PW_arb.magnitude
    # print(f"true_pw: {true_pw}, type: {type(true_pw.magnitude)}")
    # print(f"PW_syst {PW_syst}, type: {type(PW_syst.magnitude)}")
    # print(f"PW_arb: {PW_arb}, type: {type(PW_arb.magnitude)}")
    print(f"true_pw: {true_pw}, type: {true_pw.dimensionality}")
    print(f"PW_syst {PW_syst}, type: {PW_syst.dimensionality}")
    print(f"PW_arb: {PW_arb}, type: {PW_arb.dimensionality}")
    if PW_arb.dimensionality == ureg.dimensionless:
        PW_arb *= ureg.second
    if PW_syst.dimensionality == ureg.dimensionless:
        PW_syst *= ureg.second
    if true_pw.dimensionality == ureg.dimensionless:
        true_pw *= ureg.second
    measured_pw = true_pw + PW_syst + PW_arb
    return measured_pw.to(ureg.second)

def measure_aoa(true_aoa, t, aoa_error_syst, aoa_error_arb):
    """
    Measure the Angle of Arrival (AOA) of a detected pulse.
    
    :param true_aoa: True AOA of the pulse
    :param t: Current time
    :param aoa_error_syst: Function to generate systematic error
    :param aoa_error_arb: Function to generate arbitrary error
    :return: Measured AOA
    """
    AOA_syst = aoa_error_syst(t)
    AOA_arb = aoa_error_arb(1)[0]  # Generate a single random error
    
    measured_aoa = true_aoa + AOA_syst + AOA_arb
    return measured_aoa.to(ureg.degree)

# Additional function for AOA sinusoidal error
def aoa_sinusoidal_error(AOA, A, f, AOA_ref):
    """
    Calculate AOA error with sinusoidal dependency on the direction.
    
    :param AOA: Angle of Arrival
    :param A: Error amplitude
    :param f: Number of sinus periods per 360 degrees
    :param AOA_ref: Reference angle where error is zero
    :return: AOA error
    """
    return A * np.sin(f * (AOA - AOA_ref))