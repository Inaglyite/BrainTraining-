from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier


@dataclass
class TreeKTConfig:
    history_len: int = 5
    numeric_feature_cols: tuple[str, ...] = (
        "time_since_skill",
        "consecutive_errors_in_row",
        "total_attempted",
        "skill_opportunities",
        "past_wrong_ratio",
        "sum_right",
    )


class _SequentialTabularBase:
    def __init__(self, config: TreeKTConfig | None = None):
        self.config = config or TreeKTConfig()
        self.game_to_idx: Dict[str, int] = {}
        self.feature_mean: np.ndarray | None = None
        self.feature_std: np.ndarray | None = None
        self.model: Any = None

    def _predict_proba_row(self, x: np.ndarray) -> float:
        if self.model is None:
            raise RuntimeError("Model is not initialized")
        return float(self.model.predict_proba(x)[0, 1])

    def _numeric_features(self, row: pd.Series) -> np.ndarray:
        values = []
        for col in self.config.numeric_feature_cols:
            val = row.get(col, 0.0)
            if pd.isna(val):
                val = 0.0
            val = float(val)
            if val < 0:
                val = 0.0
            if col != "past_wrong_ratio":
                val = float(np.log1p(val))
            values.append(val)
        return np.asarray(values, dtype=float)

    def _normalize_numeric(self, x: np.ndarray) -> np.ndarray:
        if self.feature_mean is None or self.feature_std is None:
            return x
        return (x - self.feature_mean) / self.feature_std

    def _build_rows(self, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        games = sorted(df["game"].unique().tolist())
        self.game_to_idx = {g: i for i, g in enumerate(games)}

        features: List[np.ndarray] = []
        labels: List[int] = []

        for _, user_df in df.sort_values(["user_id", "attempt_index"]).groupby("user_id"):
            history = {g: [0] * self.config.history_len for g in games}
            for _, row in user_df.iterrows():
                g = row["game"]
                one_hot = np.zeros(len(games), dtype=float)
                one_hot[self.game_to_idx[g]] = 1.0
                hist = np.array(history[g], dtype=float)
                num = self._normalize_numeric(self._numeric_features(row))
                x = np.concatenate([one_hot, hist, num])
                features.append(x)
                labels.append(int(row["correct"]))
                history[g] = history[g][1:] + [int(row["correct"])]

        return np.vstack(features), np.array(labels, dtype=int)

    def _transform_eval_rows(self, df: pd.DataFrame) -> np.ndarray:
        games = sorted(self.game_to_idx.keys())
        probs = np.full(len(df), 0.5, dtype=float)
        order = list(df.index)
        pos_map = {idx: pos for pos, idx in enumerate(order)}

        for _, user_df in df.sort_values(["user_id", "attempt_index"]).groupby("user_id"):
            history = {g: [0] * self.config.history_len for g in games}
            for row_idx, row in user_df.iterrows():
                g = row["game"]
                one_hot = np.zeros(len(games), dtype=float)
                if g in self.game_to_idx:
                    one_hot[self.game_to_idx[g]] = 1.0
                hist = np.array(history.get(g, [0] * self.config.history_len), dtype=float)
                num = self._normalize_numeric(self._numeric_features(row))
                x = np.concatenate([one_hot, hist, num])[None, :]
                p = self._predict_proba_row(x)
                probs[pos_map[row_idx]] = p
                history[g] = history.get(g, [0] * self.config.history_len)[1:] + [int(row["correct"])]

        return probs


class RandomForestKT(_SequentialTabularBase):
    """Random Forest baseline over DKT-style handcrafted sequence features."""

    def __init__(
        self,
        config: TreeKTConfig | None = None,
        n_estimators: int = 400,
        random_state: int = 7,
        progress_mode: str = "off",
        progress_every: int = 50,
    ):
        super().__init__(config=config)
        self.n_estimators = int(n_estimators)
        self.progress_mode = progress_mode
        self.progress_every = max(1, int(progress_every))
        self.model = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=12,
            min_samples_leaf=20,
            n_jobs=-1,
            random_state=random_state,
            warm_start=self.progress_mode in {"epoch", "bar"},
        )

    def fit(self, train_df: pd.DataFrame) -> "RandomForestKT":
        x, y = self._build_rows(train_df)
        feature_dim = len(self.config.numeric_feature_cols)
        if feature_dim > 0:
            numeric = x[:, -feature_dim:]
            self.feature_mean = numeric.mean(axis=0)
            self.feature_std = numeric.std(axis=0)
            self.feature_std[self.feature_std < 1e-6] = 1.0
            x = x.copy()
            x[:, -feature_dim:] = (numeric - self.feature_mean) / self.feature_std
        if self.progress_mode == "off":
            self.model.fit(x, y)
            return self

        t0 = time.time()
        stage_sizes = list(range(self.progress_every, self.n_estimators + 1, self.progress_every))
        if not stage_sizes or stage_sizes[-1] != self.n_estimators:
            stage_sizes.append(self.n_estimators)

        stage_iter = stage_sizes
        bar = None
        if self.progress_mode == "bar":
            try:
                from tqdm import tqdm  # type: ignore

                bar = tqdm(stage_sizes, desc="RF-Seq", leave=False)
                stage_iter = bar
            except Exception:
                print("[RF-Seq] tqdm not found, fallback to epoch logging.", flush=True)
                self.progress_mode = "epoch"

        for stage_idx, n_trees in enumerate(stage_iter, start=1):
            self.model.set_params(n_estimators=int(n_trees), warm_start=True)
            self.model.fit(x, y)
            elapsed = time.time() - t0
            done_ratio = float(n_trees) / float(self.n_estimators)
            eta = elapsed * (1.0 / max(done_ratio, 1e-6) - 1.0)
            if bar is not None:
                bar.set_postfix(trees=f"{n_trees}/{self.n_estimators}")
            else:
                print(
                    f"[RF-Seq] stage {stage_idx}/{len(stage_sizes)} trees={n_trees}/{self.n_estimators} elapsed={elapsed:.1f}s eta={eta:.1f}s",
                    flush=True,
                )

        if bar is not None:
            bar.close()
        return self

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        return self._transform_eval_rows(df)


