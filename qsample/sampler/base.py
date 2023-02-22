# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/06b_sampler.base.ipynb.

# %% auto 0
__all__ = ['tolists', 'lens', 'maxlen', 'pad', 'equalize_lens', 'err_probs_tomatrix', 'sort_by_list', 'subset_occurence',
           'all_subsets', 'protocol_all_subsets', 'protocol_subset_occurence', 'Sampler']

# %% ../../nbs/06b_sampler.base.ipynb 3
from .tree import CountTree, Variable, Constant

from ..callbacks import CallbackList
from tqdm.auto import tqdm
import itertools as it
import numpy as np
import qsample.math as math
from ..noise import E0
import dill as pickle

from collections.abc import Iterable

# %% ../../nbs/06b_sampler.base.ipynb 5
# Convert elements of list into list (if not already)
tolists = lambda l: [e if isinstance(e,Iterable) else [e] for e in l]

# Compute lens of sublists in list
lens = lambda list_of_lists: list(map(len,list_of_lists))

# Compute maximum len of list of sublists
maxlen = lambda list_of_lists: max(lens(list_of_lists))

# Fill list `l` to len `targ_len` by duplicating elements
pad = lambda l,targ_len: np.append(l, [l[-1]] * (targ_len - len(l)))

def equalize_lens(mixed_list: list):
    """Convert mixed list of lists and elements to list of lists, s.t.
    each sublist has the same length as the longest sublist."""
    list_of_lists = tolists(mixed_list)
    return [pad(e,maxlen(list_of_lists)) for e in list_of_lists]

def err_probs_tomatrix(err_probs: dict, groups: list) -> np.ndarray:
    """Convert dict of error probabilities into matrix of dimensions
    (error probability)x(circuit location group)."""
    err_probs = sort_by_list(err_probs, groups)
    return np.array(equalize_lens(err_probs.values())).T

def sort_by_list(d: dict, l: list) -> dict:
    """Sort dictionary keys by order of keys in list."""
    return dict(sorted(d.items(), key=lambda pair: l.index(pair[0])))

def subset_occurence(groups: list, subsets: np.array, group_prob_range: np.array) -> np.array:
    """Calculate matrix of subset occurences, Aws."""
    Aws = [math.binom(subset, lens(groups), group_prob_range) for subset in subsets]
    return np.product(Aws, axis=-1)

def all_subsets(groups: list) -> list:
    """Calculate all possible subset tuples from list of lists containing
    group elements for each group."""
    return list(it.product( *[tuple(range(N+1)) for N in lens(groups)]))

def protocol_all_subsets(protocol_groups: dict) -> dict:
    """Calculate all possible subset tuples for each circuit."""
    return {cid: all_subsets(groups_dict.values()) for cid,groups_dict in protocol_groups.items()}

def protocol_subset_occurence(protocol_groups: dict, protocol_subsets: dict, group_probs: dict) -> dict:
    """Calculate all subset occurences for each circuit."""
    return {cid: {subset: Aw for subset, Aw in zip(subsets, subset_occurence(protocol_groups[cid].values(),subsets,group_probs))}
                  for cid,subsets in protocol_subsets.items()}

# %% ../../nbs/06b_sampler.base.ipynb 6
class Sampler:
    """Base class for other Sampler classes to inherit
    
    Attributes
    ----------
    protocol : Protocol
        Protocol to sample "marked" events from
    simulator : StabilizerSimulator or StatevectorSimulator
        Simulator used to simulate circuit execution on
    n_qubits : int
        Number of qubits used in protocol
    err_model : ErrorModel
        Error model used during circuit simulation
    trees : dict of CountTree
        `CountTree`s used to accumulate sampling information. One tree per sample.
    """
    
    def __init__(self, protocol, simulator, err_probs={"0":{}}, err_model=None):
        """
        Parameters
        ----------
        protocol : Protocol
            Protocol to sample "marked" events from
        simulator : StabilizerSimulator or StatevectorSimulator
            Simulator used to simulate circuit execution on
        err_probs : dict
            Error probabilites per location group; must match location group names of error model
        err_model : ErrorModel
            Error model used during circuit simulation
        """
        self.protocol = protocol
        self.simulator = simulator
        self.n_qubits = protocol.n_qubits
        self.err_model = err_model() if err_model else E0()
        
        self._set_subsets()
        
        assert isinstance(err_probs, dict)
        assert set(err_probs.keys()) == set(self.err_model.groups)

        self.trees = dict()
        for prob_vec in err_probs_tomatrix(err_probs, self.err_model.groups):
            tree = CountTree(fault_tolerance_level=2 if self.protocol.fault_tolerant else 1,
                             constants=protocol_subset_occurence(self.protocol_groups, self.protocol_subsets, prob_vec))
            self.trees[tuple(prob_vec)] = tree
         
    def _set_subsets(self):
        """(Re)calculate location groups per circuit in protocol and its possible subsets."""
        self.protocol_groups = {cid: self.err_model.group(circuit) for cid, circuit in self.protocol._circuits.items()}
        self.protocol_subsets = protocol_all_subsets(self.protocol_groups)
        
    def save(self, path):
        """Save sampler object to path"""
        with open(path, 'wb') as fp:
            pickle.dump(self, fp)
    
    @staticmethod
    def load(path):
        """Load and return sampler object from path"""
        with open(path, 'rb') as fp:
            data = pickle.load(fp)
        return data

    def optimize(self, tree_node, circuit):
        """Must be overwritten by child class."""
        raise NotImplemented
            
    def run(self, n_shots: int, callbacks=[]) -> None:
        """Run `n_shots` protocol simulations per sample (i.e. physical error rate).
        
        Parameters
        ----------
        n_shots : int
            Number of shots (i.e. protocol runs) obtained per sample
        callbacks : list
            List of callbacks executed during sampling process
        """
        
        if not isinstance(callbacks, CallbackList):
            callbacks = CallbackList(sampler=self, callbacks=callbacks)
        callbacks.on_sampler_begin()
        
        for prob_vec, tree in self.trees.items():
            self.stop_sampling = False
            self.tree_idx = prob_vec
   
            for _ in tqdm(range(n_shots), desc=f'p_phy={",".join(list(f"{p:.2E}" for p in prob_vec))}', leave=True):
                callbacks.on_protocol_begin()

                state = self.simulator(self.n_qubits)
                tree_node = None

                for name, circuit in self.protocol:
                    callbacks.on_circuit_begin()

                    tree_node = tree.add(name=name, parent=tree_node, node_type=Variable)
                    tree_node.count += 1
                    opt_out = dict()

                    if circuit:
                        if not circuit._noisy:
                            msmt = state.run(circuit)
                            subset = (0,)
                        else:
                            opt_out = self.optimize(tree_node, circuit, prob_vec)
                            fault_circuit = self.err_model.run(circuit, opt_out['flocs'])
                            msmt = state.run(circuit, fault_circuit)
                            subset = opt_out['subset']
                            
                        tree_node = tree.add(name=subset, parent=tree_node, node_type=Constant, circuit_id=circuit.id,
                                             det=True if circuit._ff_det and not any(subset) else False)
                        tree_node.count += 1
                              
                        self.protocol.send(msmt)

                    elif name != None:
                        tree.marked_leaves.add(tree_node)
                    
                    callbacks.on_circuit_end(locals() | opt_out)

                callbacks.on_protocol_end()
                if self.stop_sampling: break
            
        callbacks.on_sampler_end()
