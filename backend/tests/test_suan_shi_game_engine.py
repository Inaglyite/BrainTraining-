import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("SQLITE_DB_PATH", str(Path(tempfile.gettempdir()) / "yusnxing-test-game-data.db"))

from app.services.game_engine import GameEngine


class SuanShiGameEngineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = GameEngine()

    def test_suan_shi_waits_for_final_two_answers_before_completion(self) -> None:
        with patch("app.services.game_engine.sqlite_store.get_user_n_back_level", return_value=2), \
             patch("app.services.game_engine.sqlite_store.list_interactions", return_value=[]), \
             patch("app.services.game_engine.sqlite_store.update_user_n_back_level"), \
               patch("app.services.game_engine.sqlite_store.get_user_game_difficulty", return_value=None), \
               patch("app.services.game_engine.sqlite_store.upsert_user_game_difficulty"), \
             patch("app.services.game_engine.sqlite_store.get_time_since_last_same_game", return_value=None), \
             patch("app.services.game_engine.sqlite_store.create_session"), \
             patch("app.services.game_engine.sqlite_store.get_user_counters") as get_user_counters, \
             patch("app.services.game_engine.sqlite_store.insert_interaction"), \
             patch("app.services.game_engine.sqlite_store.update_session"), \
             patch("app.services.game_engine.sqlite_store.update_user_first_test_completed"):
            get_user_counters.return_value.total_attempted = 0
            get_user_counters.return_value.skill_opportunities = 0

            state = self.engine.create_session("suan-shi", 600, "tester", 1.0)
            total = state.suanshi_total_questions
            self.assertEqual(total, 20)

            while state.status != "completed":
                if state.suanshi_can_answer:
                    gesture = str(state.suanshi_target_answer)
                else:
                    gesture = "1"

                state, _, _ = self.engine.apply_action("suan-shi", state.session_id, gesture)

                if state.suanshi_answered_questions == total - 2:
                    self.assertEqual(state.current_question, "请继续回答剩余题目")
                    self.assertTrue(state.suanshi_can_answer)
                    self.assertEqual(state.status, "active")

            self.assertEqual(state.suanshi_answered_questions, total)
            self.assertEqual(state.status, "completed")


if __name__ == "__main__":
    unittest.main()
