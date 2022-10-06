# AUTOGENERATED! DO NOT EDIT! File to edit: 05b_samplers.protocol_samplers.ipynb (unless otherwise specified).

__all__ = ['Sampler', 'SubsetSampler']

# Cell
import qsam.math as math
from ..circuit import partition, make_hash, unpack
from ..fault_generators import Depolar
from ..protocol import iterate
from .common import *
import qsam.samplers.callbacks as cb

import numpy as np
from tqdm.notebook import tqdm

# Cell

class Sampler:
    def __init__(self, protocol, simulator):
        self.protocol = protocol
        self.simulator = simulator
        self.n_qubits = len(set(q for c in protocol._circuits.values() for q in unpack(c)))
        self.is_setup = False

    def setup(self, sample_range, err_params):
        self.partitions = {circuit_hash: [partition(circuit, GATE_GROUPS[k]) for k in err_params.keys()]
                           for circuit_hash, circuit in self.protocol._circuits.items()}
        self.p_phys = [s * np.array(list(err_params.values())) for s in sample_range]
        self.fail_cnts = np.zeros(len(sample_range))
        self.cnts = np.zeros(len(sample_range))
        self.is_setup = True

    def stats(self, p_idx=None, var_fn=math.Wilson_var):
        if p_idx == None:
            rate = self.fail_cnts / self.cnts
            var = var_fn(rate, self.cnts)
        else:
            rate = self.fail_cnts[p_idx] / self.cnts[p_idx]
            var = var_fn(rate, self.cnts[p_idx])

        return rate, np.sqrt(var), 0.0

    # def run(self, n_samples, after_cbs=[], inner_cbs=[], outer_cbs=[]):
    def run(self, n_samples, callbacks):
        assert self.is_setup, 'Sampler not setup. Call setup(..) before run(..).'

        if not isinstance(callbacks, cb.CallbackList):
            callbacks = cb.CallbackList(sampler=self, callbacks=callbacks)
        callbacks.on_sampler_begin()

        for i, p_phy in enumerate(tqdm(self.p_phys, desc='Total')):
            self.stop_sampling = False
            self.p_idx = i

            for _ in tqdm(range(n_samples), desc=f'p_phy={",".join(list(f"{p:.2E}" for p in p_phy))}', leave=True):

                callbacks.on_protocol_begin()

                sim = self.simulator(self.n_qubits)
                p_it = iterate(self.protocol)
                node = next(p_it)
                self.cnts[i] += 1

                while node:

                    callbacks.on_circuit_begin()

                    if not self.protocol.out_edges(node):
                        self.fail_cnts[i] += 1
                        break

                    circuit_hash, circuit = self.protocol.circuit_from_node(node)
                    if not circuit._noisy or circuit_hash not in self.partitions.keys():
                        msmt = sim.run(circuit)
                    else:
                        circuit_partitions = self.partitions[circuit_hash]
                        faults = Depolar.faults_from_probs(circuit_partitions, p_phy)
                        fault_circuit = Depolar.gen_circuit(len(circuit), faults)
                        msmt = sim.run(circuit, fault_circuit)
                    _node = node
                    node = p_it.send(msmt)

                    callbacks.on_circuit_end(locals())

                callbacks.on_protocol_end()
                if self.stop_sampling: break

        callbacks.on_sampler_end()


# Cell

class SubsetSampler:
    """Subset Sampler of quantum protocols"""

    def __init__(self, protocol, simulator):
        self.protocol = protocol
        self.simulator = simulator
        self.n_qubits = len(set(q for c in protocol._circuits.values() for q in unpack(c)))
        self.tree = SampleTree()
        self.is_setup = False

    def setup(self, sample_range, err_params, p_max):
        p_max = np.array([p_max]) if isinstance(p_max, float) else np.array(p_max)
        assert len(p_max) == len(err_params)
        self.err_params = err_params
        self.partitions = protocol_partitions(self.protocol._circuits, err_params.keys())
        self.w_vecs = protocol_weight_vectors(self.partitions)
        self.Aws_pmax = protocol_subset_occurence(self.partitions, self.w_vecs, p_max)
        self.set_range(sample_range)
        self.is_setup = True

    def set_range(self, sample_range):
        p_phy_per_partition = np.array([[p_phy * mul for p_phy in sample_range] for mul in self.err_params.values()]).T
        self.Aws = protocol_subset_occurence(self.partitions, self.w_vecs, p_phy_per_partition)

    def stats(self, const='Aws', **kwargs):
        if const == 'Aws': Aws = self.Aws
        elif const == 'Aws_pmax': Aws = self.Aws_pmax
        v_L = self.tree.var(Aws)
        p_L = self.tree.rate(Aws)
        if isinstance(v_L, np.ndarray) and isinstance(p_L, int):
            p_L = np.zeros_like(v_L)
        delta = self.tree.delta(Aws)
        return p_L, np.sqrt(v_L), delta

    def run(self, n_samples, callbacks, ss_filter_fn=w_plus1_filter, ss_sel_fn=ERV_sel):
        assert self.is_setup, 'Sampler not setup. Call setup(..) before run(..).'

        if not isinstance(callbacks, cb.CallbackList):
            callbacks = cb.CallbackList(sampler=self, callbacks=callbacks)

        self.stop_sampling = False
        callbacks.on_sampler_begin()

        for i in tqdm(range(n_samples), desc='Total'):

            callbacks.on_protocol_begin()

            sim = self.simulator(self.n_qubits)
            p_it = iterate(self.protocol)
            node = next(p_it)
            tree_node = None

            while True:

                callbacks.on_circuit_begin()

                tree_node = self.tree.update(name=node, parent=tree_node)
                if node == None: break
                elif not self.protocol.out_edges(node): tree_node.is_fail = True; break

                circuit_hash, circuit = self.protocol.circuit_from_node(node)
                if circuit_hash not in self.partitions.keys() or not circuit._noisy: # correction circuits
                    msmt = sim.run(circuit)
                else:
                    w_ids = [n.ckey[1] for n in tree_node.children]
                    w_ids = ss_filter_fn(sampler=self, **locals())
                    w_idx = ss_sel_fn(sampler=self, **locals())
                    w_vec = self.w_vecs[circuit_hash][w_idx]
                    tree_node = self.tree.update(name=w_vec, parent=tree_node, ckey=(circuit_hash, w_idx),
                                                is_deterministic=True if circuit._ff_deterministic and not any(w_vec) else False)

                    faults = Depolar.faults_from_weights(self.partitions[circuit_hash], w_vec)
                    fault_circuit = Depolar.gen_circuit(len(circuit), faults)
                    msmt = sim.run(circuit, fault_circuit)

                _node = node
                node = p_it.send(msmt)
                callbacks.on_circuit_end(locals())

            callbacks.on_protocol_end()
            if self.stop_sampling: break

        callbacks.on_sampler_end()