import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("SQLITE_DB_PATH", str(Path(tempfile.gettempdir()) / "yusnxing-test-game-data.db"))

from app.services.game_engine import GameEngine


class RpsGameEngineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = GameEngine()

    def test_rps_draw_instruction_accepts_matching_gesture(self) -> None:
           with patch("app.services.game_engine.sqlite_store.get_user_game_difficulty", return_value=None), \
               patch("app.services.game_engine.sqlite_store.upsert_user_game_difficulty"), \
               patch("app.services.game_engine.sqlite_store.get_time_since_last_same_game", return_value=None), \
             patch("app.services.game_engine.sqlite_store.create_session"), \
             patch("app.services.game_engine.sqlite_store.get_user_counters") as get_user_counters, \
             patch("app.services.game_engine.sqlite_store.insert_interaction"), \
             patch("app.services.game_engine.sqlite_store.update_session"):
            get_user_counters.return_value.total_attempted = 0
            get_user_counters.return_value.skill_opportunities = 0

            state = self.engine.create_session("rps", 60, "tester", 1.0)
            session = self.engine._sessions[state.session_id]
            session.rps_instruction = "draw"
            session.rps_cpu_action = "paper"

            next_state, correct, _ = self.engine.apply_action("rps", state.session_id, "paper")

            self.assertTrue(correct)
            self.assertEqual(next_state.score, 10)


if __name__ == "__main__":
    unittest.main()
