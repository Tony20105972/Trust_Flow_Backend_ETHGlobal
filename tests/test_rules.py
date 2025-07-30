# tests/test_rules.py
import pytest
# 실제 RuleChecker 모듈의 경로에 맞게 임포트 경로를 수정하세요.
# 예: your_project_root/trustflow/rule_checker.py
from trustflow.rule_checker import RuleChecker

class TestRuleChecker:
    """RuleChecker 클래스의 다양한 규칙 검사 기능을 테스트합니다."""

    @pytest.fixture(scope="class")
    def checker(self):
        """테스트를 위한 RuleChecker 인스턴스를 제공합니다."""
        return RuleChecker()

    def test_forbidden_keyword_detection(self, checker):
        """
        금지어가 포함된 텍스트를 올바르게 감지하는지 테스트합니다.
        (예: "hack", "exploit" 등의 키워드)
        """
        assert checker.check_keyword("this text contains a hack") is True
        assert checker.check_keyword("exploit vulnerability") is True
        assert checker.check_keyword("This is a safe sentence.") is False
        assert checker.check_keyword("") is False # 빈 문자열 테스트

    def test_length_rule(self, checker):
        """
        텍스트 길이가 특정 조건을 만족하는지 테스트합니다.
        (RuleChecker에 check_length와 같은 함수가 있다고 가정)
        """
        # RuleChecker 클래스에 check_length 함수가 정의되어 있어야 합니다.
        # def check_length(self, text: str, min_len: int = 10) -> bool:
        #     return len(text) >= min_len
        if hasattr(checker, 'check_length'):
            assert checker.check_length("short", min_len=10) is False
            assert checker.check_length("this is a long enough text", min_len=10) is True
        else:
            pytest.skip("RuleChecker.check_length 함수가 정의되지 않았습니다.")

    # 추가적인 규칙 검사 테스트 케이스들을 여기에 구현합니다.
    # 예: check_sentiment, check_formatting 등
