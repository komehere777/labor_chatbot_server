from pymongo import MongoClient
from config import MONGO_URI, MONGO_DBNAME
from datetime import datetime
import pytz
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId

class MongoDBConnection:
  def __init__(self, uri, db_name):
    self.client = MongoClient(uri)
    self.db = self.client[db_name]

class Context:
  def __init__(self, db):
    self.collection = db['context']

  def get_context_all(self):
    documents = self.collection.find({}, {"_id": 0, "content": 1})

    return [doc['content'] for doc in documents]
  
class ChatHistory:
  def __init__(self, db):
      self.collection = db['chat_history']
      self.counter_collection = db['counters']

  def get_next_sequence_value(self, sequence_name):
      sequence_document = self.counter_collection.find_one_and_update(
          {"_id": sequence_name},
          {"$inc": {"sequence_value": 1}},
          upsert=True,
          return_document=True
      )
      return sequence_document["sequence_value"]

  def add_chat(self, chat_data):
      chat_data["history_id"] = self.get_next_sequence_value("history_id")
      chat_data["created_at"] = datetime.now(pytz.timezone('Asia/Seoul'))

      self.collection.insert_one(chat_data)
      return chat_data["history_id"]
  
  def update_chat(self, history_id, user_input, ai_response):

    result = self.collection.update_one(
      {"history_id": int(history_id)},
      {
        "$push": {
          "chat": {
            "user": user_input,
            "ai": ai_response,
          }
        },
      }
    )

    return result.modified_count > 0

  def get_chat(self, history_id):
    return self.collection.find_one({"history_id": int(history_id)}, {"chat":1, "_id": 0})

  def get_user_chats(self, username):
    return self.collection.find(
        {"username": username},
        {"history_id": 1, "chat": 1, "created_at": 1, "_id": 0}
    ).sort("created_at", -1)

  def delete_chat(self, history_id):
    return self.collection.delete_one({"history_id": int(history_id)})
  
class Users:
  def __init__(self, db):
    self.collection = db['users']

  def create_user(self, user_data):
    return self.collection.insert_one(user_data)
  
  def get_user_by_id(self, user_id):
    return self.collection.find_one({"_id": ObjectId(user_id)})

  def get_user_by_email(self, email):
    return self.collection.find_one({"email": email})
  
  def get_user_by_username(self, username):
    return self.collection.find_one({"email": username})

  def update_user(self, user_id, update_data):
    return self.collection.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})

  def delete_user(self, user_id):
    return self.collection.delete_one({"_id": ObjectId(user_id)})

def get_mongo_client():
  uri = MONGO_URI
  db_name = MONGO_DBNAME
  return MongoDBConnection(uri, db_name)

mongo_connection = get_mongo_client()

# 컨텍스트 가져오는 부분
def get_all_contents():
  context = Context(mongo_connection.db)

  return context.get_context_all()

# 사용자의 모든 채팅 내역 가져오는 부분
def get_user_chat_historys(username):
  collection = ChatHistory(mongo_connection.db)

  history = collection.get_user_chats(username)
  chat_history = []
  for doc in history:
    chat_history.append({
      'history_id': doc.get('history_id'),
      'chat': doc.get('chat', [])
    })
  return chat_history

# ID로 한 채팅 내역만 가져오는 부분
def get_user_chat(history_id):
  collection = ChatHistory(mongo_connection.db)

  history_id = int(history_id)
  chat = collection.get_chat(history_id)

  return chat.get('chat', [])

class User(UserMixin):
  def __init__(self, user_id, username, email, password_hash):
    self.id = user_id
    self.username = username
    self.email = email
    self.password_hash = password_hash

  @staticmethod
  def get(user_id):
    users = Users(mongo_connection.db)
    user_data = users.get_user_by_id(ObjectId(user_id))
    if not user_data:
        return None
    return User(str(user_data["_id"]), user_data["username"], user_data["email"], user_data["password_hash"])

  @staticmethod
  def get_by_email(email):
    users = Users(mongo_connection.db)
    user_data = users.get_user_by_email(email)
    if not user_data:
      return None
    return User(
      user_id=user_data['_id'],
      username=user_data['username'],
      email=user_data['email'],
      password_hash=user_data['password_hash']
    )

def create_user(username, email, password):
  users = Users(mongo_connection.db)
  existing_user = users.get_user_by_email(email) or users.get_user_by_username(username)
  if existing_user:
    return False
  hashed_password = generate_password_hash(password)
  user_id = users.create_user({
    "username": username,
    "email": email,
    "password_hash": hashed_password
  }).inserted_id
  return User.get(user_id)

def authenticate_user(email, password):
  user = User.get_by_email(email)
  if user and check_password_hash(user.password_hash, password):
    print(f"Authenticated user: {user}")  # 디버그 출력
    return user
  return None

# 새로운 채팅일 때
def add_chat(username, user, ai):
  collection = ChatHistory(mongo_connection.db)
  history_id = collection.add_chat({
    "chat": [{"user": user, "ai": ai}],
    "username": username
  })

  return history_id

# 기존의 채팅에 업데이트 할 때
def update_chat(history_id, user, ai):
  collection = ChatHistory(mongo_connection.db)
  collection.update_chat(history_id, user, ai)

def update_user_profile(user_id, username, email):
    users = Users(mongo_connection.db)

    # 이메일 중복 체크
    existing_user = users.get_user_by_email(email)
    if existing_user and str(existing_user["_id"]) != user_id:
        return False  # 이미 존재하는 이메일

    # 사용자 이름 중복 체크
    existing_user = users.get_user_by_username(username)
    if existing_user and str(existing_user["_id"]) != user_id:
        return False  # 이미 존재하는 사용자 이름

    # 프로필 업데이트
    result = users.update_user(user_id, {"username": username, "email": email})

    return result.modified_count > 0

def delete_user(user_id):
  users = Users(mongo_connection.db)

  result = users.delete_user(user_id)

  return result.deleted_count > 0

def delete_chat(history_id):
  collection = ChatHistory(mongo_connection.db)

  result = collection.delete_chat(history_id)

  return result.deleted_count > 0