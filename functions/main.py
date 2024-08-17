# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

import json
import time

from firebase_functions import https_fn
from firebase_admin import initialize_app, firestore

from openai import OpenAI

from constnats import *

initialize_app()

openai_client = OpenAI(
    api_key="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",
    organization="org-RvYM0Z0MY8EbbQksGRsdwU28",
    project="proj_I9dbD5s2inxcrtkDC8Ulsbyw"
)

assistants = [
    openai_client.beta.assistants.retrieve("asst_ZzNhAYJYr79E1BfRd486UB6C"),
    openai_client.beta.assistants.retrieve("asst_fh2qNWpcRBYVWzDCTBgKyAhn"),
    openai_client.beta.assistants.retrieve("asst_HZ35JOR0r2zHnSRIUZSuleD5")
]
thread_cols = [Fb.COL_CHAT, Fb.COL_CORR, Fb.COL_QUIZ]
thread_field_keys = [Jk.KEY_CHAT_THREAD_ID, Jk.KEY_CORR_THREAD_ID, Jk.KEY_QUIZ_THREAD_ID ]


def create_new_thread_and_run(i_learn_type: int, start_messages: list) -> tuple[str, str, str]:
    # thread 생성.
    thread = openai_client.beta.threads.create(messages=start_messages)
    # 학습 type에 따른 run 생성
    run = openai_client.beta.threads.runs.create(
        model="gpt-4o",
        thread_id=thread.id,
        assistant_id=assistants[i_learn_type].id
    )
    # run의 실행 종료 대기
    while run.status == "queued" or run.status == "in_progress":
        time.sleep(0.5)
        run = openai_client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
    # run이 제대로 실행을 종료하지 못했으면(queued, in_progress 둘 다 아님) 상태 코드 리턴
    if run.status != "completed":
        return run.status, "", None
    # 가장 마지막 메세지(assistnat가 준것)만 조회
    thread_messages = openai_client.beta.threads.messages.list(
        thread_id=thread.id,
        order="desc",
        limit=1
    )
    reply_message = thread_messages.data[0].content[0].text.value if thread_messages else ""
    return run.status, reply_message, thread.id


def retrieve_thread_and_run(learn_type_index: int, thread_id: str, message: str) -> tuple[str, str]:
    # 학습 type에 따른 run 생성
    run = openai_client.beta.threads.runs.create(
        model="gpt-4o",
        thread_id=thread_id,
        assistant_id=assistants[learn_type_index].id,
        additional_messages=[
            {
                Ok.KEY_ROLE: Ok.ROLE_USER,
                Ok.KEY_CONTENT: message
            },
        ]
    )
    # run의 실행 종료 대기
    while run.status == "queued" or run.status == "in_progress":
        time.sleep(0.5)
        run = openai_client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
    # run이 제대로 실행을 종료하지 못했으면(queued, in_progress 둘 다 아님) 상태 코드 리턴
    if run.status != "completed":
        return run.status, ""
    # 가장 마지막 메세지(assistnat가 준것)만 조회
    thread_messages = openai_client.beta.threads.messages.list(
        thread_id=thread_id,
        order="desc",
        limit=1
    )
    reply_message = thread_messages.data[0].content[0].text.value if thread_messages else ""
    return run.status, reply_message


