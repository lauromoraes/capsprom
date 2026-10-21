import pytest

torch = pytest.importorskip("torch")

from capsprom.models.capsprom import (  # noqa: E402
    CapsProm,
    CapsPromConfig,
    DynamicRoutingCapsules,
    LegacyCapsProm1CConfig,
    binary_capsule_predictions,
    capsprom_loss,
    margin_loss,
    relative_capsule_scores,
    squash,
)
from capsprom.models.sequence_cnn import SequenceCnnControl  # noqa: E402


def test_squash_is_finite_for_zero_vectors() -> None:
    result = squash(torch.zeros(2, 3, 8))
    assert torch.isfinite(result).all()
    assert torch.equal(result, torch.zeros_like(result))


def test_capsprom_reproduction_shapes_and_loss() -> None:
    config = LegacyCapsProm1CConfig(sequence_length=81)
    model = CapsProm(config)
    one_hot = torch.nn.functional.one_hot(
        torch.randint(0, 4, (2, config.sequence_length)), num_classes=4
    ).float()
    output = model(one_hot)

    assert config.primary_positions == 33
    assert config.primary_capsules == 1056
    assert output.scores.shape == (2, 1)
    assert output.capsules.shape == (2, 1, 16)
    assert output.reconstruction.shape == (2, 81, 4)
    assert torch.all((output.scores >= 0.0) & (output.scores < 1.0))
    assert torch.isfinite(capsprom_loss(output, torch.tensor([0, 1]), one_hot))


def test_margin_loss_prefers_correct_binary_scores() -> None:
    labels = torch.tensor([0, 1])
    correct = margin_loss(labels, torch.tensor([[0.05], [0.95]]))
    wrong = margin_loss(labels, torch.tensor([[0.95], [0.05]]))
    assert correct < wrong


def test_relative_capsule_score_matches_argmax_decision() -> None:
    scores = torch.tensor([[0.8, 0.2], [0.1, 0.9], [0.0, 0.0]])

    relative = relative_capsule_scores(scores)
    positive_score, predictions = binary_capsule_predictions(scores)

    assert torch.allclose(relative.sum(dim=1), torch.ones(3))
    assert torch.allclose(positive_score, torch.tensor([0.2, 0.9, 0.5]))
    assert torch.equal(predictions, torch.tensor([0, 1, 0]))
    assert torch.equal((positive_score[:2] > 0.5).long(), predictions[:2])


def test_capsprom_rejects_wrong_input_shape() -> None:
    model = CapsProm(CapsPromConfig(sequence_length=81))
    with pytest.raises(ValueError, match="shape mismatch"):
        model(torch.zeros(2, 80, 4))


def test_single_capsule_dynamic_and_uniform_routing_are_equivalent() -> None:
    torch.manual_seed(7)
    dynamic = CapsProm(LegacyCapsProm1CConfig(routing_mode="dynamic"))
    uniform = CapsProm(LegacyCapsProm1CConfig(routing_mode="uniform"))
    uniform.load_state_dict(dynamic.state_dict())
    one_hot = torch.nn.functional.one_hot(torch.randint(0, 4, (2, 81)), 4).float()

    dynamic_output = dynamic(one_hot)
    uniform_output = uniform(one_hot)

    assert torch.allclose(dynamic_output.capsules, uniform_output.capsules, atol=1e-7)


def test_two_capsule_variant_uses_class_conditioned_decoder() -> None:
    model = CapsProm(CapsPromConfig(output_capsules=2))
    one_hot = torch.nn.functional.one_hot(torch.randint(0, 4, (2, 81)), 4).float()
    labels = torch.tensor([0, 1])
    output = model(one_hot, labels=labels)

    assert output.scores.shape == (2, 2)
    assert output.capsules.shape == (2, 2, 16)
    assert torch.isfinite(capsprom_loss(output, labels, one_hot))


def test_basic_defaults_use_two_capsules_and_seminal_decoder_mask() -> None:
    config = CapsPromConfig()
    model = CapsProm(config)
    assert config.output_capsules == 2
    assert config.routing_gradient_mode == "final_iteration"
    assert config.decoder_mode == "masked_flatten"
    assert model.decoder is not None
    assert model.decoder[0].in_features == 32


