#!/usr/bin/env python3
"""
Simplified Performance Analyzer for SDUI Resolver
Анализирует производительность без внешних зависимостей
"""

import time
import json
import cProfile
import pstats
import io
import tracemalloc
import sys
import gc
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from contextlib import contextmanager

# Добавляем путь к анализируемому скрипту
sys.path.insert(0, str(Path(__file__).parent))

try:
    from sdui_resolver_final import SDUIFinalResolver, ResolveContext, ComponentTracker
except ImportError as e:
    print(f"❌ Cannot import sdui-resolver-final.py: {e}")
    print("Make sure the file exists and has correct Python syntax")
    sys.exit(1)

@dataclass
class SimpleMetrics:
    """Упрощенные метрики производительности"""
    execution_time: float = 0.0
    memory_peak: int = 0
    memory_current: int = 0
    operations_count: int = 0

class SimpleProfiler:
    """Упрощенный профилировщик"""

    def __init__(self):
        self.metrics = SimpleMetrics()
        self.start_time = 0
        self.operation_times = {}
        self.call_counts = {}

    @contextmanager
    def measure_operation(self, operation_name: str):
        """Контекстный менеджер для измерения операций"""
        start_time = time.perf_counter()

        try:
            yield
        finally:
            duration = time.perf_counter() - start_time

            if operation_name not in self.operation_times:
                self.operation_times[operation_name] = []
                self.call_counts[operation_name] = 0

            self.operation_times[operation_name].append(duration)
            self.call_counts[operation_name] += 1

    def start_profiling(self):
        """Начать профилирование"""
        tracemalloc.start()
        self.start_time = time.perf_counter()
        gc.collect()  # Принудительная сборка мусора для чистого старта

    def stop_profiling(self):
        """Завершить профилирование"""
        self.metrics.execution_time = time.perf_counter() - self.start_time

        # Пиковое использование памяти
        try:
            current, peak = tracemalloc.get_traced_memory()
            self.metrics.memory_peak = peak
            self.metrics.memory_current = current
            tracemalloc.stop()
        except:
            pass

