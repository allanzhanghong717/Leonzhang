import base64
from fastapi import FastAPI, HTTPException, Body
import uvicorn
from jose import jwt
from jose.exceptions import JWTError
from cryptography.hazmat.primitives.asymmetric import ed25519
from src.did_vc.did_registry import DIDRegistry

VERIFIER_PRIVATE_KEY, VERIFIER_PUBLIC_KEY, VERIFIER_DID = DIDRegistry.create_did_key()

app = FastAPI(title="可验证出示(VP)验证服务")

@app.get("/")
def get_verifier_info():
    return {"verifier_did": VERIFIER_DID}

def get_public_key_from_did(did: str) -> ed25519.Ed25519PublicKey:
    if not did.startswith("did:key:z"):
        raise ValueError("仅支持 did:key")
    encoded_key = did.split(':')[-1][1:]
    missing_padding = (4 - len(encoded_key) % 4) % 4
    encoded_key += '=' * missing_padding
    try:
        prefixed_public_key = base64.urlsafe_b64decode(encoded_key)
    except Exception as e:
        raise ValueError(f"解码公钥失败: {e}")
    if not prefixed_public_key.startswith(b'\xed\x01'):
        raise ValueError("不支持的密钥类型")
    public_key_bytes = prefixed_public_key[2:]
    return ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)

def public_key_to_jwk(pub_key: ed25519.Ed25519PublicKey) -> dict:
    public_bytes = pub_key.public_bytes_raw()
    return {
        "kty": "OKP",
        "crv": "Ed25519",
        "x": base64.urlsafe_b64encode(public_bytes).decode().rstrip('=')
    }

@app.post("/verify-presentation", summary="验证VP")
async def verify_presentation(signed_vp_jwt: str = Body(..., embed=True)):
    try:
        # 1. 提取 presenter DID
        unverified_vp = jwt.decode(signed_vp_jwt, key=None, options={"verify_signature": False})
        presenter_did = unverified_vp.get("iss")
        if not presenter_did or not isinstance(presenter_did, str):
            raise HTTPException(status_code=400, detail="缺少出示者DID")

        # 2. 验证 VP 签名
        presenter_pubkey = get_public_key_from_did(presenter_did)
        presenter_jwk = public_key_to_jwk(presenter_pubkey)
        vp_payload = jwt.decode(signed_vp_jwt, key=presenter_jwk, algorithms=["EdDSA"], audience=VERIFIER_DID)

        # 3. 验证 VC
        vcs = vp_payload.get("vp", {}).get("verifiableCredential", [])
        if not vcs:
            raise HTTPException(status_code=400, detail="无VC")

        verified_claims = []
        for vc_jwt in vcs:
            unverified_vc = jwt.decode(vc_jwt, key=None, options={"verify_signature": False})
            issuer_did = unverified_vc.get("iss")
            if not issuer_did or not isinstance(issuer_did, str):
                raise HTTPException(status_code=400, detail="VC缺少签发者")

            issuer_pubkey = get_public_key_from_did(issuer_did)
            issuer_jwk = public_key_to_jwk(issuer_pubkey)
            vc_payload = jwt.decode(vc_jwt, key=issuer_jwk, algorithms=["EdDSA"]) 
            verified_claims.append(vc_payload["vc"]["credentialSubject"])

        # 4. 权限判断
        for c in verified_claims:
            if c.get("role") == "高级维修工程师":
                return {"status": "success", "message": f"验证通过，欢迎{c.get('name')}"}

        raise HTTPException(status_code=403, detail="权限不足")

    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"JWT验证失败：{str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)