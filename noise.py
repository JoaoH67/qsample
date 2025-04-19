# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/07_noise.ipynb.

# %% auto 0
__all__ = ['DEPOLAR1', 'DEPOLAR2', 'XFLIP', 'ZFLIP', 'ErrorModel', 'E0', 'E1', 'E1_1', 'E2', 'E3', 'E3_1', 'S4', 'S1', 'S2']

# %% ../nbs/07_noise.ipynb 3
import numpy as np
import stim
from .circuit import Circuit, GATES, GATES_stim, unpack

# %% ../nbs/07_noise.ipynb 5
DEPOLAR1 = {"X", "Y", "Z"}
DEPOLAR2 = {('I', 'X'), ('I', 'Y'), ('I', 'Z'),
            ('X', 'I'), ('X', 'X'), ('X', 'Y'), ('X', 'Z'),
            ('Y', 'I'), ('Y', 'X'), ('Y', 'Y'), ('Y', 'Z'),
            ('Z', 'I'), ('Z', 'X'), ('Z', 'Y'), ('Z', 'Z')}
XFLIP = {"X"}
ZFLIP = {"Z"}

# %% ../nbs/07_noise.ipynb 6
class ErrorModel:
    """Representation of an incoherent error model."""
    
    groups = []
    
    def group(self, circuit):
        """Must be implemented by subclass"""
        raise NotImplemented
        
    def generate(self, fgroups, circuit):
        """Must be implemented by subclass"""
        raise NotImplemented
  
    @staticmethod
    def choose_p(groups: dict, probs: list):
        """Select elements from group g_i with probability p_i."""
        return {grp: [loc for loc in locs if np.random.random() < prob] 
                for (grp,locs), prob in zip(groups.items(), probs)}
    
    @staticmethod
    def choose_w(groups: dict, weights: list):
        """Select w_i locations for group g_i in groups"""
        return {grp: [locs[i] for i in np.random.choice(len(locs), weight, replace=False)]
                for (grp,locs),weight in zip(groups.items(), weights)}
    
    def run(self, circuit, fgroups):
        """Generate new Circuit of same length as `Circuit` with faults generated
        by `self.generate` and corresponding location for each group in fgroups."""
        
        
        fault_circuit = Circuit([{} for _ in range(circuit.n_ticks)])
        for (tidx, qb), fop in self.generate(fgroups, circuit):
            if isinstance(qb, tuple):
                for q,op in zip(qb,fop):
                    if op == "I": continue
                    qbs = fault_circuit[tidx].get(op,set())
                    qbs.add(q)
                    fault_circuit[tidx][op] = qbs
            elif isinstance(qb, int):
                qbs = fault_circuit[tidx].get(fop,set())
                qbs.add(qb)
                fault_circuit[tidx][fop] = qbs
        return fault_circuit 

# %% ../nbs/07_noise.ipynb 7
class E0(ErrorModel):
    """No-Error error model"""
    
    groups = ["0"]
    
    def group(self, circuit):
        return {"0": {}}
    
    def run(self, *args, **kwargs):
        return None

# %% ../nbs/07_noise.ipynb 8
class E1(ErrorModel):
    """One prob/weight for all 1- and 2-qubit gates"""
    
    groups = ["q"]
    
    def group(self, circuit):
                
        gates = GATES["q1"] | GATES["q2"]
        if len(circuit)>1000:
            print(circuit)
        return {"q": [(ti,q) for ti,t in enumerate(circuit) for g,qs in t.items() for q in qs if g in gates]}
    
    def generate(self, fgroups, circuit):
        
        errsets = {
            "q1": DEPOLAR1,
            "q2": DEPOLAR2
        }
                
        for grp, locs in fgroups.items():
            for loc in locs:
                if isinstance(loc[1], tuple):
                    errset = errsets["q2"]
                else:
                    errset = errsets["q1"]
                fop = list(errset)[np.random.choice(len(errset))]
                yield loc, fop

# %% ../nbs/07_noise.ipynb 9
class E1_1(ErrorModel):
    """One prob/weight for all 1- and 2-qubit gates and measurements"""
    
    groups = ["q"]
    
    def group(self, circuit):
        gates = GATES["q1"] | GATES["q2"] | GATES["meas"]
        return {"q": [(ti,q) for ti,t in enumerate(circuit) for g,qs in t.items() for q in qs if g in gates]}
    
    def generate(self, fgroups, circuit):
        
        errsets = {
            "q1": DEPOLAR1,
            "q2": DEPOLAR2
        }
                
        for grp, locs in fgroups.items():
            for loc in locs:
                if isinstance(loc[1], tuple):
                    errset = errsets["q2"]
                else:
                    errset = errsets["q1"]
                fop = list(errset)[np.random.choice(len(errset))]
                yield loc, fop

# %% ../nbs/07_noise.ipynb 10
class E2(ErrorModel):
    """Individual errors on 1-qubit and 2-qubit gates."""
    
    groups = ["q1", "q2"]
    
    def group(self, circuit):
        gates = {"q1": GATES["q1"], "q2": GATES["q2"]}
        return {grp: [(ti,q) for ti,t in enumerate(circuit) for g,qs in t.items() 
                      for q in qs if g in gset] for grp,gset in gates.items()}
    
    def generate(self, fgroups, circuit):
        errsets = {
            "q1": DEPOLAR1,
            "q2": DEPOLAR2
        }
        
        for grp, locs in fgroups.items():
            for loc in locs:
                if isinstance(loc[1], tuple):
                    errset = errsets["q2"]
                else:
                    errset = errsets["q1"]
                fop = list(errset)[np.random.choice(len(errset))]
                yield loc, fop

