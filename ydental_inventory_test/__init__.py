from . import models
from . import tests


def pre_init_hook(env):
    from .models.adapter import guard
    guard(env)
