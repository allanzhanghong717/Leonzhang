import time
from datetime import datetime, timedelta
from fastapi import FastAPI
import uvicorn
from jose import jwt
from pydantic import BaseModel
from src.did_vc.did_registry import DIDRegistry

ISSUER_PRIVATE_KEY, ISSUER_PUBLIC_KEY, ISSUER_DID = DIDRegistry.create_did_key()

app = FastAPI(title="可验证凭证(VC)签发服务")

class CredentialRequest(BaseModel):
    subject_did: str
    credential_subject: dict
    credential_type: str = "VerifiableCredential"
    evidence: list = None

@app.post("/issue-credential", summary="签发可验证凭证")
def issue_credential(request: CredentialRequest):
    vc_payload = {
        "iss": ISSUER_DID,
        "sub": request.subject_did,
        "nbf": int(time.time()),
        "exp": int((datetime.now() + timedelta(days=365)).timestamp()),
        "vc": {
            "@context": ["https://www.w3.org/2018/credentials/v1"],
            "type": [request.credential_type],
            "issuer": ISSUER_DID,
            "issuanceDate": datetime.now().isoformat() + "Z",
            "credentialSubject": request.credential_subject
        }
    }
    if request.evidence:
        vc_payload["vc"]["evidence"] = request.evidence

    headers = {"alg": "EdDSA", "typ": "JWT"}
    signed_vc_jwt = jwt.encode(vc_payload, ISSUER_PRIVATE_KEY, algorithm="EdDSA", headers=headers)
    return {"verifiableCredential": signed_vc_jwt}

if __name__ == "__main__":"
    uvicorn.run(app, host="127.0.0.1", port=8000)