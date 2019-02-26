import asyncio

from datetime import timedelta

from typing import Callable

import logger
from mutations.exceptions import ReconciliationError

__author__ = "Noah Hummel"
log = logger.get(__name__)


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
    log.debug(f"Checking {result.kind} "
              f"{result.metadata.namespace}/{result.metadata.name}: "
              f"{predicate.__name__}? {retval}")
    return retval


def wait_for_reconciliation(predicate: Callable, timeout: timedelta,
                            fn: Callable, *args, **kwargs):
    asyncio.run(_wait_for_reconciliation(predicate, timeout, fn, *args,
                                         **kwargs))


async def _wait_for_reconciliation(predicate: Callable, timeout: timedelta,
                                   fn: Callable, *args, **kwargs):
    async def _reconciled():
        done = False
        while not done:
            done = check_resource(predicate, fn, *args, **kwargs)
            await asyncio.sleep(3, 6)

    try:
        log.debug(f"Waiting for cluster state to reconcile "
                  f"({timeout.seconds}s)...")
        await asyncio.wait_for(_reconciled(), timeout=timeout.seconds)
    except asyncio.TimeoutError:
        log.debug(f"Cluster state not reconciled after {timeout.seconds}s.")
        raise ReconciliationError()