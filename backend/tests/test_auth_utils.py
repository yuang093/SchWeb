from app.utils.auth_utils import get_basic_auth_header

def test_get_basic_auth_header():
    client_id = "test_id"
    client_secret = "test_secret"
    # base64("test_id:test_secret") -> dGVzdF9pZDp0ZXN0X3NlY3JldA==
    expected = "Basic dGVzdF9pZDp0ZXN0X3NlY3JldA=="
    result = get_basic_auth_header(client_id, client_secret)
    assert result == expected
    print("test_get_basic_auth_header passed!")

if __name__ == "__main__":
    test_get_basic_auth_header()
