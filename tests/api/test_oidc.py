from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from tests.utils import unique_str

from flask.testing import FlaskClient

from webapp.repositories import AppDatabase


class MockPyJWKClient:
    def __init__(self, pub):
        self.key = pub

    def get_signing_key_from_jwt(self, token):
        return self


def test_oidc_backchannel_logout(db: AppDatabase, client: FlaskClient):
    sid = unique_str()
    now = datetime.now(timezone.utc)
    payload = {
        "iat": now - timedelta(seconds=15),
        "exp": now + timedelta(seconds=15),
        "jti": "1a9887a0-287e-ce83-d64a-be6db240bab6",
        "iss": "https://sso.example.com/realms/test",
        "aud": "kispython.ru",
        "sub": "2ad8cc13-c49f-400a-b099-d835e0688391",
        "typ": "Logout",
        "sid": sid,
        "events": {
            "http://schemas.openid.net/event/backchannel-logout": {}
        }
    }

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = key.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
    tok = jwt.encode(payload, key, algorithm="RS256")

    with patch('webapp.views.student.jwks', MockPyJWKClient(pub)):
        response = client.post(
            '/logout/lks/backchannel',
            data={'logout_token': tok},
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

    assert response.status_code == 200
    assert db.students.is_session_blocked(sid)
