import qsample as qs
import qiskit
import time
import stim
import numpy as np
import matplotlib.pyplot as plt
import time
import re
from tqdm.notebook import tqdm

def Conversion_test():
    test_circuit_1 = qs.Circuit([  {"init": {0,1,2,4,3,5,6,7}},
                        {"H": {0,1,3}},
                        {"CNOT": {(0,4)}},
                        {"CNOT": {(1,2)}},
                        {"CNOT": {(3,5)}},
                        {"Qd": {5,6,7}},
                        {"S": {4,1,2}},
                        {"Rd": {3,5,7}},
                        {"measure": {7}} ], noisy=False)

    stim_circuit_1 = test_circuit_1.to_stim_circuit

    test_circuit_2 = qs.Circuit(noisy=False).from_stim_circuit(repr(stim_circuit_1))
    stim_circuit_2 = test_circuit_2.to_stim_circuit

    assert stim_circuit_1.__eq__(stim_circuit_2)




fails = []

def Steane_test():
    eft = qs.Circuit(noisy=True)
    sz_123 = qs.Circuit(noisy=True)
    meas7 = qs.Circuit(noisy=False)

    eft.from_stim_circuit("""R 0 1 2 3 4 5 6 7
    H 0 1 3
                            CNOT 0 4 1 2 3 5 0 6 3 4 1 5 0 2 5 6 4 7 2 7 5 7
                            M 7""")

    sz_123.from_stim_circuit("""R 8
    CNOT 0 8 1 8 3 8 6 8
                                M 8""")

    meas7.from_stim_circuit("""M 0 1 2 3 4 5 6""")





    k1 = 0b0001111
    k2 = 0b1010101
    k3 = 0b0110011
    k12 = k1 ^ k2
    k23 = k2 ^ k3
    k13 = k1 ^ k3
    k123 = k12 ^ k3
    stabilizerGenerators = [k1, k2, k3]
    stabilizerSet = [0, k1, k2, k3, k12, k23, k13, k123]

    def hamming2(x, y):
        count, z = 0, x ^ y
        while z:
            count += 1
            z &= z - 1
        return count

    
    def logErr(out):
        global fails
        c = np.array([hamming2(out, i) for i in stabilizerSet])
        d = np.flatnonzero(c <= 1)
        e = np.array([hamming2(out ^ (0b1111111), i) for i in stabilizerSet])
        f = np.flatnonzero(e <= 1)
        if len(d) != 0:
            return False
        elif len(f) != 0:
            fails.append(out)
            return True
        if len(d) != 0 and len(f) != 0: 
            raise('-!-!-CANNOT BE TRUE-!-!-')

    def flagged_z_look_up_table_1(z):
        s = [z]

        if s == [1]:
            return True
        else: 
            return False

    functions = {"logErr": logErr, "lut": flagged_z_look_up_table_1}

    steane0 = qs.Protocol(check_functions=functions, fault_tolerant=True)

    steane0.add_nodes_from(['ENC', 'Z2', 'meas'], circuits=[eft, sz_123, meas7])
    steane0.add_node('X_COR', circuit=qs.Circuit(noisy=True).from_stim_circuit("""X 6"""))
    steane0.add_edge('START', 'ENC', check='True')
    steane0.add_edge('ENC', 'meas', check='ENC[-1]==0')
    steane0.add_edge('ENC', 'Z2', check='ENC[-1]==1')
    steane0.add_edge('Z2', 'X_COR', check='lut(Z2[-1])')
    steane0.add_edge('Z2', 'meas', check='not lut(Z2[-1])')
    steane0.add_edge('X_COR', 'meas', check='True')
    steane0.add_edge('meas', 'FAIL', check='logErr(meas[-1])')
    
    
    err_model = qs.noise.E1
    q = [1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 0.5]
    err_params = {'q': q}

    begin = time.time()
    stim_sam = qs.SubsetSampler(protocol=steane0, simulator=qs.StimSimulator,  p_max={'q': 0.1}, err_model=err_model, err_params=err_params, L=3)
    stim_sam.run(2000)
    end = time.time()
    stim_time = end-begin

    v2 = stim_sam.stats()[0]
    w2 = stim_sam.stats()[2]
    
    plt.plot(q, v2, label = "Input = STIM")
    plt.plot(q, w2)


    plt.xscale('log')
    plt.yscale('log')
    plt.legend()

    print(stim_time)