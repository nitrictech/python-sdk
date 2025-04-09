#
# Copyright (c) 2021 Nitric Technologies Pty Ltd.
#
# This file is part of Nitric Python 3 SDK.
# See https://github.com/nitrictech/python-sdk for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from enum import Enum
from typing import Callable, List, TypeVar, Optional

# The environment variable key that will be used to determine the current Nitric lifecycle/executing environment
NITRIC_ENVIRONMENT = 'NITRIC_ENVIRONMENT'


# Possible nitric execution environments
class LifecycleStage(Enum):
    """Represents the different stages of the Nitric application lifecycle."""

    # Local development run (using nitric run/start)
    LOCAL_RUN = 'run'

    # Local development requirements building/collection (using nitric up)
    BUILD = 'build'

    # When the code is running in a deployed environment
    CLOUD = 'cloud'


def get_current_lifecycle() -> LifecycleStage:
    """
    Get the current lifecycle stage from the environment variable.

    Returns:
        The current lifecycle stage.

    Raises:
        ValueError: If the NITRIC_ENVIRONMENT environment variable is not set or is invalid.
    """
    lifecycle = os.environ.get(NITRIC_ENVIRONMENT)

    if not lifecycle or lifecycle not in [stage.value for stage in LifecycleStage]:
        raise ValueError(
            f"Unable to determine the current Nitric lifecycle, please ensure the {NITRIC_ENVIRONMENT} "
            "environment variable is set"
        )

    return LifecycleStage(lifecycle)


def is_in_lifecycle(stages: List[LifecycleStage]) -> bool:
    """
    Check if the current environment is one of the provided stages.

    Args:
        stages: The stages to check against.

    Returns:
        True if the current stage is in the provided stages, False otherwise.
    """
    current_stage = get_current_lifecycle()
    return current_stage in stages


T = TypeVar('T')


def when_in_lifecycles(stages: List[LifecycleStage], callback: Callable[[], T]) -> Optional[T]:
    """
    If the current environment is one of the provided stages, execute the provided callback.

    Args:
        stages: The stages to check against.
        callback: The callback to execute if the current stage is in the provided stages.

    Returns:
        The result of the callback if executed, None otherwise.
    """
    if is_in_lifecycle(stages):
        return callback()
    return None


def when_running(callback: Callable[[], T]) -> Optional[T]:
    """
    If the current environment is running (local or cloud), execute the provided callback.

    Args:
        callback: The callback to execute if the current stage is running.

    Returns:
        The result of the callback if executed, None otherwise.
    """
    return when_in_lifecycles([LifecycleStage.LOCAL_RUN, LifecycleStage.CLOUD], callback)


def when_collecting(callback: Callable[[], T]) -> Optional[T]:
    """
    If the current environment is collecting requirements, execute the provided callback.

    Args:
        callback: The callback to execute if the current stage is collecting.

    Returns:
        The result of the callback if executed, None otherwise.
    """
    return when_in_lifecycles([LifecycleStage.BUILD], callback)


def is_running() -> bool:
    """
    Check if the current lifecycle is running the app.

    Returns:
        True if the current stage is running, False otherwise.
    """
    return is_in_lifecycle([LifecycleStage.LOCAL_RUN, LifecycleStage.CLOUD])


def is_collecting() -> bool:
    """
    Check if the current lifecycle is collecting application requirements.

    Returns:
        True if the current stage is collecting, False otherwise.
    """
    return is_in_lifecycle([LifecycleStage.BUILD])


# Create a class to match the Node SDK's export style
class Lifecycle:
    """Lifecycle utilities for Nitric applications."""

    @staticmethod
    def lifecycle_is(stages: List[LifecycleStage]) -> bool:
        """
        Check if the current environment is one of the provided stages.

        Args:
            stages: The stages to check against.

        Returns:
            True if the current stage is in the provided stages, False otherwise.
        """
        return is_in_lifecycle(stages)

    @staticmethod
    def is_collecting() -> bool:
        """
        Check if the current lifecycle is collecting application requirements.

        Returns:
            True if the current stage is collecting, False otherwise.
        """
        return is_collecting()

    @staticmethod
    def is_running() -> bool:
        """
        Check if the current lifecycle is running the app.

        Returns:
            True if the current stage is running, False otherwise.
        """
        return is_running()

    @staticmethod
    def when(stages: List[LifecycleStage], callback: Callable[[], T]) -> Optional[T]:
        """
        If the current environment is one of the provided stages, execute the provided callback.

        Args:
            stages: The stages to check against.
            callback: The callback to execute if the current stage is in the provided stages.

        Returns:
            The result of the callback if executed, None otherwise.
        """
        return when_in_lifecycles(stages, callback)

    @staticmethod
    def when_collecting(callback: Callable[[], T]) -> Optional[T]:
        """
        If the current environment is collecting requirements, execute the provided callback.

        Args:
            callback: The callback to execute if the current stage is collecting.

        Returns:
            The result of the callback if executed, None otherwise.
        """
        return when_collecting(callback)

    @staticmethod
    def when_running(callback: Callable[[], T]) -> Optional[T]:
        """
        If the current environment is running (local or cloud), execute the provided callback.

        Args:
            callback: The callback to execute if the current stage is running.

        Returns:
            The result of the callback if executed, None otherwise.
        """
        return when_running(callback)
