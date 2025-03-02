"""Implementation of Conditional Glow."""

import torch
import torch.nn as nn
from torch.nn import functional as F

from nflows.distributions.normal import StandardNormal
from nflows.flows.base import Flow
from nflows.nn import nets as nets
from nflows.transforms.base import CompositeTransform
from nflows.transforms.coupling import AdditiveCouplingTransform, AffineCouplingTransform
from nflows.transforms.lu import LULinear
from nflows.transforms.normalization import BatchNorm, ActNorm

class ConditionalGlow(Flow):
    """ A version of Conditional Glow for 1-dim inputs.

    Reference:
    > TODO
    """

    def __init__(
        self,
        features,
        hidden_features,
        num_layers,
        num_blocks_per_layer,
        activation=F.relu,
        dropout_probability=0.5,
        context_features=None,
        batch_norm_within_layers=True,
        use_affine_coupling=False,
        scale_activation="DEFAULT",
        clamp=2.0,
    ):
        if use_affine_coupling:
            coupling_constructor = AffineCouplingTransform
        else:
            coupling_constructor = AdditiveCouplingTransform  # AffineCouplingTransform  # AdditiveCouplingTransform

        mask = torch.ones(features)
        mask[::2] = -1

        def create_resnet(in_features, out_features):
            return nets.ResidualNet(
                in_features,
                out_features,
                hidden_features=hidden_features,
                num_blocks=num_blocks_per_layer,
                activation=activation,
                context_features=context_features,
                dropout_probability=dropout_probability,
                use_batch_norm=batch_norm_within_layers,
            )

        layers = []
        for _ in range(num_layers):
            layers.append(ActNorm(features=features))
            layers.append(LULinear(features=features))
            transform = coupling_constructor(
                mask=mask, transform_net_create_fn=create_resnet, scale_activation=scale_activation, clamp=clamp
            )
            mask *= -1
            layers.append(transform)

        super().__init__(
            transform=CompositeTransform(layers),
            distribution=StandardNormal([features])
        )
