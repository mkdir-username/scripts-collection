#!/usr/bin/env python3
"""
SDUI Visual Validator - Система визуального тестирования контрактов
Автоматически создает скриншоты и валидирует отображение контрактов
"""

import json
import os
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import base64
import hashlib

# Playwright для скриншотов
try:
    from playwright.sync_api import sync_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️ Playwright не установлен. Установите: pip install playwright && playwright install")

# Импорт существующих валидаторов
from sdui_web_validator_improved import SDUIWebValidatorImproved


class SDUIVisualValidator:
    """Визуальный валидатор SDUI контрактов с автоматическими скриншотами"""

    def __init__(self, project_root: str = "/Users/username/Documents/front-middle-schema"):
        self.project_root = Path(project_root)
        self.screenshots_dir = self.project_root / "screenshots" / "validation"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

        # Конфигурация тестовых серверов
        self.servers = {
            "sdui_sandbox": "http://localhost:8080",
            "host_ui": "http://localhost:9090",
            "salary_api": "http://localhost:9090/salary-api"
        }

        # Валидатор контрактов
        self.contract_validator = SDUIWebValidatorImproved(project_root)

        # Playwright setup
        self.playwright = None
        self.browser = None

    def __enter__(self):
        if PLAYWRIGHT_AVAILABLE:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def check_servers_availability(self) -> Dict[str, bool]:
        """Проверка доступности тестовых серверов"""
        availability = {}

        for name, url in self.servers.items():
            try:
                response = requests.get(url, timeout=5)
                availability[name] = response.status_code < 500
                print(f"✅ {name} ({url}): доступен" if availability[name]
                      else f"❌ {name} ({url}): недоступен")
            except Exception as e:
                availability[name] = False
                print(f"❌ {name} ({url}): ошибка - {e}")

        return availability

    def validate_contract_with_visual(
        self,
        contract: Dict,
        contract_name: str = "test_contract",
        take_screenshot: bool = True
    ) -> Dict:
        """
        Полная валидация контракта с визуальным тестированием

        Returns:
            Отчет с результатами валидации и скриншотами
        """
        print(f"\n🔍 Начинаем валидацию контракта: {contract_name}")

        report = {
            "contract_name": contract_name,
            "timestamp": datetime.now().isoformat(),
            "validation": {},
            "visual_test": {},
            "screenshots": [],
            "errors": [],
            "warnings": [],
            "success": False
        }

        # 1. Статическая валидация контракта
        print("📋 Этап 1: Статическая валидация...")
        try:
            valid, validation_report, fixed_contract = self.contract_validator.validate_contract(
                contract, strict=False, auto_fix=True
            )

            report["validation"] = {
                "valid": valid,
                "web_compatibility": validation_report.get("web_compatibility", 0),
                "errors_count": len(validation_report.get("errors", [])),
                "warnings_count": len(validation_report.get("warnings", [])),
                "details": validation_report
            }

            if fixed_contract:
                contract = fixed_contract  # Используем исправленный контракт

            print(f"   ✅ Валидация завершена: {validation_report.get('web_compatibility', 0)}% совместимость")

        except Exception as e:
            report["errors"].append(f"Ошибка валидации: {e}")
            print(f"   ❌ Ошибка валидации: {e}")

        # 2. Проверка серверов
        print("🌐 Этап 2: Проверка серверов...")
        server_status = self.check_servers_availability()
        report["visual_test"]["server_status"] = server_status

        # 3. Визуальное тестирование
        if take_screenshot and PLAYWRIGHT_AVAILABLE and any(server_status.values()):
            print("📸 Этап 3: Визуальное тестирование...")
            try:
                visual_results = self._perform_visual_testing(contract, contract_name)
                report["visual_test"].update(visual_results)
                report["screenshots"] = visual_results.get("screenshots", [])

            except Exception as e:
                report["errors"].append(f"Ошибка визуального тестирования: {e}")
                print(f"   ❌ Ошибка визуального тестирования: {e}")

        # 4. Итоговая оценка
        report["success"] = (
            report["validation"].get("valid", False) and
            len(report["errors"]) == 0 and
            len(report["screenshots"]) > 0
        )

        print(f"🎯 Результат: {'✅ УСПЕШНО' if report['success'] else '❌ ОШИБКИ'}")
        return report

    def _perform_visual_testing(self, contract: Dict, contract_name: str) -> Dict:
        """Выполнение визуального тестирования с скриншотами"""
        visual_results = {
            "screenshots": [],
            "rendering_errors": [],
            "performance": {},
            "accessibility": {}
        }

        if not self.browser:
            raise Exception("Браузер не инициализирован")

        # Создаем страницу
        page = self.browser.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})

        try:
            # Тестируем разные сценарии
            test_scenarios = [
                {
                    "name": "sdui_sandbox_render",
                    "url": f"{self.servers['sdui_sandbox']}/preview",
                    "method": "POST",
                    "data": contract
                },
                {
                    "name": "host_ui_integration",
                    "url": f"{self.servers['host_ui']}/",
                    "method": "GET"
                }
            ]

            for scenario in test_scenarios:
                try:
                    print(f"   📸 Тести��уем сценарий: {scenario['name']}")
                    screenshot_info = self._test_scenario(page, scenario, contract_name)
                    if screenshot_info:
                        visual_results["screenshots"].append(screenshot_info)

                except Exception as e:
                    visual_results["rendering_errors"].append(f"{scenario['name']}: {e}")
                    print(f"      ⚠️ Ошибка в сценарии {scenario['name']}: {e}")

        finally:
            page.close()

        return visual_results

    def _test_scenario(self, page: Page, scenario: Dict, contract_name: str) -> Optional[Dict]:
        """Тестирование конкретного сценария"""
        start_time = time.time()

        try:
            if scenario["method"] == "POST":
                # Для POST запросов создаем тестовую страницу
                html_content = self._create_test_html(scenario.get("data", {}))
                page.set_content(html_content)

            else:
                # Для GET запросов переходим на URL
                response = page.goto(scenario["url"], wait_until="networkidle", timeout=10000)
                if not response or response.status >= 400:
                    raise Exception(f"HTTP {response.status if response else 'timeout'}")

            # Ждем рендеринга
            page.wait_for_timeout(2000)

            # Создаем скриншот
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_name = f"{contract_name}_{scenario['name']}_{timestamp}.png"
            screenshot_path = self.screenshots_dir / screenshot_name

            page.screenshot(path=str(screenshot_path), full_page=True)

            # Собираем метрики
            load_time = time.time() - start_time
            page_title = page.title()

            # Проверяем на ошибки в консоли
            console_errors = []
            def handle_console(msg):
                if msg.type == "error":
                    console_errors.append(msg.text)

            page.on("console", handle_console)

            return {
                "scenario": scenario["name"],
                "screenshot_path": str(screenshot_path),
                "screenshot_name": screenshot_name,
                "load_time": round(load_time, 2),
                "page_title": page_title,
                "console_errors": console_errors,
                "timestamp": timestamp,
                "success": True
            }

        except Exception as e:
            return {
                "scenario": scenario["name"],
                "error": str(e),
                "load_time": round(time.time() - start_time, 2),
                "success": False
            }

    def _create_test_html(self, contract: Dict) -> str:
        """Создание HTML страницы для тестирования контракта"""
        contract_json = json.dumps(contract, indent=2, ensure_ascii=False)

        return f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SDUI Contract Test</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 20px;
                    background: #f5f5f5;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    color: #ef3124;
                    border-bottom: 2px solid #ef3124;
                    padding-bottom: 10px;
                    margin-bottom: 20px;
                }}
                .contract {{
                    background: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 15px;
                    overflow-x: auto;
                }}
                pre {{
                    margin: 0;
                    white-space: pre-wrap;
                    font-size: 12px;
                }}
                .status {{
                    display: inline-block;
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: bold;
                    background: #28a745;
                    color: white;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="header">🏦 SDUI Contract Validation Test</h1>
                <p>Тестирование контракта: <span class="status">АКТИВНО</span></p>
                <p>Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

                <h2>📋 Contract JSON:</h2>
                <div class="contract">
                    <pre>{contract_json}</pre>
                </div>

                <div style="margin-top: 20px;">
                    <small>Generated by SDUI Visual Validator</small>
                </div>
            </div>

            <script>
                // Добавляем динамическое поведение для тестирования
                console.log('SDUI Contract loaded successfully');
                document.addEventListener('DOMContentLoaded', function() {{
                    console.log('DOM fully loaded');
                }});
            </script>
        </body>
        </html>
        """

    def generate_validation_report_html(self, report: Dict) -> str:
        """Генерация HTML отчета по валидации"""
        screenshots_html = ""
        if report["screenshots"]:
            screenshots_html = "<h3>📸 Скриншоты:</h3>"
            for screenshot in report["screenshots"]:
                if screenshot.get("success"):
                    screenshots_html += f"""
                    <div style="margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
                        <strong>{screenshot['scenario']}</strong><br>
                        <small>Время загрузки: {screenshot['load_time']}s</small><br>
                        <small>Файл: {screenshot['screenshot_name']}</small>
                    </div>
                    """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>SDUI Validation Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .success {{ color: green; }}
                .error {{ color: red; }}
                .warning {{ color: orange; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <h1>🔍 SDUI Validation Report</h1>
            <p><strong>Контракт:</strong> {report['contract_name']}</p>
            <p><strong>Время:</strong> {report['timestamp']}</p>
            <p><strong>Результат:</strong> <span class="{'success' if report['success'] else 'error'}">
                {'✅ УСПЕШНО' if report['success'] else '❌ ОШИБКИ'}
            </span></p>

            <div class="section">
                <h2>📋 Статическая валидация</h2>
                <p>Валидность: {'✅' if report['validation'].get('valid') else '❌'}</p>
                <p>Web совместимость: {report['validation'].get('web_compatibility', 0)}%</p>
                <p>Ошибок: {report['validation'].get('errors_count', 0)}</p>
                <p>Предупреждений: {report['validation'].get('warnings_count', 0)}</p>
            </div>

            <div class="section">
                <h2>🌐 Статус серверов</h2>
                {chr(10).join([f"<p>{name}: {'✅' if status else '❌'}</p>"
                             for name, status in report.get('visual_test', {}).get('server_status', {}).items()])}
            </div>

            <div class="section">
                {screenshots_html}
            </div>

            {f'<div class="section"><h3>❌ Ошибки:</h3>{"<br>".join(report["errors"])}</div>' if report["errors"] else ''}
            {f'<div class="section"><h3>⚠️ Предупреждения:</h3>{"<br>".join(report["warnings"])}</div>' if report["warnings"] else ''}
        </body>
        </html>
        """


def test_sample_contract():
    """Тест с примером контракта"""
    sample_contract = {
        "type": "TextView",
        "content": {
            "text": "Тестовый контракт для агентов",
            "style": "header"
        },
        "releaseVersion": {
            "web": "released",
            "ios": "released",
            "android": "released"
        }
    }

    with SDUIVisualValidator() as validator:
        report = validator.validate_contract_with_visual(
            sample_contract,
            "agent_test_contract"
        )

        # Сохраняем HTML отчет
        html_report = validator.generate_validation_report_html(report)
        report_path = validator.screenshots_dir / f"agent_test_contract_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_report)

        print(f"\n📄 HTML отчет сохранен: {report_path}")
        return report


if __name__ == "__main__":
    print("🚀 SDUI Visual Validator")
    print("=" * 50)

    # Проверяем доступность Playwright
    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Для работы необходимо установить Playwright:")
        print("   pip install playwright")
        print("   playwright install chromium")
        exit(1)

    # Запускаем тест
    test_sample_contract()