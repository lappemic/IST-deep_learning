# Character-level Machine Translation 
A vanilla characterlevel machine translation model using an encoder-decoder architecture with an autoregressive LSTM as the decoder and a Bidirectional LSTM in the encoder is implemented. At each 
time-step, the LSTM decoder receives as input the embedding of the current word, then each output at each timestep has dropout applied and the resulting decoder state is 
used in the next timestep. In the end, all decoder outputs are concatenated to form an output sequence.  
An attention mechanism is added to the decoder (bilinear attention), which weights the contribution of the diﬀerent source characters, according to relevance for the current prediction.\

The model can be used as follows:
```python
python hw2-q3.py [-h] [--lr LR] [--dropout DROPOUT] [--n_epochs N_EPOCHS] [--batch_size BATCH_SIZE] 
			[--hidden_size HIDDEN_SIZE] [--seed SEED] [--use_attn]
```

to use the model with the default values, use the following command:
```python
python hw2-q3.py
```

Like that the model is trained with 50 epochs, learning rate of 0.003, a dropout rate of 0.3, a hidden size of 128, and a batch size of 64 and Adam as optimizer.
