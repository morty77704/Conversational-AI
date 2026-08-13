from fastapi.testclient import TestClient  # 可以在测试进程中模拟 HTTP 客户端，不需要真的启动 Uvicorn。

from main import app

client = TestClient(app)  # 创建测试客户端，之后可以用它发送 GET、POST、DELETE 请求。


def test_health_live():
    response = client.get("/health/live")

    assert response.status_code == 200  # 模拟向健康接口发送 GET 请求。
    assert response.json() == {"status": "ok"}  # 检查返回内容，而不是只判断接口能否访问。这能防止接口虽然返回 200，内容却不符合需求。


if __name__ == "__main__":
    test_health_live()
