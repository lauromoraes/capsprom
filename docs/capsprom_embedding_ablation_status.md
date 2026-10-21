# CapsProm Representation Ablation Status

## Audit conclusion

The proposed comparison of one-hot `k=1`, trainable embedding `k=1`, and
trainable embedding `k=2` has not been implemented or executed as a three-arm
ablation.

| Arm | Encoder code | CapsProm model support | Versioned experiment configuration | MLflow execution | Validated comparison |
| --- | --- | --- | --- | --- | --- |
| One-hot `k=1` | Implemented | Implemented | Implemented | Executed in smoke, learnability, decoder, optimizer, and trace diagnostics | Development validation only |
| Trainable embedding `k=1` | Not implemented | Not implemented | Not present | No matching run | No |
| Trainable embedding `k=2` | Not implemented | Not implemented | Not present | No matching run | No |

Evidence for the first arm includes `encode_one_hot` in
`src/capsprom/neural_training.py`, the tensor-only `CapsProm.forward` interface,
`configs/capsprom_basic_canonical_v1.yaml`, model and runner tests, local neural
checkpoints/states under the ignored `outputs/neural_smoke` tree, and finished
MLflow runs whose names begin with `capsprom-`. The MLflow database contains no
run name matching an embedding CapsProm experiment.

The generic feature layer implements one-hot k-mer matrices, including a tested
`k=2` encoder, named multi-head mappings, and a DNA-BERT feature encoder. These
capabilities do not create a trainable token embedding and are not connected to
the current CapsProm input. `configs/example_experiment.yaml` is an example of
feature configuration, not evidence of execution.

## Requirements before the ablation

The missing work is a separately named `Embedding-CapsProm` input module,
deterministic `A,C,G,T` k-mer vocabularies, versioned `k=1` and `k=2` contracts,
shape/gradient/resume tests, parameter-budget reporting, and a common
dataset/fold/seed orchestration contract. The one-hot and embedding arms must use
identical folds, ten canonical seeds, checkpoint-selection rules, maximum
epochs, patience, metric code, and external-test gating. Different token length
(`81` for `k=1`, `80` for `k=2`) and parameter counts must be reported rather
than hidden as equivalent conditions.

No real ablation job should begin until canonical fold orchestration passes its
continuous-versus-resumed fixture validation.
