import os

hp_search_arguments = ['-learning_rate 0.00001 -optimizer "adam" -dropout 0.3', 
                       '-learning_rate 0.0005 -optimizer "adam" -dropout 0.3', 
                       '-learning_rate 0.01 -optimizer "adam" -dropout 0.3']

for arg in hp_search_arguments:
    print('****************************************************************************************************************')
    print('Training model with hp_search_arguments', arg)
    print('****************************************************************************************************************')
    os.system('python hw2-q2.py {}'.format(arg))