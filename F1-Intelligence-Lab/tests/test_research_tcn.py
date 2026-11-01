import json

import pytest

torch = pytest.importorskip("torch")

from f1_intelligence_lab.research.tcn import GRU, MLP, TCN, parameter_count, run_fixture


def test_sequence_model_shapes_and_parameter_budgets():
    x = torch.zeros((4, 10, 7))
    models = [GRU(7), TCN(7), MLP(7, 10)]
    assert all(model(x).shape == (4,) for model in models)
    assert all(parameter_count(model) < 2000 for model in models)


def test_tcn_fixture_smoke_and_determinism(tmp_path):
    first = run_fixture(str(tmp_path / "first"))
    second = run_fixture(str(tmp_path / "second"))
    assert (first / "results.json").read_bytes() == (second / "results.json").read_bytes()
    result = json.loads((first / "results.json").read_text())
    assert len(result["cells"]) == 12
    assert all(
        set(cell["models"]) == {"sequence_boosting", "gru", "tcn", "mlp"}
        for cell in result["cells"]
    )
