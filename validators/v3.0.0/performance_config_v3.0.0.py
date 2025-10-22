#!/usr/bin/env python3
"""
Performance Configuration for SDUI Web Validator v3.0.0
Конфигурация производительности с оптимизациями
"""

from dataclasses import dataclass
from typing import Optional
from functools import lru_cache
import os

@dataclass
class PerformanceConfig:
    """Конфигурация производительности валидатора"""

    # Cache settings
    schema_cache_enabled: bool = True
    schema_cache_max_size: int = 256
    position_map_cache_enabled: bool = True
    position_map_cache_max_size: int = 128

    # File processing
    lazy_loading_enabled: bool = True
    stream_large_files: bool = True
    large_file_threshold_kb: int = 500

    # Parallel processing
    parallel_validation_enabled: bool = True
    max_workers: Optional[int] = None  # None = CPU count
    batch_size: int = 10

    # Memory management
    memory_pooling_enabled: bool = True
    max_memory_mb: int = 512
    gc_threshold: int = 100  # файлов до сборки мусора

    # Performance targets (ms)
    target_small_file: int = 100      # <100KB
    target_medium_file: int = 500     # 100KB-1MB
    target_large_file: int = 2000     # >1MB
    target_batch_100: int = 10000     # 100 files

    # Optimization flags
    use_compiled_regex: bool = True
    use_line_index: bool = True
    skip_validation_on_cache_hit: bool = False

    @classmethod
    def from_env(cls) -> 'PerformanceConfig':
        """Создает конфигурацию из переменных окружения"""
        return cls(
            schema_cache_enabled=os.getenv('VALIDATOR_SCHEMA_CACHE', 'true').lower() == 'true',
            parallel_validation_enabled=os.getenv('VALIDATOR_PARALLEL', 'true').lower() == 'true',
            max_workers=int(os.getenv('VALIDATOR_MAX_WORKERS', '0')) or None,
            lazy_loading_enabled=os.getenv('VALIDATOR_LAZY_LOADING', 'true').lower() == 'true',
        )

    @classmethod
    def production(cls) -> 'PerformanceConfig':
        """Конфигурация для production среды"""
        return cls(
            schema_cache_max_size=512,
            position_map_cache_max_size=256,
            parallel_validation_enabled=True,
            memory_pooling_enabled=True,
        )

    @classmethod
    def development(cls) -> 'PerformanceConfig':
        """Конфигурация для development среды"""
        return cls(
            schema_cache_max_size=128,
            position_map_cache_max_size=64,
            parallel_validation_enabled=False,
            skip_validation_on_cache_hit=False,
        )

    @classmethod
    def minimal(cls) -> 'PerformanceConfig':
        """Минимальная конфигурация (без оптимизаций)"""
        return cls(
            schema_cache_enabled=False,
            position_map_cache_enabled=False,
            lazy_loading_enabled=False,
            parallel_validation_enabled=False,
            memory_pooling_enabled=False,
        )

    def validate_targets(self, actual: dict) -> dict:
        """Проверяет соответствие фактических метрик целевым"""
        results = {}

        targets = {
            'small': self.target_small_file,
            'medium': self.target_medium_file,
            'large': self.target_large_file,
        }

        for category, target_ms in targets.items():
            if category in actual:
                actual_ms = actual[category]['median']
                passed = actual_ms <= target_ms
                results[category] = {
                    'target': target_ms,
                    'actual': actual_ms,
                    'passed': passed,
                    'margin': ((target_ms - actual_ms) / target_ms) * 100 if passed else None
                }

        return results


# Singleton instance
_config: Optional[PerformanceConfig] = None

def get_config() -> PerformanceConfig:
    """Получает глобальную конфигурацию"""
    global _config
    if _config is None:
        _config = PerformanceConfig.from_env()
    return _config

def set_config(config: PerformanceConfig):
    """Устанавливает глобальную конфигурацию"""
    global _config
    _config = config

