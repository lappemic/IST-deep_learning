#!/usr/bin/env python

# Deep Learning Homework 2

import argparse

import torch
from torch.utils.data import DataLoader
import torch.nn as nn
from torch import optim
import torch.nn.functional as F
import torchvision
from matplotlib import pyplot as plt
import numpy as np

import utils

class CNN(nn.Module):
    
    def __init__(self, dropout_prob):
        """
        The __init__ should be used to declare what kind of layers and other
        parameters the module has. For example, a CNN module has convolution,
        max pooling, activation, linear, and other types of layers. For an 
        idea of how to us pytorch for this have a look at
        https://pytorch.org/docs/stable/nn.html
        """
        super(CNN, self).__init__()
        # image shape: [28, 28]
        self.conv1 = nn.Conv2d(1, 8, kernel_size=(5, 5), stride=(1, 1), padding=(2, 2)) # TODO: Include padding=() -> preserve image size
        # image shape: [28, 28]
        self.pool = nn.MaxPool2d(kernel_size=(2, 2), stride=(2, 2))
        # image shape: [14, 14]
        self.conv2 = nn.Conv2d(8, 16, kernel_size=(3, 3), stride=(1, 1), padding=0)
        # image shape: [12, 12]
        # TODO: check again affine transformation 1:
        # Nr. of input features = number of output channels (16) x output width (6) x output height (6)
        self.fc1 = nn.Linear(16*6*6, 600)
        # image shape: [600]... # TODO: What is exact image shape here?
        self.dropout = nn.Dropout(p=dropout_prob)
        # TODO: check again affine transformation 2 and 3:
        self.fc2 = nn.Linear(600, 120) # (# of output features fc1, # given)
        self.fc3 = nn.Linear(120, 10) # (# of ouput features fc2, # classes)
        
    def forward(self, x):
        """
        x (batch_size x n_channels x height x width): a batch of training 
        examples

        Every subclass of nn.Module needs to have a forward() method. forward()
        describes how the module computes the forward pass. This method needs 
        to perform all the computation needed to compute the output from x. 
        This will include using various hidden layers, pointwise nonlinear 
        functions, and dropout. Don't forget to use logsoftmax function before 
        the return

        One nice thing about pytorch is that you only need to define the
        forward pass -- this is enough for it to figure out how to do the
        backward pass.
        """
        # print('x.shape:', x.shape)
        # x.shape = [8, 1, 28, 28]
        x = self.pool(F.relu(self.conv1(x)))
        # x.shape from convolution = [8, 1, 24, 24]
        # x.shape from maxpool = [8, 1, 12, 12]
        x = self.pool(F.relu(self.conv2(x)))
        # x.shape from conv = [8, 1, 10, 10]
        # x.shape from maxpool = [8, 1, 6, 6]
        # print('x.shape after second convo:', x.shape)
        # x = torch.flatten(x, 1) # flatten all dimensions except batch
        # print('x.shape aftre flattening:', x.shape)
        x = x.view(x.size(0), -1) # TODO: Check if torch.flatten of x.view is needed - not verified yet
        # print('x.shape after view:', x.shape)
        x = F.relu(self.dropout(self.fc1(x))) # changing order of activation and droput due to computational efficiency
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        x = F.log_softmax(x, dim=1)
        
        return x
        

def train_batch(X, y, model, optimizer, criterion, **kwargs):
    """
    X (n_examples x n_features)
    y (n_examples): gold labels
    model: a PyTorch defined model
    optimizer: optimizer used in gradient step
    criterion: loss function

    To train a batch, the model needs to predict outputs for X, compute the
    loss between these predictions and the "gold" labels y using the criterion,
    and compute the gradient of the loss with respect to the model parameters.

    Check out https://pytorch.org/docs/stable/optim.html for examples of how
    to use an optimizer object to update the parameters.

    This function should return the loss (tip: call loss.item()) to get the
    loss as a numerical value that is not part of the computation graph.
    """
    # print('X.shape:', X.shape)
    optimizer.zero_grad()
    y_pred = model(X)
    # print('y_pred.shape:', y_pred.shape)
    # print('y_pred:', y_pred)
    # print('y.shape:', y.shape)
    # print('y:', y)
    loss = criterion(y_pred, y)
    loss.backward()
    optimizer.step()
    
    return loss.item()

