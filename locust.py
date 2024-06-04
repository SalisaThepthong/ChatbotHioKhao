from locust import HttpUser, task, between

class FoodRecommenderUser(HttpUser):
    wait_time = between(1, 5)  # Simulate user think time between requests

    @task
    def recommend_food(self):
        # Replace with the actual endpoint URL for getting recommendations
        response = self.client.post("/recommendation", data={"Customer_id": "test_user_1"})
        response.raise_for_status()

    @task
    def add_user(self):
        # Replace with the actual endpoint URL for adding users
        # Adjust data based on your user information schema
        response = self.client.post("/users", data={
            "Customer_id": "test_user_2",
            "Customer_name": "John Doe",
            "type": "new",
            "Choose": "Thai food"
        })
        response.raise_for_status()

    @task
    def add_health_data(self):
        # Replace with the actual endpoint URL for adding health data
        # Adjust data based on your health data schema
        response = self.client.post("/health", data={
            "Customer_id": "test_user_3",
            "health": "diabetes"
        })
        response.raise_for_status()

    @task
    def add_comment(self):
        # Replace with the actual endpoint URL for adding comments
        # Adjust data based on your comment schema
        response = self.client.post("/comment", data={
            "Customer_id": "test_user_4",
            "comment": "This is a great recommendation system!"
        })
        response.raise_for_status()

if __name__ == "__main__":
    # Adjust these settings based on your desired test load
    from locust import HttpUser, task, between

    class WebsiteUser(HttpUser):
        wait_time = between(1, 2)  # Simulate user think time between requests
        users = 10  # Number of simulated users
        spawn_rate = 1  # Number of users spawned per second

    from locust import web

    @web.app
    class MyCustomWeb(web.LocustWeb):
        pass

    if __name__ == "__main__":
        import os
        os.environ['LOCUST_WEB_PORT'] = '8089'  # Change port if needed
        web. locust_wsgi_app = MyCustomWeb().wsgi_app
        web.func = WebsiteUser
        web.main()
