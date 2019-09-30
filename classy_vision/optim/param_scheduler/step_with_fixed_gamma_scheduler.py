#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from typing import Any, Dict

from . import ClassyParamScheduler, UpdateInterval, register_param_scheduler
from .step_scheduler import StepParamScheduler


@register_param_scheduler("step_with_fixed_gamma")
class StepWithFixedGammaParamScheduler(ClassyParamScheduler):
    """
    Decays the param value by gamma at equal number of steps so as to have the
    specified total number of decays.
    Can also specify an optional warm up period where the lr is gradually
    ramped up to the initial lr.

    Example:
      base_lr: 0.1
      gamma: 0.1
      num_decays: 3
      num_epochs: 120

    Then the param value will be 0.1 for epochs 0-29, 0.01 for
    epochs 30-59, 0.001 for epoch 60-89, 0.0001 for epochs 90-119.
    """

    @classmethod
    def from_config(cls, config: Dict[str, Any]):
        for key in ["base_lr", "gamma", "num_decays", "num_epochs"]:
            assert key in config, f"Step with fixed decay scheduler requires: {key}"
        for key in ["base_lr", "gamma"]:
            assert (
                isinstance(config[key], (int, float)) and config[key] > 0
            ), f"{key} must be a positive number"
        for key in ["num_decays", "num_epochs"]:
            assert (
                isinstance(config[key], int) and config[key] > 0
            ), f"{key} must be a positive integer"

        warmup = None
        if "warmup" in config:
            assert (
                "epochs" in config["warmup"] and "init_lr" in config["warmup"]
            ), "warmup config requires two keys: 'epoch' and 'init_lr'"
            warmup = StepParamScheduler.Warmup(**config["warmup"])

        return cls(
            base_lr=config["base_lr"],
            num_decays=config["num_decays"],
            gamma=config["gamma"],
            num_epochs=config["num_epochs"],
            warmup=warmup,
        )

    def __init__(self, base_lr, num_decays, gamma, num_epochs, warmup=None):
        super().__init__()

        self.base_lr = base_lr
        self.num_decays = num_decays
        self.gamma = gamma
        self.num_epochs = num_epochs
        values = [base_lr]
        for _ in range(num_decays):
            values.append(values[-1] * gamma)

        self._step_param_scheduler = StepParamScheduler(
            num_epochs=num_epochs, values=values, warmup=warmup
        )

        # make this a STEP scheduler
        self.update_interval = UpdateInterval.STEP

    def __call__(self, where: float) -> float:
        return self._step_param_scheduler(where)