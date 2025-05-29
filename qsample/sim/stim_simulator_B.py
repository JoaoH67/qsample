import stim
import numpy as np
from copy import deepcopy
from ..circuit import qs2stim, stim2qs, Circuit


class StimSimulator_B():
    """The bare minimum needed for the CHP simulation."""
    
    def __init__(self, num_qubits) -> None:
        """Initialize to |0>"""
        self.state = stim.TableauSimulator()
            

    def run(self, circuit, fault_circuit=None):
        new_circuit = deepcopy(circuit)
        if fault_circuit:
            offset = 0
            for i, j in enumerate(fault_circuit._ticks):
                if len(j):
                    new_circuit.insert(i+offset, j)
                    offset+=1
        stim_circuit = stim.Circuit(qs2stim(new_circuit))
        self.state.do(stim_circuit)
        if circuit.n_measurements == 0:
            msmt = None
        else:

            msmt = []
            for i in range(circuit.n_measurements):
                msmt.append(self.state.measure(circuit.measured_qubits[i]))
   
            msmt = bin(np.dot(np.array(msmt)[::-1], 2**np.arange(circuit.n_measurements)))
        return msmt
            
        