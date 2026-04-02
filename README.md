# DID/VC 身份验证系统

## 项目概述

本项目实现了一个基于 DID（去中心化身份）和 VC（可验证凭证）的完整身份验证系统，包括：

- **DID 生成和解析**：支持 `did:key` 格式的身份标识
- **VC 签发服务**：签发可验证凭证
- **身份钱包**：管理用户凭证
- **VP 验证服务**：验证出示的凭证

## 快速开始

### 1. 环境准备

```bash
# 克隆仓库
git clone https://github.com/allanzhanghong717/Leonzhang.git
cd Leonzhang

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动服务

**终端1 - 启动 VC 签发服务**
```bash
source venv/bin/activate
python -m src.did_vc.vc_issuer_service
```
看到 `Uvicorn running on http://127.0.0.1:8000` 表示成功

**终端2 - 启动 VP 验证服务**
```bash
source venv/bin/activate
python -m src.did_vc.vp_verifier_service
```
看到 `Uvicorn running on http://127.0.0.1:8001` 表示成功

**终端3 - 运行演示脚本**
```bash
source venv/bin/activate
python src/did_vc/identity_wallet_sdk.py
```

### 3. 预期输出

```
用户 DID: did:key:z...
钱包：成功为did:key:z...添加凭证
验证者 DID: did:key:z...

=== 生成的 VP (JWT) ===
eyJ...
=======================

验证结果: {'status': 'success', 'message': '验证通过，欢迎张工'}
```

## 项目结构

```
src/
├── __init__.py
└── did_vc/
    ├── __init__.py
    ├── did_registry.py           # DID 生成和解析
    ├── vc_issuer_service.py      # VC 签发服务 (端口8000)
    ├── identity_wallet_sdk.py    # 身份钱包演示脚本
    └── vp_verifier_service.py    # VP 验证服务 (端口8001)
```

## API 文档

### VC 签发服务 (http://127.0.0.1:8000)

**POST /issue-credential**

请求体：
```json
{
  "subject_did": "did:key:z...",
  "credential_subject": {"name": "张工", "role": "高级维修工程师"},
  "credential_type": "VerifiableCredential",
  "evidence": []
}
```

响应：
```json
{
  "verifiableCredential": "eyJ..."
}
```

### VP 验证服务 (http://127.0.0.1:8001)

**GET /**

获取验证者 DID

响应：
```json
{
  "verifier_did": "did:key:z..."
}
```

**POST /verify-presentation**

请求体：
```json
{
  "signed_vp_jwt": "eyJ..."
}
```

验证成功响应：
```json
{
  "status": "success",
  "message": "验证通过，欢迎张工"
}
```

## 故障排查

### 问题1：422 Validation Error

**原因**：请求体格式不正确

**解决方案**：
- 确保 `signed_vp_jwt` 字段存在
- 检查 JWT 格式是否正确

### 问题2：500 Internal Server Error

**原因**：服务端异常

**解决方案**：
1. 查看错误服务所在终端的错误信息
2. 确保两个服务都在运行
3. 检查依赖是否完整：`pip install -r requirements.txt`

### 问题3：连接被拒绝

**原因**：服务未启动

**解决方案**：
1. 确保虚拟环境已激活
2. 检查终端是否显示 `Uvicorn running` 信息
3. 确保端口 8000 和 8001 未被占用

## 技术栈

- **FastAPI**：Web 框架
- **PyJWT**：JWT 处理
- **cryptography**：密码学库（Ed25519 签名）
- **Pydantic**：数据验证

## License

MIT