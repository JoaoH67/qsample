# AUTOGENERATED! DO NOT EDIT! File to edit: 04_fault_generators.ipynb (unless otherwise specified).

__all__ = ['to_ndarray', 'pad', 'ONE_QUBIT_GATES', 'TWO_QUBIT_GATES', 'MEAS_GATES', 'INIT_GATES', 'GATE_GROUPS',
           'FaultGenerator', 'Depolarizing']

# Cell
from .circuit import Circuit, partition, unpack
import numpy as np
import itertools as it

# Cell
def to_ndarray(e):
    if isinstance(e, np.ndarray): return e
    elif isinstance(e, (list, tuple, set)): return np.array(e)
    else: return np.array([e])

# Cell
def pad(lst,size,val):
    return np.append(lst, [val] * (size - len(lst))) if len(lst) < size else lst

# Cell
ONE_QUBIT_GATES = {'H', 'X', 'Y', 'Z', 'I', 'S', 'Sd', 'T', 'Td', 'Q', 'Qd', 'R', 'Rd'}
TWO_QUBIT_GATES = {'CNOT', 'MSd'}
MEAS_GATES = {'measure'}
INIT_GATES = {'init'}

GATE_GROUPS = {'p': ONE_QUBIT_GATES | TWO_QUBIT_GATES,
               'p1': ONE_QUBIT_GATES,
               'p2': TWO_QUBIT_GATES,
               'm': MEAS_GATES,
               'in': INIT_GATES
               }

# Cell
class FaultGenerator:

    def __init__(self, err_params, one_qubit_faults, two_qubit_faults):
        self.partition_names = list(err_params.keys())
        p_phy = [to_ndarray(p) for p in err_params.values()]
        psize = max(p.size for p in p_phy)
        self.p_phy = np.array([pad(p,psize,p[-1]) for p in p_phy]).T

        self.ONE_QUBIT_FAULTS = one_qubit_faults
        self.TWO_QUBIT_FAULTS = two_qubit_faults

    def configure(self, circuit):
        if isinstance(circuit, dict):
            partitions = {c_hash: [self._partition(circuit, name) for name in self.partition_names]
                          for c_hash, circuit in circuit.items()}
        else:
            partitions = [self._partition(circuit, name) for name in self.partition_names]
        self.partitions = partitions

    def _partition(self, circuit, partition_name):
        if partition_name in GATE_GROUPS:
            return partition(circuit, GATE_GROUPS[partition_name])
        elif partition_name == 'id':
            n_qubits = circuit.n_qubits
            n_ticks = circuit.n_ticks
            return [(i,loc) for i, tick in enumerate(circuit) for loc in unpack(tick)]
        elif partition_name == 'x1':
            n_qubits = circuit.n_qubits
            active_locs = partition(circuit, GATE_GROUPS['p1'])
            out = set()
            for tick, qb in active_locs:
                if qb-1 >= 0 and (tick,qb-1):
                    out.add( (tick,qb-1) )
                if qb+1 <= n_qubits and (tick,qb+1):
                    out.add( (tick,qb-1) )
            return list(out)
        elif partition_name == 'x2':
            # common / not-common neighbors.
            # target/control qubit neighbors Ex. MS(6,3): faulty: (3,2),(3,4),(3,5),(3,7), (5,6),(6,7),(6,2),(6,4)
            # special operators per gate
            pass
        else:
            raise KeyError(f'Unkown partition {partition_name}.')

    def faults_from_probs(self, ps, c_hash=None):
        """Select fault locs by random number < p for elements in partitions"""
        if c_hash: partitions = self.partitions[c_hash]
        else: partitions = self.partitions
        return [loc for locs,p in zip(partitions, ps) for loc in locs if np.random.random() < p]

    def faults_from_weights(self, ws, c_hash=None):
        """Select fault locs by random choice of w elements per partition"""
        if c_hash: partitions = self.partitions[c_hash]
        else: partitions = self.partitions
        return [par[i] for par,w in zip(partitions,ws) for i in np.random.choice(len(par),w,replace=False)]

    def gen_circuit(self, n_ticks, faults=[]):
        """Generate an empty circuit with given faults"""
        fault_circuit = Circuit([{} for _ in range(n_ticks)])
        for (tick_index,qubit) in faults:
            if isinstance(qubit, int):
                f_gate = np.random.choice(self.ONE_QUBIT_FAULTS)
                qb_set = fault_circuit[tick_index].get(f_gate, set()) # get previous f_gate type fault
                qb_set.add(qubit) # append faults in this tick
                fault_circuit[tick_index][f_gate] = qb_set # udpate
            elif isinstance(qubit, (list,set,tuple)):
                f_gates = self.TWO_QUBIT_FAULTS[np.random.choice(len(self.TWO_QUBIT_FAULTS))]
                for f_gate, qubit_i in zip(f_gates, qubit):
                    if f_gate != "I":
                        qb_set = fault_circuit[tick_index].get(f_gate, set())
                        qb_set.add(qubit_i)
                        fault_circuit[tick_index][f_gate] = qb_set
        return fault_circuit

# Cell
class Depolarizing(FaultGenerator):

    ONE_QUBIT_FAULTS = ['X', 'Y', 'Z']
    TWO_QUBIT_FAULTS = [
        ('I', 'X'), ('I', 'Y'), ('I', 'Z'),
        ('X', 'I'), ('X', 'X'), ('X', 'Y'), ('X', 'Z'),
        ('Y', 'I'), ('Y', 'X'), ('Y', 'Y'), ('Y', 'Z'),
        ('Z', 'I'), ('Z', 'X'), ('Z', 'Y'), ('Z', 'Z')
    ]

    def __init__(self, err_params):
        super().__init__(err_params, self.ONE_QUBIT_FAULTS, self.TWO_QUBIT_FAULTS)