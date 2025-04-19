# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/03_circuit.ipynb.

# %% auto 0
__all__ = ['GATES', 'unpack', 'draw_circuit', 'Circuit']

# %% ../nbs/03_circuit.ipynb 3
from collections.abc import MutableSequence
from functools import cached_property
from hashlib import sha1
import latextools
import stim

# %% ../nbs/03_circuit.ipynb 4
GATES = {
    "init": {"init"},
    "q1": {"I", "X", "Y", "Z", "H", "T", "Q", "Qd", "S", "Sd", "R", "Rd", "Rx", "Ry", "Rz"},
    "q2": {"CNOT", "MSd"},
    "meas": {"measure"}
}

# 
GATES_stim = {
    
    "q1": {"I", "X", "Y", "Z",
    "C_NXYZ", "C_NZYX", "C_XNYZ", "C_XYNZ", "C_XYZ", "C_ZNYX", "C_ZYNX", "C_ZYX",
    "H", "H_NXY", "H_NXZ", "H_NYZ", "H_XY", "H_XZ", "H_YZ",
    "S", "S_DAG",
    "SQRT_X", "SQRT_X_DAG", "SQRT_Y", "SQRT_Y_DAG", "SQRT_Z", "SQRT_Z_DAG"
                    }, 
        
    "q2":{"CNOT", "CX", "CXSWAP", "CY", "CZ", "CZSWAP",
    "II", "ISWAP", "ISWAP_DAG",
    "SQRT_XX", "SQRT_XX_DAG", "SQRT_YY", "SQRT_YY_DAG", "SQRT_ZZ", "SQRT_ZZ_DAG",
    "SWAP", "SWAPCX", "SWAPCZ",
    "XCX", "XCY", "XCZ", "YCX", "YCY", "YCZ", "ZCX", "ZCY", "ZCZ"
                            }, 
    
    "meas":{"M", "MR", "MRX", "MRY", "MRZ", "MX", "MY", "MZ", "R", "RX", "RY", "RZ", 
                    "MXX", "MYY", "MZZ", "MPP", "SPP", "SPP_DAG"}}


stim2qs_GATES = {
    "I":"I", "X":"X", "Y":"Y", "Z":"Z",
    "H":"H", "S":"S", "S_DAG":"Sd",
    "SQRT_X":"Q", "SQRT_X_DAG":"Qd", "SQRT_Y":"R", "SQRT_Y_DAG":"Rd", "SQRT_Z":"S", "SQRT_Z_DAG":"Sd",
    "CX":"CNOT", "CNOT":"CNOT"
}

qs2stim_GATES = {
    "I":"I", "X":"X", "Y":"Y", "Z":"Z",
    "H":"H", "S":"S", "S_DAG":"Sd",
    "Q":"SQRT_X", "Qd":"SQRT_X_DAG", "R":"SQRT_Y", "Rd":"SQRT_Y_DAG", "S":"SQRT_Z", "Sd":"SQRT_Z_DAG",
    "CNOT":"CNOT"
}

# %% ../nbs/03_circuit.ipynb 5
def unpack(seq):
    """Generator to unpack all values of dicts inside
    a list of dicts
    
    Parameters
    ----------
    seq : Iterable
        Iterable to recursively unpack
    """
    
    if isinstance(seq, (tuple,set,list,Circuit)):
        yield from (x for y in seq for x in unpack(y))
    elif isinstance(seq, dict):
        yield from (x for v in seq.values() for y in v for x in unpack(y))
    else:
        yield seq