def test_disabled_decoder_avoids_reconstruction_graph_and_parameters() -> None:
    enabled = CapsProm(CapsPromConfig(sequence_length=28, decoder_mode="selected_vector"))
    disabled = CapsProm(CapsPromConfig(sequence_length=28, decoder_mode="disabled"))
    one_hot = torch.nn.functional.one_hot(torch.randint(0, 4, (2, 28)), 4).float()
    labels = torch.tensor([0, 1])

    disabled_output = disabled(one_hot, labels=labels)

    assert disabled.decoder is None
    assert disabled_output.reconstruction is None
    assert sum(p.numel() for p in disabled.parameters()) < sum(
        p.numel() for p in enabled.parameters()
    )
    assert torch.isfinite(capsprom_loss(disabled_output, labels, one_hot, 0.0))
    with pytest.raises(ValueError, match="decoder is disabled"):
        capsprom_loss(disabled_output, labels, one_hot, 0.0005)


def test_one_iteration_routing_matches_uniform_weighted_vote_oracle() -> None:
    torch.manual_seed(11)
    layer = DynamicRoutingCapsules(3, 4, 2, 5, 1)
    inputs = torch.randn(2, 3, 4)
    votes = torch.einsum("bid,ijdo->bijo", inputs, layer.weight)
    expected = squash(votes.sum(dim=1) / layer.output_capsules)
    assert torch.allclose(layer(inputs), expected, atol=1e-7)


def test_reconstruction_sum_is_element_count_scaled_mean() -> None:
    config = CapsPromConfig(sequence_length=28, convolution_filters=8, primary_channels=2)
    model = CapsProm(config)
    one_hot = torch.nn.functional.one_hot(torch.randint(0, 4, (2, 28)), 4).float()
    labels = torch.tensor([0, 1])
    output = model(one_hot, labels=labels)
    margin = margin_loss(labels, output.scores)
    mean_total = capsprom_loss(output, labels, one_hot, 1.0, "mean")
    sum_total = capsprom_loss(output, labels, one_hot, 1.0, "sum_per_sample")
    assert torch.allclose(sum_total - margin, (mean_total - margin) * (28 * 4))


@pytest.mark.parametrize("decoder_mode", ["selected_vector", "masked_flatten"])
@pytest.mark.parametrize("reduction", ["mean", "sum_per_sample"])
def test_all_trainable_blocks_receive_finite_gradients(
    decoder_mode: str, reduction: str
) -> None:
    config = CapsPromConfig(
        sequence_length=28,
        convolution_filters=8,
        primary_channels=2,
        primary_dim=4,
        output_dim=4,
        decoder_hidden=(8, 8),
        decoder_mode=decoder_mode,
    )
    model = CapsProm(config)
    one_hot = torch.nn.functional.one_hot(torch.randint(0, 4, (4, 28)), 4).float()
    labels = torch.tensor([0, 1, 0, 1])
    loss = capsprom_loss(
        model(one_hot, labels=labels), labels, one_hot, 0.0005, reduction
    )
    loss.backward()
    for parameter in (
        model.convolution.weight,
        model.primary_convolution.weight,
        model.digit_capsules.weight,
        model.decoder[0].weight,
    ):
        assert parameter.grad is not None
        assert torch.isfinite(parameter.grad).all()
        assert torch.count_nonzero(parameter.grad) > 0


def test_final_iteration_routing_keeps_trainable_gradient_path() -> None:
    model = CapsProm(
        CapsPromConfig(output_capsules=2, routing_gradient_mode="final_iteration")
    )
    one_hot = torch.nn.functional.one_hot(torch.randint(0, 4, (2, 81)), 4).float()
    labels = torch.tensor([0, 1])
    capsprom_loss(model(one_hot, labels=labels), labels, one_hot).backward()
    gradient = model.digit_capsules.weight.grad
    assert gradient is not None
    assert torch.isfinite(gradient).all()
    assert torch.count_nonzero(gradient) > 0


def test_cnn_control_returns_one_logit_per_sequence() -> None:
    model = SequenceCnnControl()
    one_hot = torch.nn.functional.one_hot(torch.randint(0, 4, (3, 81)), 4).float()
    assert model(one_hot).shape == (3,)
