# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

import json
import time

from firebase_functions import https_fn
from firebase_admin import initialize_app

from openai import OpenAI

from constnats import *


initialize_app()

openai_client = OpenAI(
    api_key="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",
    organization="org-RvYM0Z0MY8EbbQksGRsdwU28",
    project="proj_I9dbD5s2inxcrtkDC8Ulsbyw"
)

chat_assistant = openai_client.beta.assistants.retrieve("asst_ZzNhAYJYr79E1BfRd486UB6C")
corr_assistant = openai_client.beta.assistants.retrieve("asst_fh2qNWpcRBYVWzDCTBgKyAhn")
quiz_assistant = openai_client.beta.assistants.retrieve("asst_HZ35JOR0r2zHnSRIUZSuleD5")


@https_fn.on_request()
def on_request_example(req: https_fn.Request) -> https_fn.Response:
    return https_fn.Response(f"This is test")


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
    student_info_message = f"""
    학생 정보를 알려드리겠습니다.\n
    - 이름:{received_data.get(Jk.KEY_NAME)}\n
    - 나이:{received_data.get(Jk.KEY_AGE)}\n
    - 모국어:{received_data.get(Jk.KEY_NATIVE_LANG)}\n
    - 학습하고 싶은 언어:{received_data.get(Jk.KEY_LEARN_LANG)}\n
    - 학습하고 싶은 언어에 대한 학생의 수준:{Jk.KEY_LEVEL}
    """

    # 모든 스레드의 첫 메세지는 학생정보
    start_message = [
            {
                Ok.KEY_ROLE: Ok.ROLE_USER,
                Ok.KEY_CONTENT: student_info_message
            },
        ]

    # 3개의 스레드를 생성.
    chat_thread = openai_client.beta.threads.create(messages=start_message)
    corr_thread = openai_client.beta.threads.create(messages=start_message)
    quiz_thread = openai_client.beta.threads.create(messages=start_message)

    # 3개의 run 생성
    chat_run = openai_client.beta.threads.runs.create(
        model="GPT-4o mini",
        thread_id=chat_thread.id,
        assistant_id=chat_assistant.id
    )
    corr_run = openai_client.beta.threads.runs.create(
        model="GPT-4o mini",
        thread_id=corr_thread.id,
        assistant_id=corr_assistant.id
    )
    quiz_run = openai_client.beta.threads.runs.create(
        model="GPT-4o mini",
        thread_id=quiz_thread.id,
        assistant_id=quiz_assistant.id
    )

    # 3개의 run의 실행 종료 대기
    while chat_run.status == "queued" or chat_run.status == "in_progress":
        time.sleep(0.5)
        chat_run = openai_client.beta.threads.runs.retrieve(
            thread_id=chat_thread.id,
            run_id=chat_run.id
        )
    while corr_run.status == "queued" or corr_run.status == "in_progress":
        time.sleep(0.5)
        corr_run = openai_client.beta.threads.runs.retrieve(
            thread_id=corr_thread.id,
            run_id=corr_run.id
        )
    while quiz_run.status == "queued" or quiz_run.status == "in_progress":
        time.sleep(0.5)
        quiz_run = openai_client.beta.threads.runs.retrieve(
            thread_id=quiz_thread.id,
            run_id=quiz_run.id
        )

    # TODO: 여기서 각 run의 status가 "completed"가 아닌 경우를 처리해야 하는데, 일단 통과

    chat_reply_message = ""
    corr_reply_message = ""
    quiz_reply_message = ""

    # ai 응답 받기

    if chat_run.status == "completed":
        chat_thread_messages = openai_client.beta.threads.messages.list(
            thread_id=chat_thread.id,
            order="desc",
            limit=1
        )
        if chat_thread_messages:
            chat_reply_message = chat_thread_messages.data[0].content[0].text.value

    if corr_run.status == "completed":
        corr_thread_messages = openai_client.beta.threads.messages.list(
            thread_id=corr_thread.id,
            order="desc",
            limit=1
        )
        if corr_thread_messages:
            corr_reply_message = corr_thread_messages.data[0].content[0].text.value

    if quiz_run.status == "completed":
        quiz_thread_messages = openai_client.beta.threads.messages.list(
            thread_id=quiz_thread.id,
            order="desc",
            limit=1
        )
        if quiz_thread_messages:
            quiz_reply_message = quiz_thread_messages.data[0].content[0].text.value

    print(f"Chat:\n{chat_reply_message}")
    print(f"Corr:\n{corr_reply_message}")
    print(f"Quiz:\n{quiz_reply_message}")

    # JSON 형식으로 응답 데이터 생성
    response_data = {
        "name": received_data.get("name", ""),
        "age": received_data.get("age", ""),
        "nativeLang": received_data.get("nativeLang", ""),
        "learnLang": received_data.get("learnLang", ""),
        "level": received_data.get("level", ""),
        "userDocId": received_data.get("userDocId", ""),
        "threadId": "thread id",
        "message": f"여기에 인공지능의 메세지를 넣어서 보내줄 것입니다."
    }

    return https_fn.Response(json.dumps({"data": response_data}), mimetype='application/json')


