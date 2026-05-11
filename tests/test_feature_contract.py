import importlib


def test_feature_modules_importable():
    for mod in (
        "src.features.build_features",
        "src.features.feature_key",
        "src.features.regime",
    ):
        importlib.import_module(mod)
