from __future__ import annotations

from dataclasses import dataclass
from typing import Dict
import time

import numpy as np
import pandas as pd


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


@dataclass
class RaschConfig:
    lr: float = 0.03
    n_epochs: int = 30
    l2: float = 1e-3
    seed: int = 0
    progress_mode: str = "off"  # off | epoch | bar
    progress_every: int = 5


class RaschIRT:
    """Simple 1PL (Rasch) model trained with batch gradient descent."""

    def __init__(self, config: RaschConfig | None = None):
        self.config = config or RaschConfig()
        self.user_idx: Dict[str, int] = {}
        self.item_idx: Dict[str, int] = {}
        self.theta: np.ndarray | None = None
        self.b: np.ndarray | None = None

    def fit(self, df: pd.DataFrame) -> "RaschIRT":
        rng = np.random.default_rng(self.config.seed)
        users = sorted(df["user_id"].unique().tolist())
        items = sorted(df["item_id"].unique().tolist())
        self.user_idx = {u: i for i, u in enumerate(users)}
        self.item_idx = {it: i for i, it in enumerate(items)}

        u = df["user_id"].map(self.user_idx).to_numpy(dtype=int)
        i = df["item_id"].map(self.item_idx).to_numpy(dtype=int)
        y = df["correct"].to_numpy(dtype=float)

        self.theta = rng.normal(0.0, 0.1, len(users))
        self.b = rng.normal(0.0, 0.1, len(items))

        n_epochs = int(self.config.n_epochs)
        progress_every = max(1, int(self.config.progress_every))
        epoch_iter = range(n_epochs)
        bar = None
        if self.config.progress_mode == "bar":
            try:
                from tqdm import trange  # type: ignore

                bar = trange(n_epochs, desc="Rasch", leave=False)
                epoch_iter = bar
            except Exception:
                print("[Rasch] tqdm not found, fallback to epoch logging.", flush=True)
                self.config.progress_mode = "epoch"

        t0 = time.time()
        for epoch in epoch_iter:
            logit = self.theta[u] - self.b[i]
            p = _sigmoid(logit)
            err = y - p

            grad_theta = np.zeros_like(self.theta)
            grad_b = np.zeros_like(self.b)
            np.add.at(grad_theta, u, err)
            np.add.at(grad_b, i, -err)

            grad_theta -= self.config.l2 * self.theta
            grad_b -= self.config.l2 * self.b

            self.theta += self.config.lr * grad_theta
            self.b += self.config.lr * grad_b

            # Remove location ambiguity: center both sets each epoch.
            self.theta -= np.mean(self.theta)
            self.b -= np.mean(self.b)

            # Binary cross-entropy + L2 penalty for progress display.
            eps = 1e-7
            ce = -np.mean(y * np.log(p + eps) + (1.0 - y) * np.log(1.0 - p + eps))
            l2_term = 0.5 * self.config.l2 * (float(np.mean(self.theta**2)) + float(np.mean(self.b**2)))
            loss = ce + l2_term

            if bar is not None:
                bar.set_postfix(loss=f"{loss:.4f}")
            elif self.config.progress_mode == "epoch":
                is_boundary = (epoch + 1) % progress_every == 0 or epoch == 0 or (epoch + 1) == n_epochs
                if is_boundary:
                    elapsed = time.time() - t0
                    avg_ep = elapsed / (epoch + 1)
                    eta = avg_ep * (n_epochs - epoch - 1)
                    print(
                        f"[Rasch] epoch {epoch + 1}/{n_epochs} loss={loss:.4f} elapsed={elapsed:.1f}s eta={eta:.1f}s",
                        flush=True,
                    )

        if bar is not None:
            bar.close()

        return self

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        if self.theta is None or self.b is None:
            raise RuntimeError("Model is not fitted.")
        p = np.full(len(df), 0.5, dtype=float)
        for pos, (_, row) in enumerate(df.iterrows()):
            u_idx = self.user_idx.get(row["user_id"])
            i_idx = self.item_idx.get(row["item_id"])
            if u_idx is None and i_idx is None:
                p[pos] = 0.5
            elif u_idx is None:
                p[pos] = float(_sigmoid(np.array([-self.b[i_idx]]))[0])
            elif i_idx is None:
                p[pos] = float(_sigmoid(np.array([self.theta[u_idx]]))[0])
            else:
                p[pos] = float(_sigmoid(np.array([self.theta[u_idx] - self.b[i_idx]]))[0])
        return p

    def estimate_theta_online(
        self,
        user_history: pd.DataFrame,
        init_theta: float = 0.0,
        n_steps: int = 6,
        clip: float = 3.5,
    ) -> float:
        """Estimate one user's theta from recent responses using Newton updates."""
        if self.b is None:
            raise RuntimeError("Model is not fitted.")
        theta = float(init_theta)
        hist = user_history[user_history["item_id"].isin(self.item_idx.keys())]
        if hist.empty:
            return theta

        item_ids = hist["item_id"].tolist()
        y = hist["correct"].to_numpy(dtype=float)
        b_vals = np.array([self.b[self.item_idx[it]] for it in item_ids])

        for _ in range(n_steps):
            p = _sigmoid(theta - b_vals)
            grad = float(np.sum(y - p))
            hess = -float(np.sum(p * (1.0 - p))) - 1e-6
            theta = np.clip(theta - grad / hess, -clip, clip)
        return float(theta)

    def item_difficulties(self) -> Dict[str, float]:
        if self.b is None:
            raise RuntimeError("Model is not fitted.")
        return {item: float(self.b[idx]) for item, idx in self.item_idx.items()}


def fit_per_game(train_df: pd.DataFrame, config: RaschConfig | None = None) -> Dict[str, RaschIRT]:
    models: Dict[str, RaschIRT] = {}
    grouped = list(train_df.groupby("game"))
    total = len(grouped)
    for idx, (game, game_df) in enumerate(grouped, start=1):
        if (config or RaschConfig()).progress_mode != "off":
            print(f"[IRT(1PL)] game {idx}/{total}: {game} ({len(game_df)} rows)", flush=True)
        m = RaschIRT(config)
        m.fit(game_df)
        models[game] = m
    return models


def estimate_user_skill_vector(
    models: Dict[str, RaschIRT], user_history: pd.DataFrame
) -> Dict[str, float]:
    theta = {}
    for game, model in models.items():
        theta[game] = model.estimate_theta_online(user_history[user_history["game"] == game])
    return theta

