"""
Neural Oracle: Temporal Retention Prediction (10/10)
====================================================

Upgraded Neural Engine using PyTorch to predict multi-point
retention curves based on deep multimodal embeddings.
"""

import numpy as np
import logging
from pathlib import Path
from src.services.optimization.model_registry import base_registry_service

logger = logging.getLogger(__name__)

# Lazy PyTorch imports - torch is heavy and not always available
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    import sys
    sys.modules.pop("torch", None)
    torch = None
    nn = None
    optim = None
    logger.warning("PyTorch not available - NeuralOracle will raise at runtime if called")


if TORCH_AVAILABLE:
    class RetentionNeuralNet(nn.Module):
        """Multimodal MLP for Retention Curve Prediction."""
        def __init__(self, input_dim: int = 520, output_dim: int = 4):
            super(RetentionNeuralNet, self).__init__()
            self.network = nn.Sequential(
                nn.Linear(input_dim, 256),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(256, 128),
                nn.ReLU(),
                nn.Linear(128, 64),
                nn.ReLU(),
                nn.Linear(64, output_dim),
                nn.Sigmoid(),
            )

        def forward(self, x):
            return self.network(x)
else:
    class RetentionNeuralNet:
        """Stub - PyTorch not available."""
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "PyTorch is required for RetentionNeuralNet. "
                "Install it with: pip install torch"
            )
        def to(self, device):
            return self
        def eval(self):
            pass
        def train(self, mode=True):
            pass


class NeuralOracle:
    """The Scientific Heart of Ettametta: Temporal Deep Learning."""
    def __init__(self, model_path: str | None = None):
        if not TORCH_AVAILABLE:
            raise ImportError(
                "PyTorch is required for NeuralOracle. "
                "Install it with: pip install torch"
            )

        if model_path:
            self.model_path = Path(model_path)
        else:
            self.model_path = Path(base_registry_service.get_champion_path())

        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        if self.device.type == "cpu":
            torch.set_num_threads(1)

        self.model = RetentionNeuralNet().to(self.device)
        self._load_model()

        self.num_dim = 8
        self.clip_dim = 512

    def _load_model(self):
        if self.model_path.exists():
            try:
                self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
                self.model.eval()
                logger.info(f"Neural Oracle weights loaded from {self.model_path.name}")
            except Exception as e:
                logger.exception(f"Failed to load Neural Oracle from {self.model_path}: {e}")

    def reload_champion(self):
        self.model_path = Path(base_registry_service.get_champion_path())
        self._load_model()
        logger.info(f"Neural Oracle hot-swapped to new Champion: {self.model_path.name}")

    def predict_curve(self, numerical_features: list[float], clip_embedding: np.ndarray | None = None) -> np.ndarray:
        if clip_embedding is None:
            clip_embedding = np.zeros(self.clip_dim)
        x = np.concatenate([clip_embedding, numerical_features])
        x_tensor = torch.FloatTensor(x).to(self.device).unsqueeze(0)
        with torch.no_grad():
            curve = self.model(x_tensor).cpu().numpy()[0]
        return curve

    def train_cycle(self, train_loader: "torch.utils.data.DataLoader", epochs: int = 5):
        self.model.train()
        optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        criterion = nn.MSELoss()
        for epoch in range(epochs):
            total_loss = 0
            for batch_x, batch_y in train_loader:
                batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)
                optimizer.zero_grad()
                outputs = self.model(batch_x)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
            logger.info(f"Neural Epoch {epoch+1} Loss: {total_loss/len(train_loader):.4f}")
        torch.save(self.model.state_dict(), self.model_path)
        self.model.eval()


class _LazyOracle:
    """Lazily initializes NeuralOracle on first attribute access."""
    def __init__(self):
        self._instance = None
    def _get(self):
        if self._instance is None:
            self._instance = NeuralOracle()
        return self._instance
    def __getattr__(self, name):
        return getattr(self._get(), name)


base_oracle_service = _LazyOracle()
