### [Autonomous Safe Code Patch]
**Target Service:** payment_service
**Objective:** Prevent NoneType subscript error.

```python
def verify_jwt(token: str):
    payload = decode_jwt(token)
    user_id = payload.get('user_id') if payload else None
    if not user_id:
        raise ValueError('Payload missing user_id')
    return user_id
```

*AST Syntax Validation:* Passed ✅