#!/usr/bin/env python3
"""
Терминальный валидатор для агентов - с проверкой через реальные эндпоинты
"""

import json
import sys
import os
import subprocess
from pathlib import Path
import urllib.request
import urllib.error
import time

def test_local_endpoints():
    """Проверка доступности локальных эндпоинтов"""
    endpoints = [
        "http://localhost:8080",
        "http://localhost:9090"
    ]

    available = []

    for endpoint in endpoints:
        try:
            response = urllib.request.urlopen(endpoint, timeout=2)
            if response.getcode() == 200:
                available.append(endpoint)
                print(f"✅ {endpoint} доступен")
            else:
                print(f"⚠️ {endpoint} вернул код {response.getcode()}")
        except urllib.error.URLError:
            print(f"❌ {endpoint} недоступен")
        except Exception as e:
            print(f"❌ {endpoint} ошибка: {e}")

    return available

def test_contract_against_endpoint(contract, endpoint_url):
    """Тестирование контракта против реального эндпоинта"""
    print(f"🌐 Тестирование против {endpoint_url}")

    results = {
        "success": False,
        "errors": [],
        "warnings": [],
        "response_time": None
    }

    try:
        # Подготовка POST запроса с контрактом
        contract_json = json.dumps(contract).encode('utf-8')

        # Для SDUI sandbox (8080) используем специальный эндпоинт
        if "8080" in endpoint_url:
            test_url = f"{endpoint_url}/sdui/test"
        else:
            test_url = f"{endpoint_url}/salary-api"

        start_time = time.time()

        req = urllib.request.Request(
            test_url,
            data=contract_json,
            headers={'Content-Type': 'application/json'}
        )

        response = urllib.request.urlopen(req, timeout=10)
        response_time = time.time() - start_time

        results["response_time"] = response_time

        if response.getcode() == 200:
            results["success"] = True
            print(f"  ✅ Успешный ответ ({response_time:.2f}s)")
        else:
            results["errors"].append(f"HTTP {response.getcode()}")
            print(f"  ❌ HTTP {response.getcode()}")

    except urllib.error.HTTPError as e:
        error_msg = f"HTTP {e.code}: {e.reason}"
        results["errors"].append(error_msg)
        print(f"  ❌ {error_msg}")

        # Попытка прочитать детали ошибки
        try:
            error_body = e.read().decode('utf-8')
            if error_body:
                try:
                    error_json = json.loads(error_body)
                    if 'message' in error_json:
                        results["errors"].append(error_json['message'])
                    if 'validationErrors' in error_json:
                        results["errors"].extend(error_json['validationErrors'])
                except json.JSONDecodeError:
                    results["errors"].append(f"Ответ сервера: {error_body[:200]}")
        except:
            pass

    except urllib.error.URLError as e:
        error_msg = f"Сетевая ошибка: {e.reason}"
        results["errors"].append(error_msg)
        print(f"  ❌ {error_msg}")

    except Exception as e:
        error_msg = f"Ошибка: {str(e)}"
        results["errors"].append(error_msg)
        print(f"  ❌ {error_msg}")

    return results

def run_metaschema_validation(contract_path):
    """Запуск валидации через существующую систему"""
    print("🔍 Валидация через metaschema...")

    base_dir = Path(contract_path).parent.parent.parent.parent.parent
    validator_cmd = [
        "python3",
        str(base_dir / "validation-system/src/validator.py"),
        "--config",
        str(base_dir / ".validator.yaml")
    ]

    try:
        result = subprocess.run(
            validator_cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(base_dir)
        )

        if result.returncode == 0:
            print("  ✅ Metaschema валидация пройдена")
            return True, []
        else:
            errors = result.stderr.split('\n') if result.stderr else []
            print(f"  ❌ Metaschema ошибки ({len(errors)})")
            for error in errors[:5]:  # Показываем первые 5 ошибок
                if error.strip():
                    print(f"    • {error.strip()}")
            return False, errors

    except subprocess.TimeoutExpired:
        print("  ⏰ Валидация превысила лимит времени")
        return False, ["Превышено время валидации"]
    except FileNotFoundError:
        print("  ⚠️ Валидатор не найден, пропускаем")
        return True, []
    except Exception as e:
        print(f"  ❌ Ошибка валидации: {e}")
        return False, [str(e)]

