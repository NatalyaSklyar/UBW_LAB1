import numpy as np
import matplotlib.pyplot as plt


def plot_results(measured_distances: np.ndarray, estimated_positions: np.ndarray,
                 estimated_velocities: np.ndarray, dt: float) -> None:
    """
    Визуализация результатов фильтрации.

    :param measured_distances: Массив измеренных расстояний
    :param estimated_positions: Массив оцененных позиций
    :param estimated_velocities: Массив оцененных скоростей
    :param dt: Временной шаг
    """
    time_steps = np.arange(len(measured_distances)) * dt

    plt.figure(figsize=(10, 6))

    # График положения
    plt.subplot(2, 1, 1)
    plt.plot(time_steps, measured_distances, label='Измеренные расстояния', marker='o', linestyle='dashed')
    plt.plot(time_steps, estimated_positions, label='Оцененные позиции (EKF)', linestyle='-', color='r')
    plt.title('Оценка положения')
    plt.xlabel('Время (сек)')
    plt.ylabel('Позиция (м)')
    plt.legend()

    # График скорости
    plt.subplot(2, 1, 2)
    plt.plot(time_steps, estimated_velocities, label='Оцененная скорость (EKF)', linestyle='-', color='g')
    plt.title('Оценка скорости')
    plt.xlabel('Время (сек)')
    plt.ylabel('Скорость (м/с)')
    plt.legend()

    plt.subplots_adjust(hspace=0.5)
    plt.savefig("data/plt.png")
    plt.show()
