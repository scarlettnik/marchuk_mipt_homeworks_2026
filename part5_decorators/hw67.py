import json
from datetime import UTC, datetime
from functools import wraps
from typing import Any, ParamSpec, Protocol, TypeVar
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."
DEFAULT_CRITICAL_COUNT = 5
DEFAULT_RECOVERY_TIME = 30


P = ParamSpec("P")
R_co = TypeVar("R_co", covariant=True)


class CallableWithMeta(Protocol[P, R_co]):
    __name__: str
    __module__: str

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...


class BreakerError(Exception):
    def __init__(self, func_name: str, block_time: datetime) -> None:
        super().__init__(TOO_MUCH)
        self.func_name = func_name
        self.block_time = block_time


class CircuitBreaker:
    def __init__(
        self,
        critical_count: int = DEFAULT_CRITICAL_COUNT,
        time_to_recover: int = DEFAULT_RECOVERY_TIME,
        triggers_on: type[Exception] = Exception,
    ) -> None:
        errors = []
        if not critical_count > 0:
            errors.append(ValueError(INVALID_CRITICAL_COUNT))
        if not time_to_recover > 0:
            errors.append(ValueError(INVALID_RECOVERY_TIME))
        if errors:
            raise ExceptionGroup(VALIDATIONS_FAILED, errors)

        self.critical_count = critical_count
        self.time_to_recover = time_to_recover
        self.triggers_on = triggers_on
        self._failed_count = 0
        self._block_time: datetime | None = None

    def __call__(self, func: CallableWithMeta[P, R_co]) -> CallableWithMeta[P, R_co]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R_co:
            func_name = f"{func.__module__}.{func.__name__}"
            self._check_block(func_name)
            try:
                result = func(*args, **kwargs)
            except self.triggers_on as error:
                self._register_error(func_name, error)
                raise
            self._reset_state()
            return result

        return wrapper

    def _check_block(self, func_name: str) -> None:
        if self._block_time is None:
            return
        delta = datetime.now(UTC) - self._block_time
        if delta.total_seconds() >= self.time_to_recover:
            self._reset_state()
            return
        raise BreakerError(func_name, self._block_time)

    def _register_error(self, func_name: str, error: Exception) -> None:
        self._failed_count += 1
        if self._failed_count < self.critical_count:
            return

        self._block_time = datetime.now(UTC)
        raise BreakerError(func_name, self._block_time) from error

    def _reset_state(self) -> None:
        self._failed_count = 0
        self._block_time = None


circuit_breaker = CircuitBreaker(5, 30, Exception)


# @circuit_breaker
def get_comments(post_id: int) -> Any:
    """
    Получает комментарии к посту

    Args:
        post_id (int): Идентификатор поста

    Returns:
        list[dict[int | str]]: Список комментариев
    """
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())


if __name__ == "__main__":
    comments = get_comments(1)
