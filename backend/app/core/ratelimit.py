"""进程内登录限流。

定位: 个人博客单实例部署, 不值得为此引入 Redis/slowapi。这里用一个滑动窗口计数器
即可拦住脚本化的暴力破解与撞库。

局限(要知道):
    - 状态在进程内存里: 多 worker / 多实例部署时各自计数, 且重启即清空。
      真需要跨实例限流时, 换 Redis 或交给反代的 limit_req。
    - 内存占用与"不同 key 的数量"成正比, 所以 key 集合会随清理淘汰而收敛。
"""

import threading
import time
from collections import defaultdict

from fastapi import HTTPException, status


class LoginRateLimiter:
    """按 key(通常是 "IP:账号") 统计失败次数的滑动窗口限流器。"""

    def __init__(self, max_attempts: int = 10, window_seconds: int = 300) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)
        # 同一进程内 FastAPI 的同步端点跑在线程池里, 需要自己加锁
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> list[float]:
        """丢掉窗口外的记录, 返回窗口内的剩余记录。"""
        kept = [t for t in self._hits[key] if now - t < self.window_seconds]
        if kept:
            self._hits[key] = kept
        else:
            # 不保留空列表, 避免 key 无限增长
            self._hits.pop(key, None)
        return kept

    def check(self, key: str) -> None:
        """超出阈值时抛 429。应在校验密码之前调用。"""
        now = time.monotonic()
        with self._lock:
            kept = self._prune(key, now)
            if len(kept) >= self.max_attempts:
                retry_after = int(self.window_seconds - (now - kept[0])) + 1
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"登录尝试过于频繁, 请 {retry_after} 秒后重试",
                    headers={"Retry-After": str(retry_after)},
                )
            self._hits[key].append(now)

    def reset(self, key: str) -> None:
        """登录成功后清空该 key 的失败记录。"""
        with self._lock:
            self._hits.pop(key, None)


# 5 分钟内 10 次失败即锁定该 "IP+账号" 组合
login_limiter = LoginRateLimiter(max_attempts=10, window_seconds=300)
