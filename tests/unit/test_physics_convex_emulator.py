import pytensor.tensor as pt
import numpy as np
import pytensor
from src.physics.convex_emulator import convex_emulator

def test_convex_emulator():
    x = pt.dvector('x')
    y = convex_emulator(x)
    f = pytensor.function([x], y)
    
    val = np.array([1.0, 2.0])
    # 0.5 * 1^2 + 1 = 1.5
    # 0.5 * 2^2 + 2 = 4.0
    # sum = 5.5
    assert np.isclose(f(val), 5.5)
