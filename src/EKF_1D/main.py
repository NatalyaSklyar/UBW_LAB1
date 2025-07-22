import json
import sys
import numpy as np
from pipeline import run_ekf
from visualisation import plot_results

def main():
    if len(sys.argv) < 2:
        print("Использование: python3 src/EKF_1D/main.py <путь_к_входному_json_файлу> <путь_к_выходному_json_файлу>")
        sys.exit(1)

    filein = sys.argv[1]
    fileout = sys.argv[2]
    visualisation_file = sys.argv[3]

    # Параметры
    dt = 0.1  # Временной шаг (в секундах)
    initial_state = [0.0, 0.0]  # Начальное состояние [x, vx]
    anchor_x = 0.0  # Координата anchor по x

    measurement_noise = float(input("Введите погрешность измерений в м² в (измерено): "))
    process_noise = float(input("Введите шум процесса м²: "))
    initial_state[0] = float(input("Введите изначальное расстояние между UWB-трекерами в мм: ")) + 0.00001
    statistical_error = float(input("Введите статическую ошибку (измерено) в мм: "))


    # Массив измерений расстояний
    measured_distances = np.array(list(map(lambda x: x - statistical_error, json.load(open(filein, "r")))))

    # Запуск EKF
    estimated_positions, estimated_velocities = (
        run_ekf(measured_distances, dt, process_noise, measurement_noise, initial_state, anchor_x))

    data = {
        "estimated_positions": list(estimated_positions),
        "estimated_velocities": list(estimated_velocities),
    }
    with open(fileout, "w", encoding="utf-8") as file:
        json.dump(data, file)

    # Визуализация результатов
    plot_results(measured_distances, estimated_positions, estimated_velocities, dt, path_to_png=visualisation_file)

if __name__ == "__main__":
    main()