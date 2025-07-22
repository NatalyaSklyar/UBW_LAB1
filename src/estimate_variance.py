import numpy as np
import sys
import json

def main():
    if len(sys.argv) < 2:
        print("Использование: python estimate_variance.py <путь_к_JSON_файлу>")
        sys.exit(1)

    filepath = sys.argv[1]

    try:
        with open(filepath, 'r') as f:
            measurements = json.load(f)
            if not isinstance(measurements, list) or not all(isinstance(x, (int, float)) for x in measurements):
                raise ValueError("JSON должен содержать один список чисел.")
    except Exception as e:
        print(f"Ошибка при чтении или разборе JSON-файла: {e}")
        sys.exit(1)

    if not measurements:
        print("Список измерений пуст.")
        sys.exit(1)

    real_distance = float(input("Введите реальное расстояние в миллиметрах: "))

    x = np.array(measurements)
    mean_x = np.mean(x)
    variance = np.var(x)  # Дисперсия
    std_dev = np.sqrt(variance)  # Стандартное отклонение
    error = mean_x - real_distance  # Погрешность среднего измерения

    print(f"\nРезультаты:")
    print(f"Количество измерений: {len(x)}")
    print(f"Среднее значение измерений: {mean_x:.4f} мм")
    print(f"Погрешность (среднее - реальное): {error:.4f} мм")
    print(f"Дисперсия измерений (σ²): {variance:.6f} мм²")
    print(f"Стандартное отклонение (σ): {std_dev:.6f} мм")

if __name__ == "__main__":
    main()