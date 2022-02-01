from __future__ import print_function, division
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim import lr_scheduler
import torchvision
from torchvision import datasets, models, transforms
import matplotlib.pyplot as plt
import numpy as np
import time
import os
import copy
import pandas as pd
print(
    torch.cuda.is_available(),
    torch.cuda.current_device(),
    torch.cuda.get_device_name(0),
    sep='\n'
)
data_info = r'dataset\data_info.csv'
df = pd.read_csv(data_info, header=0)
print(df.head(5))