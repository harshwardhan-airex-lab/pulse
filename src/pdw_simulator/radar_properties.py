import numpy as np
import numpy.ma as ma
from scipy import stats
from pdw_simulator.scenario_geometry_functions import get_unit_registry
ureg = get_unit_registry()

def constant_rotation_period(t, t0, alpha0, T_rot):
    """
    Calculate the angle for constant rotation period.
    
    :param t: Current time
    :param t0: Start time
    :param alpha0: Initial angle at t0
    :param T_rot: Rotation period
    :return: Current angle
    """
    return alpha0 + 2 * np.pi * (t - t0) / T_rot

def varying_rotation_period(t, t0, alpha0, T_rot, A, s, phi0):
    """
    Calculate the angle for varying rotation period.
    
    :param t: Current time
    :param t0: Start time
    :param alpha0: Initial angle at t0
    :param T_rot: Constant component of rotation period
    :param A: Amplitude of variation relative to constant component
    :param s: Angular frequency of variation relative to constant component
    :param phi0: Start phase of variation
    :return: Current angle
    """
    omega0 = 2 * np.pi / T_rot
    B = (A / s) * (np.cos(s * omega0 * t0 + phi0) - np.cos(phi0))
    return alpha0 + omega0 * (t - t0) - (A / s) * np.cos(s * omega0 * t + phi0) + B

def calculate_varying_period(t, T_rot, A, s, phi0):
    """
    Calculate the varying rotation period.
    
    :param t: Current time
    :param T_rot: Constant component of rotation period
    :param A: Amplitude of variation relative to constant component
    :param s: Angular frequency of variation relative to constant component
    :param phi0: Start phase of variation
    :return: Current rotation period
    """
    omega0 = 2 * np.pi / T_rot
    return T_rot / (1 + A * np.sin(s * omega0 * t + phi0))



def calculate_rotation_angles(start_time, end_time, time_step, rotation_type, params):
    """
    Calculate rotation angles and periods over time.
    
    :param start_time: Start time of calculation
    :param end_time: End time of calculation
    :param time_step: Time step for calculation
    :param rotation_type: 'constant' or 'varying'
    :param params: Dictionary of parameters for the rotation calculation
    :return: List of [time, angle, period] triples
    """
    times = np.arange(start_time, end_time + time_step, time_step)
    if rotation_type == 'constant':
        angles = constant_rotation_period(times, params['t0'], params['alpha0'], params['T_rot'])
        periods = np.full_like(times, params['T_rot'])
    elif rotation_type == 'varying':
        angles = varying_rotation_period(times, params['t0'], params['alpha0'], params['T_rot'], 
                                         params['A'], params['s'], params['phi0'])
        periods = calculate_varying_period(times, params['T_rot'], params['A'], params['s'], params['phi0'])
    else:
        raise ValueError("Invalid rotation type. Must be 'constant' or 'varying'.")
    
    return list(zip(times, angles, periods))



########## Pulse Repetition Interval ############ 
# Fixed PRI
# Stagger PRI
# Switched PRI
#Jitter PRI 

def fixed_pri(start_time, end_time, pri):
    """
    Generate fixed PRI pulses.
    
    :param start_time: Start time of the simulation (seconds)
    :param end_time: End time of the simulation (seconds)
    :param pri: Fixed PRI value (seconds)
    :return: Array of pulse times
    """
    return np.arange(start_time, end_time, pri)


def stagger_pri(start_time, end_time, pri_pattern):
    """
    Generate stagger PRI pulses.
    
    :param start_time: Start time of the simulation (seconds)
    :param end_time: End time of the simulation (seconds)
    :param pri_pattern: List of PRI values for the stagger pattern (seconds)
    :return: Array of pulse times
    """
    pulse_times = []
    current_time = start_time
    pri_index = 0
    
    while current_time < end_time:
        pulse_times.append(current_time)
        current_time += pri_pattern[pri_index]
        pri_index = (pri_index + 1) % len(pri_pattern)
    
    return np.array(pulse_times)


