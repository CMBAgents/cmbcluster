from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union

# --- General Models ---

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = "healthy"

# --- Data Analysis Models ---

class DataGenerationRequest(BaseModel):
    """Request model for generating sample data."""
    data_type: str = Field(..., description="Type of data to generate.", examples=["Random Normal", "CMB Temperature Map", "Galaxy Survey", "Time Series"])
    n_points: int = Field(1000, gt=0, le=10000, description="Number of data points to generate.")

class DataGenerationResponse(BaseModel):
    """Response model for generated data."""
    data_type: str
    data: Any
    statistics: Optional[Dict[str, float]] = None
    message: str


class Galaxy(BaseModel):
    """Represents a single galaxy in the survey data."""
    ra: float = Field(..., description="Right Ascension")
    dec: float = Field(..., description="Declination")
    redshift: float = Field(..., description="Redshift value")


class GalaxyDataResponse(BaseModel):
    """Response model for the galaxy survey data endpoint."""
    data: List[Galaxy]


# --- Calculator Models ---

class BasicMathRequest(BaseModel):
    """Request model for basic calculator operations."""
    num1: float
    operation: str = Field(..., examples=["+", "-", "*", "/", "**", "log", "exp"])
    num2: Optional[float] = None # Optional for unary operations like log, exp

class CalculationResponse(BaseModel):
    """Response model for a calculation."""
    result: Union[float, str]

class ArrayCalculationRequest(BaseModel):
    """Request model for array operations."""
    size: int = Field(100, gt=0, le=5000)

class ArrayStatistics(BaseModel):
    """Statistics of a numerical array."""
    mean: float
    std_dev: float
    min: float
    max: float

class ArrayCalculationResponse(BaseModel):
    """Response model for array operations."""
    statistics: ArrayStatistics
    values_preview: List[float] # Preview of the first 100 values

# --- Cosmology Models ---

class CosmologyPlotResponse(BaseModel):
    """Response model for cosmology plot data."""
    plot_type: str
    x_values: List[float]
    y_values: List[float]
    x_label: str
    y_label: str
    title: str

# --- Notebook Models ---

class NotebookExecutionRequest(BaseModel):
    """Request model for executing code in the notebook."""
    code: str

class NotebookExecutionResponse(BaseModel):
    """Response model for notebook code execution."""
    status: str
    stdout: str
    stderr: str
    # Plots could be represented as base64 encoded strings or URLs
    plots: List[Any] = []
    message: str = "This endpoint is a placeholder and does not execute code."
