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

from qiskit import QuantumCircuit
from qiskit.test import QiskitTestCase
from qiskit.transpiler.instruction_durations import InstructionDurations
from qiskit.transpiler.passes import PadDelay
from qiskit.transpiler.passmanager import PassManager

from qiskit_scheduling_extension.compact import CompactScheduleAnalysis


class TestCompactScheduling(QiskitTestCase):
    """Tests the CompactScheduling pass"""

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

        durations = InstructionDurations(
            [("h", None, 200), ("cx", [0, 1], 700), ("cx", [1, 2], 900), ("measure", None, 1000)]
        )

        pm = PassManager([CompactScheduleAnalysis(durations), PadDelay()])
        compact_qc = pm.run(qc)

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

        self.assertEqual(expected, compact_qc)

    def test_compact_can_shift_block(self):
        """Test if Compact scheduling can shift front blocks towards the back and
        back blocks towards the front.

        (input)
                                                              ░ ┌─┐
           q_0: ──■─────────────────────────────■─────────────░─┤M├─────────
                ┌─┴─┐                         ┌─┴─┐           ░ └╥┘┌─┐
           q_1: ┤ X ├────────────■─────────■──┤ X ├───────────░──╫─┤M├──────
                └───┘     ┌───┐┌─┴─┐     ┌─┴─┐├───┤           ░  ║ └╥┘┌─┐
           q_2: ───────■──┤ H ├┤ X ├──■──┤ X ├┤ H ├──■────────░──╫──╫─┤M├───
                ┌───┐┌─┴─┐├───┤└───┘┌─┴─┐├───┤└───┘┌─┴─┐┌───┐ ░  ║  ║ └╥┘┌─┐
           q_3: ┤ H ├┤ X ├┤ H ├─────┤ X ├┤ H ├─────┤ X ├┤ H ├─░──╫──╫──╫─┤M├
                └───┘└───┘└───┘     └───┘└───┘     └───┘└───┘ ░  ║  ║  ║ └╥┘
        meas: 4/═════════════════════════════════════════════════╩══╩══╩══╩═
                                                                 0  1  2  3
        (Compact scheduled)
                                  ┌─────────────────┐                            »
           q_0: ────────■─────────┤ Delay(1000[dt]) ├────────────────────────────»
                      ┌─┴─┐       └─────────────────┘                            »
           q_1: ──────┤ X ├────────────────────────────────────────────■─────────»
                ┌─────┴───┴──────┐                        ┌───┐      ┌─┴─┐       »
           q_2: ┤ Delay(750[dt]) ├─────────────────────■──┤ H ├──────┤ X ├───────»
                ├────────────────┤       ┌───┐       ┌─┴─┐├───┤┌─────┴───┴──────┐»
           q_3: ┤ Delay(700[dt]) ├───────┤ H ├───────┤ X ├┤ H ├┤ Delay(400[dt]) ├»
                └────────────────┘       └───┘       └───┘└───┘└────────────────┘»
        meas: 4/═════════════════════════════════════════════════════════════════»
                                                                                 »
        «                                                                        »
        «   q_0: ───────────────────────────────■────────────────────────────────»
        «        ┌────────────────┐           ┌─┴─┐                              »
        «   q_1: ┤ Delay(200[dt]) ├──■────────┤ X ├──────────────────────────────»
        «        └────────────────┘┌─┴─┐      ├───┤            ┌────────────────┐»
        «   q_2: ────────■─────────┤ X ├──────┤ H ├─────────■──┤ Delay(750[dt]) ├»
        «              ┌─┴─┐       ├───┤┌─────┴───┴──────┐┌─┴─┐└─────┬───┬──────┘»
        «   q_3: ──────┤ X ├───────┤ H ├┤ Delay(400[dt]) ├┤ X ├──────┤ H ├───────»
        «              └───┘       └───┘└────────────────┘└───┘      └───┘       »
        «meas: 4/════════════════════════════════════════════════════════════════»
        «                                                                        »
        «                           ░ ┌─┐
        «   q_0: ───────────────────░─┤M├─────────
        «                           ░ └╥┘┌─┐
        «   q_1: ───────────────────░──╫─┤M├──────
        «                           ░  ║ └╥┘┌─┐
        «   q_2: ───────────────────░──╫──╫─┤M├───
        «        ┌────────────────┐ ░  ║  ║ └╥┘┌─┐
        «   q_3: ┤ Delay(700[dt]) ├─░──╫──╫──╫─┤M├
        «        └────────────────┘ ░  ║  ║  ║ └╥┘
        «meas: 4/══════════════════════╩══╩══╩══╩═
        «                              0  1  2  3
        """
        qc = QuantumCircuit(4)
        qc.cx(0, 1)
        qc.h(3)
        qc.cx(2, 3)
        qc.h([2, 3])
        qc.cx(1, 2)
        qc.cx(2, 3)
        qc.cx(1, 2)
        qc.h([2, 3])
        qc.cx(2, 3)
        qc.h(3)
        qc.cx(0, 1)
        qc.measure_all()

        durations = InstructionDurations(
            [
                ("h", None, 50),
                ("cx", [0, 1], 1000),
                ("cx", [1, 2], 400),
                ("cx", [2, 3], 200),
                ("measure", None, 1000),
            ]
        )
        pm = PassManager([CompactScheduleAnalysis(durations), PadDelay()])
        compact_qc = pm.run(qc)

        expected = QuantumCircuit(4)
        expected.delay(750, 2)
        expected.delay(700, 3)
        expected.cx(0, 1)
        expected.h(3)
        expected.cx(2, 3)
        expected.h([2, 3])
        expected.delay(400, 3)
        expected.cx(1, 2)
        expected.delay(1000, 0)
        expected.delay(200, 1)
        expected.cx(2, 3)
        expected.cx(1, 2)
        expected.h([2, 3])
        expected.delay(400, 3)
        expected.cx(2, 3)
        expected.h(3)
        expected.cx(0, 1)
        expected.delay(750, 2)
        expected.delay(700, 3)
        expected.measure_all()

        self.assertEqual(expected, compact_qc)
