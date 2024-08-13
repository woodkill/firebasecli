class Jk: # JSON KEY
    KEY_CREATED_AT = "createdAt"
    KEY_NAME = "name"
    KEY_AGE = "age"
    KEY_NATIVE_LANG = "nativeLang"
    KEY_LEARN_LANG = "learnLang"
    KEY_LEVEL = "level"
    KEY_DOC_ID = "userDocId"
    KEY_CHAT_ID = "chatDocId"
    KEY_ROLE = "role"
    KEY_MESSAGE = "message"
    KEY_ID = "id"
    KEY_CHAT_THREAD_ID = "chatThreadId"
    KEY_CORR_THREAD_ID = "corrThreadId"
    KEY_QUIZ_THREAD_ID = "quizThreadId"

class Fb: # Firebase KEY, COLLECTION, DOCUMENT
    COL_USERS = "users" # 1단계
    COL_SETTINGS = "settings"
    # 각 사용자 doc 밑에
    COL_CHAT = "chat"   # 2단계
    COL_CORR = "corr"   # 2단계
    COL_QUIZ = "quiz"   # 2단계


class Ok: # OpenAi KEY
    KEY_ROLE = "role"
    KEY_CONTENT = "content"
    ROLE_USER = "user"
    ROLE_ASSIST = "assistant"
    ROLE_SYSTEM = "system"


class Lt: # Learn Type
    I_CHAT = 0
    I_CORR = 1
    I_QUIZ = 2
    KEY_CHAT = "chat"
    KEY_CORR = "corr"
    KEY_QUIZ = "quiz"