# %% ../nbs/03_circuit.ipynb 6
def draw_circuit(circuit, path=None, scale=2):
    """Draw circuit using `latextools` library
    
    Parameters
    ----------
    circuit : Circuit
        The circuit to draw
    path : str or None
        The path to save the resulting image to (optional)
    scale : int
        The scale of the image
        
    Returns
    -------
    drawSvg.drawing.Drawing
        Image object
    """
    
    n_qubits = max(unpack(circuit)) + 1
    cmat = [["",""] + [r"\qw" for _ in range(circuit.n_ticks - 1)] for _ in range(n_qubits)]

    for col, tick in enumerate(circuit,1):
        for gate, qbs in tick.items():
            if gate in GATES['q2']:
                for qbtup in qbs:
                    ctrl, targ = qbtup[0], qbtup[1]
                    delta = targ - ctrl

                    cmat[ctrl][col] = r"\ctrl{%d}" % delta
                    sym = r"\targ" if gate == "CNOT" else r"\gate{%s}" % gate
                    cmat[targ][col] = sym
                continue
            elif gate == "measure": sym = r"\meter"
            elif gate == "init": sym = r"\push{\ket{0}}"

            elif gate in GATES['q1']: 
                sym = r"\gate{%s}" % gate
            else:
                raise Exception(f'Unknown gate {gate}')

            for row in qbs:
                cmat[row][col] = sym

    tex_str = r"\\".join([" & ".join([e for e in row]) for row in cmat])
    pdf = latextools.render_qcircuit(tex_str, const_row=False, const_col=True)
    svg = pdf.as_svg().as_drawing(scale=scale)
    if path: svg.saveSvg(path)
    return svg

def pair_elements(lst): # Helper function for converting 2 qubit gates from QSample to STIM
    return [(lst[i], lst[i + 1]) for i in range(0, len(lst), 2)]

# %% ../nbs/03_circuit.ipynb 7
class Circuit(MutableSequence):
    """Representation of a quantum circuit
    
    Attributes
    ----------
    _ticks : list of dict
        List of ticks in the circuit
    noisy : bool
        If true, circuit is subject to noise during sampling
    ff_deterministic : bool
        If true, the measurement result of the circuit in the
        fault-free case is always deterministic
    qubits : set
        Set of qubits "touched" by circuit
    n_qubits : int
        Numbers of qubits "touched" by circuit
    n_ticks : int
        Number of ticks in circuit
    id : str
        Unique circuit identifier
    """
    
    def __init__(self, ticks=None, noisy=True):
        """
        Parameters
        ----------
        ticks : list
            List of ticks defining a circuit
        noisy : bool
            If true, circuit is subject to noise during sampling
        """
        if isinstance(ticks, str): # If input is a STIM circuit
            self._ticks = ["foo"]
            
            for instruction in ticks.split('\n'):
                instruction_list = instruction.split(' ')
                is_target = False
                target_list = []
                for i in instruction_list:
                    if len(i)!=0 and not is_target:
                        name = i
                        is_target = True
                    elif len(i)!=0:
                        target_list.append(int(i))
                            
                if name in GATES_stim["q1"]:
                    try:
                        qs_gate = stim2qs_GATES[name]
                    except KeyError:
                        print("Gate {} not implemented in QSample".format(name))
                        break
                    
                    targets = set()
                    for target in target_list:
                        targets.update({target})
                    tick = {qs_gate: targets}
                    self._ticks.insert(-1, tick)

                elif name in GATES_stim["q2"]:
                    try:
                        qs_gate = stim2qs_GATES[name]
                    except KeyError:
                        print("Gate {} not implemented in QSample".format(name))
                        break

                    for target in pair_elements(target_list):
                        tick = {qs_gate: {target}}
                        self._ticks.insert(-1, tick)

                elif name in GATES_stim["meas"]:
                    targets = set()
                    for target in target_list:
                        targets.update({target})

                    if name=="M":
                        self._ticks.insert(-1, {"measure": targets})
                    elif name=="R":
                        self._ticks.insert(-1, {"init": targets})
                    elif name=="MR":
                        self._ticks.insert(-1, {"measure": targets})
                        self._ticks.insert(-1, {"init": targets})
                    else:
                        print("Gate {} not implemented in QSample".format(name))
                        break
            self.__delitem__(-1)

        else:
            self._ticks = ticks if ticks else [] # Must do this way, else keeps appending to same instance
        self.noisy = noisy
        
    def __getitem__(self, tick_index):
        return self._ticks[tick_index]
    
    def __setitem__(self, tick_index, tick):
        self._ticks[tick_index] = tick
        
    def __delitem__(self, tick_index):
        del self._ticks[tick_index]
        
    def __len__(self):
        return len(self._ticks)
    
    def insert(self, tick_index, tick):
        """Insert a tick into a circuit
        
        Parameters
        ----------
        tick_index : int
            Index at which tick is inserted (tick indices to right incremented by 1)
        tick : dict
            Tick dictionary to insert
        """
        self._ticks.insert(tick_index, tick)
    
    def __str__(self):
        if self._ticks == []:
            return "__empty__"
        str_list = []
        for i, tick in enumerate(self._ticks):
            str_list.append(f"{i}: {str(tick)}")
        return "\n".join(str_list)
    
    @cached_property
    def qubits(self):  
        """Set of qubits used in circuit"""
        return set(unpack(self._ticks))
    
    @cached_property
    def n_qubits(self):
        """Number of qubits used in circuit"""
        return len(self.qubits)
    
    @cached_property
    def n_ticks(self):
        """Number of ticks"""
        return len(self._ticks)
    
    @cached_property    
    def measured_qubits(self):
        """Set of qubits measured in circuit"""
        measured_qubits = set()
        for i, tick in enumerate(self._ticks):
            if list(tick.keys())[0] == "measure":
                measured_qubits.update(list(tick.values())[0])
                        
        return list(measured_qubits)
    
    @cached_property 
    def n_measurements(self):
        """Number of measured qubits in the circuit"""
        return len(self.measured_qubits)
    
    @property
    def id(self):
        """Unique circuit identifier"""
        return sha1((repr(self)).encode('UTF-8')).hexdigest()[:5]

    def draw(self, path=None, scale=2):
        """Draw the circuit"""
        return draw_circuit(self, path, scale)
    
    