def switched_pri(start_time, end_time, pri_pattern, repetitions):
    """
    Generate switched PRI pulses.
    
    :param start_time: Start time of the simulation (seconds)
    :param end_time: End time of the simulation (seconds)
    :param pri_pattern: List of PRI values for the switched pattern (seconds)
    :param repetitions: List of repetition counts for each PRI value
    :return: Array of pulse times
    """
    pulse_times = []
    current_time = start_time
    
    while current_time < end_time:
        for pri, rep in zip(pri_pattern, repetitions):
            for _ in range(rep):
                if current_time >= end_time:
                    break
                pulse_times.append(current_time)
                current_time += pri
    
    return np.array(pulse_times)

# @numba_optimize()
# def jitter_pri(start_time, end_time, mean_pri, jitter_percentage):
#     """
#     Generate jitter PRI pulses.
    
#     :param start_time: Start time of the simulation (seconds)
#     :param end_time: End time of the simulation (seconds)
#     :param mean_pri: Mean PRI value (seconds)
#     :param jitter_percentage: Jitter as a percentage of mean PRI
#     :return: Array of pulse times
#     """
#     pulse_times = []
#     current_time = start_time
    
#     std_dev = mean_pri * (jitter_percentage / 100)
    
#     while current_time < end_time:
#         pulse_times.append(current_time)
#         jittered_pri = stats.truncnorm(
#             (0 - mean_pri) / std_dev,
#             (np.inf - mean_pri) / std_dev,
#             loc=mean_pri,
#             scale=std_dev
#         ).rvs()
#         current_time += jittered_pri
    
#     return np.array(pulse_times)


def jitter_pri(start_time, end_time, mean_pri, jitter_percentage):
    """
    Generate jitter PRI pulses using numpy's random number generation.
    """
    pulse_times = []
    current_time = start_time
    
    # Calculate standard deviation
    std_dev = mean_pri * (jitter_percentage / 100)
    
    while current_time < end_time:
        pulse_times.append(current_time)
        
        # Generate random jitter with clipping to ensure positive values
        jitter = np.random.normal(0, std_dev)
        jittered_pri = max(mean_pri + jitter, mean_pri * 0.1)  # Ensure PRI doesn't go below 10% of mean
        
        current_time += jittered_pri
    
    return np.array(pulse_times)

######### Frequency Functions 

#Doppler Shift in Frequency
def calculate_doppler_shift(transmitted_frequency, relative_velocity):
    """
    Calculate the Doppler shift in frequency based on relative velocity.
    
    Args:
        transmitted_frequency: Original transmitted frequency (with units)
        relative_velocity: Relative velocity between radar and target (with units)
    
    Returns:
        Doppler shift with appropriate units
    """
    # Convert to base units for calculation
    f = transmitted_frequency.to(ureg.Hz).magnitude
    v = relative_velocity.to(ureg.meter / ureg.second).magnitude
    c = 299792458  # Speed of light in m/s
    
    doppler_shift = -2 * f * v / c
    return doppler_shift * ureg.Hz

def calculate_relative_velocity(radar_position, radar_velocity, sensor_position, sensor_velocity):
    """
    Calculate the relative velocity between radar and sensor along their line of sight.
    """
    # Convert positions and velocities to base units
    r_pos = np.array([radar_position[0].to(ureg.meter).magnitude, 
                     radar_position[1].to(ureg.meter).magnitude])
    r_vel = np.array([radar_velocity[0].to(ureg.meter/ureg.second).magnitude, 
                     radar_velocity[1].to(ureg.meter/ureg.second).magnitude])
    s_pos = np.array([sensor_position[0].to(ureg.meter).magnitude, 
                     sensor_position[1].to(ureg.meter).magnitude])
    s_vel = np.array([sensor_velocity[0].to(ureg.meter/ureg.second).magnitude, 
                     sensor_velocity[1].to(ureg.meter/ureg.second).magnitude])
    
    # Calculate unit vector pointing from radar to sensor
    displacement = s_pos - r_pos
    distance = np.linalg.norm(displacement)
    if distance == 0:
        return 0.0 * ureg.meter / ureg.second
    
    unit_vector = displacement / distance
    
    # Calculate relative velocity vector
    relative_velocity = s_vel - r_vel
    
    # Project relative velocity onto line of sight
    radial_velocity = np.dot(relative_velocity, unit_vector)
    
    return radial_velocity * ureg.meter / ureg.second

