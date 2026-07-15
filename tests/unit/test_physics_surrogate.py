import pytest
import numpy as np
import pytensor.tensor as pt
import pytensor

def test_convex_emulator_gradients():
    try:
        from src.physics.convex_emulator import convex_emulator
    except ImportError:
        pytest.fail("convex_emulator not implemented yet")
        
    # Simulated building geometry inputs
    x = pt.dvector('x')
    
    # Run the emulator
    y = convex_emulator(x)
    
    # Calculate gradients
    grads = pt.grad(y, x)
    
    # Compile function to evaluate gradients
    f_grad = pytensor.function([x], grads)
    
    # Test with simulated data
    test_x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    calculated_grads = f_grad(test_x)
    
    # Assert valid, non-NaN gradients
    assert not np.any(np.isnan(calculated_grads)), "Gradients contain NaN values"
    assert not np.any(np.isinf(calculated_grads)), "Gradients contain Inf values"
