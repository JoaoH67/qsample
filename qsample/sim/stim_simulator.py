import stim
import numpy as np
from copy import deepcopy
from ..circuit import Circuit


from .mixin import CircuitRunnerMixin

import random
from typing import Union, Any

class MeasureResult:
    """A measurement's output and whether it was random or not."""

    def __init__(self, value: bool, determined: bool):
        self.value = bool(value)
        self.determined = bool(determined)

    def __bool__(self):
        return self.value

    def __eq__(self, other):
        if isinstance(other, (bool, int)):
            return self.value == other
        if isinstance(other, MeasureResult):
            return self.value == other.value and self.determined == other.determined
        return NotImplemented

    def __str__(self):
        return '{} ({})'.format(self.value,
                                ['random', 'determined'][self.determined])

    def __repr__(self):
        return 'MeasureResult(value={!r}, determined={!r})'.format(
            self.value,
            self.determined)

# %% ../../nbs/05b_sim.stabilizer.ipynb 5
class StimSimulator(CircuitRunnerMixin):
    """The bare minimum needed for the CHP simulation."""
    
    def __init__(self, num_qubits):
        self.state = stim.TableauSimulator()
    def I(self, qubit: int) -> None:
        pass
    def X(self, qubit: int) -> None:
        """X gate"""
        self.state.x(qubit)
    def Y(self, qubit: int) -> None:
        """Y gate"""
        self.state.y(qubit)    
    def Z(self, qubit: int) -> None:
        """Z gate"""
        self.state.z(qubit)
    def H(self, qubit:int) -> None:
        """H gate"""
        self.state.h(qubit)
    def Q(self, qubit:int) -> None:
        """Q gate"""
        self.state.q(qubit)
    def Qd(self, qubit:int) -> None:
        """Qd gate"""
        self.state.q_dag(qubit)
    def R(self, qubit:int) -> None:
        """R gate"""
        self.state.r(qubit)
    def Rd(self, qubit:int) -> None:
        """Rd gate"""
        self.state.r_dag(qubit)
    def S(self, qubit:int) -> None:
        """S gate"""
        self.state.s(qubit)
    def Sd(self, qubit:int) -> None:
        """Sd gate"""
        self.state.s_dag(qubit)

    def CNOT(self, control: int, target: int) -> None:
        """CNOT gate"""
        self.state.cnot(control, target)

    def init(self, qubit: int) -> None:
        """R = reset"""
        self.state.reset(qubit)
    def measure(self, qubit: int) -> None:
        """R = reset"""
        self.state.measure(qubit)
        result = self.state.measure(qubit)
        return MeasureResult(result, determined=True)