class XGBoostKT(_SequentialTabularBase):
    """XGBoost baseline over DKT-style handcrafted sequence features."""

    def __init__(
        self,
        config: TreeKTConfig | None = None,
        random_state: int = 7,
        progress_mode: str = "off",
        progress_every: int = 20,
    ):
        super().__init__(config=config)
        self.progress_mode = progress_mode
        self.progress_every = max(1, int(progress_every))
        try:
            from xgboost import XGBClassifier  # type: ignore
        except Exception as exc:
            raise ImportError("xgboost is required for XGBoostKT. Install with `pip install xgboost`.") from exc

        self.model = XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.06,
            subsample=0.9,
            colsample_bytree=0.9,
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=random_state,
            n_jobs=-1,
        )

    def fit(self, train_df: pd.DataFrame) -> "XGBoostKT":
        x, y = self._build_rows(train_df)
        feature_dim = len(self.config.numeric_feature_cols)
        if feature_dim > 0:
            numeric = x[:, -feature_dim:]
            self.feature_mean = numeric.mean(axis=0)
            self.feature_std = numeric.std(axis=0)
            self.feature_std[self.feature_std < 1e-6] = 1.0
            x = x.copy()
            x[:, -feature_dim:] = (numeric - self.feature_mean) / self.feature_std
        if self.progress_mode != "off":
            print(
                f"[XGBoost-Seq] boosting rounds={self.model.n_estimators}, log_every={self.progress_every}",
                flush=True,
            )
        self.model.fit(
            x,
            y,
            eval_set=[(x, y)] if self.progress_mode != "off" else None,
            verbose=self.progress_every if self.progress_mode != "off" else False,
        )
        return self

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        return self._transform_eval_rows(df)

