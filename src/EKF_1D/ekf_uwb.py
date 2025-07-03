import numpy as np


class EKF_UWB:
    def __init__(self, dt: float, process_noise: float, measurement_noise: float,
                 initial_state: list[float], anchor_x: float):
        self.dt = dt  # Временной шаг
        self.x = np.array(initial_state, dtype=float)  # Состояние [x, vx]
        self.P = np.eye(2) * 100  # Ковариация (начальная неопределённость)
        self.Q = np.eye(2) * process_noise  # Шум процесса
        self.R = np.array([[measurement_noise]])  # Шум измерений
        self.anchor_x = anchor_x  # Координата anchor по x

    def predict(self):
        # Матрица перехода
        F = np.array([[1, self.dt],
                      [0, 1]])

        self.x = F @ self.x  # Прогноз состояния
        self.P = F @ self.P @ F.T + self.Q  # Обновление ковариации

    def update(self, measured_distance: float):
        xa = self.anchor_x  # Координата anchor
        x, vx = self.x  # Распаковка состояния

        # Нелинейная функция измерения (расстояние до anchor с учётом скорости)
        h = np.array([[np.abs(x + vx * self.dt - xa)]])

        # Якобиан H
        epsilon = 1e-6
        H = np.array([[(x + vx * self.dt - xa) / (np.abs(x + vx * self.dt - xa) + epsilon), 0]])

        # Инновация и её ковариация
        y_residual = np.array([[measured_distance]]) - h  # Разница измерений
        S = H @ self.P @ H.T + self.R  # Ковариация инновации
        K = self.P @ H.T @ np.linalg.inv(S) if np.linalg.det(S) != 0 else np.zeros((2, 1))  # Коэффициент Калмана

        # Обновление состояния
        self.x += (K @ y_residual).flatten()
        self.P = (np.eye(2) - K @ H) @ self.P

    def get_state(self) -> np.ndarray:
        return self.x.copy()