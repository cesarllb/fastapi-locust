from locust import HttpUser, task, constant, run_single_user
from faker import Faker

fake = Faker()


class CreateUser(HttpUser):
    host = "http://127.0.0.1:8000"
    wait_time = constant(1)

    @task
    def create_new_user(self):
        fake_username = fake.user_name()
        fake_email = fake.email()
        diasbled = fake.boolean()
        fake_password = fake.password()
        endpoint = "/register"
        json_payload = {
            "username": fake_username,
            "email": fake_email,
            "disabled": diasbled,
            "password": fake_password
        }
        with self.client.post(endpoint, catch_response=True, json=json_payload, name="REGISTER") as response:
            json_resp = response.json()
            if response.status_code == 200:
                # response is success
                
                print(json_resp)
            else:
                print("Unsuccesfull Request")
                json_resp = response.json()
                print(json_resp)

if __name__ == "__main__":
    run_single_user(CreateUser)