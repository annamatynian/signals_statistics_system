"""
Тест для проверки конфигурации системы
"""
import os
import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

def test_env_variables():
    """Проверка наличия необходимых переменных окружения"""
    print("\n=== Проверка переменных окружения ===\n")

    required_vars = [
        "GOOGLE_SERVICE_ACCOUNT_JSON",
        "GOOGLE_SHEETS_SPREADSHEET_ID"
    ]

    optional_vars = [
        "BINANCE_API_KEY",
        "BYBIT_API_KEY",
        "COINBASE_API_KEY",
        "TRADING_ALERT_PUSHOVER_API_TOKEN",
        "TELEGRAM_BOT_TOKEN",
        "PROXY_URL"
    ]

    missing_required = []

    # Проверка обязательных переменных
    print("📋 Обязательные переменные:")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Показываем только первые/последние символы для безопасности
            if len(value) > 20:
                display_value = f"{value[:10]}...{value[-10:]}"
            else:
                display_value = "***"
            print(f"  ✅ {var}: {display_value}")
        else:
            print(f"  ❌ {var}: НЕ УСТАНОВЛЕНА")
            missing_required.append(var)

    # Проверка опциональных переменных
    print("\n📋 Опциональные переменные:")
    for var in optional_vars:
        value = os.getenv(var)
        if value and value.strip():
            print(f"  ✅ {var}: установлена")
        else:
            print(f"  ⚠️  {var}: не установлена (необязательная)")

    if missing_required:
        print(f"\n❌ ОШИБКА: Отсутствуют обязательные переменные: {', '.join(missing_required)}")
        return False

    print("\n✅ Все обязательные переменные окружения присутствуют!")
    return True


def test_dependencies():
    """Проверка установленных зависимостей"""
    print("\n\n=== Проверка установленных зависимостей ===\n")

    dependencies = {
        "pydantic": "Модели данных",
        "aiohttp": "Асинхронные HTTP запросы",
        "ccxt": "API криптобирж",
        "google.oauth2": "Google Sheets API",
        "googleapiclient": "Google API Client",
        "pytest": "Тестирование",
        "dotenv": "Загрузка .env файлов"
    }

    all_installed = True

    for module, description in dependencies.items():
        try:
            __import__(module)
            print(f"  ✅ {module:20} - {description}")
        except ImportError:
            print(f"  ❌ {module:20} - {description} (НЕ УСТАНОВЛЕН)")
            all_installed = False

    if not all_installed:
        print("\n❌ Некоторые зависимости не установлены!")
        print("   Запустите: pip install -r requirements.txt")
        return False

    print("\n✅ Все необходимые зависимости установлены!")
    return True


def test_project_structure():
    """Проверка структуры проекта"""
    print("\n\n=== Проверка структуры проекта ===\n")

    project_root = Path(__file__).parent.parent.parent

    required_paths = [
        "src/models/signal.py",
        "src/models/price.py",
        "src/services/sheets_reader.py",
        "src/services/signal_manager.py",
        "src/services/price_checker.py",
        "src/storage/base.py",
        "src/storage/json_storage.py",
        "src/exchanges/base.py",
        "src/exchanges/binance.py",
        "tests/conftest.py"
    ]

    all_exist = True

    for path_str in required_paths:
        full_path = project_root / path_str
        if full_path.exists():
            print(f"  ✅ {path_str}")
        else:
            print(f"  ❌ {path_str} (отсутствует)")
            all_exist = False

    if not all_exist:
        print("\n❌ Некоторые файлы проекта отсутствуют!")
        return False

    print("\n✅ Структура проекта корректна!")
    return True


def main():
    """Главная функция теста"""
    print("=" * 70)
    print("  ПРОВЕРКА КОНФИГУРАЦИИ SIGNALS STATISTICS SYSTEM")
    print("=" * 70)

    results = {
        "Переменные окружения": test_env_variables(),
        "Зависимости": test_dependencies(),
        "Структура проекта": test_project_structure()
    }

    print("\n" + "=" * 70)
    print("  ИТОГОВЫЙ РЕЗУЛЬТАТ")
    print("=" * 70 + "\n")

    for test_name, result in results.items():
        status = "✅ УСПЕШНО" if result else "❌ ОШИБКА"
        print(f"  {test_name:30} {status}")

    all_passed = all(results.values())

    print("\n" + "=" * 70)
    if all_passed:
        print("  ✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print("  ❌ НЕКОТОРЫЕ ПРОВЕРКИ НЕ ПРОЙДЕНЫ")
        print("  📝 Проверьте ошибки выше и исправьте конфигурацию")
    print("=" * 70 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
