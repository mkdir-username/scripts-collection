#!/bin/bash

# Клонируем репозиторий
git clone "$1"

# Получаем имя папки из URL репозитория
REPO_NAME=$(basename "$1" .git)

# Переходим в папку
# cd "$REPO_NAME" || exit
echo "============================================================"
echo "cd $REPO_NAME"

