# Gunicorn 설정
timeout = 300  # 5분
workers = 2    # 워커 수 줄임
worker_class = 'sync'  # 동기 워커 사용
threads = 4
max_requests = 1000
max_requests_jitter = 50 