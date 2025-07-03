import json

from pipeline import run_ekf
from visualisation import plot_results

# Параметры
dt = 0.1  # Временной шаг (в секундах)
process_noise = 0.5  # Шум процесса
measurement_noise = 0.5  # Шум измерений
initial_state = [0.0, 0.0]  # Начальное состояние [x, vx]
anchor_x = 0.0  # Координата anchor по x

measurement_noise = float(input("Enter measurement noise (recomended 0.5): "))
process_noise = float(input("Enter process noise (recomended 0.5): "))
initial_state[0] = float(input("Enter initial distance between UWB-trackers: "))


# Массив измерений расстояний
measured_distances = json.load(open("data/log.json", "r"))

# Запуск EKF
estimated_positions, estimated_velocities = (
    run_ekf(measured_distances, dt, process_noise, measurement_noise, initial_state, anchor_x))

data = {
    "estimated_positions": list(estimated_positions),
    "estimated_velocities": list(estimated_velocities),
}
with open("data/estimated_data.json", "w", encoding="utf-8") as file:
    json.dump(data, file)

# Визуализация результатов
plot_results(measured_distances, estimated_positions, estimated_velocities, dt)
