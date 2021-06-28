# Environment

There are some Environment Variables you should
set if you want to use a Database or Redis.

## Database

Name         | Default              | Description
-------------|----------------------|------------
`DB_DRIVER`  | `postgresql+asyncpg` | The Database Driver to use
`DB_HOST`    | `localhost`          | Host of the DB Server
`DB_PORT`    | `5432`               | Port of the Database
`DB_USERNAME`| `postgres`           | Database Username
`DB_PASSWORD`| ` `                  | Database Password
`DB_DATABASE`|                      | Name of the Database

## Redis
Name         | Default              | Description
-------------|----------------------|------------
`REDIS_HOST` | `localhost`          | Host of the Redis Server
`REDIS_PORT` | `63792`              | Port of the Redis Server

## JWT
Name                             | Default              | Description
---------------------------------|----------------------|------------
`JWT_SECRET_KEY`                 |                      | Secret Key for JWT Authentication
`JWT_ALGORITHM`                  | `HS256`              | The Algorithm for JWT
`JWT_ACCESS_TOKEN_EXPIRE_MINUTES`|`30`                  | Expire time for the Access Token
`JWT_REFRESH_TOKEN_EXPIRE_MINUTES`|`360`                | Expire time for the Refresh Token

## Other
Name         | Default              | Description
-------------|----------------------|------------
`LOG_LEVEL` | `INFO`                | Log Level e.g. `DEBUG`, `INFO`, `WARNING` or `ERROR`