@https_fn.on_request()
def on_request_start_new(req: https_fn.Request) -> https_fn.Response:
    # JSON 데이터 추출
    json_req = req.get_json(silent=True)
    if not json_req:
        # 오류 응답
        print("No JSON request received")
        error_response = {"error": "No JSON request received"}
        return https_fn.Response(json.dumps(error_response), status=400, mimetype='application/json')
    print(f"Received JSON request: {json_req}")

    received_data = json_req.get("data", None)
    if not received_data:
        # 오류 응답
        print("No data key in received JSON request")
        error_response = {"error": "No data key in received JSON request"}
        return https_fn.Response(json.dumps(error_response), status=400, mimetype='application/json')
    print(f"data: {received_data}")

    # 스레드를 만들 때 첫 메세지로 넣을 학생 정보를 문자열로 만든다.
    name = received_data.get(Jk.KEY_NAME)
    age = received_data.get(Jk.KEY_AGE)
    nativeLang = received_data.get(Jk.KEY_NATIVE_LANG)
    learnLang = received_data.get(Jk.KEY_LEARN_LANG)
    level = received_data.get(Jk.KEY_LEVEL)

    student_info_message = f"""
    학생 정보를 알려드리겠습니다.\n
    - 이름:{name}\n
    - 나이:{age}\n
    - 모국어:{nativeLang}\n
    - 학습하고 싶은 언어:{learnLang}\n
    - 학습하고 싶은 언어에 대한 학생의 수준:{level}
    """

    userDocId = received_data.get(Jk.KEY_DOC_ID)

    # 모든 스레드의 첫 메세지는 학생정보
    start_messages = [
        {
            Ok.KEY_ROLE: Ok.ROLE_USER,
            Ok.KEY_CONTENT: student_info_message
        },
    ]

    # colud function call의 응답 준비
    response_data = {}

    # Firestore 클라이언트 생성
    db = firestore.client()

    # 이 사용자의 User Doc
    userDoc_ref = db.collection(Fb.COL_USERS).document(userDocId)

    # chat, corr, quiz 각각 스레드와 런을 만들어 실행하고 결과를 받는다.
    for i in [Lt.I_CHAT, Lt.I_CORR, Lt.I_QUIZ]:
        # 같은 첫번째 메세지로 스레드를 만들고 실행시킨다
        status, message, thread_id = create_new_thread_and_run(i, start_messages)
        if status == "completed":
            print(f"{thread_cols[i]} : {message}")
            # user Doc에 각 학습방식 스레드 Id 저장
            userDoc_ref.update({thread_field_keys[i]: thread_id})
            response_data[thread_field_keys[i]] = thread_id
            # user Doc 밑에 해당 collection을(chat, corr, quiz) 만들고 대화 메세지를 넣는다.
            doc_ref = userDoc_ref.collection(thread_cols[i]).document()
            doc_ref.set({
                Jk.KEY_ID: doc_ref.id,
                Jk.KEY_ROLE: Ok.ROLE_ASSIST,
                Jk.KEY_MESSAGE: message,
                Jk.KEY_CREATED_AT: firestore.SERVER_TIMESTAMP
            })

    # user Doc에 새로 만든 3개 학습 방식 thread id를 기록
    userDoc_ref.update(response_data)

    # 새로운 학생으로 시작되었다는 Settings 메세지를 settings collection에 넣는다.
    col_settings = db.collection(Fb.COL_SETTINGS)
    doc_ref = col_settings.document()
    doc_ref.set({
        Jk.KEY_ID: doc_ref.id,
        Jk.KEY_MESSAGE: f"{name}({age})님의 {learnLang} 학습을 도와드리겠습니다.\n세가지 학습 방식을 잘 활용해 보세요.",
        Jk.KEY_ROLE: Ok.ROLE_ASSIST,
        Jk.KEY_CREATED_AT: firestore.SERVER_TIMESTAMP
    })

    # 생성된 스레드 Id 정보를 응답으로 보낸다.
    return https_fn.Response(json.dumps({"data": response_data}), mimetype='application/json')


@https_fn.on_request()
def on_request_user_message(req: https_fn.Request) -> https_fn.Response:
    # JSON 데이터 추출
    json_req = req.get_json(silent=True)
    if not json_req:
        # 오류 응답
        print("No JSON request received")
        error_response = {"error": "No JSON request received"}
        return https_fn.Response(json.dumps(error_response), status=400, mimetype='application/json')
    print(f"Received JSON request: {json_req}")

    received_data = json_req.get("data", None)
    if not received_data:
        # 오류 응답
        print("No data key in received JSON request")
        error_response = {"error": "No data key in received JSON request"}
        return https_fn.Response(json.dumps(error_response), status=400, mimetype='application/json')
    print(f"data: {received_data}")

    learn_type = received_data.get(Jk.KEY_LEARN_TYPE)
    user_doc_id = received_data.get(Jk.KEY_DOC_ID)
    thread_id = received_data.get(Jk.KEY_THREAD_ID)
    message = received_data.get(Jk.KEY_MESSAGE)
    print(f"learnType:{learn_type}, userDocId:{user_doc_id}, threadId:{thread_id}, message:{message}")

    learn_type_index = Lt.I_CHAT if learn_type == Lt.KEY_CHAT else Lt.I_CORR if learn_type == Lt.KEY_CORR else Lt.I_QUIZ

    # colud function call의 응답 준비
    response_data: dict = {}

    # Firestore 클라이언트 생성
    db = firestore.client()

    # 이 사용자의 User Doc
    userDoc_ref = db.collection(Fb.COL_USERS).document(user_doc_id)

    status, message = retrieve_thread_and_run(learn_type_index, thread_id, message)
    if status == "completed":
        print(f"{thread_cols[learn_type_index]} : {message}")
        # user Doc에 각 학습방식 스레드 Id 저장
        # user Doc 밑에 해당 chat collection에 AI의 대화 메세지를 넣는다.
        doc_ref = userDoc_ref.collection(thread_cols[learn_type_index]).document()
        doc_ref.set({
            Jk.KEY_ID: doc_ref.id,
            Jk.KEY_ROLE: Ok.ROLE_ASSIST,
            Jk.KEY_MESSAGE: message,
            Jk.KEY_CREATED_AT: firestore.SERVER_TIMESTAMP
        })
        response_data[Jk.KEY_RESULT] = Rc.RC_SUCCESS
    else:
        response_data[Jk.KEY_RESULT] = Rc.RC_FAIL

    # 처리결과를 응답으로 보낸다.
    return https_fn.Response(json.dumps({"data": response_data}), mimetype='application/json')
