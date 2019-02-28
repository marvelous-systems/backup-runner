import asyncio
import random

from datetime import timedelta

from typing import Callable, Tuple, List, Dict, Coroutine, Union

import logger
from mutations.exceptions import ReconciliationError

__author__ = "Noah Hummel"
log = logger.get(__name__)


Predicate = Callable


def check_resource(predicate: Predicate, fn: Callable, *args, **kwargs) -> bool:
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
    try:
        log.debug(f"Checking {result.kind} "
                  f"{result.metadata.namespace}/{result.metadata.name}: "
                  f"{predicate.__name__}? {retval}")
    except AttributeError:  # debug print only works for k8s resources
        pass
    return retval


def _poll_resource(predicate: Predicate, fn: Callable, *args, **kwargs) \
        -> Coroutine:
    """Polls fn in random intervals until fn's return satisfies a predicate.

    Args:
        predicate: Function Any -> bool
        fn: Any function.
        *args: Positional args for fn.
        **kwargs: Key word args for fn.

    Returns:
        Coroutine which polls fn in random intervals and sleeps in between.
        The Coroutine halts if predicate is satisfied by fn's return.
    """
    async def _reconciled():
        done = False
        while not done:
            done = check_resource(predicate, fn, *args, **kwargs)
            await asyncio.sleep(random.uniform(3, 6))
    return _reconciled()


def wait_for_reconciliation_blocking(predicate: Predicate, timeout: timedelta,
                                     fn: Callable, *args, **kwargs):
    """Wait until fn's return satisfies predicate or timeout is reached.

    Fn is polled by executing it with *args and **kwargs in random intervals
    and testing its return with predicate. Blocks until either the predicate is
    satisfied or the operation is cancelled by a timeout.

    Args:
        timeout: Time to wait for predicate to be satisfied.
        predicate: Function Any -> bool
        fn: Any function.
        *args: Positional args for fn.
        **kwargs: Key word args for fn.

    Raises:
        ReconciliationError:
            If the predicate was not satisfied within timeout.
    """
    asyncio.run(wait_for_reconciliation(predicate, timeout, fn, *args,
                                        **kwargs))


async def wait_for_reconciliation(predicate: Callable, timeout: timedelta,
                                  fn: Callable, *args, **kwargs):
    """Wait until fn's return satisfies predicate or timeout is reached.

    Fn is polled by executing it with *args and **kwargs in random intervals
    and testing its return with predicate. Waits until either the predicate is
    satisfied or the operation is cancelled by a timeout.

    Args:
        timeout: Time to wait for predicate to be satisfied.
        predicate: Function Any -> bool
        fn: Any function.
        *args: Positional args for fn.
        **kwargs: Key word args for fn.

    Raises:
        ReconciliationError:
            If the predicate was not satisfied within timeout.
    """
    try:
        log.debug(f"Waiting for cluster state to reconcile "
                  f"({timeout.seconds}s)...")
        await asyncio.wait_for(_poll_resource(predicate, fn, *args, **kwargs),
                               timeout=timeout.seconds)
    except asyncio.TimeoutError:
        log.debug(f"Cluster state not reconciled after {timeout.seconds}s.")
        raise ReconciliationError()


def wait_for_total_reconciliation_blocking(timeout: timedelta,
                                           *args: Union[
                                               Tuple[Predicate, Callable],
                                               Tuple[Predicate, Callable, List],
                                               Tuple[Predicate, Callable, Dict],
                                               Tuple[Predicate, Callable, List,
                                                     Dict]
                                           ]):
    """Waits until multiple fns satisfy some predicates.

    Takes a list of parameters for wait_for_reconciliation as Tuples and waits
    until wither all of them reconcile or a timeout is reached.

    Args:
        timeout: Time to wait for predicate to be satisfied.
        *args: List of parameters for wait_for_reconciliation as Tuples.

    Raises:
        ReconciliationError:
            If the predicates were not satisfied within timeout.
    """
    asyncio.run(wait_for_total_reconciliation(timeout, *args))


async def wait_for_total_reconciliation(timeout: timedelta,
                                        *args: Union[
                                            Tuple[Predicate, Callable],
                                            Tuple[Predicate, Callable, List],
                                            Tuple[Predicate, Callable, Dict],
                                            Tuple[Predicate, Callable, List,
                                                  Dict]
                                        ]):
    """Waits until multiple fns satisfy some predicates.

    Takes a list of parameters for wait_for_reconciliation as Tuples and waits
    until wither all of them reconcile or a timeout is reached.

    Args:
        timeout: Time to wait for predicate to be satisfied.
        *args: List of parameters for wait_for_reconciliation as Tuples.

    Raises:
        ReconciliationError:
            If the predicates were not satisfied within timeout.
    """
    tasks = []
    for poll_args in args:
        poll_args = list(poll_args)  # tuples are immutable
        list_arg = [] if len(poll_args) < 4 else poll_args[2]
        kw_arg = dict() if len(poll_args) < 4 else poll_args[3]

        if len(poll_args) == 3:
            if type(poll_args[2]) is dict:
                kw_arg = poll_args[2]
            elif type(poll_args[2]) is list:
                list_arg = poll_args[2]

        tasks.append(_poll_resource(poll_args[0], poll_args[1], *list_arg,
                                    **kw_arg))

    poll_all = asyncio.gather(*tasks)
    try:
        await asyncio.wait_for(poll_all, timeout=timeout.seconds)
    except TimeoutError:
        raise ReconciliationError
