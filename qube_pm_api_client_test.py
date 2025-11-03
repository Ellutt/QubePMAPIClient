import os
from src.qube_pm_api_client.main import QubePMPLAPIClient
from dotenv import load_dotenv

load_dotenv()

def test_login_logout():
    base_url = os.getenv("QUBE_PM_API_URL")
    client_session_key = os.getenv("QUBE_PM_CLIENT_SESSION_KEY")
    username = os.getenv("QUBE_PM_USERNAME")
    password = os.getenv("QUBE_PM_PASSWORD")
    group = os.getenv("QUBE_PM_GROUP")

    client = QubePMPLAPIClient(
        base_url=base_url,
        client_session_key=client_session_key,
        username=username,
        password=password,
        group=group,
    )

    # Test login
    login_response = client.login()
    assert login_response.status_code == 200
    assert b"<Login-Overload-4Response" in login_response.content

    # Test logout
    logout_response = client.logout(client_session_key)
    assert logout_response.status_code == 200
    assert b"<LogoutResponse" in logout_response.content

if __name__ == "__main__":
    test_login_logout()