import cv2
import numpy as np

drawing = False  # Флаг для рисования (типа "рисуем или нет")
points = []      # Точки, которые нарисовал пользователь (ну, куда ж без них)
width, height = 800, 600  # Размеры холста
canvas = np.ones((height, width, 3), dtype=np.uint8) * 255  # Белый фон (ну, типа "чистота")
result_area = np.zeros((100, width, 3), dtype=np.uint8)  # Область для вывода результатов
result_area[:] = (70, 30, 70)  # Серый цвет (ну, типа "стильно")

# Функция для обработки событий мыши (типа "ловит клики и движения")
def draw_circle(event, x, y, flags, param):
    global drawing, points

    if event == cv2.EVENT_LBUTTONDOWN:  # ЕСЛИ НАЖАЛИ ЛЕВУЮ КНОПКУ МЫШИ
        if y < height - 100:  # Проверяем, что клик был не в области результатов (а то че за фигня)
            drawing = True  # Начинаем рисовать
            points = []  # Очищаем старые точки (типа "новый круг, новые точки")

    elif event == cv2.EVENT_MOUSEMOVE:  # ЕСЛИ МЫШКА ДВИГАЕТСЯ
        if drawing and y < height - 10:  # Рисуем только вне области результатов (а то опять фигня)
            points.append((x, y))  # Добавляем точку в список (типа "рисуем линию")

    elif event == cv2.EVENT_LBUTTONUP:  # ЕСЛИ ОТПУСТИЛИ ЛЕВУЮ КНОПКУ МЫШИ
        drawing = False  # Закончили рисовать (типа "всё, хватит")

# Функция для проверки, замкнута ли фигура (типа "круг или не круг")
def is_closed_figure(points):
    if len(points) < 20:  # Если точек мало, то это не круг (ну, логично)
        return False
    # Проверяем, близки ли первая и последняя точки (типа "замкнутость")
    distance = np.sqrt((points[0][0] - points[-1][0])**2 + (points[0][1] - points[-1][1])**2)
    return distance < 20  # Если расстояние меньше порога, то круг замкнут

# Функция для вычисления коэффициента формы (типа "насколько круглый")
def calculate_circularity(contour):
    perimeter = cv2.arcLength(contour, True)  # Длина периметра
    area = cv2.contourArea(contour)  # Площадь
    if perimeter == 0:  # Если периметр нулевой, то это не круг (ну, очевидно)
        return 0
    return (4 * np.pi * area) / (perimeter**2)  # Формула для круглости

# Функция для вычисления плавности контура (типа "насколько гладкий")
def calculate_smoothness(contour):
    perimeter = cv2.arcLength(contour, True)  # Длина периметра
    approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)  # Аппроксимация контура
    return len(approx)  # Чем меньше точек, тем глаже

# ОСНОВНОЙ ЦИКЛ (ТИПА "БЕСКОНЕЧНЫЙ ЦИКЛ, ПОКА НЕ НАЖМЕШЬ 'q'")
cv2.namedWindow('Draw Circle')
cv2.setMouseCallback('Draw Circle', draw_circle)

