from collections import OrderedDict

import torch
import torch.nn as nn
import torch.nn.functional as F

import flwr as fl
from opacus import PrivacyEngine

# Adapted from the PyTorch quickstart example.


# Define parameters.
PARAMS = {
    "batch_size": 32,
    "train_split": 0.7,
    "local_epochs": 1,
}
PRIVACY_PARAMS = {
    # 'target_epsilon': 5.0,
    "target_delta": 1e-5,
    "noise_multiplier": 0.4,
    "max_grad_norm": 1.2,
}
DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


# Define model used for training.
class Net(nn.Module):
    def __init__(self) -> None:
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(3, 6, 5)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(6, 16, 5)
        self.fc1 = nn.Linear(16 * 5 * 5, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = x.view(-1, 16 * 5 * 5)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x


def train(net, optimizer, trainloader, epochs):
    criterion = torch.nn.CrossEntropyLoss()
    losses = []
    for _ in range(epochs):
        epoch_loss = 0
        for images, labels in trainloader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            optimizer.zero_grad()
            loss = criterion(net(images), labels)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
    return losses


def test(net, testloader):
    criterion = torch.nn.CrossEntropyLoss()
    correct, loss = 0, 0.0
    with torch.no_grad():
        for data in testloader:
            images, labels = data[0].to(DEVICE), data[1].to(DEVICE)
            outputs = net(images)
            loss += criterion(outputs, labels).item()
            _, predicted = torch.max(outputs.data, 1)
            correct += (predicted == labels).sum().item()
    accuracy = correct / len(testloader.dataset)
    return loss, accuracy


# Define Flower client.
class DPCifarClient(fl.client.NumPyClient):
    def __init__(self, model, trainloader, testloader) -> None:
        super().__init__()
        self.model = model
        self.trainloader = trainloader
        self.testloader = testloader
        self.optimizer = torch.optim.SGD(self.model.parameters(), lr=0.001, momentum=0.9)
        # Create a privacy engine which will add DP and keep track of the privacy budget.
        self.privacy_engine = PrivacyEngine()
        self.model, self.optimzer, self.trainloader = self.privacy_engine.make_private(            
            module=self.model,
            optimizer=self.optimizer,
            data_loader=self.trainloader,
            max_grad_norm=PRIVACY_PARAMS["max_grad_norm"],
            noise_multiplier=PRIVACY_PARAMS["noise_multiplier"],)

    def get_parameters(self, config):
        return [val.cpu().numpy() for _, val in self.model.state_dict().items()]

    def set_parameters(self, parameters):
        params_dict = zip(self.model.state_dict().keys(), parameters)
        state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
        self.model.load_state_dict(state_dict, strict=True)

    def fit(self, parameters, config):
        self.set_parameters(parameters)
        losses = train(
            self.model, self.optimzer, self.trainloader, PARAMS["local_epochs"]
        )
        return (
            self.get_parameters(config={}),
            len(self.trainloader),
        )

    def evaluate(self, parameters, config):
        self.set_parameters(parameters)
        loss, accuracy = test(self.model, self.testloader)
        return float(loss), len(self.testloader), {"accuracy": float(accuracy)}