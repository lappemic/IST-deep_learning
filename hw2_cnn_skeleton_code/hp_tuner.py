import os

hp_search_arguments = ['-learning_rate 0.001 -optimizer "adam"', '-learning_rate 0.01 -optimizer "adam"', '-learning_rate 0.1 -optimizer "adam"']

for arg in hp_search_arguments:
    print('****************************************************************************************************************')
    print('Training model with hp_search_arguments', arg)
    print('****************************************************************************************************************')
    os.system('python hw2-q2.py mlp {}'.format(arg))