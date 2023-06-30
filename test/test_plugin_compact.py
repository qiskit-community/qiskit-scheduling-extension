# This code is part of Qiskit.
#
# (C) Copyright IBM 2023.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Test the CompactScheduling pass"""

from qiskit import QuantumCircuit, transpile
from qiskit.test import QiskitTestCase
from qiskit.transpiler.preset_passmanagers.plugin import list_stage_plugins


class TestCompactScheduling(QiskitTestCase):
    """Tests the CompactScheduling plugin"""

    def test_plugin_in_list(self):
        """Test compact scheduling plugin is installed."""
        self.assertIn("compact", list_stage_plugins("scheduling"))

    def test_compact(self):
        """Test if Compact scheduling yields expected schedule.

        (input)
                ┌───┐               ┌───┐ ░ ┌─┐
           q_0: ┤ H ├──■─────────■──┤ H ├─░─┤M├──────
                └───┘┌─┴─┐     ┌─┴─┐└───┘ ░ └╥┘┌─┐
           q_1: ─────┤ X ├──■──┤ X ├──────░──╫─┤M├───
                ┌───┐└───┘┌─┴─┐├───┤      ░  ║ └╥┘┌─┐
           q_2: ┤ H ├─────┤ X ├┤ H ├──────░──╫──╫─┤M├
                └───┘     └───┘└───┘      ░  ║  ║ └╥┘
        meas: 3/═════════════════════════════╩══╩══╩═
                                             0  1  2

        (Compact scheduled)
                      ┌───┐            ┌────────────────┐           ┌───┐        ░ ┌─┐
           q_0: ──────┤ H ├─────────■──┤ Delay(900[dt]) ├──■────────┤ H ├────────░─┤M├──────
                ┌─────┴───┴──────┐┌─┴─┐└────────────────┘┌─┴─┐┌─────┴───┴──────┐ ░ └╥┘┌─┐
           q_1: ┤ Delay(200[dt]) ├┤ X ├────────■─────────┤ X ├┤ Delay(200[dt]) ├─░──╫─┤M├───
                ├────────────────┤├───┤      ┌─┴─┐       ├───┤├────────────────┤ ░  ║ └╥┘┌─┐
           q_2: ┤ Delay(700[dt]) ├┤ H ├──────┤ X ├───────┤ H ├┤ Delay(700[dt]) ├─░──╫──╫─┤M├
                └────────────────┘└───┘      └───┘       └───┘└────────────────┘ ░  ║  ║ └╥┘
        meas: 3/════════════════════════════════════════════════════════════════════╩══╩══╩═
                                                                                    0  1  2
        """
        qc = QuantumCircuit(3)
        qc.h([0, 2])
        qc.cx(0, 1)
        qc.cx(1, 2)
        qc.cx(0, 1)
        qc.h([0, 2])
        qc.measure_all()

        durations = [
            ("h", None, 200),
            ("cx", [0, 1], 700),
            ("cx", [1, 2], 900),
            ("measure", None, 1000)
        ]

        actual = transpile(
            qc, instruction_durations=durations, scheduling_method="compact", optimization_level=0
        )

        expected = QuantumCircuit(3)
        expected.delay(200, 1)
        expected.delay(700, 2)
        expected.h([0, 2])
        expected.cx(0, 1)
        expected.cx(1, 2)
        expected.delay(900, 0)
        expected.cx(0, 1)
        expected.h([0, 2])
        expected.delay(200, 1)
        expected.delay(700, 2)
        expected.measure_all()

        self.assertEqual(expected, actual)
