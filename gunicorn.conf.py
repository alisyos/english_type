# Gunicorn 설정
timeout = 600  # 10분으로 증가
workers = 1    # 단일 워커로 변경
worker_class = 'sync'  # 동기 워커 사용
threads = 2    # 스레드 수 감소
max_requests = 500
max_requests_jitter = 50
worker_tmp_dir = '/tmp'  # 임시 디렉토리 명시
preload_app = True      # 앱 미리 로드 