import torch
from .DatasetLoaders import RealDataset, NeuralNetwork

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class AiPrediction:
    def __init__(self, model_path, dataset_file):
        """
        Initializes the AiPrediction class.

        Args:
            model_path (str): The file path to the saved PyTorch model state dictionary.
            dataset_file (str): The file path to the dataset CSV file used for training,
                                which is needed to get the normalization statistics.
        """
        # Load the dataset to get normalization statistics
        dataset = RealDataset(file_location=dataset_file)
        self.input_min = torch.tensor(
            dataset.input_min, dtype=torch.float32, device=device)
        self.input_max = torch.tensor(
            dataset.input_max, dtype=torch.float32, device=device)
        self.output_min = torch.tensor(
            dataset.output_min, dtype=torch.float32, device=device)
        self.output_max = torch.tensor(
            dataset.output_max, dtype=torch.float32, device=device)

        # Initialize the model and load the trained weights
        self.model = NeuralNetwork().to(device)
        self.model.load_state_dict(torch.load(model_path, map_location=device))
        self.model.eval()

    def _normalize_input(self, input_data):
        """Normalizes the input data using the saved min and max values."""
        return (input_data - self.input_min) / (self.input_max - self.input_min)

    def _denormalize_output(self, output_data):
        """Denormalizes the output data to the original scale."""
        return output_data * (self.output_max - self.output_min) + self.output_min

    def predict(self, input_data):
        """
        Makes a prediction on the given input data.

        Args:
            input_data (list or np.ndarray): A list or NumPy array of 9 input features.

        Returns:
            np.ndarray: The denormalized prediction from the model.
        """
        with torch.no_grad():
            # Convert input to a tensor and move it to the correct device
            input_tensor = torch.tensor(
                input_data, dtype=torch.float32, device=device)
            # Normalize the input
            normalized_input = self._normalize_input(input_tensor)
            # Add a batch dimension and make a prediction
            prediction_normalized = self.model(normalized_input.unsqueeze(0))
            # Denormalize the prediction
            prediction_denormalized = self._denormalize_output(
                prediction_normalized)
            # Return the result as a NumPy array
            return prediction_denormalized.cpu().numpy()
