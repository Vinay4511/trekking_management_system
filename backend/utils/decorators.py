from functools import wraps
from flask_jwt_extended import (
    create_access_token,
    get_jwt,
    jwt_required,
)
from flask import jsonify

def role_required(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args,**kwargs):
            claims = get_jwt()
            user_role = claims.get("role")
            if user_role not in allowed_roles:
                return (jsonify(
                        {
                            "message": f"Access forbidden: Requires one of {list(allowed_roles)} roles"
                        }
                    ),403,)
            return fn(*args, **kwargs)
        return wrapper
    return decorator