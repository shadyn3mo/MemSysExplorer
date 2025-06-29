import torch
import torch.nn as nn
import torch.nn.functional as F

class LeNet(nn.Module):
    def __init__(self, num_classes=10):
        super(LeNet, self).__init__()
        # Input: 1x28x28 (MNIST)
        self.conv1 = nn.Conv2d(in_channels=1, out_channels=4, kernel_size=5, stride=1, padding=2) # Output: 4x28x28
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2) # Output: 4x14x14
        
        self.conv2 = nn.Conv2d(in_channels=4, out_channels=8, kernel_size=5, stride=1, padding=0) # Output: 8x10x10
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2) # Output: 8x5x5
        
        self.fc1 = nn.Linear(8 * 5 * 5, 50) 
        self.fc2 = nn.Linear(50, num_classes)

    def forward(self, x):
        x = self.pool1(F.relu(self.conv1(x)))
        x = self.pool2(F.relu(self.conv2(x)))
        x = x.view(-1, 8 * 5 * 5)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return x

if __name__ == '__main__':
    net = LeNet()
    print(net)
    dummy_input = torch.randn(1, 1, 28, 28)
    output = net(dummy_input)
    print(f"Output shape: {output.shape}") 