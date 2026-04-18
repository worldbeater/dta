import datetime
import jwt

from tests.utils import unique_str
from flask.testing import FlaskClient

from webapp.repositories import AppDatabase


def test_oidc_backchannel_logout(db: AppDatabase, client: FlaskClient):
    sid = unique_str()
    now = datetime.datetime.now()
    payload = {
        "iat": now,
        "exp": now + datetime.timedelta(minutes=5),
        "jti": "1a9887a0-287e-ce83-d64a-be6db240bab6",
        "iss": "https://sso.example.com/realms/test",
        "aud": "test",
        "sub": "2ad8cc13-c49f-400a-b099-d835e0688391",
        "typ": "Logout",
        "sid": sid,
        "events": {
            "http://schemas.openid.net/event/backchannel-logout": {}
        }
    }

    key = unique_str()
    logout_token = jwt.encode(payload, key, algorithm="HS256")
    response = client.post(
        '/logout/lks/backchannel',
        data={'logout_token': logout_token},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    assert response.status_code == 200
    assert db.students.is_session_blocked(sid)
