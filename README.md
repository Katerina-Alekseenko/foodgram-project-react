# Foodgram - Продуктовый помощник

«Продуктовый помощник»: это ресурс, на котором пользователи могут опубликовать рецепты, добавляют рецепты других авторов в избранное и подписываятся на их публикации. Сервис «Список покупок» позволит пользователям создавать список продуктов, которые нужно купить для приготовления выбранных блюд. Список покупок можно выгрузить в удобном PDF файле, который можно взять с собой в магазин.

## Установка локально

1. Склонировать репозиторий к себе на компьютер:

```bash
git@github.com:Katerina-Alekseenko/foodgram-project-react.git
cd foodgram-project-react
```

2. Cоздать и активировать виртуальное окружение:

```bash
python -m venv venv
```

```bash
. venv/bin/activate
```

3. Cоздайте файл `.env` в директории `/infra/` с содержанием:

```bash
cd infra/
touch .env
```

```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
```

4. Выполните миграции:

```bash
python manage.py migrate
```

5. Запустите сервер:

```bash
python manage.py runserver
```

## Запуск проекта в Docker контейнере

1. Установите Docker.

Параметры запуска описаны в файлах `docker-compose.yml` и `nginx.conf`

2. Запустите docker compose:

```bash
docker-compose up -d --build
```  

3. Выполните миграции:

```bash
docker-compose exec backend python manage.py migrate
```

4. Создайте суперпользователя:

```bash
docker-compose exec backend python manage.py createsuperuser
```

5. Через сайт <http://62.84.124.155/admin> после аутентификации добавить теги (завтрак, обед и ужин)

6. Заупстите процесс сбора статики:

```bash
docker-compose exec backend python manage.py collectstatic --no-input
```

## Сайт

Сайт доступен по ссылке: <http://62.84.124.155>

## Доступ в админку 

электронная почта:

```bash
katrinale@yandex.ru
```

пароль:

```bash
123
```

## Автор

Алексеенко Екатерина Анатольевна
