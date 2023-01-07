import os


learning_rates = [0.00001, 0.0005, 0.01]
hidden_sizes = [100, 200]
dropout_probs = [0.3, 0.5]
activation = ['relu', 'tanh']

hp_search_arguments = ['-learning_rate 0.001 -optimizer adam', '-learning_rate 0.01 -optimizer adam', '-learning_rate 0.1 -optimizer adam']

for arg in hp_search_arguments:
    print('****************************************************************************************************************')
    print('Training model with hp_search_arguments', arg)
    print('****************************************************************************************************************')
    os.system('python hw1-q2.py mlp {}'.format(arg))