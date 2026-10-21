"""Classical model factory."""

from __future__ import annotations

from ..config import ExperimentConfig


def build_model(config: ExperimentConfig):
    import sklearn

    if config.model.name == "logistic_regression":
        from sklearn.linear_model import LogisticRegression

        hyperparameters = {
            "max_iter": 1000,
            "class_weight": "balanced",
            "random_state": config.data.random_seed,
        }
        hyperparameters.update(config.model.hyperparameters)
        return LogisticRegression(**hyperparameters), hyperparameters, [
            f"scikit-learn=={sklearn.__version__}"
        ]

    if config.model.name == "xgboost":
        import xgboost
        from xgboost import XGBClassifier

        hyperparameters = {
            "objective": "binary:logistic",
            "eval_metric": "logloss",
            "random_state": config.data.random_seed,
            "n_jobs": -1,
        }
        hyperparameters.update(config.model.hyperparameters)
        requirements = [
            f"scikit-learn=={sklearn.__version__}",
            f"xgboost=={xgboost.__version__}",
        ]
        return XGBClassifier(**hyperparameters), hyperparameters, requirements

    raise ValueError(f"unsupported model {config.model.name!r}")
