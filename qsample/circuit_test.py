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