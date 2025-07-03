import re
import json

with open("../data/log.txt", "r", encoding="utf-8") as file:
    lines = file.readlines()

# Извлекаем только строки вида "...Distance:345 mm"
pattern = re.compile(r'Distance:(\d+)\s*mm')
distances = []

for line in lines:
    match = pattern.search(line)
    if match:
        distances.append(int(match.group(1)))

# Записываем в log.json
with open("data/data_row.json", "w", encoding="utf-8") as json_file:
    json.dump(distances, json_file, indent=2)

print("Данные записаны в log.json")