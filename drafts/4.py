# Импортируем библиотеки
import cv2  # Это для работы с картинками
import numpy as np  # Это для математики

# Глобальные переменные (я пока не знаю, как лучше сделать)
drawing = False  # Рисуем или нет
points = []  # Тут будут точки, которые нарисовал пользователь
reference_circle = None  # Это будет эталонный круг

# Функция для мышки
def draw_circle(event, x, y, flags, param):
    global drawing, points  # Глобальные переменные, потому что я пока не знаю, как иначе

    # Если нажали левую кнопку мыши
    if event == cv2.EVENT_LBUTTONDOWN:
        # Проверяем, что кликнули не в области результатов
        if y < height - 100:  # Область результатов внизу
            drawing = True  # Начинаем рисовать
            points = []  # Очищаем старые точки

    # Если двигаем мышку
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing and y < height - 100:  # Рисуем только вне области результатов
            points.append((x, y))  # Добавляем точку в список

    # Если отпустили кнопку мыши
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False  # Перестаем рисовать

# Функция для проверки, замкнута ли фигура
def is_closed_figure(points, threshold=20):
    if len(points) < 3:  # Если точек меньше 3, фигура не замкнута
        return False
    # Считаем расстояние между первой и последней точкой
    first_point = points[0]
    last_point = points[-1]
    distance = np.sqrt((first_point[0] - last_point[0])**2 + (first_point[1] - last_point[1])**2)
    return distance < threshold  # Если расстояние маленькое, фигура замкнута

# Функция для вычисления "круглости" фигуры
def calculate_circularity(contour):
    perimeter = cv2.arcLength(contour, True)  # Длина периметра
    area = cv2.contourArea(contour)  # Площадь
    if perimeter == 0:  # Чтобы не делить на ноль
        return 0
    return (4 * np.pi * area) / (perimeter**2)  # Формула для круглости

# Функция для вычисления симметричности
def calculate_symmetry(contour, center):
    moments = cv2.moments(contour)  # Моменты фигуры
    if moments["m00"] == 0:  # Чтобы не делить на ноль
        return 0
    # Центр масс фигуры
    cx = int(moments["m10"] / moments["m00"])
    cy = int(moments["m01"] / moments["m00"])
    # Расстояние между центром масс и центром эталонного круга
    return np.sqrt((cx - center[0])**2 + (cy - center[1])**2)

# Функция для вычисления плавности контура
def calculate_smoothness(contour):
    perimeter = cv2.arcLength(contour, True)  # Длина периметра
    # Аппроксимация контура (упрощение)
    approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
    return len(approx)  # Количество точек в упрощенном контуре

# Размеры холста
width, height = 800, 600

# Создаем белый холст
canvas = np.ones((height, width, 3), dtype=np.uint8) * 255  # Белый фон

# Область для вывода результатов (серая)
result_area = np.zeros((100, width, 3), dtype=np.uint8)
result_area[:] = (200, 200, 200)  # Заливаем серым

# Создаем окно и привязываем функцию для мышки
cv2.namedWindow('Draw Circle')
cv2.setMouseCallback('Draw Circle', draw_circle)

# Основной цикл
while True:
    # Копируем холст, чтобы не портить оригинал
    display_canvas = canvas.copy()

    # Рисуем линии между точками, которые нарисовал пользователь
    if len(points) > 1:
        for i in range(1, len(points)):
            cv2.line(display_canvas, points[i - 1], points[i], (0, 255, 0), 2)

    # Если пользователь закончил рисовать
    if not drawing and len(points) > 0:
        # Очищаем область результатов
        result_area[:] = (200, 200, 200)

        # Проверяем, замкнута ли фигура
        if not is_closed_figure(points):
            cv2.putText(result_area, "Фигура не замкнута!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        else:
            # Создаем маску для фигуры пользователя
            mask = np.zeros((height, width), dtype=np.uint8)
            for i in range(1, len(points)):
                cv2.line(mask, points[i - 1], points[i], 255, 2)

            # Находим контуры
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if len(contours) > 0:
                # Вычисляем моменты для нахождения центра
                M = cv2.moments(contours[0])
                if M["m00"] != 0:
                    # Центр масс фигуры
                    center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                    # Вычисляем средний радиус
                    distances = [np.sqrt((point[0] - center[0])**2 + (point[1] - center[1])**2) for point in points]
                    radius = int(np.mean(distances))

                    # Рисуем эталонный круг
                    cv2.circle(display_canvas, center, radius, (255, 0, 0), 2)

                    # Создаем маску для фигуры пользователя
                    user_mask = np.zeros((height, width), dtype=np.uint8)
                    cv2.drawContours(user_mask, contours, -1, 255, -1)

                    # Создаем маску для эталонного круга
                    reference_mask = np.zeros((height, width), dtype=np.uint8)
                    cv2.circle(reference_mask, center, radius, 255, -1)

                    # Объединяем маски
                    combined_mask = cv2.bitwise_or(user_mask, reference_mask)

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

                    # Заливаем фон белым
                    background_mask = cv2.bitwise_not(combined_mask)
                    display_canvas[background_mask == 255] = (255, 255, 255)

                    # Вычисляем метрики
                    deviations = [abs(np.sqrt((point[0] - center[0])**2 + (point[1] - center[1])**2) - radius) for point in points]
                    rmse = np.sqrt(np.mean(np.square(deviations)))  # Среднеквадратичное отклонение
                    max_deviation = np.max(deviations)  # Максимальное отклонение
                    drawn_area = cv2.contourArea(contours[0])  # Площадь фигуры
                    ideal_area = np.pi * (radius**2)  # Площадь эталонного круга
                    area_ratio = drawn_area / ideal_area  # Отношение площадей
                    circularity = calculate_circularity(contours[0])  # Круглость
                    symmetry = calculate_symmetry(contours[0], center)  # Симметричность
                    smoothness = calculate_smoothness(contours[0])  # Плавность

                    # Выводим статистику
                    cv2.putText(result_area, f"RMSE: {rmse:.2f}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
                    cv2.putText(result_area, f"Max Dev: {max_deviation:.2f}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
                    cv2.putText(result_area, f"Area Ratio: {area_ratio:.2f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
                    cv2.putText(result_area, f"Circularity: {circularity:.2f}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
                    cv2.putText(result_area, f"Symmetry: {symmetry:.2f}", (300, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
                    cv2.putText(result_area, f"Smoothness: {smoothness}", (300, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)

    # Объединяем холст и область результатов
    combined_canvas = np.vstack((display_canvas, result_area))

    # Показываем результат
    cv2.imshow('Draw Circle', combined_canvas)

    # Выход по нажатию 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Закрываем окно
cv2.destroyAllWindows()