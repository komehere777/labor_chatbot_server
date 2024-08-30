from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for,
    flash,
)
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from utils import *
from config import SECRET_KEY
from model import (
    get_user_chat_historys,
    get_user_chat,
    User,
    create_user,
    authenticate_user,
    update_user_profile,
    delete_user,
    delete_chat,
)
from bson import ObjectId
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email
import logging

app = Flask(__name__)

app.secret_key = SECRET_KEY
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = True

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.session_protection = "strong"

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In")

class UserProfileForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Update Profile")

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)

@login_manager.user_loader
def load_user(user_id):
    print(f"Attempting to load user with id: {user_id}")  # 디버그 출력
    user = User.get(user_id)
    session['username'] = user.username if user else ''
    print(f"Loading user: {user}")  # 디버그 출력
    return User.get(ObjectId(user_id))

@app.route('/')
@login_required
def chat():
    # 채팅 히스토리와 ID 초기화
    session['chat_history'] = ''
    session['history_id'] = ''

    # 로그인 된 유저의 채팅 내역 가져오는 부분
    history = get_user_chat_historys(current_user.username)

    return render_template('chat.html', history = history, user = current_user)

@app.route("/check_auth")
def check_auth():
    return jsonify({"authenticated": current_user.is_authenticated})

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = authenticate_user(email, password)
        if user:
            login_user(user)
            session["user_id"] = str(user.id)
            print(f"User {user.id} logged in successfully.")  # 디버그 출력
            return redirect(url_for("chat"))
        else:
            print("Authentication failed.")  # 디버그 출력
    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    print(f"User {current_user.id} is logging out.")  # 디버그 출력
    logout_user()
    session.clear()
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        user = create_user(username, email, password)
        if user:
            login_user(user)
            print(f"User {user.id} registered and logged in.")  # 디버그 출력
            return redirect(url_for("login"))
        else:
            flash("already user exists")
            print("User registration failed: already exists.")  # 디버그 출력
    return render_template("register.html")

@app.route('/get_response', methods=['POST'])
def get_response():
    
    # 유저가 보낸 메시지를 받음
    user_input = request.json.get("message")

    # 채팅 내역과 ID를 세션에서 가져옵니다. 없으면 초기화
    chat_history = session.get('chat_history', '')
    history_id = session.get('history_id', '')
    
    # AI로부터 유저 질문에 대한 답변을 받는 부분
    ai_response, user = get_ai_response(user_input, chat_history)

    # 대화 내역 저장
    chat_history = chat_history + f"\nUser: {user}\nAI: {ai_response}"

    # 채팅 내역 저장
    if history_id:
        update_chat(history_id, user_input, ai_response)
    else:
        history_id = add_chat(session['username'], user_input, ai_response)

    # 세션에 채팅 내역과 ID 업데이트
    session['history_id'] = history_id
    session['chat_history'] = chat_history
    
    # JSON 형태로 응답을 반환
    return jsonify({"response": ai_response})

@app.route('/history/<history_id>')
@login_required
def history(history_id):

    # History ID를 세션에 저장
    session['history_id'] = history_id

    # 세션에서 유저이름 가져와서 채팅 내역 불러오는 부분 ( current_user 에서 가져와도 됨 )
    history = get_user_chat_historys(session['username']) # 유저의 전체 채팅 내역 로드
    chat = get_user_chat(history_id) # 해당 채팅만 로드
    print(chat)
    return render_template('history.html', history = history, chat = chat, user = current_user)

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    logging.debug(f"Accessing profile. Current user: {current_user}")
    logging.debug(f"Is authenticated: {current_user.is_authenticated}")

    form = UserProfileForm(obj=current_user)
    if form.validate_on_submit():
        if update_user_profile(current_user.id, form.username.data, form.email.data):
            flash("Profile updated successfully", "success")
            return redirect(url_for("profile"))
        else:
            flash("Failed to update profile", "error")

    history = get_user_chat_historys(current_user.username)

    return render_template("user_profile.html", form=form, history=history)

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    # 데이터베이스에서 유저 ID 제거
    delete_user(current_user.id)

    return redirect(url_for("login"))

@app.route('/delete_chat_data/<int:history_id>', methods=['POST'])
@login_required
def delete_chat_data(history_id):

    # 데이터베이스에서 해당 ID의 채팅 history 제거
    result = delete_chat(history_id)

    return jsonify({"success": result})

if __name__ == "__main__":
    app.run('0.0.0.0', port=5001, debug=True)