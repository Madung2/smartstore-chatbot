from locust import task, between
from locust_plugins.websocket import WebSocketUser
import json

class ChatbotWebSocketUser(WebSocketUser):
    wait_time = between(1, 2)

    @task
    def chat(self):
        message = {
            "question": "스마트스토어 판매자 등록 방법 알려줘",
            "top_k": 3
        }
        self.connect()  # host/ws 경로로 자동 연결
        self.send(json.dumps(message))
        for _ in range(10):  # 10번까지 응답 대기(실제 종료 조건에 맞게 수정)
            response = self.receive()
            print("응답:", response)