while True:
    display_canvas = canvas.copy()

    # Рисование круга пользователя (типа "зелёные линии")
    if len(points) > 1:
        for i in range(1, len(points)):
            cv2.line(display_canvas, points[i - 1], points[i], (0, 255, 0), 2)  # Зелёные линии

    # Если пользователь закончил рисовать (типа "отпустил кнопку мыши")
    if not drawing and len(points) > 0:
        result_area[:] = (70, 30, 70)  # Очищаем область результатов

        if not is_closed_figure(points):
            cv2.putText(result_area, "Фигура не замкнута!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        else:
            # Находим контур нарисованной фигуры (типа "ищем границы")
            mask = np.zeros((height, width), dtype=np.uint8)
            for i in range(1, len(points)):
                cv2.line(mask, points[i - 1], points[i], 255, 2)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if len(contours) > 0:
                # Находим центр и средний радиус (типа "идеальный круг")
                M = cv2.moments(contours[0])
                if M["m00"] != 0:
                    center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))  # Центр масс
                    distances = [np.sqrt((point[0] - center[0])**2 + (point[1] - center[1])**2) for point in points]
                    radius = int(np.mean(distances))  # Средний радиус

                    # Рисуем эталонный круг (синий) (типа "идеал")
                    cv2.circle(display_canvas, center, radius, (255, 0, 0), 2)

                    # Создаем маску для фигуры пользователя (типа "заливка")
                    user_mask = np.zeros((height, width), dtype=np.uint8)
                    cv2.drawContours(user_mask, contours, -1, 255, -1)

                    # Создаем маску для эталонного круга (типа "заливка идеала")
                    reference_mask = np.zeros((height, width), dtype=np.uint8)
                    cv2.circle(reference_mask, center, radius, 255, -1)

                    # Объединяем маски пользователя и эталонного круга (типа "сравнение")
                    combined_mask = cv2.bitwise_or(user_mask, reference_mask)

                    # Создаем маски для отклонений (типа "красный и синий")
                    deviation_mask_red = np.zeros_like(display_canvas)  # Красный для внешних отклонений
                    deviation_mask_blue = np.zeros_like(display_canvas)  # Синий для внутренних отклонений

                    # Заполняем маски только внутри фигуры пользователя (типа "сравнение")
                    for y in range(height):
                        for x in range(width):
                            if user_mask[y, x] == 255:  # Только внутри фигуры пользователя
                                dist = np.sqrt((x - center[0])**2 + (y - center[1])**2) - radius
                                if dist > 0:
                                    deviation_mask_red[y, x] = (0, 0, 255)  # Красный
                                elif dist < 0:
                                    deviation_mask_blue[y, x] = (255, 0, 0)  # Синий

                    # Наложение масок с прозрачностью (типа "красиво")
                    alpha = 0.3  # Прозрачность
                    display_canvas = cv2.addWeighted(deviation_mask_red, alpha, display_canvas, 1 - alpha, 0)
                    display_canvas = cv2.addWeighted(deviation_mask_blue, alpha, display_canvas, 1 - alpha, 0)

                    # Заливаем фон белым цветом вокруг обоих кругов (типа "чистота")
                    background_mask = cv2.bitwise_not(combined_mask)
                    display_canvas[background_mask == 255] = (255, 255, 255)

                    # Вычисление метрик (типа "насколько хорошо")
                    deviations = [abs(np.sqrt((point[0] - center[0])**2 + (point[1] - center[1])**2) - radius) for point in points]
                    rmse = np.sqrt(np.mean(np.square(deviations)))  # Среднеквадратичное отклонение
                    max_deviation = np.max(deviations)  # Максимальное отклонение

                    # Отношение площадей (типа "насколько большой")
                    drawn_area = cv2.contourArea(contours[0])
                    ideal_area = np.pi * (radius**2)
                    area_ratio = drawn_area / ideal_area

                    # Коэффициент формы (Circularity) (типа "насколько круглый")
                    circularity = calculate_circularity(contours[0])

                    # Плавность контура (типа "насколько гладкий")
                    smoothness = calculate_smoothness(contours[0])

                    # Вывод результатов (типа "показываем, что получилось")
                    cv2.putText(result_area, f"RMSE: {rmse:.2f}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (5, 5, 255), 1)
                    cv2.putText(result_area, f"Max Dev: {max_deviation:.2f}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (5, 55, 255), 1)
                    cv2.putText(result_area, f"Area Ratio: {area_ratio:.2f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (55, 105, 255), 1)
                    cv2.putText(result_area, f"Circularity: {circularity:.2f}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (105, 150, 255), 1)
                    cv2.putText(result_area, f"Smoothness: {smoothness}", (200, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (155, 205, 255), 1)

    # Объединяем холст и область результатов (типа "финальное изображение")
    combined_canvas = np.vstack((display_canvas, result_area))

    # Отображение холста (типа "показываем пользователю")
    cv2.imshow('Draw Circle', combined_canvas)

    # Выход по нажатию клавиши 'q' (типа "закрыть программу")
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Закрытие окна (типа "всё, конец")
cv2.destroyAllWindows()