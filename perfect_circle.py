import cv2 # на удивление в некоторых местах очень похоже на то что было с подводной камерой
import numpy as np

drawing = False  
points = []     
width = 800
height = 600 


canvas = np.ones((height, width, 3), dtype=np.uint8) * 255 
result_area = np.zeros((100, width, 3), dtype=np.uint8) 
result_area[:] = (70, 30, 70) 




def draw_circle(event, x, y, flags, param):
    global drawing, points

    if event == cv2.EVENT_LBUTTONDOWN:  
        if y < height - 100:  
            drawing = True
            points = []  

    elif event == cv2.EVENT_MOUSEMOVE:  
        if drawing and y < height - 10:  
            points.append((x, y))  

    elif event == cv2.EVENT_LBUTTONUP: 
        drawing = False  



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

# вычисление коэффициента
def calculate_circularity(contour):
    perimeter = cv2.arcLength(contour, True)
    area = cv2.contourArea(contour)
    if perimeter == 0:
        return 0
    circularity = (4 * np.pi * area) / (perimeter**2)
    return circularity  


#вычисление плавности контура
def calculate_smoothness(contour):
    perimeter = cv2.arcLength(contour, True)  
    approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)  
    return len(approx)  


cv2.namedWindow('Draw Circle')
cv2.setMouseCallback('Draw Circle', draw_circle)

while True:
    display_canvas = canvas.copy()

    
    if len(points) > 1:# Рисование
        for i in range(1, len(points)):
            cv2.line(display_canvas, points[i - 1], points[i], (0, 255, 0), 2)  # Зелёные линии

    
    if not drawing and len(points) > 0:
        result_area[:] = (70, 30, 70)  

        if not is_closed_figure(points):
            cv2.putText(result_area, "How dare you just scribble on me?", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        else:
            # Находим контур
            mask = np.zeros((height, width), dtype=np.uint8)
            for i in range(1, len(points)):
                cv2.line(mask, points[i - 1], points[i], 255, 2)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if len(contours) > 0:
                # эталонеее
                M = cv2.moments(contours[0])
                if M["m00"] != 0:
                    center_x = int(M["m10"] / M["m00"])
                    center_y = int(M["m01"] / M["m00"])
                    center = (center_x, center_y)  # Центр масс
                    distances = [np.sqrt((point[0] - center[0])**2 + (point[1] - center[1])**2) for point in points]
                    radius = int(np.mean(distances))  

                    cv2.circle(display_canvas, center, radius, (255, 0, 0), 2)

                    # маска пользователя
                    user_mask = np.zeros((height, width), dtype=np.uint8)
                    cv2.drawContours(user_mask, contours, -1, 255, -1)




                    reference_mask = np.zeros((height, width), dtype=np.uint8)
                    cv2.circle(reference_mask, center, radius, 255, -1)

                    # Объединяем маски пользователя и эталонного круга
                    combined_mask = cv2.bitwise_or(user_mask, reference_mask)#bitwise_or крутая тема спомощью этого я убрал противную серость 

                    # Создаем маски для отклонений
                    deviation_mask_red = np.zeros_like(display_canvas)  
                    deviation_mask_blue = np.zeros_like(display_canvas)  

                    for y in range(height):
                        for x in range(width):
                            if user_mask[y, x] == 255:  
                                dist = np.sqrt((x - center[0])**2 + (y - center[1])**2) - radius
                                if dist > 0:
                                    deviation_mask_red[y, x] = (0, 0, 255)  
                                elif dist < 0:
                                    deviation_mask_blue[y, x] = (255, 0, 0) 

                   
                    alpha = 0.3  
                    display_canvas = cv2.addWeighted(deviation_mask_red, alpha, display_canvas, 1 - alpha, 0)
                    display_canvas = cv2.addWeighted(deviation_mask_blue, alpha, display_canvas, 1 - alpha, 0)

                    # я так избавился от противной серости
                    background_mask = cv2.bitwise_not(combined_mask)
                    display_canvas[background_mask == 255] = (255, 255, 255)

                    # Вычисление метрик
                    deviations = [abs(np.sqrt((point[0] - center[0])**2 + (point[1] - center[1])**2) - radius) for point in points]
                    rmse = np.sqrt(np.mean(np.square(deviations)))  # Сред
                    max_deviation = np.max(deviations)  

                    # Отношение площадей
                    drawn_area = cv2.contourArea(contours[0])
                    ideal_area = np.pi * (radius**2)
                    area_ratio = drawn_area / ideal_area

                    # Circularity
                    circularity = calculate_circularity(contours[0])

                    # Плавность контура
                    smoothness = calculate_smoothness(contours[0])

                    cv2.putText(result_area, f"RMSE: {rmse:.2f}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (5, 5, 255), 1)
                    cv2.putText(result_area, f"Max Dev: {max_deviation:.2f}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (5, 55, 255), 1)
                    cv2.putText(result_area, f"Area Ratio: {area_ratio:.2f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (55, 105, 255), 1)
                    cv2.putText(result_area, f"Circularity: {circularity:.2f}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (105, 150, 255), 1)
                    cv2.putText(result_area, f"Smoothness: {smoothness}", (200, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (155, 205, 255), 1)

    combined_canvas = np.vstack((display_canvas, result_area))

    cv2.imshow('Draw Circle', combined_canvas)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()