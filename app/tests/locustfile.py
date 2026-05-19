import uuid
from locust import HttpUser, task, between


class AuthUser(HttpUser):
    wait_time = between(1, 2)
    token = None
    user_id = None

    def on_start(self):
        self.user_id = str(uuid.uuid4())[:8]
        # Register then login on start
        self.client.post("/auth/register", json={
            "email": f"user_{self.user_id}@test.com",
            "password": "TestPassword123!"
        })
        response = self.client.post("/auth/login", json={
            "email": f"user_{self.user_id}@test.com",
            "password": "TestPassword123!"
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")

    @task(3)
    def get_me(self):
        if self.token:
            self.client.get(
                "/users/me",
                headers={"Authorization": f"Bearer {self.token}"}
            )

    @task(1)
    def refresh_token(self):
        if self.token:
            self.client.post(
                "/auth/refresh",
                headers={"Authorization": f"Bearer {self.token}"}
            )
