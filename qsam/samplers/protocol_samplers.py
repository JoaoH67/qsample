# AUTOGENERATED! DO NOT EDIT! File to edit: 05b_samplers.protocol_samplers.ipynb (unless otherwise specified).

__all__ = ['ONE_QUBIT_GATES', 'TWO_QUBIT_GATES', 'GATE_GROUPS', 'Sampler']

# Cell
import qsam.math as math
from ..circuit import partition, make_hash, unpack
from ..fault_generators import Depolar
from ..protocol import iterate
from .sampler_mixins import SubsetAnalytics

import numpy as np
from flexdict import FlexDict
# import itertools as it
# import networkx as nx

# Cell
ONE_QUBIT_GATES = {'H', 'X', 'Z'}
TWO_QUBIT_GATES = {'CNOT'}

GATE_GROUPS = {'p': ONE_QUBIT_GATES | TWO_QUBIT_GATES,
               'p1': ONE_QUBIT_GATES,
               'p2': TWO_QUBIT_GATES,
               }

# Cell
class Sampler:
    def __init__(self, protocol, simulator):
        self.protocol = protocol
        self.simulator = simulator
        self.n_qubits = len(set(q for c in protocol._circuits.values() for q in unpack(c)))

    def run(self, n_samples, sample_range, err_params, var=math.Wilson_var, eval_fns=None):

        fail_cnts = np.zeros(len(sample_range)) # one fail counter per sample point
        partitions = {circuit_hash: [partition(circuit, GATE_GROUPS[k]) for k in err_params.keys()]
                     for circuit_hash, circuit in self.protocol._circuits.items()}

        for i,sample_pt in enumerate(sample_range): # n_samples at sample_pt

            p_phy = np.array(list(err_params.values())) * sample_pt

            for _ in range(n_samples):

                sim = self.simulator(self.n_qubits)
                p_it = iterate(self.protocol, eval_fns)
                node = next(p_it)

                while node:

                    if node == 'EXIT':
                        fail_cnts[i] += 1
                        break
                    else:
                        circuit_hash, circuit = self.protocol.circuit_from_node(node)
                        circuit_partitions = partitions[circuit_hash]
                        faults = Depolar.faults_from_probs(circuit_partitions, p_phy)
                        fault_circuit = Depolar.gen_circuit(len(circuit), faults)
                        msmt = sim.run(circuit, fault_circuit)
                        node = p_it.send(msmt)

        p_L = fail_cnts / n_samples
        std = np.sqrt( var(p_L, n_samples) )
        return p_L, std