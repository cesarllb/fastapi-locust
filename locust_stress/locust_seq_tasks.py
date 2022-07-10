from typing import Optional
from urllib import response
from locust import HttpUser, SequentialTaskSet, task, constant, events
from faker import Faker
from pydantic import BaseModel
from datetime import datetime
from requests.exceptions import JSONDecodeError
import csv


class UserRegisterModel(BaseModel):
    # User model
    username: str
    email: str
    disabled: bool = False
    password: str


class RegisterXlsxSchema(UserRegisterModel):
    start_time: datetime = datetime.now()
    response_status_code: int
    api_endpoint: str
    json_payload: dict
    response_payload_json: Optional[dict] = None
    response_headers: Optional[dict] = None
    elapsed_times_seconds: Optional[float] = None

fieldnames = list(RegisterXlsxSchema.schema()["properties"].keys())

fake: Faker = Faker()
output_json = []


@events.test_stop.add_listener
def on_test_stop(**kw):
    # Generate CSV report
    
    with open('test4.csv', 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames = fieldnames)
        writer.writeheader()
        writer.writerows(output_json)


class RegisterLoginTaskSet(SequentialTaskSet):
    """
    1)creates new user
    2)send post request to login endpoint, get JWT Token
    3)Check /user/me Endpoint
    """
    JWT_TOKEN: str = None

    @task
    def register_user(self):
        # Create New user
        start_time = datetime.now()
        api_endpoint: str = "/register"
        fake_username: str = fake.user_name()
        fake_email: str = fake.email()
        disabled: str = fake.boolean()
        fake_password = fake.password()
        user = UserRegisterModel(
            username=fake_username,
            email=fake_email,
            disabled=disabled,
            password=fake_password
        )
        json_payload = user.dict()
        with self.client.post(api_endpoint, catch_response=True, json=json_payload, name="Register") as response:
            response_status_code = response.status_code
            try:
                respnose_payload = response.json()
            except JSONDecodeError:
                respnose_payload = {}
            response_headers = response.headers
            elapsed_time = response.elapsed.total_seconds()
            xlsx_data = RegisterXlsxSchema(
                username=fake_username,
                email=fake_email,
                disabled=disabled,
                password=fake_password,
                start_time=start_time,
                response_status_code=response_status_code,
                api_endpoint=api_endpoint,
                json_payload=json_payload,
                response_payload_json=respnose_payload,
                response_headers=response_headers,
                elapsed_times_seconds=elapsed_time
            )
            output_json.append(xlsx_data.dict())


class RegisterUser(HttpUser):
    host = "http://127.0.0.1:8000"
    tasks = [RegisterLoginTaskSet]
    wait_time = constant(2)
