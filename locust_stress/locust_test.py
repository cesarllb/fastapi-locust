from locust import TaskSet, HttpLocust, task

class BlazeDemoTaskSet(TaskSet):

        def setup(self):
            print("hello from taskset setup")

        def teardown(self):
            print("hello from taskset teardown")

        def on_start(self):
            print("hello from taskset on_start")

        def on_stop(self):
            print("hello from taskset on_stop")

        @task
        def reserve_task(self):
            post_response = self.client.post(
                url="/reserve.php",
                params={"toPort": "Buenos Aries", "fromPort": "Paris"})

class BlazeDemoUser(HttpLocust):
        task_set = BlazeDemoTaskSet
        min_wait = 500
        max_wait = 1500
        host = "http://www.blazedemo.com"

        def setup(self):
            print("hello from httplocust setup")

        def teardown(self):
            print("hello from httplocust teardown")