def reset_config():
    """Сбрасывает конфигурацию на дефолтную"""
    global _config
    _config = None


# Performance monitoring decorators
import time
from functools import wraps
from typing import Callable, Any

def profile_performance(threshold_ms: int = 100):
    """
    Декоратор для профилирования производительности функций

    Args:
        threshold_ms: Порог в миллисекундах для вывода предупреждения
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start = time.perf_counter()
            result = func(*args, **kwargs)
            end = time.perf_counter()

            duration_ms = (end - start) * 1000

            if duration_ms > threshold_ms:
                print(f"⚠️ Performance warning: {func.__name__} took {duration_ms:.2f}ms (threshold: {threshold_ms}ms)")

            return result
        return wrapper
    return decorator


def memoize_with_ttl(maxsize: int = 128, ttl_seconds: int = 3600):
    """
    Декоратор для мемоизации с TTL (Time To Live)

    Args:
        maxsize: Максимальный размер кэша
        ttl_seconds: Время жизни записи в кэше
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        cache_times = {}

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Создаем ключ кэша
            key = (args, tuple(sorted(kwargs.items())))

            # Проверяем TTL
            if key in cache:
                age = time.time() - cache_times[key]
                if age < ttl_seconds:
                    return cache[key]
                else:
                    # Запись устарела, удаляем
                    del cache[key]
                    del cache_times[key]

            # Вычисляем результат
            result = func(*args, **kwargs)

            # Сохраняем в кэш (с учетом maxsize)
            if len(cache) >= maxsize:
                # Удаляем самую старую запись
                oldest_key = min(cache_times, key=cache_times.get)
                del cache[oldest_key]
                del cache_times[oldest_key]

            cache[key] = result
            cache_times[key] = time.time()

            return result

        # Добавляем метод для очистки кэша
        wrapper.cache_clear = lambda: (cache.clear(), cache_times.clear())
        wrapper.cache_info = lambda: {
            'size': len(cache),
            'maxsize': maxsize,
            'ttl': ttl_seconds
        }

        return wrapper
    return decorator


# Memory management utilities
import gc
import sys

class MemoryPool:
    """Пул памяти для больших объектов"""

    def __init__(self, max_size_mb: int = 512):
        self.max_size_mb = max_size_mb
        self.current_size = 0
        self.objects = []

    def allocate(self, obj: Any) -> bool:
        """Выделяет память для объекта"""
        obj_size = sys.getsizeof(obj) / 1024 / 1024  # MB

        if self.current_size + obj_size > self.max_size_mb:
            self.gc_collect()

        if self.current_size + obj_size <= self.max_size_mb:
            self.objects.append(obj)
            self.current_size += obj_size
            return True

        return False

    def gc_collect(self):
        """Принудительная сборка мусора"""
        self.objects.clear()
        gc.collect()
        self.current_size = 0

    def get_stats(self) -> dict:
        """Статистика использования памяти"""
        return {
            'current_mb': self.current_size,
            'max_mb': self.max_size_mb,
            'utilization': (self.current_size / self.max_size_mb) * 100,
            'objects_count': len(self.objects)
        }


# Example usage
if __name__ == '__main__':
    # Production config
    prod_config = PerformanceConfig.production()
    print("Production Config:")
    print(f"  Schema Cache: {prod_config.schema_cache_max_size}")
    print(f"  Parallel: {prod_config.parallel_validation_enabled}")
    print(f"  Memory Pool: {prod_config.memory_pooling_enabled}")

    # Validate against targets
    actual_stats = {
        'small': {'median': 0.52},
        'medium': {'median': 3.32},
    }

    validation = prod_config.validate_targets(actual_stats)
    print("\nTarget Validation:")
    for category, result in validation.items():
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"  {category}: {status} ({result['actual']:.2f}ms / {result['target']}ms)")
        if result['margin']:
            print(f"    Margin: {result['margin']:.1f}% under target")
