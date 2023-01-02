__all__ = ["init_nodes", "init_cache", "bind", "vectorize", "gradvalues", "jit"]

from ..core import Function, VarCollection, Vectorize, GradValues, Jit, _
from .variables import NodeVar

import functools
import contextlib


def bind(*arg_vars, **kwarg_vars):
    """Decorator to bind a function to a set of variables."""

    def decorator(f):
        vc = functools.reduce(
            lambda x, y: x + y, (m.vars() for m in arg_vars), VarCollection()
        ) + functools.reduce(
            lambda x, y: x + y,
            (m.vars().rename(k) for k, m in kwarg_vars.items()),
            VarCollection(),
        )

        def wrapper(*args, **kwargs):
            try:
                _original = {k: f.__globals__.get(k, None) for k in kwarg_vars.keys()}
                f.__globals__.update(kwarg_vars)
                return f(*args, **kwargs)
            finally:
                f.__globals__.update(_original)

        return Function(wrapper, vc)

    return decorator


@contextlib.contextmanager
def init_nodes(model, *args, filter=_(NodeVar), in_axis=None, out_axis=None, **kwargs):
    if len(args):
        if in_axis is None:
            in_axis = (0,) * len(args)
        if out_axis is None:
            out_axis = (0,)
        yield Vectorize(bind(model)(model.__call__), filter, in_axis, out_axis)(*args, **kwargs)
    else:
        yield

    model.clear_cache()
    model.clear_nodes()


@contextlib.contextmanager
def init_cache(model):
    model.clear_cache()
    yield


def vectorize(*args, **kwargs):
    def decorator(f):
        return Vectorize(f, *args, **kwargs)

    return decorator


def gradvalues(*args, **kwargs):
    def decorator(f):
        return GradValues(f, *args, **kwargs)

    return decorator


def jit(*args, static_argnums=None, **kwargs):
    def decorator(f):
        return Jit(f, *args, **kwargs, static_argnums=static_argnums)

    return decorator
