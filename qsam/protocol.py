# AUTOGENERATED! DO NOT EDIT! File to edit: 02_protocol.ipynb (unless otherwise specified).

__all__ = ['Protocol', 'draw_protocol', 'default_fns', 'iterate', 'save_protocol', 'load_protocol']

# Cell
import networkx as nx
from .circuit import make_hash, Circuit
from functools import lru_cache
import pickle
import simpleeval

# Cell
class Protocol(nx.DiGraph):
    """Representation of a Quantum Error Correction protocol"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._circuits = {} # hash table

    def add_node(self, name, circuit):
        circuit_hash = make_hash(circuit)
        self._circuits[circuit_hash] = circuit
        super().add_node(name, circuit_hash=circuit_hash)

    def update_node(self, name, circuit):
        circuit_hash = make_hash(circuit)
        self._circuits[circuit_hash] = circuit
        self.nodes[node]['circuit_hash'] = circuit_hash

    def add_nodes_from(self, names, circuits):
        if not isinstance(circuits, (list,tuple,set)):
            circuits = [circuits] * len(names)
        for name, circuit in zip(names, circuits):
            self.add_node(name, circuit)

    def circuit_from_node(self, node):
        circuit_hash = self.circuit_hash(node)
        circuit = self._circuits[circuit_hash]
        return circuit

    def circuit_hash(self, node):
        return self.nodes(data='circuit_hash')[node]

    @lru_cache(maxsize=128)
    def checks(self, node):
        adj_nodes = self.out_edges(node)
        return {pair[1]: self.edges[pair]['check'] for pair in adj_nodes}

# Cell
def draw_protocol(protocol):
    """Draw graph representation of protocol"""

    pos = nx.kamada_kawai_layout(protocol)
    col_val_map = {'START': '#99ccff', 'EXIT': '#ff9999'}
    col_vals = [col_val_map.get(node, '#ffb266') for node in protocol.nodes]
    nx.draw(protocol, pos, node_color=col_vals, with_labels=True)
    edge_labels = nx.get_edge_attributes(protocol, 'check')
    nx.draw_networkx_edge_labels(protocol, pos, edge_labels)

# Cell
default_fns = simpleeval.DEFAULT_FUNCTIONS.copy()
default_fns.update(
    len=len,
    bin=bin,
    parity=lambda x, y: bin(x).count('1') % 2 == y if x else False
)

# Cell
def iterate(protocol, eval_fns={}):
    """Iterator over protocol"""

    hist = {}
    node = "START"
    name_handler = lambda ast_node: hist.get(ast_node.id, None)

    if eval_fns: eval_fns.update(default_fns)
    else: eval_fns = default_fns

    while True:
        checks = protocol.checks(node)
        next_nodes = [(nn,c) for nn,c in checks.items() if simpleeval.simple_eval(c, names=name_handler, functions=eval_fns)]

        if len(next_nodes) == 0:
            yield None
        elif len(next_nodes) == 1:
            node, check_ret = next_nodes[0]

            if isinstance(check_ret, Circuit): # check return can be Circuit in case of COR nodes.
                protocol.update_node(node, check_ret)

            msmt = yield node
            hist[node] = hist.get(node,[]) + [msmt]
        else:
            raise Exception(f"Too many checks True for node {node}.")

# Cell
def save_protocol(protocol, fname, path='.'):
    """Saves a protocol to `path` with file name `fname`"""
    file = open(f'{path}/{fname}.proto', 'wb')
    pickle.dump(protocol,file)
    file.close()

# Cell
def load_protocol(fname, path='.'):
    """Loads a protocol from `path` with file name `fname`"""
    file = open(f'{path}/{fname}.proto', 'rb')
    res = pickle.load(file)
    file.close()
    return res