import pytest
import os
from dotenv import load_dotenv

load_dotenv()

from src.qube_pm_api_client.main import QubePMPLAPIClient, QubePMPLAPISession

@pytest.fixture
def base_url() -> str:
    # fetch from .env
    return os.getenv("KTS_URL")

@pytest.fixture
def session(base_url: str) -> QubePMPLAPISession:
    client = QubePMPLAPIClient(base_url=base_url, username=os.getenv("KTS_USERNAME"), password=os.getenv("KTS_PASSWORD"), group=os.getenv("KTS_GROUP"))
    return client.get_session()

def test_get_users(session: QubePMPLAPISession):
    response = session.get_users()
    assert response is not None
    assert response.status_code == 200
    assert b"<user-lookup success=\"true\">" in response.content

def test_close_report(session: QubePMPLAPISession):
    response = session.close_report()
    assert response is not None
    assert response.status_code == 200
    assert b"CloseReportResponse" in response.content

def test_logout(session: QubePMPLAPISession):
    response = session.logout()
    assert response is not None
    assert response.status_code == 200
    assert b"LogoutResponse" in response.content