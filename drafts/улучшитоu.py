import cv2
import numpy as np


drawing = False
points = []

# Размеры холста
width = 800
height = 600

# Создание белого холста
canvas = np.ones((height, width, 3), dtype=np.uint8) * 255

# Область для вывода результатов
result_area = np.zeros((100, width, 3), dtype=np.uint8)
result_area[:, :] = (70, 30, 70) 


def draw_circle(event, x, y, flags, param):
    global drawing, points

    
    if event == cv2.EVENT_LBUTTONDOWN:
    
        if y < height - 100:
            drawing = True
            points = [] 

    elif event == cv2.EVENT_MOUSEMOVE:
       
        if drawing and y < height - 10:
            points.append((x, y)) 

    # Если отпущена левая кнопка мыши
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False  

# Функция для проверки, замкнута ли фигура
def is_closed_figure(points):
    if len(points) < 20:
        return False

    # расстояние
    first_point = points[0]
    last_point = points[-1]
    distance = np.sqrt((first_point[0] - last_point[0])**2 + (first_point[1] - last_point[1])**2)

    if distance < 20:
        return True
    else:
        return False

# Функция для вычисления коэффициента округлости
def calculate_circularity(contour):
    perimeter = cv2.arcLength(contour, True)
    area = cv2.contourArea(contour)
    if perimeter == 0:
        return 0
    # Формула округлости
    circularity = (4 * np.pi * area) / (perimeter**2)
    return circularity

# Функция для вычисления плавности контура
def calculate_smoothness(contour):
    perimeter = cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)#апроксимация кстати была в лекциях

    # Возвращаем количество вершин аппроксимированного контура
    return len(approx)


cv2.namedWindow('Draw Circle')
cv2.setMouseCallback('Draw Circle', draw_circle)

# Основной цикл
while True:
    display_canvas = canvas.copy()
    if len(points) > 1:
        for i in range(1, len(points)):
            cv2.line(display_canvas, points[i - 1], points[i], (0, 255, 0), 2)

    # Если рисование завершено
    if not drawing and len(points) > 0:
        result_area[:, :] = (70, 30, 70)

        # Проверка
        if not is_closed_figure(points):
            # Если фигура не замкнута, выводим сообщение
            cv2.putText(result_area, "How dare you just scribble on me?", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        else:
            # Создаём маску для фигуры
            mask = np.zeros((height, width), dtype=np.uint8)

            # Рисуем линии на маске
            for i in range(1, len(points)):
                cv2.line(mask, points[i - 1], points[i], 255, 2)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if len(contours) > 0:
                # Вычисляем моменты контура
                M = cv2.moments(contours[0])

                if M["m00"] != 0:
                    # Находим центр масс
                    center_x = int(M["m10"] / M["m00"])
                    center_y = int(M["m01"] / M["m00"])
                    center = (center_x, center_y)

                    # Вычисляем средний радиус
                    distances = []
                    for point in points:
                        dx = point[0] - center_x
                        dy = point[1] - center_y
                        distance = np.sqrt(dx**2 + dy**2)
                        distances.append(distance)
                    radius = int(np.mean(distances))

                    # Рисуем эталонный круг
                    cv2.circle(display_canvas, center, radius, (255, 0, 0), 2)

                    # Создаём маску для фигуры пользователя
                    user_mask = np.zeros((height, width), dtype=np.uint8)
                    cv2.drawContours(user_mask, contours, -1, 255, -1)

                    # Создаём маску для эталонного круга
                    reference_mask = np.zeros((height, width), dtype=np.uint8)
                    cv2.circle(reference_mask, center, radius, 255, -1)

                    # Создаём маски для отклонений
                    deviation_mask_red = np.zeros((height, width, 3), dtype=np.uint8)  # Для положительных отклонений
                    deviation_mask_blue = np.zeros((height, width, 3), dtype=np.uint8)  # Для отрицательных отклонений

                    # Заполняем маски отклонений
                    for y in range(height):
                        for x in range(width):
                            if user_mask[y, x] == 255:  # Если точка принадлежит фигуре пользователя
                                dx = x - center_x
                                dy = y - center_y
                                dist = np.sqrt(dx**2 + dy**2) - radius

                                if dist > 0:
                                    deviation_mask_red[y, x] = (0, 0, 255)  # Красный для положительных отклонений
                                elif dist < 0:
                                    deviation_mask_blue[y, x] = (255, 0, 0)  # Синий для отрицательных отклонений

                    # Наложение масок отклонений на холст
                    alpha = 0.3  # Прозрачность
                    for y in range(height):
                        for x in range(width):
                            for c in range(3):
                                display_canvas[y, x, c] = (1 - alpha) * display_canvas[y, x, c] + alpha * deviation_mask_red[y, x, c]
                                display_canvas[y, x, c] = (1 - alpha) * display_canvas[y, x, c] + alpha * deviation_mask_blue[y, x, c]

                    # Заливаем фон белым цветом
                    for y in range(height):
                        for x in range(width):
                            if user_mask[y, x] == 0 and reference_mask[y, x] == 0:
                                display_canvas[y, x] = (255, 255, 255)

                    # Вычисляем метрики
                    deviations = []
                    for point in points:
                        dx = point[0] - center_x
                        dy = point[1] - center_y
                        dist = np.sqrt(dx**2 + dy**2) - radius
                        deviations.append(abs(dist))

                    # Среднеквадратичное отклонение
                    rmse = np.sqrt(np.mean(np.square(deviations)))

                    # Максимальное отклонение
                    max_deviation = np.max(deviations)

                    # Площадь фигуры пользователя
                    drawn_area = cv2.contourArea(contours[0])

                    # Площадь эталонного круга
                    ideal_area = np.pi * (radius**2)

                    # Отношение площадей
                    area_ratio = drawn_area / ideal_area

                    # Округлость
                    circularity = calculate_circularity(contours[0])

                    # Плавность
                    smoothness = calculate_smoothness(contours[0])

                    # Выводим метрики на область результатов
                    cv2.putText(result_area, f"RMSE: {rmse:.2f}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (5, 5, 255), 1)
                    cv2.putText(result_area, f"Max Dev: {max_deviation:.2f}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (5, 55, 255), 1)
                    cv2.putText(result_area, f"Area Ratio: {area_ratio:.2f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (55, 105, 255), 1)
                    cv2.putText(result_area, f"Circularity: {circularity:.2f}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (105, 150, 255), 1)
                    cv2.putText(result_area, f"Smoothness: {smoothness}", (200, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (155, 205, 255), 1)

    # Объединяем холст и область результатов
    combined_canvas = np.vstack((display_canvas, result_area))

    # Отображаем результат
    cv2.imshow('Draw Circle', combined_canvas)

    # Выход по нажатию клавиши 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Закрываем окно
cv2.destroyAllWindows()