# %% ../nbs/07_noise.ipynb 11
class E3(ErrorModel):
    """Errors on all gates individual + idle."""
    
    groups = ["q1", "q2", "meas", "idle", "init"]
    
    def group(self, circuit):
        groups =  {grp: [(ti,q) for ti,t in enumerate(circuit) for g,qs in t.items() 
                         for q in qs if g in gset] for grp,gset in GATES.items()}
        qbs = set(unpack(circuit))
        groups['idle'] = [(ti,q) for ti,t in enumerate(circuit) for q in qbs.difference(set(unpack(t)))]
        return groups
    
    def generate(self, fgroups, circuit):
        
        errsets = {
            'q1': DEPOLAR1,
            'q2': DEPOLAR2,
            'meas': XFLIP,
            'idle': ZFLIP,
            'init': XFLIP   
        }
        
        for grp, locs in fgroups.items():
            for loc in locs:
                fop = list(errsets[grp])[np.random.choice(len(errsets[grp]))]
                yield loc, fop

# %% ../nbs/07_noise.ipynb 12
class E3_1(ErrorModel):
    """Like E3, but idle locations split in two subsets."""
    
    groups = ["q1", "q2", "meas", "idle1", "idle2", "init"]
    
    def group(self, circuit):
        groups =  {i: [(ti,q) for ti,t in enumerate(circuit) for g,qs in t.items() 
                          for q in qs if g in gset] for i,gset in GATES.items()}
        qbs = set(unpack(circuit))
        groups['idle1'] = [(ti,q) for ti,t in enumerate(circuit) 
                           for q in qbs.difference(set(unpack(t))) 
                           if not any([op in GATES['q2'] for op in t.keys()])]
        groups['idle2'] = [(ti,q) for ti,t in enumerate(circuit) 
                           for q in qbs.difference(set(unpack(t))) 
                           if any([op in GATES['q2'] for op in t.keys()])]
        return groups
    
    def generate(self, fgroups, circuit):
        
        errsets = {
            'q1': DEPOLAR1,
            'q2': DEPOLAR2,
            'meas': XFLIP,
            'idle1': DEPOLAR1,
            'idle2': DEPOLAR1,
            'init': XFLIP   
        }
        
        for grp, locs in fgroups.items():
            for loc in locs:
                fop = list(errsets[grp])[np.random.choice(len(errsets[grp]))]
                yield loc, fop

# %% ../nbs/07_noise.ipynb 13
class S4(ErrorModel):
    """Depolarizing noise on all operations, 4 parameters"""
    groups = ["q1", "q2", "meas", "init"]

    def group(self, circuit):
        groups = {grp: [(ti, q) for ti, t in enumerate(circuit) for g, qs in t.items()
                        for q in qs if g in gset] for grp, gset in GATES.items()}
        qbs = set(unpack(circuit))
        return groups

    def generate(self, fgroups, circuit):

        errsets = {
            'q1': DEPOLAR1,
            'q2': DEPOLAR2,
            'meas': DEPOLAR1,
            'init': DEPOLAR1
        }

        for grp, locs in fgroups.items():
            for loc in locs:
                fop = list(errsets[grp])[np.random.choice(len(errsets[grp]))]
                yield loc, fop

# %% ../nbs/07_noise.ipynb 14
class S1(ErrorModel):
    """Single parameter depolarizing noise on all operations
    
    See App. D and sections 3B and 3D in paper
    
    """
    groups = ["q"]

    def group(self, circuit):
        gates = GATES["q1"] | GATES["q2"] | GATES["meas"] | GATES["init"]
        return {"q": [(ti, q) for ti, t in enumerate(circuit) for g, qs in t.items() for q in qs if g in gates]}

    def generate(self, fgroups, circuit):

        errsets = {
            "q1": DEPOLAR1,
            "q2": DEPOLAR2,
            'meas': DEPOLAR1,
            'init': DEPOLAR1
        }

        for grp, locs in fgroups.items():
            for loc in locs:
                if isinstance(loc[1], tuple):
                    errset = errsets["q2"]
                else:
                    errset = errsets["q1"]
                fop = list(errset)[np.random.choice(len(errset))]
                yield loc, fop

# %% ../nbs/07_noise.ipynb 15
class S2(ErrorModel):
    """Individual errors on 1-qubit and 2-qubit gates. Depolarizing noise with 1-qubit rate on init and meas
    
    See App. D and section 3C in paper
    
    """
    groups = ["q1", "q2"]

    def group(self, circuit):
        gates = {"q1": GATES["q1"] | GATES["meas"] | GATES["init"], "q2": GATES["q2"]}
        return {grp: [(ti, q) for ti, t in enumerate(circuit) for g, qs in t.items()
                      for q in qs if g in gset] for grp, gset in gates.items()}

    def generate(self, fgroups, circuit):
        errsets = {
            "q1": DEPOLAR1,
            "q2": DEPOLAR2
        }

        for grp, locs in fgroups.items():
            for loc in locs:
                if isinstance(loc[1], tuple):
                    errset = errsets["q2"]
                else:
                    errset = errsets["q1"]
                fop = list(errset)[np.random.choice(len(errset))]
                yield loc, fop
