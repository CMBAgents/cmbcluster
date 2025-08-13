import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List

# --- Data Analysis Logic ---

def generate_data(data_type: str, n_points: int) -> Tuple[Any, Dict[str, float]]:
    """
    Generates different types of sample data based on user selection.
    Returns the data and optional statistics.
    """
    stats = {}
    if data_type == "Random Normal":
        data = np.random.randn(n_points)
        stats = {
            "mean": np.mean(data),
            "std": np.std(data),
            "min": np.min(data),
            "max": np.max(data)
        }
        return data.tolist(), stats

    elif data_type == "CMB Temperature Map":
        nside = 64
        npix = 12 * nside**2
        data = np.random.normal(0, 1e-5, npix)  # μK fluctuations
        return data.tolist(), {}

    elif data_type == "Galaxy Survey":
        n_gal = min(n_points, 5000)
        ra = np.random.uniform(0, 360, n_gal)
        dec = np.random.uniform(-90, 90, n_gal)
        z = np.random.exponential(0.3, n_gal)
        data = pd.DataFrame({'ra': ra, 'dec': dec, 'redshift': z})
        return data.to_dict(orient='records'), {}

    elif data_type == "Time Series":
        t = np.linspace(0, 10, n_points)
        signal = np.sin(2 * np.pi * t) + 0.1 * np.random.randn(n_points)
        data = pd.DataFrame({'time': t, 'signal': signal})
        return data.to_dict(orient='records'), {}

    raise ValueError(f"Unknown data type: {data_type}")

# --- Calculator Logic ---

def perform_basic_math(num1: float, operation: str, num2: float = None) -> float | str:
    """Performs a basic mathematical calculation."""
    try:
        if operation == "+":
            return num1 + num2
        elif operation == "-":
            return num1 - num2
        elif operation == "*":
            return num1 * num2
        elif operation == "/":
            if num2 == 0:
                return "Division by zero!"
            return num1 / num2
        elif operation == "**":
            return num1 ** num2
        elif operation == "log":
            if num1 <= 0:
                return "Invalid input for log"
            return np.log(num1)
        elif operation == "exp":
            return np.exp(num1)
        else:
            return "Invalid operation"
    except Exception as e:
        return f"Error: {str(e)}"

def perform_array_operations(size: int) -> Tuple[Dict[str, float], List[float]]:
    """Generates a random array and calculates its statistics."""
    arr = np.random.randn(size)
    stats = {
        "mean": np.mean(arr),
        "std_dev": np.std(arr),
        "min": np.min(arr),
        "max": np.max(arr),
    }
    preview = arr[:min(100, len(arr))].tolist()
    return stats, preview

# --- Cosmology Logic ---

def get_cmb_power_spectrum() -> Dict[str, Any]:
    """Simulates a CMB temperature power spectrum."""
    l = np.arange(2, 3000)
    # Simplified model: just the basic shape
    cl = 1e12 * np.exp(-(l - 200)**2 / (2 * 100**2)) / l**2
    y_values = l * (l + 1) * cl / (2 * np.pi)

    return {
        "plot_type": "CMB Power Spectrum",
        "x_values": l.tolist(),
        "y_values": y_values.tolist(),
        "x_label": "Multipole l",
        "y_label": "l(l+1)Cl/2pi [uK^2]",
        "title": "CMB Temperature Power Spectrum"
    }

def get_galaxy_correlation_function() -> Dict[str, Any]:
    """Simulates a galaxy two-point correlation function."""
    r = np.logspace(-1, 2, 50)  # Mpc/h
    xi = (r / 5)**(-1.8)  # Power law

    return {
        "plot_type": "Galaxy Two-Point Correlation Function",
        "x_values": r.tolist(),
        "y_values": xi.tolist(),
        "x_label": "r [Mpc/h]",
        "y_label": "xi(r)",
        "title": "Galaxy Two-Point Correlation Function"
    }
