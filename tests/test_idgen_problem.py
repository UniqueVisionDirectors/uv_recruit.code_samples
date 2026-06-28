import pytest

from app.idgen.problem import ProblemIssuer


def test_problem_issuer_is_not_implemented_yet():
    # 学習者がここを実装する。未実装のうちは NotImplementedError。
    with pytest.raises(NotImplementedError):
        ProblemIssuer().issue()