class SDUIPerformanceAnalyzer:
    """Анализатор производительности SDUI Resolver"""

    def __init__(self, script_path: str):
        self.script_path = Path(script_path)
        self.base_path = self.script_path.parent

    def create_test_schema(self, complexity: str = "simple", size: int = 10) -> Dict:
        """Создать тестовую схему"""
        if complexity == "simple":
            return {
                "name": "SimpleTestSchema",
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "value": {"type": "number"}
                }
            }

        elif complexity == "medium":
            schema = {
                "name": "MediumTestSchema",
                "type": "object",
                "definitions": {}
            }

            # Создаем цепочку ссылок
            for i in range(size):
                schema["definitions"][f"Component{i}"] = {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "data": {"type": "object"},
                        "next": {"$ref": f"#/definitions/Component{(i + 1) % size}"}
                    }
                }

            schema["properties"] = {
                "root": {"$ref": "#/definitions/Component0"}
            }

            return schema

        else:  # complex
            schema = {
                "name": "ComplexTestSchema",
                "type": "object",
                "definitions": {}
            }

            # Создаем сложную структуру с множественными ссылками
            for i in range(size):
                references = []
                for j in range(min(3, size)):
                    ref_target = (i + j + 1) % size
                    references.append({"$ref": f"#/definitions/Component{ref_target}"})

                schema["definitions"][f"Component{i}"] = {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "children": {
                            "type": "array",
                            "items": {"oneOf": references}
                        },
                        "parent": {
                            "$ref": f"#/definitions/Component{(i - 1) % size}"
                        }
                    }
                }

            return schema

    def benchmark_resolution(self, schema: Dict, max_depth: int = 20) -> Tuple[Dict, SimpleMetrics]:
        """Бенчмарк разрешения схемы"""

        # Создаем временный файл
        test_file = self.base_path / "temp_test_schema.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(schema, f)

        profiler = SimpleProfiler()
        profiler.start_profiling()

        try:
            resolver = SDUIFinalResolver(str(self.base_path))
            result = resolver.resolve_file(str(test_file), max_depth=max_depth)
        except Exception as e:
            result = {"error": str(e), "traceback": str(e)}
        finally:
            profiler.stop_profiling()
            test_file.unlink()

        return result, profiler.metrics

    def test_scalability(self) -> Dict:
        """Тест масштабируемости"""
        print("📈 Testing scalability...")

        results = {}
        component_counts = [5, 10, 20, 50, 100]

        for count in component_counts:
            print(f"  Testing {count} components...")

            schema = self.create_test_schema("medium", count)
            result, metrics = self.benchmark_resolution(schema)

            results[f"components_{count}"] = {
                "execution_time": metrics.execution_time,
                "memory_peak_mb": metrics.memory_peak / 1024 / 1024 if metrics.memory_peak else 0,
                "success": isinstance(result, dict) and "_metadata" in result,
                "total_resolutions": result.get("_metadata", {}).get("total_resolutions", 0) if isinstance(result, dict) else 0,
                "total_stubs": result.get("_metadata", {}).get("total_stubs", 0) if isinstance(result, dict) else 0
            }

        return results

    def test_depth_performance(self) -> Dict:
        """Тест производительности по глубине"""
        print("🔍 Testing depth performance...")

        results = {}
        depths = [5, 10, 20, 30, 50]

        # Используем схему средней сложности
        schema = self.create_test_schema("complex", 20)

        for depth in depths:
            print(f"  Testing max_depth={depth}...")

            result, metrics = self.benchmark_resolution(schema, depth)

            results[f"depth_{depth}"] = {
                "execution_time": metrics.execution_time,
                "memory_peak_mb": metrics.memory_peak / 1024 / 1024 if metrics.memory_peak else 0,
                "success": isinstance(result, dict) and "_metadata" in result,
                "total_resolutions": result.get("_metadata", {}).get("total_resolutions", 0) if isinstance(result, dict) else 0,
                "total_stubs": result.get("_metadata", {}).get("total_stubs", 0) if isinstance(result, dict) else 0
            }

        return results

    def test_complexity_types(self) -> Dict:
        """Тест различных типов сложности"""
        print("🧮 Testing complexity types...")

        results = {}
        complexities = ["simple", "medium", "complex"]

        for complexity in complexities:
            print(f"  Testing {complexity} schema...")

            schema = self.create_test_schema(complexity, 20)
            result, metrics = self.benchmark_resolution(schema)

            results[complexity] = {
                "execution_time": metrics.execution_time,
                "memory_peak_mb": metrics.memory_peak / 1024 / 1024 if metrics.memory_peak else 0,
                "success": isinstance(result, dict) and "_metadata" in result,
                "schema_size_kb": len(json.dumps(schema)) / 1024,
                "total_resolutions": result.get("_metadata", {}).get("total_resolutions", 0) if isinstance(result, dict) else 0
            }

        return results

    def profile_with_cprofile(self) -> str:
        """Детальное профилирование"""
        print("🔬 Running cProfile analysis...")

        schema = self.create_test_schema("medium", 15)
        test_file = self.base_path / "temp_profile_schema.json"

        with open(test_file, 'w') as f:
            json.dump(schema, f)

        try:
            pr = cProfile.Profile()
            resolver = SDUIFinalResolver(str(self.base_path))

            pr.enable()
            result = resolver.resolve_file(str(test_file), max_depth=20)
            pr.disable()

            # Создаем отчет
            s = io.StringIO()
            ps = pstats.Stats(pr, stream=s)
            ps.sort_stats('cumulative')
            ps.print_stats(15)  # Топ 15 функций

            return s.getvalue()

        finally:
            test_file.unlink()

    def analyze_algorithmic_complexity(self, scalability_results: Dict) -> Dict:
        """Анализ алгоритмической сложности"""

        complexity_analysis = {}

        # Извлекаем данные
        components = []
        times = []

        for key, data in scalability_results.items():
            if key.startswith("components_"):
                count = int(key.split("_")[1])
                components.append(count)
                times.append(data["execution_time"])

        if len(components) < 2:
            return {"error": "Insufficient data for complexity analysis"}

        # Сортируем по количеству компонентов
        paired = list(zip(components, times))
        paired.sort()
        components, times = zip(*paired)

        # Вычисляем отношения роста
        growth_ratios = []
        for i in range(1, len(times)):
            if times[i-1] > 0:
                ratio = times[i] / times[i-1]
                component_ratio = components[i] / components[i-1]
                growth_ratios.append(ratio / component_ratio)

        avg_growth = sum(growth_ratios) / len(growth_ratios) if growth_ratios else 1.0

        # Классификация сложности
        if avg_growth < 1.2:
            complexity_class = "O(n) - Linear"
        elif avg_growth < 2.0:
            complexity_class = "O(n log n) - Linearithmic"
        elif avg_growth < 3.0:
            complexity_class = "O(n²) - Quadratic"
        else:
            complexity_class = "O(n³+) - Polynomial or worse"

        complexity_analysis = {
            "estimated_complexity": complexity_class,
            "average_growth_factor": avg_growth,
            "growth_ratios": growth_ratios,
            "data_points": list(zip(components, times))
        }

        return complexity_analysis

    def identify_bottlenecks(self, all_results: Dict) -> List[Dict]:
        """Идентификация узких мест"""

        bottlenecks = []

        # Анализ времени выполнения
        scalability = all_results.get("scalability", {})
        if scalability:
            max_time = max(data["execution_time"] for data in scalability.values())
            if max_time > 1.0:  # Более 1 секунды
                bottlenecks.append({
                    "type": "execution_time",
                    "severity": "high" if max_time > 5.0 else "medium",
                    "description": f"Maximum execution time: {max_time:.2f}s",
                    "recommendation": "Consider caching, memoization, or algorithm optimization"
                })

        # Анализ использования памяти
        max_memory = 0
        for result_set in all_results.values():
            if isinstance(result_set, dict):
                for data in result_set.values():
                    if isinstance(data, dict) and "memory_peak_mb" in data:
                        max_memory = max(max_memory, data["memory_peak_mb"])

        if max_memory > 100:  # Более 100MB
            bottlenecks.append({
                "type": "memory_usage",
                "severity": "high" if max_memory > 500 else "medium",
                "description": f"Peak memory usage: {max_memory:.1f}MB",
                "recommendation": "Implement memory pooling or reduce deep copying"
            })

        # Анализ соотношения stub'ов
        depth_results = all_results.get("depth_performance", {})
        if depth_results:
            for depth_key, data in depth_results.items():
                if data.get("total_resolutions", 0) > 0:
                    stub_ratio = data.get("total_stubs", 0) / data["total_resolutions"]
                    if stub_ratio > 0.5:  # Более 50% заглушек
                        bottlenecks.append({
                            "type": "high_stub_ratio",
                            "severity": "medium",
                            "description": f"High stub ratio ({stub_ratio:.1%}) at {depth_key}",
                            "recommendation": "Increase max_depth or optimize component tracking"
                        })

        return bottlenecks

    def run_comprehensive_analysis(self) -> Dict:
        """Комплексный анализ производительности"""
        print("🚀 Starting comprehensive performance analysis...")

        results = {
            "scalability": self.test_scalability(),
            "depth_performance": self.test_depth_performance(),
            "complexity_types": self.test_complexity_types(),
            "detailed_profile": self.profile_with_cprofile()
        }

        # Анализ алгоритмической сложности
        results["algorithmic_complexity"] = self.analyze_algorithmic_complexity(results["scalability"])

        # Идентификация узких мест
        results["bottlenecks"] = self.identify_bottlenecks(results)

        return results

