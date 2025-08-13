from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict

from ..auth import get_current_user
from . import logic
from . import models

router = APIRouter(
    prefix="/science",
    tags=["Scientific Computing"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/health", response_model=models.HealthResponse)
async def health_check():
    """Health check for the scientific computing service."""
    return models.HealthResponse(status="healthy")

@router.post("/analysis/generate", response_model=models.DataGenerationResponse)
async def generate_data(request: models.DataGenerationRequest):
    """Generate various types of scientific data."""
    try:
        data, stats = logic.generate_data(request.data_type, request.n_points)
        return models.DataGenerationResponse(
            data_type=request.data_type,
            data=data,
            statistics=stats,
            message=f"Successfully generated {request.n_points} points of {request.data_type} data."
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@router.post("/calculator/basic", response_model=models.CalculationResponse)
async def basic_math(request: models.BasicMathRequest):
    """Perform basic mathematical operations."""
    result = logic.perform_basic_math(request.num1, request.operation, request.num2)
    if isinstance(result, str) and ("Error" in result or "zero" in result):
        raise HTTPException(status_code=400, detail=result)
    return models.CalculationResponse(result=result)

@router.post("/calculator/array", response_model=models.ArrayCalculationResponse)
async def array_operations(request: models.ArrayCalculationRequest):
    """Generate a random array and return its statistics."""
    stats, preview = logic.perform_array_operations(request.size)
    return models.ArrayCalculationResponse(
        statistics=models.ArrayStatistics(**stats),
        values_preview=preview
    )

@router.get("/cosmology/power-spectrum", response_model=models.CosmologyPlotResponse)
async def get_power_spectrum():
    """Get data for a simulated CMB power spectrum plot."""
    plot_data = logic.get_cmb_power_spectrum()
    return models.CosmologyPlotResponse(**plot_data)

@router.get("/cosmology/correlation-function", response_model=models.CosmologyPlotResponse)
async def get_correlation_function():
    """Get data for a simulated galaxy correlation function plot."""
    plot_data = logic.get_galaxy_correlation_function()
    return models.CosmologyPlotResponse(**plot_data)

@router.post("/notebook/execute", response_model=models.NotebookExecutionResponse)
async def execute_notebook_code(request: models.NotebookExecutionRequest):
    """
    Placeholder for a secure code execution endpoint.
    WARNING: This endpoint is a placeholder and does not execute code for security reasons.
    A secure, sandboxed environment is required for this functionality.
    """
    return models.NotebookExecutionResponse(
        status="placeholder",
        stdout="",
        stderr="",
        message="This endpoint is a placeholder and does not execute code for security reasons."
    )
