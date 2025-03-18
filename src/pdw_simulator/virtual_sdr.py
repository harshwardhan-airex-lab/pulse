import numpy as np
class VirtualSDR:
    def __init__(self):
        """
        Initialize Virtual SDR with aggressive effects
        """
        self.adc_resolution = 12
        self.adc_sample_rate = 81.44e6
        self.noise_figure = 9
        self.freq_range = (70e6, 6e9)
        
        # Variation parameters
        self.amplitude_variation = 18.0    # 8 dB variation
        self.freq_variation = 20e6        # 20 MHz variation
        self.multipath_prob = 0.6        # 30% chance of multipath
        self.dropout_prob = 0.2           # 10% pulse dropouts
        self.collision_prob = 0.45        # 25% collision probability
        self.freq_drift_rate = 1e6        # 1 MHz/s drift rate
        
    def process_pdw_data(self, pdw_df):
        """Process PDW data with realistic effects"""
        processed_df = pdw_df.copy()
        processed_df = processed_df.sort_values('Time').reset_index(drop=True)
        
        # 1. First apply dropouts (before other effects)
        dropout_mask = np.random.random(len(processed_df)) >= self.dropout_prob
        processed_df = processed_df[dropout_mask].reset_index(drop=True)
        
        # Get time array after dropouts
        time_array = processed_df['Time'].values
        n_samples = len(processed_df)
        
        # 2. Amplitude variations
        processed_df['Amplitude'] += np.random.normal(0, self.amplitude_variation, n_samples)
        
        # 3. Frequency variations with drift
        freq_drift = self.freq_drift_rate * time_array * np.sin(2 * np.pi * 0.1 * time_array)
        processed_df['Frequency'] += freq_drift
        processed_df['Frequency'] += np.random.normal(0, self.freq_variation, n_samples)
        
        # 4. Multipath effects
        multipath_mask = np.random.random(n_samples) < self.multipath_prob
        processed_df.loc[multipath_mask, 'Amplitude'] += np.random.uniform(-12, -3, sum(multipath_mask))
        processed_df.loc[multipath_mask, 'PulseWidth'] *= np.random.uniform(1.2, 1.8, sum(multipath_mask))
        
        # 5. Pulse collisions
        for i in range(n_samples-1):
            if np.random.random() < self.collision_prob:
                collision_window = min(3, n_samples - i)
                processed_df.iloc[i:i+collision_window, processed_df.columns.get_loc('Amplitude')] *= np.random.uniform(0.5, 1.5, collision_window)
                processed_df.iloc[i:i+collision_window, processed_df.columns.get_loc('Frequency')] += np.random.normal(0, self.freq_variation * 2, collision_window)
                processed_df.iloc[i:i+collision_window, processed_df.columns.get_loc('PulseWidth')] *= np.random.uniform(0.7, 1.3, collision_window)
        
        # 6. Signal fading
        fading_mask = np.random.random(n_samples) < 0.2
        processed_df.loc[fading_mask, 'Amplitude'] -= np.random.uniform(5, 15, sum(fading_mask))
        
        # 7. Timing jitter
        processed_df['TOA'] += np.random.normal(0, 5e-7, n_samples)
        
        # 8. AOA variations
        systematic_error = 3 * np.sin(2 * np.pi * 0.05 * time_array)
        processed_df['AOA'] += systematic_error
        processed_df['AOA'] += np.random.normal(0, 5.0, n_samples)
        
        # 9. Receiver effects
        max_power = -20  # dBm
        noise_floor = -85  # dBm
        
        # Saturation effects
        near_saturation = processed_df['Amplitude'] > (max_power - 10)
        processed_df.loc[near_saturation, 'Amplitude'] = max_power - (10 * np.exp(-(processed_df.loc[near_saturation, 'Amplitude'] - max_power + 10)/5))
        
        # Noise floor
        noise_mask = processed_df['Amplitude'] < noise_floor
        processed_df.loc[noise_mask, 'Amplitude'] = noise_floor + np.random.exponential(2, sum(noise_mask))
        
        # 10. Intermodulation (only if we have enough samples)
        if n_samples > 1:
            intermod_mask = np.random.random(n_samples) < 0.15
            intermod_idx = np.where(intermod_mask)[0]
            valid_idx = intermod_idx[intermod_idx > 0]
            if len(valid_idx) > 0:
                processed_df.loc[valid_idx, 'Frequency'] = (3 * processed_df.loc[valid_idx-1, 'Frequency'].values - 
                                                          2 * processed_df.loc[valid_idx, 'Frequency'].values)/2
                processed_df.loc[valid_idx, 'Amplitude'] -= np.random.uniform(10, 20, len(valid_idx))
        
        return processed_df