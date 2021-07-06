build:
	docker compose up -d --build

up:
	docker compose up -d

down:
	docker compose down

app:
	docker compose exec app bash

mysql-root:
	docker-compose exec db bash -c 'mysql -uroot -p${MYSQL_PASSWORD} ${MYSQL_DATABASE}'
