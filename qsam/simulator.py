# AUTOGENERATED! DO NOT EDIT! File to edit: 03_simulator.ipynb (unless otherwise specified).

__all__ = ['Simulator']

# Cell
from .nbtools import patch

# Cell
class Simulator:
    """Interface for quantum state simulation"""
    def __init__(self, n_qubits):
        self.n_qubits = n_qubits

    def _apply_gate(self, gate_symbol, qubits):
        """Apply a gate to the `qubits` of the current state."""
        gate = getattr(self, gate_symbol.upper())
        args = (qubits,) if type(qubits)==int else qubits
        return gate(*args)

    def run(self, circuit, fault_circuit=None):
        """Apply gates in `circuit` sequentially to current state.
        If `fault_circuit` is specified apply fault gates at end of each tick."""
        measurements = []
        for tick_index in range(circuit.n_ticks):

            for gate, qubits in circuit[tick_index].items():
                for qubit in qubits:
                    res = self._apply_gate(gate, qubit)
                    if res: measurements.append((tick_index,res))

            for f_gate, f_qubits in fault_circuit[tick_index].items():
                for f_qubit in f_qubits:
                    self._apply_gate(f_gate, f_qubit)

        return measurements