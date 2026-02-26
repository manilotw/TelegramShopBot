# TelegramShop

Телеграм-бот для продажи товаров с интеграцией Strapi CMS

![](.screenshots/11.jpg) ![](.screenshots/22.jpg) ![](.screenshots/33.jpg)

## Требования

- Python 3.7+
- Node.js 14+ (для Strapi)
- npm или yarn

## Установка и настройка

### Шаг 1: Установка Strapi

1. Создайте новый проект Strapi:
```bash
npx create-strapi-app@latest strapi-backend --quickstart
```

2. После установки Strapi автоматически откроется в браузере на `http://localhost:1337/admin`

3. Создайте учетную запись администратора (имя, email, пароль)

### Шаг 2: Настройка коллекций в Strapi

1. В админ-панели Strapi перейдите в **Content-Type Builder**

2. Создайте коллекцию **Product** с полями:
   - `name` (Text) - обязательное
   - `description` (Text) - обязательное
   - `price` (Number - decimal) - обязательное
   - `weight` (Number - decimal)
   - `image` (Media - Multiple files)

3. Создайте коллекцию **Cart** с полями:
   - `telegram_chat_id` (Text) - обязательное, уникальное
   - `items` (Relation - has many Cart Items)

4. Создайте коллекцию **Cart Item** с полями:
   - `product` (Relation - belongs to Product)
   - `quantity` (Number - integer) - обязательное
   - `cart` (Relation - belongs to Cart)

5. Создайте коллекцию **Customer** с полями:
   - `name` (Text) - обязательное
   - `email` (Email) - обязательное

6. Сохраните изменения (кнопка **Save**). Strapi перезагрузится.

### Шаг 3: Настройка прав доступа в Strapi

1. Перейдите в **Settings** → **Users & Permissions Plugin** → **Roles** → **Public**

2. Раскройте все коллекции (Product, Cart, Cart-Item, Customer) и отметьте галочками:
   - `find`
   - `findOne`
   - `create`
   - `update`
   - `delete`

3. Для **Upload** отметьте `upload` и `find`

4. Нажмите **Save**

### Шаг 4: Получение API токена Strapi

1. В Strapi перейдите в **Settings** → **API Tokens**

2. Нажмите **Create new API Token**

3. Заполните:
   - **Name**: `telegram-bot`
   - **Token duration**: `Unlimited`
   - **Token type**: `Full access`

4. Нажмите **Save** и **скопируйте токен** (он показывается только один раз!)

### Шаг 5: Создание Telegram бота

1. Откройте Telegram и найдите бота [@BotFather](https://t.me/BotFather)

2. Отправьте команду `/newbot`

3. Следуйте инструкциям:
   - Введите имя бота (например: `My Shop Bot`)
   - Введите username бота (например: `myshop_bot`)

4. **Скопируйте токен**, который выдаст BotFather

### Шаг 6: Установка Telegram бота

1. Клонируйте репозиторий:
```bash
git https://github.com/manilotw/TelegramShopBot.git
cd TelegramShopBot
```

2. Создайте виртуальное окружение:
```bash
python -m venv env
```

3. Активируйте виртуальное окружение:
```bash
# Windows
env\Scripts\activate

# Linux/Mac
source env/bin/activate
```

4. Установите зависимости:
```bash
pip install -r requirements.txt
```

### Шаг 7: Настройка переменных окружения

1. Создайте файл `.env` в корневой папке проекта

2. Добавьте переменные окружения:
```env
STRAPI_BASE_URL=http://localhost:1337
STRAPI_API_TOKEN=ваш_токен_strapi_скопированный_на_шаге_4
TELEGRAM_TOKEN=ваш_токен_telegram_скопированный_на_шаге_5
```

### Шаг 8: Добавление товаров в Strapi

1. Откройте Strapi админ-панель: `http://localhost:1337/admin`

2. Перейдите в **Content Manager** → **Product**

3. Нажмите **Create new entry**

4. Заполните данные товара:
   - Name: `Пицца Маргарита`
   - Description: `Классическая пицца с томатами и моцареллой`
   - Price: `450`
   - Weight: `0.5`
   - Image: Загрузите изображение товара

5. Нажмите **Save** и **Publish**

6. Повторите для других товаров

## Запуск

1. Убедитесь, что Strapi запущен (в папке `strapi-backend`):
```bash
npm run develop
```

2. В другом терминале запустите Telegram бота:
```bash
cd telegram-shop
python main.py
```

3. Откройте Telegram и найдите вашего бота

4. Отправьте команду `/start`

## Структура проекта

```
TelegramShopBot/
├── main.py              # Основной файл бота
├── strapi.py            # Модуль для работы со Strapi API
├── requirements.txt     # Зависимости Python
├── .env                # Переменные окружения
└── README.md           # Документация
```

## Возможности бота

- 📦 Просмотр каталога товаров
- 🛒 Добавление товаров в корзину
- 📝 Оформление заказа с указанием email
- ❌ Удаление товаров из корзины
- 💰 Подсчет итоговой стоимости

## Решение проблем

**Ошибка подключения к Strapi:**
- Убедитесь, что Strapi запущен на `http://localhost:1337`
- Проверьте правильность API токена в `.env`

**Бот не отвечает:**
- Проверьте правильность Telegram токена
- Убедитесь, что бот запущен

**Товары не отображаются:**
- Проверьте, что товары опубликованы (Published) в Strapi
- Проверьте права доступа в Strapi (Шаг 3)

## Лицензия

MIT