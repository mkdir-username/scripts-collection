def split_markdown_file(input_file, lines_per_chunk=10000):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            chunk_number = 1
            lines = []
            for line in f:
                lines.append(line)
                if len(lines) >= lines_per_chunk:
                    output_file = f"{input_file.replace('.md', '')}_part_{chunk_number}.md"
                    with open(output_file, 'w', encoding='utf-8') as out_f:
                        out_f.writelines(lines)
                    print(f"Создан файл: {output_file}")
                    lines = []
                    chunk_number += 1

            # Записываем оставшиеся строки, если они есть
            if lines:
                output_file = f"{input_file.replace('.md', '')}_part_{chunk_number}.md"
                with open(output_file, 'w', encoding='utf-8') as out_f:
                    out_f.writelines(lines)
                print(f"Создан файл: {output_file}")
                
        print(f"Файл {input_file} успешно разделен на {chunk_number} частей")
        
    except FileNotFoundError:
        print(f"Ошибка: Файл {input_file} не найден")
    except Exception as e:
        print(f"Ошибка при обработке файла: {e}")

if __name__ == "__main__":
    input_filename = "/Users/username/Documents/front-middle-schema/SDUI/functions_sdui.md"
    split_markdown_file(input_filename)