def predict(model, X):
    """X (n_examples x n_features)"""
    scores = model(X)  # (n_examples x n_classes)
    predicted_labels = scores.argmax(dim=-1)  # (n_examples)
    return predicted_labels


def evaluate(model, X, y):
    """
    X (n_examples x n_features)
    y (n_examples): gold labels
    """
    model.eval()
    y_hat = predict(model, X)
    n_correct = (y == y_hat).sum().item()
    n_possible = float(y.shape[0])
    model.train()
    return n_correct / n_possible


def plot(epochs, plottable, ylabel='', name=''):
    plt.clf()
    plt.xlabel('Epoch')
    plt.ylabel(ylabel)
    plt.plot(epochs, plottable)
    plt.savefig('%s.png' % (name), bbox_inches='tight')


activation = {}
def get_activation(name):
    def hook(model, input, output):
        activation[name] = output.detach()
    return hook

def plot_feature_maps(model, train_dataset):
    
    model.conv1.register_forward_hook(get_activation('conv1'))
    
    data, _ = train_dataset[4]
    data.unsqueeze_(0)
    output = model(data)

    plt.imshow(data.reshape(28,-1)) 
    plt.savefig('original_image.png')

    k=0
    act = activation['conv1'].squeeze()
    fig,ax = plt.subplots(2,4,figsize=(12, 8))
    
    for i in range(act.size(0)//3):
        for j in range(act.size(0)//2):
            ax[i,j].imshow(act[k].detach().cpu().numpy())
            k+=1  
            plt.savefig('activation_maps.png') 


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-epochs', default=20, type=int,
                        help="""Number of epochs to train for. You should not
                        need to change this value for your plots.""")
    parser.add_argument('-batch_size', default=8, type=int,
                        help="Size of training batch.")
    parser.add_argument('-learning_rate', type=float, default=0.01,
                        help="""Learning rate for parameter updates""")
    parser.add_argument('-l2_decay', type=float, default=0)
    parser.add_argument('-dropout', type=float, default=0.8)
    parser.add_argument('-optimizer',
                        choices=['sgd', 'adam'], default='sgd')
    
    opt = parser.parse_args()

    utils.configure_seed(seed=42)

    data = utils.load_classification_data()
    dataset = utils.ClassificationDataset(data)
    train_dataloader = DataLoader(
        dataset, batch_size=opt.batch_size, shuffle=True)
    dev_X, dev_y = dataset.dev_X, dataset.dev_y
    test_X, test_y = dataset.test_X, dataset.test_y

    # initialize the model
    model = CNN(opt.dropout)
    
    # get an optimizer
    optims = {"adam": torch.optim.Adam, "sgd": torch.optim.SGD}

    optim_cls = optims[opt.optimizer]
    optimizer = optim_cls(
        model.parameters(), lr=opt.learning_rate, weight_decay=opt.l2_decay
    )
    
    # get a loss criterion
    criterion = nn.NLLLoss()
    
    # training loop
    epochs = np.arange(1, opt.epochs + 1)
    train_mean_losses = []
    valid_accs = []
    train_losses = []
    for ii in epochs:
        print('########### Training epoch {} #############'.format(ii))
        for X_batch, y_batch in train_dataloader:
            # print('X_batch.shape:', X_batch.shape)
            # print('X_batch[1]:', X_batch[1])
            loss = train_batch(
                X_batch, y_batch, model, optimizer, criterion)
            train_losses.append(loss)

        mean_loss = torch.tensor(train_losses).mean().item()
        print(' -Training loss: %.4f' % (mean_loss))

        train_mean_losses.append(mean_loss)
        valid_accs.append(evaluate(model, dev_X, dev_y))
        print(' -Valid acc: %.4f' % (valid_accs[-1]))

    print('Final Test acc: %.4f' % (evaluate(model, test_X, test_y)))
    # plot
    config = "{}-{}-{}-{}".format(opt.learning_rate, opt.dropout, opt.l2_decay, opt.optimizer)

    plot(epochs, train_mean_losses, ylabel='Loss', name='CNN-training-loss-{}'.format(config))
    plot(epochs, valid_accs, ylabel='Accuracy', name='CNN-validation-accuracy-{}'.format(config))
    
    plot_feature_maps(model, dataset)

if __name__ == '__main__':
    main()
