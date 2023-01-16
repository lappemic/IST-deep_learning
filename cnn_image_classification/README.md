# Image Classification with CNNs
A convolutional neural network is implemented to perform classification using the Kuzushiji-MNIST dataset. The network has the following structure:
-  A convolution layer with 8 output channels, a kernel of size 5x5, stride of 1, and padding of 2 to preserve the original image size.

- A rectiﬁed linear unit activation function.

- A max pooling with kernel size 2x2 and stride of 2.

- A convolution layer with 16 output channels, a kernel of size 3x3, stride of 1, and padding of zero.

- A rectiﬁed linear unit activation function.

- A max pooling with kernel size 2x2 and stride of 2.

- An aﬃne transformation with 600 output features (to determine the number of input features use the number of channels, width and height of the output of the second block. Hint: The number of input 
features = number of output channels × output width × output height).

- A rectiﬁed linear unit activation function.

- A dropout layer with a dropout probability of 0.3.

- An aﬃne transformation with 120 output features.

- A rectiﬁed linear unit activation function.

- An aﬃne transformation with the number of classes followed by an output LogSoftmax layer.

The model can be used as follows:
````python
python hw2-q2.py [-h] [-epochs EPOCHS] [-batch_size BATCH_SIZE] [-learning_rate LEARNING_RATE] [-l2_decay L2_DECAY] [-dropout DROPOUT] [-optimizer {sgd,adam}]
```
