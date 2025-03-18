# PULSE: Python Unified Library for Sensor Emulation

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

PULSE is a comprehensive Python library for synthetic sensor data generation, developed jointly by Zenteiq Aitech Innovations Private Limited and the AiREX (AI for Research and Engineering eXcellence) Lab at Indian Institute of Science, Bangalore. It provides a unified interface for simulating realistic datasets from various sensors and radars across multiple domains.

## Overview

PULSE enables developers, data scientists, and researchers to generate realistic sensor data for:

- Testing algorithms
- Validating data pipelines
- Prototyping IoT applications
- Simulating sensor networks
- Training and testing ML models

without the need for physical hardware.

## Features

- **Comprehensive Sensor Coverage**: Simulate data from dozens of sensor types across multiple domains
- **Configurable Parameters**: Adjustable settings for noise levels, ranges, and frequencies
- **Time-Series Generation**: Generate continuous or burst-based time-series data
- **Synthetic Anomalies**: Inject realistic anomalies for testing
- **Easy Integration**: Simple Python API for quick implementation
- **Error Modeling**: Support for various error models including Constant, Linear, Sinusoidal, Gaussian, and Uniform
- **High-Performance Computing**: Optimized numerical computations using JAX and NumPy

## Project Structure

```
pulse_pdw/
├── src/
│   └── pulse/
│       ├── __init__.py
│       ├── core/
│       │   └── pdw_simulator/
│       │       ├── __init__.py
│       │       ├── main.py               # Core simulation execution
│       │       ├── models.py             # Core classes (Scenario, Radar, Sensor)
│       │       ├── radar_properties.py   # Radar-specific functions
│       │       ├── sensor_properties.py  # Sensor-specific functions
│       │       └── scenario_geometry.py  # Geometry calculations
│       └── sensors/
│           ├── air/
│           ├── sea/
│           ├── ground/
│           └── infrastructure/
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Test fixtures and configuration
│   ├── test_models.py           # Tests for core classes
│   ├── test_integration.py      # Integration tests
│   └── fixtures/
│       └── test_config.yaml     # Test configuration data
│
├── apps/
│   └── app.py            # Streamlit web interface
│
├── docs/
│   ├── README.md               # Package documentation
│   ├── API.md                  # API documentation
│   └── examples/
│       └── simulations.md      # Usage examples
│
├── examples/
│   └── basic_simulation.py     # Example scripts
│
├── LICENSE
├── README.md
├── pyproject.toml
├── pytest.ini
└── requirements.txt
```

## Current Implementation

The current version includes:

### PDW (Pulse Descriptor Word) Simulator

The PDW Simulator is a sophisticated module for modeling radar-sensor interactions. It includes:

- **Scenario Management**: Controls simulation environment and time progression
- **Radar Properties**:
  - Pulse generation patterns (Fixed, Stagger, Switched, Jitter)
  - Frequency management
  - Pulse width control
  - Antenna lobe patterns
  - Rotation patterns
- **Sensor Properties**:
  - Detection probability models
  - Measurement error models
  - Parameter measurements (TOA, Frequency, Amplitude, etc.)
- **Geometry Calculations**:
  - Position and trajectory calculations
  - Unit management using Pint

## Installation

### Development Setup using Conda

1. Create a new conda environment:

```bash
conda create -n pulse_env python=3.12
conda activate pulse_env
```

2. Install core dependencies:

```bash
conda install numpy scipy pandas streamlit pyyaml h5py plotly
conda install -c conda-forge pint
```

3. Install in development mode:

```bash
pip install -e .
```

## Quick Start

### To run using Streamlit User Interface

```bash
streamlit run apps/app.py
```

## Configuration (Optional)

To set custom Parameters,create a `config.yaml` file in your working directory:

```yaml
scenario:
  start_time: 0
  end_time: 10
  time_step: 0.1

radars:
  - name: "Radar1"
    start_position: [0, 0]
    rotation_type: "constant"
    rotation_params:
      t0: 0
      alpha0: 0
      T_rot: 4
    pri_type: "fixed"
    pri_params:
      pri: 0.001

sensors:
  - name: "Sensor1"
    start_position: [1000, 1000]
    error_model: "gaussian"
    error_params:
      mean: 0
      std: 0.1
```

## Output Format

The simulator generates data with the following fields:

- Time: Simulation time
- SensorID: Identifier of the detecting sensor
- RadarID: Identifier of the detected radar
- TOA: Time of Arrival
- Amplitude: Signal amplitude
- Frequency: Signal frequency
- PulseWidth: Pulse width
- AOA: Angle of Arrival

## Documentation

Detailed documentation is available at [docs link placeholder]. This includes:

- API Reference
- Usage Examples
- Parameter Configuration
- Simulation Tutorials

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on:

- Code of Conduct
- Development Process
- Pull Request Protocol
- Testing Requirements

To contribute:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Testing

```bash
pytest tests/
```

## Features

- [x] Improved Visualization using plotly
- [x] Support for HDF5 data format
- [x] Doppler Shift & Enhanced Frequency Measurement using FFT Interpolation
- [x] Valid Data Ranges 

## Upcoming Features

- [ ] GPU Support & High Performance Computing
- [ ] Additional sensor types and domains
- [ ] Real-time simulation capabilities
- [ ] Distributed computing support

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Citation

If you use PULSE in your research, please cite:

```bibtex
@software{pulse2025,
  title = {PULSE: Python Unified Library for Sensor Emulation},
  author = {{Zenteiq Aitech Innovations} and {AiREX Lab}},
  year = {2025},
  url = {https://github.com/zenoxml/pulse}
}
```

## Official Partners

- [**ARTPARK**](https://artpark.in) (AI & Robotics Technology Park) at IISc

## Contact

- GitHub Issues: [https://github.com/zenoxml/pulse/issues](https://github.com/zenoxml/pulse/issues)
- Email: contact@scirex.org

## Acknowledgments

- Zenteiq Aitech Innovations Private Limited
- AiREX Lab at Indian Institute of Science, Bangalore
