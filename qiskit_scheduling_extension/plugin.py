# This code is part of Qiskit.
#
# (C) Copyright IBM 2023
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Qiskit scheduling extension transpiler pass plugins."""

from qiskit.transpiler.preset_passmanagers.plugin import PassManagerStagePlugin
from qiskit.transpiler.passes import (
    PulseGates,
    TimeUnitConversion,
    InstructionDurationCheck,
    ConstrainedReschedule,
    ValidatePulseGates,
    PadDelay,
)
from qiskit.transpiler import PassManager

from qiskit_scheduling_extension.compact import CompactScheduleAnalysis


class CompactSchedulingPlugin(PassManagerStagePlugin):
    """CompactScheduling routing stage plugin."""

    def pass_manager(self, pass_manager_config, optimization_level):
        """Return the plugin pass manager."""
        pm = PassManager()
        inst_map = pass_manager_config.inst_map
        target = pass_manager_config.target
        instruction_durations = pass_manager_config.instruction_durations
        timing_constraints = pass_manager_config.timing_constraints
        if inst_map and inst_map.has_custom_gate():
            pm.append(PulseGates(inst_map=inst_map, target=target))
        # Do scheduling after unit conversion.
        pm.append(TimeUnitConversion(instruction_durations, target=target))
        pm.append(CompactScheduleAnalysis(instruction_durations, target=target))
        if (
            timing_constraints.granularity != 1
            or timing_constraints.min_length != 1
            or timing_constraints.acquire_alignment != 1
            or timing_constraints.pulse_alignment != 1
        ):
            # Run alignment analysis regardless of scheduling.

            def _require_alignment(property_set):
                return property_set["reschedule_required"]

            pm.append(
                InstructionDurationCheck(
                    acquire_alignment=timing_constraints.acquire_alignment,
                    pulse_alignment=timing_constraints.pulse_alignment,
                )
            )
            pm.append(
                ConstrainedReschedule(
                    acquire_alignment=timing_constraints.acquire_alignment,
                    pulse_alignment=timing_constraints.pulse_alignment,
                ),
                condition=_require_alignment,
            )
            pm.append(
                ValidatePulseGates(
                    granularity=timing_constraints.granularity,
                    min_length=timing_constraints.min_length,
                )
            )
        pm.append(PadDelay(target=target))

        return pm
