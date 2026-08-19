from __future__ import annotations

from typing import Optional

import numpy as np
import torch
from PIL import Image


class GradCAM:
    def __init__(self, model: torch.nn.Module, target_layer: torch.nn.Module):
        self.model = model
        self.target_layer = target_layer

        self.activations: Optional[torch.Tensor] = None
        self.gradients: Optional[torch.Tensor] = None

        self._forward_hook = target_layer.register_forward_hook(
            self._save_activations
        )

        self._backward_hook = target_layer.register_full_backward_hook(
            self._save_gradients
        )

    def _save_activations(self, module, inputs, output):
        self.activations = output.detach()

    def _save_gradients(self, module, grad_input, grad_output):
        self.gradients = grad_output[0].detach()

    def generate(
        self,
        input_tensor: torch.Tensor,
        class_index: Optional[int] = None,
    ) -> np.ndarray:
        self.model.zero_grad()

        output = self.model(input_tensor)

        if class_index is None:
            class_index = int(torch.argmax(output, dim=1).item())

        score = output[:, class_index]
        score.backward()

        if self.activations is None or self.gradients is None:
            raise RuntimeError(
                "Grad-CAM hooks did not capture activations/gradients."
            )

        weights = self.gradients.mean(dim=(2, 3), keepdim=True)

        cam = (weights * self.activations).sum(dim=1)

        cam = torch.relu(cam)

        cam = cam.squeeze(0).cpu().numpy()

        cam_min = cam.min()
        cam_max = cam.max()

        if cam_max > cam_min:
            cam = (cam - cam_min) / (cam_max - cam_min)
        else:
            cam = np.zeros_like(cam)

        return cam

    def close(self):
        self._forward_hook.remove()
        self._backward_hook.remove()


def overlay_gradcam(
    image: Image.Image,
    cam: np.ndarray,
    alpha: float = 0.45,
) -> Image.Image:
    image = image.convert("RGB")

    heatmap = Image.fromarray(
        np.uint8(cam * 255)
    ).resize(image.size)

    heatmap_np = np.asarray(heatmap).astype(np.float32) / 255.0

    # Simple red/yellow heatmap without extra dependencies
    red = np.clip(heatmap_np * 2.0, 0.0, 1.0)
    green = np.clip((heatmap_np - 0.25) * 2.0, 0.0, 1.0)
    blue = np.zeros_like(heatmap_np)

    color_heatmap = np.stack(
        [red, green, blue],
        axis=-1
    )

    image_np = np.asarray(image).astype(np.float32) / 255.0

    overlay = (
        (1.0 - alpha) * image_np
        + alpha * color_heatmap
    )

    overlay = np.clip(
        overlay * 255.0,
        0,
        255
    ).astype(np.uint8)

    return Image.fromarray(overlay)