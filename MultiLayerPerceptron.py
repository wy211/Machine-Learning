import time
import random
import numpy as np
np.seterr(all = 'ignore')

# transfer functions
# we will use softmax for the output layer and tanh for the hidden layer
# the logit sigmoid transfer function is listed even though it's not used
def sigmoid(x):
    return 1 / (1 + np.exp(-x))

# derivative of sigmoid
def dsigmoid(y):
    return y * (1.0 - y)

# using softmax as output layer is recommended for classification where outputs are mutually exclusive
def softmax(w):
    e = np.exp(w - np.amax(w))
    dist = e / np.sum(e)
    return dist

def dsoftmax(y):
    return y * (1.0 - y)

# using tanh over logistic sigmoid for the hidden layer is recommended   
def tanh(x):
    return np.tanh(x)
    
# derivative for tanh sigmoid
def dtanh(y):
    return 1 - y*y

class MLP_Classifier(object):
    """
    Basic MultiLayer Perceptron (MLP) network, adapted and from the book 'Programming Collective Intelligence' (http://shop.oreilly.com/product/9780596529321.do)
    Consists of three layers: input, hidden and output. The sizes of input and output must match data
    the size of hidden is user defined when initializing the network.
    The algorithm has been generalized to be used on any dataset.
    As long as the data is in this format: [[[x1, x2, x3, ..., xn], [y1, y2, ..., yn]],
                                           [[[x1, x2, x3, ..., xn], [y1, y2, ..., yn]],
                                           ...
                                           [[[x1, x2, x3, ..., xn], [y1, y2, ..., yn]]]
    An example is provided below with the digit recognition dataset provided by sklearn
    Fully pypy compatible.
    """
    def __init__(self, input, hidden, output, iterations, learning_rate, momentum, rate_decay):
        """
        :param input: number of input neurons
        :param hidden: number of hidden neurons
        :param output: number of output neurons
        """
        # initialize parameters
        self.iterations = iterations
        self.learning_rate = learning_rate
        self.momentum = momentum
        self.rate_decay = rate_decay
        
        # initialize arrays
        self.input = input + 1 # add 1 for bias node
        self.hidden = hidden 
        self.output = output

        # set up array of 1s for activations
        self.ai = np.ones(self.input)
        self.ah = np.ones(self.hidden)
        self.ao = np.ones(self.output)

        # create randomized weights
        # use scheme from Efficient Backprop by LeCun 1998 to initialize weights
        input_range = 1.0 / self.input ** (1/2)
        output_range = 1.0 / self.hidden ** (1/2)
        self.wi = np.random.normal(loc = 0, scale = input_range, size = (self.input, self.hidden))
        self.wo = np.random.normal(loc = 0, scale = output_range, size = (self.hidden, self.output))
        
        # create arrays of 0 for changes
        # this is essentially an array of temporary values that gets updated at each iteration
        # based on how much the weights need to change in the following iteration
        self.ci = np.zeros((self.input, self.hidden))
        self.co = np.zeros((self.hidden, self.output))

    def feedForward(self, inputs):
        """
        The feedforward algorithm loops over all the nodes in the hidden layer and
        adds together all the outputs from the input layer * their weights
        the output of each node is the sigmoid function of the sum of all inputs
        which is then passed on to the next layer.
        :param inputs: input data
        :return: updated activation output vector
        """
        if len(inputs) != self.input-1:
            raise ValueError('Wrong number of inputs you silly goose!')

        # input activations
        self.ai[0:self.input -1] = inputs

        # hidden activations
        sum = np.dot(self.wi.T, self.ai)
        self.ah = tanh(sum)
        
        # output activations
        sum = np.dot(self.wo.T, self.ah)
        self.ao = softmax(sum)
        
        return self.ao

    def backPropagate(self, targets):
        """
        For the output layer
        1. Calculates the difference between output value and target value
        2. Get the derivative (slope) of the sigmoid function in order to determine how much the weights need to change
        3. update the weights for every node based on the learning rate and sig derivative

        For the hidden layer
        1. calculate the sum of the strength of each output link multiplied by how much the target node has to change
        2. get derivative to determine how much weights need to change
        3. change the weights based on learning rate and derivative
        :param targets: y values
        :param N: learning rate
        :return: updated weights
        """
        if len(targets) != self.output:
            raise ValueError('Wrong number of targets you silly goose!')

        # calculate error terms for output
        # the delta tell you which direction to change the weights
        #output_deltas = dsigmoid(self.ao) * (targets - self.ao) # sigmoid delta calculation
        output_deltas = targets - self.ao # softmax delta calculation
        
        # calculate error terms for hidden
        # delta tells you which direction to change the weights
        error = np.dot(self.wo, output_deltas)
        hidden_deltas = dtanh(self.ah) * error
        
        # update the weights connecting hidden to output
        change = output_deltas * np.reshape(self.ah, (self.ah.shape[0],1))
        self.wo += self.learning_rate * change + self.co * self.momentum
        self.co = change

        # update the weights connecting input to hidden
        change = hidden_deltas * np.reshape(self.ai, (self.ai.shape[0], 1))
        self.wi += self.learning_rate * change + self.ci * self.momentum
        self.ci = change

        # calculate error
        error = sum(0.5 * (targets - self.ao)**2)
        #error = -sum(targets * np.log(self.ao))
        
        return error

    def test(self, patterns):
        """
        Currently this will print out the targets next to the predictions.
        Not useful for actual ML, just for visual inspection.
        """
        for p in patterns:
            print(p[1], '->', self.feedForward(p[0]))

    def train(self, patterns):
        # N: learning rate
        for i in range(self.iterations):
            error = 0.0
            random.shuffle(patterns)
            for p in patterns:
                inputs = p[0]
                targets = p[1]
                self.feedForward(inputs)
                error += self.backPropagate(targets)
                
            with open('error.txt', 'a') as errorfile:
                errorfile.write(str(error) + '\n')
                errorfile.close()
                
            if i % 10 == 0:
                print('error %-.5f' % error)
                
            # learning rate decay
            self.learning_rate = self.learning_rate * (self.learning_rate / (self.learning_rate + (self.learning_rate * self.rate_decay)))
                
    def predict(self, X):
        """
        return list of predictions after training algorithm
        """
        predictions = []
        for p in X:
            predictions.append(self.feedForward(p))
        return predictions

def demo():
    """
    run NN demo on the digit recognition dataset from sklearn
    """
    def load_data():
        data = np.loadtxt('Data/sklearn_digits.csv', delimiter = ',')

        # first ten values are the one hot encoded y (target) values
        y = data[:,0:10]
        #y[y == 0] = -1 # if you are using a tanh transfer function make the 0 into -1
        #y[y == 1] = .90 # try values that won't saturate tanh
        
        data = data[:,10:] # x data
        #data = data - data.mean(axis = 1)
        data -= data.min() # scale the data so values are between 0 and 1
        data /= data.max() # scale
        
        out = []
        print data.shape

        # populate the tuple list with the data
        for i in range(data.shape[0]):
            fart = list((data[i,:].tolist(), y[i].tolist())) # don't mind this variable name
            out.append(fart)

        return out

    X = load_data()

    print X[9] # make sure the data looks right

    NN = MLP_NeuralNetwork(64, 100, 10, iterations = 50, learning_rate = 0.5, momentum = 0.5, rate_decay = 0.01)

    NN.train(X)

    NN.test(X)

if __name__ == '__main__':
    demo()
