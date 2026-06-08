from __future__ import annotations

import pandas as pd
import pytest
from pathlib import Path

from ml.prediction.dataset_builder import build_training_dataset

pytest.importorskip("pandas")
pytest.importorskip("sklearn")
pytest.importorskip("joblib")

from ml.prediction.congestion_predictor import (
    load_model,
    predict_congestion,
    train_model,
    predict_from_model_file,
    build_arg_parser,
    _load_training_dataframe,
)


def test_training_and_prediction_pipeline(tmp_path) -> None:
    dataset_path = tmp_path / "dataset.csv"
    model_path = tmp_path / "model.pkl"
    build_training_dataset(tmp_path / "missing_logs", dataset_path)

    training_result = train_model(dataset_path, model_path)
    model = load_model(model_path)
    prediction = predict_congestion(
        model,
        {
            "total_vehicles": 18,
            "car_count": 10,
            "motorcycle_count": 4,
            "bus_count": 2,
            "truck_count": 2,
            "density": "MEDIUM",
            "emergency_present": False,
        },
    )

    assert model_path.exists()
    assert "metrics" in training_result
    assert prediction in {"LOW_CONGESTION", "MEDIUM_CONGESTION", "HIGH_CONGESTION"}


def test_load_model_missing_raises_error(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="Model file not found"):
        load_model(tmp_path / "non_existent.pkl")


def test_load_training_dataframe_empty_raises_error(tmp_path) -> None:
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("")
    with pytest.raises(ValueError):
        _load_training_dataframe(empty_csv)


def test_load_training_dataframe_missing_columns_raises_error(tmp_path) -> None:
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("timestamp,density,congestion\n1,LOW,LOW_CONGESTION\n")
    with pytest.raises(ValueError, match="Training dataset is missing columns"):
        _load_training_dataframe(bad_csv)


def test_predict_from_model_file(tmp_path) -> None:
    dataset_path = tmp_path / "dataset.csv"
    model_path = tmp_path / "model.pkl"
    build_training_dataset(tmp_path / "missing_logs", dataset_path)
    train_model(dataset_path, model_path)
    
    features = {
        "total_vehicles": 5,
        "car_count": 3,
        "motorcycle_count": 2,
        "bus_count": 0,
        "truck_count": 0,
        "density": "LOW",
        "emergency_present": True,
    }
    
    prediction = predict_from_model_file(model_path, features)
    assert prediction in {"LOW_CONGESTION", "MEDIUM_CONGESTION", "HIGH_CONGESTION"}


def test_build_arg_parser() -> None:
    parser = build_arg_parser()
    args = parser.parse_args([
        "--train", "data.csv",
        "--model-output", "out.pkl",
        "--model", "in.pkl",
        "--predict",
        "--total-vehicles", "10",
        "--emergency-present"
    ])
    assert args.train == "data.csv"
    assert args.model_output == "out.pkl"
    assert args.model == "in.pkl"
    assert args.predict is True
    assert args.total_vehicles == 10
    assert args.emergency_present is True
