# Qiskit Scheduling Extension Plugin

This repository contains standalone pass managers useful at 
[scheduling](https://qiskit.org/documentation/apidoc/transpiler.html#scheduling-stage)
stage in Qiskit transpiler.

## Install and Use plugin

To use the scheduling extension plugin first install qiskit and qiskit-scheduling-extension:

```bash
pip install qiskit
pip install qiskit-scheduling-extension
```

## Using CompactScheduling pass

Once you have the plugin package installed you can use the plugin via the
`scheduling_method="compact"` argument on Qiskit's `transpile()` function. For example,
if you wanted to use the `CompactScheduling` method to compile a 15 qubit quantum
volume circuit for a backend you would do something like:

```python

from qiskit import transpile
from qiskit.circuit.library import QuantumVolume
from qiskit.providers.fake_provider import FakePrague

qc = QuantumVolume(15)
qc.measure_all()
backend = FakePrague()

transpile(qc, backend, scheduling_method="compact")
```

# Authors and Citation

The qiskit-scheduling-extension is the work of [many people](https://github.com/qiskit-community/qiskit-scheduling-extension/graphs/contributors)
who contribute to the project at different levels.
