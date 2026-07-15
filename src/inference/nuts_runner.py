import pymc as pm

def run_inference(model, tune=1000, draws=1000):
    """
    Executes the NUTS sampler on the joint model.
    """
    with model:
        # We explicitly enforce the NUTS sampler to test the Vector-Jacobian Products
        # and measure R-hat/divergences
        idata = pm.sample(
            draws=draws, 
            tune=tune, 
            step=pm.NUTS(), 
            return_inferencedata=True, 
            progressbar=False,
            cores=1, # single core for simple toy pilot logging
            chains=2 # minimum 2 chains for R-hat calculation
        )
    return idata
