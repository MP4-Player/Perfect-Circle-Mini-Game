import cv2
import numpy as np

# Глобальные переменные
drawing = False  # Флаг для рисования
points = []      # Точки, нарисованные пользователем
reference_circle = None  # Эталонный круг (центр и радиус)

# Функция для обработки событий мыши
def draw_circle(event, x, y, flags, param):
    global drawing, points

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        points = []  # Начинаем новую фигуру

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            points.append((x, y))  # Добавляем точку в список

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False

# Функция для проверки, является ли фигура замкнутой
def is_closed_figure(points, threshold=20):
    if len(points) < 3:
        return False  # Недостаточно точек для замкнутой фигуры
    # Проверяем, близки ли первая и последняя точки
    distance = np.sqrt((points[0][0] - points[-1][0])**2 + (points[0][1] - points[-1][1])**2)
    return distance < threshold

# Создание белого фона
width, height = 800, 600
canvas = np.ones((height, width, 3), dtype=np.uint8) * 255  # Белый фон

# Создание окна и привязка функции обработки событий мыши
cv2.namedWindow('Draw Circle')
cv2.setMouseCallback('Draw Circle', draw_circle)

while True:
    # Отображение текущего состояния холста
    display_canvas = canvas.copy()

    # Рисование круга пользователя
    if len(points) > 1:
        for i in range(1, len(points)):
            cv2.line(display_canvas, points[i - 1], points[i], (0, 255, 0), 2)

    # Если пользователь закончил рисовать
    if not drawing and len(points) > 0:
        # Проверяем, замкнута ли фигура
        if not is_closed_figure(points):
            cv2.putText(display_canvas, "Фигура не замкнута!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        else:
            # Находим контур нарисованной фигуры
            mask = np.zeros((height, width), dtype=np.uint8)
            for i in range(1, len(points)):
                cv2.line(mask, points[i - 1], points[i], 255, 2)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if len(contours) > 0:
                # Находим центр и средний радиус
                M = cv2.moments(contours[0])
                if M["m00"] != 0:
                    center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))  # Центр масс
                    distances = [np.sqrt((point[0] - center[0])**2 + (point[1] - center[1])**2) for point in points]
                    radius = int(np.mean(distances))  # Средний радиус

                    # Рисуем эталонный круг
                    reference_circle = (center, radius)
                    cv2.circle(display_canvas, center, radius, (255, 0, 0), 2)

                    # Сравнение нарисованного круга с эталонным
                    if reference_circle:
                        # Вычисляем отклонения
                        deviations = [abs(np.sqrt((point[0] - center[0])**2 + (point[1] - center[1])**2) - radius) for point in points]
                        rmse = np.sqrt(np.mean(np.square(deviations)))  # Среднеквадратичное отклонение
                        max_deviation = np.max(deviations)  # Максимальное отклонение

                        # Вывод результатов
                        cv2.putText(display_canvas, f"RMSE: {rmse:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                        cv2.putText(display_canvas, f"Max Dev: {max_deviation:.2f}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # Отображение холста
    cv2.imshow('Draw Circle', display_canvas)

    # Выход по нажатию клавиши 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Закрытие окна
cv2.destroyAllWindows()