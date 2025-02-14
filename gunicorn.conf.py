# Gunicorn 설정
timeout = 300  # 5분
workers = 4
worker_class = 'gthread'
threads = 4 