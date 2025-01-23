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
        # Проверяем, что клик был вне области результатов
        if y < height - 100:  # Область результатов начинается с высоты height - 100
            drawing = True
            points = []  # Начинаем новую фигуру

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing and y < height - 100:  # Рисуем только вне области результатов
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

# Функция для вычисления коэффициента формы (Circularity)
def calculate_circularity(contour):
    perimeter = cv2.arcLength(contour, True)
    area = cv2.contourArea(contour)
    if perimeter == 0:
        return 0
    return (4 * np.pi * area) / (perimeter**2)

# Функция для вычисления симметричности
def calculate_symmetry(contour, center):
    moments = cv2.moments(contour)
    if moments["m00"] == 0:
        return 0
    cx = int(moments["m10"] / moments["m00"])
    cy = int(moments["m01"] / moments["m00"])
    return np.sqrt((cx - center[0])**2 + (cy - center[1])**2)

# Функция для вычисления плавности контура
def calculate_smoothness(contour):
    perimeter = cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
    return len(approx)

# Создание белого фона
width, height = 800, 600
canvas = np.ones((height, width, 3), dtype=np.uint8) * 255  # Белый фон

# Область для вывода результатов (серый прямоугольник)
result_area = np.zeros((100, width, 3), dtype=np.uint8)
result_area[:] = (200, 200, 200)  # Серый цвет

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
            cv2.putText(result_area, "Фигура не замкнута!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
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

                    # Рисуем эталонный круг (синий)
                    cv2.circle(display_canvas, center, radius, (255, 0, 0), 2)

                    # Создаем маску для фигуры пользователя
                    user_mask = np.zeros((height, width), dtype=np.uint8)
                    cv2.drawContours(user_mask, contours, -1, 255, -1)  # Заливаем фигуру пользователя

                    # Создаем маски для отклонений
                    deviation_mask_red = np.zeros_like(display_canvas)  # Красный для внешних отклонений
                    deviation_mask_blue = np.zeros_like(display_canvas)  # Синий для внутренних отклонений

                    # Заполняем маски только внутри фигуры пользователя
                    for y in range(height):
                        for x in range(width):
                            if user_mask[y, x] == 255:  # Только внутри фигуры пользователя
                                dist = np.sqrt((x - center[0])**2 + (y - center[1])**2) - radius
                                if dist > 0:
                                    deviation_mask_red[y, x] = (0, 0, 255)  # Красный
                                elif dist < 0:
                                    deviation_mask_blue[y, x] = (255, 0, 0)  # Синий

                    # Наложение масок с прозрачностью
                    alpha = 0.3  # Прозрачность
                    display_canvas = cv2.addWeighted(deviation_mask_red, alpha, display_canvas, 1 - alpha, 0)
                    display_canvas = cv2.addWeighted(deviation_mask_blue, alpha, display_canvas, 1 - alpha, 0)

                    # Вычисление метрик
                    deviations = [abs(np.sqrt((point[0] - center[0])**2 + (point[1] - center[1])**2) - radius) for point in points]
                    rmse = np.sqrt(np.mean(np.square(deviations)))  # Среднеквадратичное отклонение
                    max_deviation = np.max(deviations)  # Максимальное отклонение

                    # Отношение площадей
                    drawn_area = cv2.contourArea(contours[0])
                    ideal_area = np.pi * (radius**2)
                    area_ratio = drawn_area / ideal_area

                    # Коэффициент формы (Circularity)
                    circularity = calculate_circularity(contours[0])

                    # Симметричность
                    symmetry = calculate_symmetry(contours[0], center)

                    # Плавность контура
                    smoothness = calculate_smoothness(contours[0])

                    # Вывод результатов
                    result_area[:] = (200, 200, 200)  # Очищаем область результатов
                    cv2.putText(result_area, f"RMSE: {rmse:.2f}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
                    cv2.putText(result_area, f"Max Dev: {max_deviation:.2f}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
                    cv2.putText(result_area, f"Area Ratio: {area_ratio:.2f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
                    cv2.putText(result_area, f"Circularity: {circularity:.2f}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
                    cv2.putText(result_area, f"Symmetry: {symmetry:.2f}", (300, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
                    cv2.putText(result_area, f"Smoothness: {smoothness}", (300, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)

    # Объединяем холст и область результатов
    combined_canvas = np.vstack((display_canvas, result_area))

    # Отображение холста
    cv2.imshow('Draw Circle', combined_canvas)

    # Выход по нажатию клавиши 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Закрытие окна
cv2.destroyAllWindows()