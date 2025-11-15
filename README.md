# 🚀 Trading Alert System
### Автоматическая система мониторинга криптовалютных цен

[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange)](https://aws.amazon.com/lambda/)
[![DynamoDB](https://img.shields.io/badge/AWS-DynamoDB-blue)](https://aws.amazon.com/dynamodb/)
[![Gradio](https://img.shields.io/badge/Gradio-UI-brightgreen)](https://gradio.app/)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)

---

## 📋 Что это?

**Trading Alert System** - это полностью автоматическая система для мониторинга цен криптовалют на различных биржах (Binance, Bybit, Coinbase) с отправкой мгновенных уведомлений на ваш телефон когда цена достигает заданных уровней.

### ✨ Основные возможности:

- 🤖 **Автоматическая проверка** - AWS Lambda проверяет цены каждый час
- 🎨 **Красивый UI** - Gradio веб-интерфейс для управления сигналами
- 💾 **Надежное хранилище** - DynamoDB для всех данных
- 📊 **Google Sheets** - опциональное быстрое редактирование
- 📱 **Мгновенные уведомления** - Pushover notifications на телефон
- 🌐 **Мульти-биржа** - Binance, Bybit, Coinbase support
- 🔒 **Безопасность** - AWS Secrets Manager для credentials

---

## 🎯 Примеры использования

### Сценарий 1: Алерт на пробой уровня

```
Хочу узнать когда BTC пересечет $50,000 на Bybit
→ Создаю сигнал через Gradio UI
→ Lambda проверяет каждый час автоматически
→ Когда BTC > $50k → получаю уведомление на телефон 📱
```

### Сценарий 2: Мониторинг падения цены

```
Хочу купить ETH если упадет ниже $3,000
→ Создаю сигнал: ETH below $3000 на Binance
→ Lambda мониторит
→ Когда ETH < $3k → Pushover alert ✅
```

### Сценарий 3: Множество altcoin'ов

```
Мониторю 10+ криптовалют одновременно
→ Добавляю все в Google Sheets массово
→ Синхронизирую через Gradio
→ Lambda проверяет все сигналы автоматически
```

---

## 🏗️ Архитектура

```
                    ┌─────────────────┐
                    │ Google Sheets   │  ← Быстрое редактирование
                    └────────┬────────┘
                             │
                             ↓ Sync
                    ┌─────────────────┐
                    │   DynamoDB      │  ← Единый источник данных
                    └────────┬────────┘
                             │
                ┌────────────┼────────────┐
                ↓            ↓            ↓
         ┌──────────┐  ┌──────────┐  ┌──────────┐
         │  Lambda  │  │  Gradio  │  │  Sheets  │
         │  (Auto)  │  │   (UI)   │  │ (Manual) │
         └──────────┘  └──────────┘  └──────────┘
              ↓             ↓             ↓
         Проверка      Управление    Быстрое
         по cron       через Web     редактирование
```

**Компоненты:**
- **AWS Lambda** - автоматическая проверка сигналов (каждый час)
- **DynamoDB** - хранение всех сигналов
- **Gradio UI** - веб-интерфейс для управления
- **Google Sheets** - опциональное массовое редактирование
- **Pushover** - мгновенные уведомления
- **Multi-Exchange** - Binance, Bybit, Coinbase APIs

---

## ⚡ Быстрый старт (5 минут)

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/YOUR_USERNAME/trading_alert_system.git
cd trading_alert_system
```

### 2. Настройте .env файл

```bash
# Скопируйте пример
copy .env.example .env

# Отредактируйте своими ключами
notepad .env
```

**Минимум что нужно:**
```bash
# AWS
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
DYNAMODB_TABLE_NAME=trading-alerts
DYNAMODB_REGION=us-east-2

# Хотя бы одна биржа
BYBIT_API_KEY=your_key
BYBIT_API_SECRET=your_secret

# Pushover (для уведомлений)
PUSHOVER_APP_TOKEN=your_token
PUSHOVER_USER_KEY=your_user_key
```

### 3. Установите зависимости

```bash
# Создайте виртуальное окружение
python -m venv venv
venv\Scripts\activate

# Установите зависимости
pip install -r requirements.txt
```

### 4. Запустите Gradio UI

```bash
# Windows
run_gradio.bat

# Linux/Mac
python gradio_app.py
```

### 5. Откройте браузер

```
http://localhost:7860
```

**Готово!** 🎉 Теперь создайте первый сигнал через UI!

---

## 📚 Документация

### Для новичков:

- **[QUICKSTART_5MIN.md](QUICKSTART_5MIN.md)** - запустите систему за 5 минут ⚡
- **[GRADIO_GUIDE.md](GRADIO_GUIDE.md)** - полное руководство по UI
- **[FINAL_COMPLETE_GUIDE.md](FINAL_COMPLETE_GUIDE.md)** - всё в одном файле

### Для деплоя:

- **[GRADIO_DEPLOY.md](GRADIO_DEPLOY.md)** - деплой Gradio на облако
- **[DEPLOY_AWS_LAMBDA.md](DEPLOY_AWS_LAMBDA.md)** - настройка AWS Lambda

### Для разработчиков:

- **[ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)** - визуальные схемы
- **[INDEX.md](INDEX.md)** - полная навигация по документации

---

## 🎨 Gradio UI Screenshots

### Create Signal Tab
![Create Signal](docs/screenshots/create_signal.png)

### View Signals Tab
![View Signals](docs/screenshots/view_signals.png)

### Check Price Tab
![Check Price](docs/screenshots/check_price.png)

---

## 🔧 Технологический стек

**Backend:**
- Python 3.11
- AWS Lambda (serverless compute)
- DynamoDB (NoSQL database)
- boto3 (AWS SDK)
- Pydantic (data validation)

**Frontend:**
- Gradio 4.x (web UI)
- Pandas (data tables)

**Integrations:**
- Binance API
- Bybit API
- Coinbase API
- Pushover API
- Google Sheets API

**Infrastructure:**
- AWS CloudWatch (scheduling)
- AWS Secrets Manager (credentials)
- AWS S3 (Lambda deployment)
- AWS IAM (permissions)

---

## 📊 Возможности Gradio UI

### Tab 1: Create Signal
- Создание новых сигналов через форму
- Выбор биржи (Binance, Bybit, Coinbase)
- Условие (above/below)
- Целевая цена
- Опциональная синхронизация с Google Sheets

### Tab 2: View Signals
- Просмотр всех сигналов в таблице
- Фильтрация по статусу
- Обновление в реальном времени

### Tab 3: Delete Signal
- Удаление сигналов по ID
- Автоматическое обновление таблицы

### Tab 4: Check Price
- Проверка текущей цены с биржи
- Отображение 24h объема
- Real-time данные

### Tab 5: Sync from Sheets
- Массовая загрузка из Google Sheets
- Upsert логика (обновление существующих)

---

## 🚀 Деплой на Production

### Вариант 1: Hugging Face Spaces (рекомендуется)

```bash
# 1. Создайте Space на huggingface.co
# 2. Переименуйте файл
mv gradio_app.py app.py

# 3. Push в HF
git remote add hf https://huggingface.co/spaces/USERNAME/trading-signal-system
git push hf main

# 4. Настройте Secrets в HF UI
```

**Результат:** `https://huggingface.co/spaces/USERNAME/trading-signal-system`

### Вариант 2: AWS EC2

```bash
# 1. Создайте EC2 instance (t2.micro)
# 2. SSH подключение
# 3. Clone repo + install dependencies
# 4. Setup systemd service
# 5. Configure nginx (optional)
```

**Детали:** см. [GRADIO_DEPLOY.md](GRADIO_DEPLOY.md)

---

## 🔒 Безопасность

### Best Practices:

✅ **AWS Secrets Manager** - для хранения API ключей  
✅ **IAM Policies** - минимальные права доступа  
✅ **Environment Variables** - никогда не коммитим в Git  
✅ **HTTPS** - для production деплоя  
✅ **Authentication** - Gradio auth для публичного доступа  

### Что НЕ коммитить в Git:

```
.env
secret-*.json
*.pem
lambda_deployment.zip
```

---

## 📈 Roadmap

### Уже работает ✅

- [x] AWS Lambda автоматическая проверка
- [x] DynamoDB хранилище
- [x] Gradio веб-интерфейс
- [x] Google Sheets интеграция
- [x] Multi-exchange support (Binance, Bybit, Coinbase)
- [x] Pushover notifications

### В планах 🔜

- [ ] Telegram Bot интерфейс
- [ ] Discord notifications
- [ ] Email alerts
- [ ] Графики и аналитика
- [ ] Backtesting сигналов
- [ ] Больше бирж (Kraken, KuCoin)
- [ ] Mobile app (React Native)

---

## 🐛 Troubleshooting

### ❌ DynamoDB connection failed

```bash
# Проверьте AWS credentials
aws configure list

# Добавьте в .env
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
```

### ❌ No exchanges initialized

```bash
# Добавьте хотя бы одну биржу в .env
BYBIT_API_KEY=your_key
BYBIT_API_SECRET=your_secret
```

### ❌ Lambda timeout

```bash
# Увеличьте timeout в AWS Console
# Lambda → Configuration → General → Timeout → 60 seconds
```

**Больше решений:** [FINAL_COMPLETE_GUIDE.md](FINAL_COMPLETE_GUIDE.md) (раздел Troubleshooting)

---

## 📞 Support

### Документация:

- **[INDEX.md](INDEX.md)** - навигация по всем файлам
- **[FINAL_COMPLETE_GUIDE.md](FINAL_COMPLETE_GUIDE.md)** - полный гайд

### Issues:

Если нашли баг или есть предложение:
1. Проверьте [Troubleshooting](FINAL_COMPLETE_GUIDE.md)
2. Создайте Issue на GitHub

---

## 🤝 Contributing

Contributions welcome! 

1. Fork the repo
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

---

## 📄 License

MIT License - см. [LICENSE](LICENSE) файл

---

## ⭐ Star History

Если проект полезен - поставьте звезду! ⭐

---

## 🎉 Благодарности

- **AWS** - за Lambda и DynamoDB
- **Gradio** - за отличный UI фреймворк
- **Binance/Bybit/Coinbase** - за API
- **Pushover** - за notifications

---

## 📊 Stats

- **Lines of Code:** ~5,000+
- **Files:** 50+
- **Documentation:** 15+ MD files
- **Supported Exchanges:** 3 (Binance, Bybit, Coinbase)
- **AWS Services:** 5 (Lambda, DynamoDB, Secrets Manager, CloudWatch, S3)

---

## 🚀 Get Started Now!

```bash
# 1. Клонируйте
git clone https://github.com/YOUR_USERNAME/trading_alert_system.git

# 2. Настройте .env
copy .env.example .env

# 3. Установите зависимости
pip install -r requirements.txt

# 4. Запустите
run_gradio.bat

# 5. Откройте браузер
http://localhost:7860

# 🎉 Готово!
```

**Полный гайд:** [QUICKSTART_5MIN.md](QUICKSTART_5MIN.md)

---

**Made with ❤️ for crypto traders**

*Last updated: November 14, 2025*
