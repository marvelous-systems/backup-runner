import asyncio

from datetime import timedelta

from typing import Callable, Tuple, List, Dict, Coroutine

import logger
from mutations.exceptions import ReconciliationError

__author__ = "Noah Hummel"
log = logger.get(__name__)


Predicate = Callable


def check_resource(predicate: Callable, fn: Callable, *args, **kwargs) -> bool:
    """Retrieves a k8s API resource, applies predicate to it and returns result.

    Args:
        predicate:
            A function accepting the resource fetched by fn, should return
            a bool.
        fn: Kubernetes API function.
        *args: Arguments for fn.
        **kwargs: Keyword arguments for fn.

    Returns:
        Whether the fetched resource satisfies the given predicate.
    """
    result = fn(*args, **kwargs)
    retval = predicate(result)
    try:  # debug print only works for k8s resources
        log.debug(f"Checking {result.kind} "
                  f"{result.metadata.namespace}/{result.metadata.name}: "
                  f"{predicate.__name__}? {retval}")
    except Exception: pass
    return retval


def wait_for_reconciliation(predicate: Callable, timeout: timedelta,
                            fn: Callable, *args, **kwargs):
    asyncio.run(_wait_for_reconciliation(predicate, timeout, fn, *args,
                                         **kwargs))


def _reconciled_fn(predicate,fn, *args, **kwargs) -> Coroutine:
    async def _reconciled():
        done = False
        while not done:
            done = check_resource(predicate, fn, *args, **kwargs)
            await asyncio.sleep(3, 6)
    return _reconciled()


async def _wait_for_reconciliation(predicate: Callable, timeout: timedelta,
                                   fn: Callable, *args, **kwargs):
    try:
        log.debug(f"Waiting for cluster state to reconcile "
                  f"({timeout.seconds}s)...")
        await asyncio.wait_for(_reconciled_fn(predicate, fn, *args, **kwargs),
                               timeout=timeout.seconds)
    except asyncio.TimeoutError:
        log.debug(f"Cluster state not reconciled after {timeout.seconds}s.")
        raise ReconciliationError()


def wait_for_total_reconciliation(timeout: timedelta,
                                  *args: Tuple[Predicate, Callable, List, Dict]):
    asyncio.run(_wait_for_total_reconciliation(timeout, *args))


async def _wait_for_total_reconciliation(timeout: timedelta,
                                  *args: Tuple[Predicate, Callable, List, Dict]):
    tasks = []
    for state in args:
        state = list(state)  # tuples are immutable
        if len(state) < 3:
            state.append([])  # no *args
        if len(state) < 4:
            state.append(dict())  # no **kwargs

        tasks.append(_reconciled_fn(state[0], state[1], *state[2], **state[3]))

    awaitable = asyncio.gather(*tasks)
    try:
        await asyncio.wait_for(awaitable, timeout=timeout.seconds)
    except TimeoutError:
        raise ReconciliationError
