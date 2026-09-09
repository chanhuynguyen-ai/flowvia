# Worker

Process Python/Celery dự kiến dùng chung modules với FastAPI. PostgreSQL giữ trạng thái run/step/attempt; Redis chỉ làm queue. Claim có lease/fence; schema validate; execute handler; persist state và outbox. Human approval ghi wait rồi nhả worker. Retry giới hạn và chống side effect trùng. Chưa có Celery app trong bộ sườn.
