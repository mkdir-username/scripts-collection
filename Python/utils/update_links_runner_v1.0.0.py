import os
import re
import sys

DEFAULT_PATH = os.path.expanduser("~/Documents/front-middle-schema")

def replace_links_in_markdown(file_path):
    # Открываем файл для чтения
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Регулярное выражение для поиска ссылок формата "$ref": "path/to/AnyFileName"
    # Исключаем ссылки, начинающиеся с "#"
    pattern = r'("\$ref":\s*")([^#][^"]+)(")'

    # Функция замены
    def replacement(match):
        # Извлекаем путь к файлу
        ref_path = match.group(2)
        # Извлекаем имя файла (последний элемент пути)
        file_name = os.path.basename(ref_path)
        # Формируем новую ссылку
        return f'"$ref": [{file_name}]({ref_path})'

    # Заменяем ссылки
    new_content = re.sub(pattern, replacement, content)

    # Записываем изменения обратно в файл
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(new_content)

def rename_json_files(directory):
    try:
        for entry in os.listdir(directory):
            file_path = os.path.join(directory, entry)

            # Проверяем, является ли элемент директорией
            if os.path.isdir(file_path):
                # Пропускаем директории, названные .JSON (регистр не имеет значения)
                if entry.lower() == ".json":
                    print(f"Пропущена директория: {file_path}")
                    continue
                # Если это директория, рекурсивно вызываем функцию
                rename_json_files(file_path)
            elif entry.endswith(".json"):
                # Если это файл с расширением .json, переименовываем его
                new_file_path = os.path.join(
                    directory, os.path.splitext(entry)[0] + ".md"
                )
                os.rename(file_path, new_file_path)
                print(f"Переименован: {file_path} -> {new_file_path}")
    except Exception as e:
        print(f"Ошибка при обработке директории {directory}: {e}")

def process_markdown_files(directory):
    # Проходим по всем файлам и подкаталогам в указанной директории
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                try:
                    replace_links_in_markdown(file_path)
                    print(f"Ссылки в файле {file_path} успешно обновлены.")
                except Exception as e:
                    print(f"Ошибка при обработке файла {file_path}: {e}")

if __name__ == "__main__":
    # Проверяем количество аргументов
    if len(sys.argv) > 2:
        print("Использование: python script.py [<путь_к_директории>]")
        sys.exit(1)

    # Если путь не указан, используем путь по умолчанию
    directory_path = sys.argv[1] if len(sys.argv) == 2 else DEFAULT_PATH

    if not os.path.isdir(directory_path):
        print(f"Ошибка: {directory_path} не является директорией.")
        sys.exit(1)

    # Переименовываем файлы .json в .md
    rename_json_files(directory_path)

    # Обрабатываем файлы .md
    process_markdown_files(directory_path)
