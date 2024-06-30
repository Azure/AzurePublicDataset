import numpy as np
import scipy.optimize as opt
import matplotlib.pyplot as plt
import warnings

# ignore warnings
warnings.filterwarnings("ignore")

def exponential_func(x, a, b, c):
    return a * np.exp(-b * x) + c

def linear_func(x, a, b):
    return a * x + b

def quadratic_func(x, a, b, c):
    return a * x**2 + b * x + c

def cubic_func(x, a, b, c, d):
    return a * x**3 + b * x**2 + c * x + d

# check if data forms horizontal line - if so, return horizontal line
def check_horizontal(x_data, y_data):
    if len(set(y_data)) == 1:
        # return function that works with both scalar and array inputs
        return lambda x: np.ones(np.array(x).shape) * y_data[0]
    return None

# fit function to data
def fit(func, x_data, y_data, plot=False):
    # popt: optimal values for the parameters
    # pcov: covariance matrix
    if isinstance(x_data, list):
        x_data = np.array(x_data)
    if isinstance(y_data, list):
        y_data = np.array(y_data)
    popt, pcov = opt.curve_fit(func, x_data, y_data)

    if plot:
        x_fit = np.linspace(x_data[0], x_data[-1], 100)
        y_fit = func(x_fit, *popt)
        plt.plot(x_data, y_data, 'o', label='data')
        plt.plot(x_fit, y_fit, label='fit')
        plt.legend()
        plt.show()
    
    # return func with optimal parameters
    return lambda x: func(x, *popt)

def fit_cubic(data_dict, plot=False):
    x_data = [float(x) for x in data_dict]
    y_data = [float(y) for y in data_dict.values()]
    # check if data forms horizontal line - if so, return horizontal line
    horizontal = check_horizontal(x_data, y_data)
    if horizontal:
        if plot:
            x_fit = np.linspace(x_data[0], x_data[-1], 100)
            y_fit = horizontal(x_fit)
            plt.plot(x_data, y_data, 'o', label='data')
            plt.plot(x_fit, y_fit, label='fit')
            plt.legend()
            plt.show()
        return horizontal
    return fit(cubic_func, x_data, y_data, plot)
