import pandas as pd
import torch
import torch.nn as nn
import os

device = torch.accelerator.current_accelerator(
).type if torch.accelerator.is_available() else "cpu"


class SimulationDataset(torch.utils.data.Dataset):
    def __init__(self, file_location='simulation_results.csv', normalize=True):
        simulation_results = pd.read_csv(file_location)
        dataset = simulation_results[['flow_35', 'flow_33', 'flow_5', 'flow_18', 'pressure_22', 'pressure_15',
                                      # should also add node_27
                                      'pressure_5', 'pressure_4', 'pressure_3', 'flow_9', 'pressure_8']].values

        # Remove rows with NaN values
        dataset = dataset[~pd.isna(dataset).any(axis=1)]
        self.original_dataset = dataset.copy()
        self.min_values = dataset.min(axis=0)
        self.max_values = dataset.max(axis=0)
        if normalize:
            # Normalize the dataset
            dataset = (dataset - self.min_values) / \
                (self.max_values - self.min_values)
        self.data = torch.tensor(dataset, dtype=torch.float32, device=device)

        self.input_min = self.min_values[:9]
        self.input_max = self.max_values[:9]
        self.output_min = self.min_values[9:]
        self.output_max = self.max_values[9:]

    def denormalize(self, dataset):
        # Denormalize the dataset to the original range
        dataset = dataset * (self.max_values -
                             self.min_values) + self.min_values
        return dataset

    def denormalize_output(self, data):
        # Denormalize the output data to the original range
        _max_values = torch.tensor(
            self.max_values, dtype=torch.float32, device=device)
        _min_values = torch.tensor(
            self.min_values, dtype=torch.float32, device=device)
        data = data * (_max_values[9:] - _min_values[9:]) + _min_values[9:]
        return data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        x = self.data[idx, :9]
        y = self.data[idx, 9:]
        return x, y


class RealDataset(torch.utils.data.Dataset):
    def __init__(self, file_location='dataset/real_dataset.csv', normalize=True):
        print(os.getcwd())
        simulation_results = pd.read_csv(file_location)
        dataset = simulation_results[['flow1', 'flow2', 'flow3', 'flow4', 'pressure1', 'pressure2',
                                      # should also add node_27
                                      'pressure3', 'pressure4', 'pressure5', 'flow5', 'pressure6']].values

        # Remove rows with NaN values
        dataset = dataset[~pd.isna(dataset).any(axis=1)]
        self.original_dataset = dataset.copy()
        self.min_values = dataset.min(axis=0)
        self.max_values = dataset.max(axis=0)
        if normalize:
            # Normalize the dataset
            dataset = (dataset - self.min_values) / \
                (self.max_values - self.min_values)
        self.data = torch.tensor(dataset, dtype=torch.float32, device=device)

        self.input_min = self.min_values[:9]
        self.input_max = self.max_values[:9]
        self.output_min = self.min_values[9:]
        self.output_max = self.max_values[9:]

    def denormalize(self, dataset):
        # Denormalize the dataset to the original range
        dataset = dataset * (self.max_values -
                             self.min_values) + self.min_values
        return dataset

    def denormalize_output(self, data):
        # Denormalize the output data to the original range
        _max_values = torch.tensor(
            self.max_values, dtype=torch.float32, device=device)
        _min_values = torch.tensor(
            self.min_values, dtype=torch.float32, device=device)
        data = data * (_max_values[9:] - _min_values[9:]) + _min_values[9:]
        return data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        x = self.data[idx, :9]
        y = self.data[idx, 9:]
        return x, y


class NeuralNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        self.flatten = nn.Flatten()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(9, 512),
            nn.Dropout(0.2),
            nn.ReLU(),
            nn.Linear(512, 512),
            nn.Dropout(0.2),
            nn.ReLU(),
            nn.Linear(512, 2),
        )

    def forward(self, x):
        logits = self.linear_relu_stack(x)
        return logits