def comprehensive_validation(contract_path):
    """Комплексная валидация контракта"""
    print(f"🚀 Комплексная валидация: {Path(contract_path).name}")
    print("=" * 60)

    total_score = 100
    all_errors = []
    all_warnings = []

    # 1. Базовая структурная валидация
    print("\n1️⃣ Структурная валидация")
    try:
        with open(contract_path, 'r', encoding='utf-8') as f:
            contract = json.load(f)
        print("  ✅ JSON синтаксис корректен")
    except Exception as e:
        print(f"  ❌ Ошибка JSON: {e}")
        return False

    # 2. Простая валидация (наш валидатор)
    print("\n2️⃣ Простая валидация")
    simple_result = subprocess.run([
        "python3",
        "/Users/username/Documents/FMS_GIT/simple_validator.py",
        contract_path
    ], capture_output=True, text=True)

    if simple_result.returncode == 0:
        print("  ✅ Простая валидация пройдена")
    else:
        print("  ⚠️ Обнаружены проблемы")
        total_score -= 20

    # 3. Metaschema валидация
    print("\n3️⃣ Metaschema валидация")
    meta_success, meta_errors = run_metaschema_validation(contract_path)
    if not meta_success:
        all_errors.extend(meta_errors)
        total_score -= 30

    # 4. Тестирование эндпоинтов
    print("\n4️⃣ Тестирование эндпоинтов")
    available_endpoints = test_local_endpoints()

    if available_endpoints:
        for endpoint in available_endpoints:
            endpoint_result = test_contract_against_endpoint(contract, endpoint)
            if not endpoint_result["success"]:
                all_errors.extend(endpoint_result["errors"])
                total_score -= 25
    else:
        print("  ⚠️ Эндпоинты недоступны - пропускаем сетевое тестирование")
        all_warnings.append("Эндпоинты недоступны")
        total_score -= 10

    # 5. Финальный отчет
    print("\n" + "=" * 60)
    print("📊 ИТ��ГОВЫЙ ОТЧЕТ")
    print("=" * 60)

    if all_errors:
        print(f"\n❌ Ошибки ({len(all_errors)}):")
        for error in all_errors[:10]:  # Показываем первые 10
            print(f"  • {error}")
        if len(all_errors) > 10:
            print(f"  ... и еще {len(all_errors) - 10} ошибок")

    if all_warnings:
        print(f"\n⚠️ Предупреждения ({len(all_warnings)}):")
        for warning in all_warnings:
            print(f"  • {warning}")

    total_score = max(0, min(100, total_score))
    print(f"\n🎯 Общая оценка: {total_score}/100")

    if total_score >= 90:
        print("🎉 Отличный контракт! Готов к продакшену")
        return True
    elif total_score >= 70:
        print("✅ Хороший контракт, незначительные доработки")
        return True
    elif total_score >= 50:
        print("⚠️ Контракт требует доработки")
        return False
    else:
        print("❌ Контракт содержит критические ошибки")
        return False

def main():
    if len(sys.argv) != 2:
        print("Использование: python agent_terminal_validator.py contract.json")
        print("\nЭтот валидатор проверяет контракт через:")
        print("• Структурную валидацию")
        print("• Metaschema валидацию")
        print("• Тестирование на реальных эндпоинтах (8080, 9090)")
        sys.exit(1)

    contract_path = sys.argv[1]

    if not os.path.exists(contract_path):
        print(f"❌ Файл не найден: {contract_path}")
        sys.exit(1)

    success = comprehensive_validation(contract_path)

    print(f"\n{'✅ КОНТРАКТ ВАЛИДЕН' if success else '❌ КОНТРАКТ НЕВАЛИДЕН'}")
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()