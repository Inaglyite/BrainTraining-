from __future__ import annotations

import time

from app.services.game_engine import GameEngine


def run_smoke_test() -> None:
    engine = GameEngine()
    user_id = f"test-user-{int(time.time() * 1000)}"

    sx = engine.create_session("shu-xiang", 60, user_id, 1.0)
    assert sx.box_count is not None

    sx_after_open, sx_correct, _ = engine.apply_action("shu-xiang", sx.session_id, str(sx.box_count))
    assert sx_correct is True
    assert sx_after_open.score == 10
    assert sx_after_open.user_id == user_id

    wrong_box_gesture = "9" if str(sx_after_open.box_count) != "9" else "8"
    sx_after_fist, sx_wrong, _ = engine.apply_action("shu-xiang", sx.session_id, wrong_box_gesture)
    assert sx_wrong is False
    assert sx_after_fist.score == 5

    ss = engine.create_session("suan-shi", 60, user_id, 1.0)
    assert ss.current_question is not None
    assert ss.n_back_level == 2
    assert ss.suanshi_can_answer is False
    assert ss.suanshi_total_questions == 20

    q = ss.current_question.replace("= ?", "")
    left, right = [x.strip() for x in q.split("+")]
    ans = int(left) + int(right)
    assert 1 <= int(left) <= 9
    assert 1 <= int(right) <= 9
    assert 1 <= ans <= 9

    ss_after_open, ss_ok, _ = engine.apply_action("suan-shi", ss.session_id, str(ans))
    assert ss_ok is False
    assert ss_after_open.score == 0
    assert ss_after_open.suanshi_can_answer is False

    q2 = ss_after_open.current_question.replace("= ?", "")
    left2, right2 = [x.strip() for x in q2.split("+")]
    ans2 = int(left2) + int(right2)
    assert 1 <= int(left2) <= 9
    assert 1 <= int(right2) <= 9
    assert 1 <= ans2 <= 9

    ss_after_second_warmup, ss_second_warmup_ok, _ = engine.apply_action("suan-shi", ss.session_id, str(ans2))
    assert ss_second_warmup_ok is False
    assert ss_after_second_warmup.score == 0
    assert ss_after_second_warmup.suanshi_can_answer is True
    assert ss_after_second_warmup.suanshi_target_answer == ans

    ss_after_second, ss_second_ok, _ = engine.apply_action("suan-shi", ss.session_id, str(ans))
    assert ss_second_ok is True
    assert ss_after_second.score == 10

    wrong_digit = "9" if str(ss_after_second.suanshi_target_answer) != "9" else "8"
    ss_after_fist, ss_wrong, _ = engine.apply_action("suan-shi", ss.session_id, wrong_digit)
    assert ss_wrong is False
    assert ss_after_fist.score == 5
    assert ss_after_open.current_question is not None

    rps = engine.create_session("rps", 60, user_id, 1.0)
    assert rps.rps_cpu_action is not None
    assert rps.rps_instruction is not None

    win_map = {"rock": "paper", "paper": "scissors", "scissors": "rock"}
    lose_map = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
    choose = win_map[rps.rps_cpu_action] if rps.rps_instruction == "win" else lose_map[rps.rps_cpu_action]
    rps_after, rps_ok, _ = engine.apply_action("rps", rps.session_id, choose)
    assert rps_ok is True
    assert rps_after.score == 10

    print("smoke_test: ok")


if __name__ == "__main__":
    run_smoke_test()

