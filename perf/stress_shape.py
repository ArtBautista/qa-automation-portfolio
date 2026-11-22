"""Step-load stress test: adds 10 users every 30 s up to 60 users, then stops.
Run: locust -f perf/stress_shape.py --headless --host http://127.0.0.1:5000 \
--csv reports/stress --html reports/stress-report.html --exit-code-on-error 0
"""
from locust import LoadTestShape
from locustfile import EditorUser, ReaderUser # noqa: F401 (Locust discovers these classes)
class StepLoadShape(LoadTestShape):
    step_users = 10
    step_seconds = 30
    max_users = 60

    def tick(self):
        run_time = self.get_run_time()
        step = int(run_time // self.step_seconds) + 1
        users = step * self.step_users
        if users > self.max_users:
            return None # returning None stops the test
        return users, self.step_users