def qs2stim(circuit):
    stim_circuit = ""
    for tick in circuit._ticks:
        name = list(tick.keys())[0]
        
        if name in GATES["q1"]:
            try:
                instruction = qs2stim_GATES[name]+" "
            except KeyError:
                print("Gate {} not implemented in STIM".format(name))
                break
            for i in list(tick.values())[0]:
                instruction += str(i)
                instruction += " "
            stim_circuit+=(instruction+"\n")
            
        if name in GATES["q2"]:
            try:
                instruction = qs2stim_GATES[name]+" "
            except KeyError:
                print("Gate {} not implemented in STIM".format(name))
                break
            for i in list(tick.values())[0]:
                instruction += (str(i[0])+ " " + str(i[1]) + "\n")
                instruction += "TICK"
            stim_circuit+=(instruction+"\n")
            
        if name in GATES["meas"]:
            instruction = "M "
            for i in list(tick.values())[0]:
                instruction += str(i)
                instruction += " "
            stim_circuit+=(instruction+"\n")
        
        if name in GATES["init"]:
            instruction = "R "
            for i in list(tick.values())[0]:
                instruction += str(i)
                instruction += " "
            stim_circuit+=(instruction+"\n")
                
    return stim_circuit


def stim2qs(circuit, noisy=True):
    qs_circuit = Circuit([{"I": {1}}], noisy=noisy)
    for instruction in circuit:
        name = instruction.name
        targets = set()
        if name in GATES_stim["q1"]:
            try:
                qs_gate = stim2qs_GATES[name]
            except KeyError:
                print("Gate {} not implemented in QSample".format(name))
                break
                
            for target in instruction.target_groups():
                targets.update({target[0].value})
            tick = {qs_gate: targets}
            qs_circuit.insert(-1, tick)
        
        elif name in GATES_stim["q2"]:
            try:
                qs_gate = stim2qs_GATES[name]
            except KeyError:
                print("Gate {} not implemented in QSample".format(name))
                break
            
            for target in instruction.target_groups():
                tick = {qs_gate: {(target[0].value, target[1].value)}}
                qs_circuit.insert(-1, tick)
            
        elif name in GATES_stim["meas"]:
            targets = set()
            for target in instruction.target_groups():
                targets.update({target[0].value})
                
            if name=="M":
                qs_circuit.insert(-1, {"measure": targets})
            elif name=="R":
                qs_circuit.insert(-1, {"init": targets})
            elif name=="MR":
                qs_circuit.insert(-1, {"measure": targets})
                qs_circuit.insert(-1, {"init": targets})
            else:
                print("Gate {} not implemented in QSample".format(name))
                break
        
        #qs_circuit.__delitem__(2)
    return qs_circuit