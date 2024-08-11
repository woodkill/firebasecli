# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

import json

from firebase_functions import https_fn
from firebase_admin import initialize_app

from openai import OpenAI

initialize_app()

openai_client = OpenAI(
    api_key="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",
    organization="org-RvYM0Z0MY8EbbQksGRsdwU28",
    project="proj_I9dbD5s2inxcrtkDC8Ulsbyw"
)

assistant = openai_client.beta.assistants.retrieve("asst_UBCeDtnCKs0E37tRMg3399cW")

@https_fn.on_request()
def on_request_example(req: https_fn.Request) -> https_fn.Response:
    return https_fn.Response(f"This is test")


@https_fn.on_request()
def on_request_start_new(req: https_fn.Request) -> https_fn.Response:

    # JSON 데이터 추출
    request_data = req.get_json(silent=True)
    if not request_data:
        # 오류 응답
        print("No JSON data received")
        error_response = {"error": "No JSON data received"}
        return https_fn.Response(json.dumps(error_response), status=400, mimetype='application/json')
    print(f"Received JSON data: {request_data}")

    received_data = request_data.get("data", None)
    if not received_data:
        # 오류 응답
        print("No data key in received JSON data")
        error_response = {"error": "No data key in received JSON data"}
        return https_fn.Response(json.dumps(error_response), status=400, mimetype='application/json')
    print(f"data: {received_data}")

    # openai thread 생성
    # assitant와 thread 연결
    # ai 에게 말하기
    # ai 응답 받기

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


