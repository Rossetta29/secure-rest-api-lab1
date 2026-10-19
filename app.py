from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import jwt
import datetime
from markupsafe import escape
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = "super-secret-key-for-lab-change-me-please"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lab.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 数据库模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.LargeBinary, nullable=False)

# JWT校验中间件，增加 wraps 修复重名bug
def token_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"message": "Token missing"}),401
        try:
            token = token.replace("Bearer ","")
            payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            current_user_id = payload["user_id"]
        except jwt.InvalidTokenError:
            return jsonify({"message":"Invalid or expired token"}),401
        return func(current_user_id,*args,**kwargs)
    return wrapper

# 1.登录接口 POST /auth/login
@app.route("/auth/login",methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password").encode("utf-8")
    user:User = User.query.filter_by(username=username).first()
    if not user or not bcrypt.checkpw(password, user.password_hash):
        return jsonify({"message":"Wrong username or password"}),401
    # 颁发JWT，有效期30分钟
    token = jwt.encode({
        "user_id":user.id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    }, app.config["SECRET_KEY"], algorithm="HS256")
    return jsonify({"access_token":token})

# 2.受保护接口 GET /api/data
@app.route("/api/data",methods=["GET"])
@token_required
def get_data(current_user_id):
    raw_data = {"message":"protected resource","user_id":escape(current_user_id)}
    return jsonify(raw_data)

#3.自己新增接口 GET /api/userinfo/<int:user_id>
@app.route("/api/userinfo/<int:user_id>",methods=["GET"])
@token_required
def get_user_info(current_user_id,user_id):
    u = User.query.get(user_id)
    if not u:
        return jsonify({"msg":"user not found"}),404
    safe_username = escape(u.username)
    return jsonify({"id":u.id,"username":safe_username})

#初始化数据库，创建测试账号
with app.app_context():
    db.create_all()
    # 创建测试用户 admin / TestPass123!
    if not User.query.filter_by(username="admin").first():
        hash_pw = bcrypt.hashpw(b"TestPass123!", bcrypt.gensalt())
        new_user = User(username="admin", password_hash=hash_pw)
        db.session.add(new_user)
        db.session.commit()

if __name__ == "__main__":
    app.run(debug=False)