def generate_performance_report(analysis_results: Dict) -> str:
    """Генерация отчета о производительности"""

    report = []
    report.append("=" * 80)
    report.append("📊 SDUI RESOLVER PERFORMANCE ANALYSIS REPORT")
    report.append("=" * 80)
    report.append("")

    # 1. Обзор производительности
    report.append("🔍 1. PERFORMANCE OVERVIEW")
    report.append("-" * 40)

    complexity_types = analysis_results.get("complexity_types", {})
    if complexity_types:
        for complexity, data in complexity_types.items():
            report.append(f"{complexity.upper():8}: {data['execution_time']:.3f}s | {data['memory_peak_mb']:.1f}MB | {data['total_resolutions']} resolutions")

    report.append("")

    # 2. Масштабируемость
    report.append("📈 2. SCALABILITY ANALYSIS")
    report.append("-" * 40)

    scalability = analysis_results.get("scalability", {})
    if scalability:
        report.append("Components | Time (s) | Memory (MB) | Resolutions | Growth")
        report.append("-" * 55)

        prev_time = None
        for key in sorted(scalability.keys(), key=lambda x: int(x.split("_")[1])):
            data = scalability[key]
            components = key.split("_")[1]
            time_val = data["execution_time"]
            memory_val = data["memory_peak_mb"]
            resolutions = data["total_resolutions"]

            growth = ""
            if prev_time and prev_time > 0:
                ratio = time_val / prev_time
                growth = f"x{ratio:.1f}"

            report.append(f"{components:>9} | {time_val:>7.3f} | {memory_val:>10.1f} | {resolutions:>11} | {growth}")
            prev_time = time_val

    report.append("")

    # 3. Алгоритмическая сложность
    report.append("🧮 3. ALGORITHMIC COMPLEXITY")
    report.append("-" * 40)

    complexity = analysis_results.get("algorithmic_complexity", {})
    if complexity and "estimated_complexity" in complexity:
        report.append(f"Estimated complexity: {complexity['estimated_complexity']}")
        report.append(f"Average growth factor: {complexity['average_growth_factor']:.2f}")

        if complexity["average_growth_factor"] > 2.0:
            report.append("⚠️  WARNING: Algorithm shows poor scalability")
        elif complexity["average_growth_factor"] > 1.5:
            report.append("⚠️  CAUTION: Algorithm may not scale well for large inputs")
        else:
            report.append("✅ Algorithm shows good scalability characteristics")

    report.append("")

    # 4. Производительность по глубине
    report.append("🔍 4. DEPTH PERFORMANCE")
    report.append("-" * 40)

    depth_perf = analysis_results.get("depth_performance", {})
    if depth_perf:
        report.append("Max Depth | Time (s) | Memory (MB) | Stubs/Total")
        report.append("-" * 45)

        for key in sorted(depth_perf.keys(), key=lambda x: int(x.split("_")[1])):
            data = depth_perf[key]
            depth = key.split("_")[1]
            time_val = data["execution_time"]
            memory_val = data["memory_peak_mb"]

            stubs = data.get("total_stubs", 0)
            total = data.get("total_resolutions", 1)
            stub_ratio = stubs / total if total > 0 else 0

            report.append(f"{depth:>9} | {time_val:>7.3f} | {memory_val:>10.1f} | {stub_ratio:>10.1%}")

    report.append("")

    # 5. Узкие места
    report.append("🎯 5. PERFORMANCE BOTTLENECKS")
    report.append("-" * 40)

    bottlenecks = analysis_results.get("bottlenecks", [])
    if bottlenecks:
        for bottleneck in bottlenecks:
            severity_icon = "🔴" if bottleneck["severity"] == "high" else "🟡"
            report.append(f"{severity_icon} {bottleneck['type'].upper()}: {bottleneck['description']}")
            report.append(f"   💡 {bottleneck['recommendation']}")
    else:
        report.append("✅ No significant bottlenecks detected")

    report.append("")

    # 6. Рекомендации
    report.append("💡 6. OPTIMIZATION RECOMMENDATIONS")
    report.append("-" * 40)

    recommendations = []

    # Анализируем результаты
    if complexity and complexity.get("average_growth_factor", 1) > 2.0:
        recommendations.append("🔧 ALGORITHM: Implement caching for resolved components to reduce redundant computations")

    if any(data.get("memory_peak_mb", 0) > 100 for result_set in analysis_results.values()
           if isinstance(result_set, dict) for data in result_set.values() if isinstance(data, dict)):
        recommendations.append("🔧 MEMORY: Replace deepcopy with shallow copying where possible")

    # Общие рекомендации
    recommendations.extend([
        "🔧 CACHING: Implement file-level caching to avoid repeated JSON parsing",
        "🔧 LAZY LOADING: Load external schemas only when needed",
        "🔧 COMPONENT TRACKING: Optimize component deduplication algorithm",
        "🔧 MEMORY POOLING: Reuse objects instead of creating new ones",
        "🔧 PARALLEL PROCESSING: Process independent branches concurrently"
    ])

    for rec in recommendations:
        report.append(rec)

    report.append("")
    report.append("=" * 80)

    return "\n".join(report)

def main():
    """Главная функция"""
    import argparse

    parser = argparse.ArgumentParser(description="SDUI Resolver Performance Analyzer")
    parser.add_argument("--script", default="/Users/username/Scripts/Python/sdui-resolver-final.py",
                       help="Path to sdui-resolver-final.py")
    parser.add_argument("--output", help="Output file for the report")
    parser.add_argument("--verbose", action="store_true", help="Show detailed cProfile output")

    args = parser.parse_args()

    # Проверяем существование скрипта
    script_path = Path(args.script)
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return

    # Создаем анализатор
    analyzer = SDUIPerformanceAnalyzer(str(script_path))

    # Запускаем анализ
    print("🚀 Starting SDUI Resolver Performance Analysis...")
    analysis_results = analyzer.run_comprehensive_analysis()

    # Генерируем отчет
    report = generate_performance_report(analysis_results)

    # Выводим отчет
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"📄 Report saved to: {args.output}")
    else:
        print(report)

    # Детальный профиль если нужен
    if args.verbose:
        print("\n" + "=" * 80)
        print("🔬 DETAILED CPROFILE ANALYSIS")
        print("=" * 80)
        print(analysis_results.get("detailed_profile", "No detailed profile available"))

if __name__ == "__main__":
    main()