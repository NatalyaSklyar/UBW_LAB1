import re
import json
import sys

def main():
    if len(sys.argv) < 2:
        print("Использование: python convert_logs.py <путь_к_входному_txt_файлу> <путь_к_выходному_json_файлу>")
        sys.exit(1)

    filein = sys.argv[1]
    fileout = sys.argv[2]

    with open(filein, "r", encoding="utf-8") as file:
        lines = file.readlines()

    # Извлекаем только строки вида "...Distance:345 mm"
    pattern = re.compile(r'Distance:(\d+)\s*mm')
    distances = []

    for line in lines:
        match = pattern.search(line)
        if match:
            distances.append(int(match.group(1)))

    # Записываем в log.json
    with open(fileout, "w", encoding="utf-8") as json_file:
        json.dump(distances, json_file, indent=2)

    print("Данные записаны в ", fileout)

if __name__ == "__main__":
    main()