def apply_doppler_effect(measured_frequency, radar, sensor):
    """
    Apply Doppler effect to measured frequency based on relative motion.
    
    Args:
        measured_frequency: Base measured frequency (with units)
        radar: Radar object
        sensor: Sensor object
    
    Returns:
        Frequency with Doppler shift applied (with units)
    """
    # Calculate relative velocity
    rel_velocity = calculate_relative_velocity(
        radar.current_position,
        radar.velocity,
        sensor.current_position,
        sensor.velocity
    )
    
    # Calculate and apply Doppler shift
    doppler_shift = calculate_doppler_shift(measured_frequency, rel_velocity)
    return measured_frequency + doppler_shift
# Frequency functions

def fixed_frequency(start_time, end_time, frequency):
    """
    Generate fixed frequency values.
    
    :param start_time: Start time of the simulation (seconds)
    :param end_time: End time of the simulation (seconds)
    :param frequency: Fixed frequency value (Hz)
    :return: Array of frequency values
    """
    return np.full(int((end_time - start_time) / 0.001), frequency)  # Assuming 1ms intervals

def stagger_frequency(start_time, end_time, frequency_pattern):
    """
    Generate stagger frequency values.
    
    :param start_time: Start time of the simulation (seconds)
    :param end_time: End time of the simulation (seconds)
    :param frequency_pattern: List of frequency values for the stagger pattern (Hz)
    :return: Array of frequency values
    """
    num_values = int((end_time - start_time) / 0.001)  # Assuming 1ms intervals
    return np.tile(frequency_pattern, num_values // len(frequency_pattern) + 1)[:num_values]

def switched_frequency(start_time, end_time, frequency_pattern, repetitions):
    """
    Generate switched frequency values.
    
    :param start_time: Start time of the simulation (seconds)
    :param end_time: End time of the simulation (seconds)
    :param frequency_pattern: List of frequency values for the switched pattern (Hz)
    :param repetitions: List of repetition counts for each frequency value
    :return: Array of frequency values
    """
    frequencies = []
    for freq, rep in zip(frequency_pattern, repetitions):
        frequencies.extend([freq] * rep)
    num_values = int((end_time - start_time) / 0.001)  # Assuming 1ms intervals
    return np.tile(frequencies, num_values // len(frequencies) + 1)[:num_values]

def jitter_frequency(start_time, end_time, mean_frequency, jitter_percentage):
    """
    Generate jitter frequency values.
    
    :param start_time: Start time of the simulation (seconds)
    :param end_time: End time of the simulation (seconds)
    :param mean_frequency: Mean frequency value (Hz)
    :param jitter_percentage: Jitter as a percentage of mean frequency
    :return: Array of frequency values
    """
    num_values = int((end_time - start_time) / 0.001)  # Assuming 1ms intervals
    # print(mean_frequency)
    # print(jitter_percentage)
    # print(type(mean_frequency))
    # print(type(jitter_percentage))
    mean_frequency=float(mean_frequency)
    std_dev = mean_frequency * (jitter_percentage / 100)
    return stats.truncnorm(
        (0 - mean_frequency) / std_dev,
        (np.inf - mean_frequency) / std_dev,
        loc=mean_frequency,
        scale=std_dev
    ).rvs(size=num_values)


########### - Pulse Width Functions - ############
# Pulse width functions
def fixed_pulse_width(start_time, end_time, pulse_width):
    """
    Generate fixed pulse width values.
    
    :param start_time: Start time of the simulation (seconds)
    :param end_time: End time of the simulation (seconds)
    :param pulse_width: Fixed pulse width value (seconds)
    :return: Array of pulse width values
    """
    return np.full(int((end_time - start_time) / 0.001), pulse_width)  # Assuming 1ms intervals

def stagger_pulse_width(start_time, end_time, pulse_width_pattern):
    """
    Generate stagger pulse width values.
    
    :param start_time: Start time of the simulation (seconds)
    :param end_time: End time of the simulation (seconds)
    :param pulse_width_pattern: List of pulse width values for the stagger pattern (seconds)
    :return: Array of pulse width values
    """
    num_values = int((end_time - start_time) / 0.001)  # Assuming 1ms intervals
    return np.tile(pulse_width_pattern, num_values // len(pulse_width_pattern) + 1)[:num_values]

def switched_pulse_width(start_time, end_time, pulse_width_pattern, repetitions):
    """
    Generate switched pulse width values.
    
    :param start_time: Start time of the simulation (seconds)
    :param end_time: End time of the simulation (seconds)
    :param pulse_width_pattern: List of pulse width values for the switched pattern (seconds)
    :param repetitions: List of repetition counts for each pulse width value
    :return: Array of pulse width values
    """
    pulse_widths = []
    for pw, rep in zip(pulse_width_pattern, repetitions):
        pulse_widths.extend([pw] * rep)
    num_values = int((end_time - start_time) / 0.001)  # Assuming 1ms intervals
    return np.tile(pulse_widths, num_values // len(pulse_widths) + 1)[:num_values]

def jitter_pulse_width(start_time, end_time, mean_pulse_width, jitter_percentage):
    """
    Generate jitter pulse width values.
    
    :param start_time: Start time of the simulation (seconds)
    :param end_time: End time of the simulation (seconds)
    :param mean_pulse_width: Mean pulse width value (seconds)
    :param jitter_percentage: Jitter as a percentage of mean pulse width
    :return: Array of pulse width values
    """
    num_values = int((end_time - start_time) / 0.001)  # Assuming 1ms intervals
    std_dev = mean_pulse_width * (jitter_percentage / 100)
    return stats.truncnorm(
        (0 - mean_pulse_width) / std_dev,
        (np.inf - mean_pulse_width) / std_dev,
        loc=mean_pulse_width,
        scale=std_dev
    ).rvs(size=num_values)



######### - Radar Antenna Lobe Pattern - ###########
def sinc_lobe_pattern(theta, theta_ml, P_ml, P_bl):
    """
    Calculate the radar antenna lobe pattern using a modified sinc function.
    
    :param theta: Angle from the antenna boresight (in radians)
    :param theta_ml: Main lobe opening angle (in radians)
    :param P_ml: Radar power at main lobe (in dB)
    :param P_bl: Radar power at back lobe (in dB)
    :return: Power at the given angle (in dB)
    """
    # Convert inputs to appropriate units
    theta = theta.to(ureg.radian).magnitude
    theta_ml = theta_ml.to(ureg.radian).magnitude
    P_ml = P_ml.to(ureg.dB).magnitude
    P_bl = P_bl.to(ureg.dB).magnitude
    # print(f"theta: {theta}")
    # print(f"theta_ml: {theta_ml}")
    # Calculate x
    # Small value to avoid division by zero
    x = 0.443 * np.sin(theta) / np.sin(theta_ml / 2)
    # x = 0.443 * np.sin(theta) / np.sin(theta_ml / 2)
    # print(f"x: {x}")
    # Calculate P_theta based on the range of theta
    P_theta = np.zeros_like(theta)

    # For theta in [-pi/2, pi/2]
    mask1 = np.abs(theta) <= np.pi/2
    sinc = ma.masked_invalid(np.sin(np.pi * x[mask1]) / (np.pi * x[mask1]))
    P_theta[mask1] = 20 * ma.log10(ma.abs(sinc)) + P_ml

    # For theta > pi/2
    mask2 = theta > np.pi/2
    P_theta[mask2] = 20 * np.log10(np.abs(np.sin(np.pi * x[mask2]) / (np.pi * x[mask2]))) + P_ml + 2/np.pi * P_bl * (theta[mask2] - np.pi/2)

    # For theta < -pi/2
    mask3 = theta < -np.pi/2
    P_theta[mask3] = 20 * np.log10(np.abs(np.sin(np.pi * x[mask3]) / (np.pi * x[mask3]))) + P_ml + 2/np.pi * P_bl * (-theta[mask3] - np.pi/2)
    power=P_theta*ureg.dBm
    return power

