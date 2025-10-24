from .OpsRamp import OpsRamp

__all__ = ['OpsRamp']

import sys
class CallableModule(sys.modules[__name__].__class__):
    def __call__(self, *args, **kwargs):
        return OpsRamp(*args, **kwargs)

sys.modules[__name__].__class__ = CallableModule