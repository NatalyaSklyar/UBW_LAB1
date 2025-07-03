import numpy as np
from ekf_uwb import EKF_UWB


def run_ekf(measured_distances: np.ndarray, dt: float, process_noise: float,
            measurement_noise: float, initial_state: list[float], anchor_x: float) -> tuple[np.ndarray, np.ndarray]:
    """
    Запуск расширенного фильтра Калмана для обработки данных UWB.

    :param measured_distances: Массив измеренных расстояний
    :param dt: Временной шаг
    :param process_noise: Шум процесса
    :param measurement_noise: Шум измерений
    :param initial_state: Начальное состояние [x, vx]
    :param anchor_x: Координата anchor по x
    :return: Оцененные позиции и скорости
    """
    ekf = EKF_UWB(dt, process_noise, measurement_noise, initial_state, anchor_x)
    estimated_positions = []
    estimated_velocities = []

    for measured_distance in measured_distances:
        ekf.predict()  # Прогнозирование
        ekf.update(measured_distance)  # Обновление с измерением
        state = ekf.get_state()
        estimated_positions.append(state[0])  # x
        estimated_velocities.append(state[1])  # vx

    return np.array(estimated_positions), np.array(estimated_velocities)
