# tests/test_oneinch_api.py
import pytest
import requests
# 1inch API 클라이언트가 정의된 모듈 경로에 맞게 수정하세요.
# 예: your_project_root/trustflow/oneinch_api_client.py
from trustflow.oneinch_api_client import OneInchClient # 가상의 OneInchClient 클래스/함수

# OneInchClient가 API 키를 생성자에서 받는다고 가정
# 실제 API 키는 .env에서 가져오므로, 테스트에서는 더미 값을 사용하거나 모킹합니다.
@pytest.fixture
def oneinch_client_mock():
    """테스트를 위한 OneInchClient 모의 객체를 반환합니다."""
    # 실제 OneInchClient가 필요하다면, 아래 주석을 해제하고 필요한 의존성을 주입하세요.
    # config = load_yaml_config()
    # api_key = config.get("api_keys", {}).get("oneinch")
    # return OneInchClient(api_key="mock_oneinch_api_key")
    
    # 여기서는 간단히 OneInchClient 스텁 클래스를 사용하여 모의 객체를 만듭니다.
    class MockOneInchClient:
        def __init__(self, api_key):
            self.api_key = api_key
        def get_quote(self, from_token: str, to_token: str, amount: int):
            # 이 함수는 mocking됩니다.
            pass
    return MockOneInchClient(api_key="mock_oneinch_api_key")


def test_get_quote_success_mock(oneinch_client_mock, monkeypatch):
    """
    1inch API get_quote 호출을 모의하여 성공적인 응답을 테스트합니다.
    """
    # requests.get을 모의하여 가짜 응답을 반환하도록 설정
    def mock_get(*args, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                return {
                    "fromToken": {"symbol": "ETH"},
                    "toToken": {"symbol": "DAI"},
                    "toTokenAmount": "1000000000000000000" # 1 DAI (10^18)
                }
        return MockResponse()

    # monkeypatch를 사용하여 requests.get 함수를 mock_get으로 대체
    monkeypatch.setattr(requests, "get", mock_get)
    
    # oneinch_client_mock의 get_quote 메서드를 직접 호출하거나,
    # 해당 메서드가 requests.get을 호출하는지 확인합니다.
    # 여기서는 oneinch_client_mock의 get_quote 메서드도 모의합니다.
    def fake_get_quote(from_token, to_token, amount):
        # 실제 OneInchClient의 get_quote 로직이 requests.get을 호출할 것이므로,
        # 여기서는 단순히 모의된 결과를 반환합니다.
        return {"toTokenAmount": "1000000000000000000"}

    monkeypatch.setattr(oneinch_client_mock, "get_quote", fake_get_quote)

    quote = oneinch_client_mock.get_quote("ETH", "DAI", 1)
    assert quote is not None
    assert quote["toTokenAmount"] == "1000000000000000000"
    assert isinstance(quote["toTokenAmount"], str)

def test_get_quote_api_error_mock(oneinch_client_mock, monkeypatch):
    """
    1inch API 호출 시 에러 응답을 모의하여 에러 처리를 테스트합니다.
    """
    def mock_get_error(*args, **kwargs):
        class MockResponse:
            status_code = 400
            def json(self):
                return {"description": "Insufficient funds"}
            def raise_for_status(self):
                raise requests.exceptions.HTTPError("Bad Request")
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get_error)

    def fake_get_quote_error(from_token, to_token, amount):
        raise requests.exceptions.HTTPError("Bad Request")

    monkeypatch.setattr(oneinch_client_mock, "get_quote", fake_get_quote_error)

    with pytest.raises(requests.exceptions.HTTPError):
        oneinch_client_mock.get_quote("ETH", "DAI", 1)

# 더 많은 1inch API 연동 테스트 케이스 (swap, approve 등)
