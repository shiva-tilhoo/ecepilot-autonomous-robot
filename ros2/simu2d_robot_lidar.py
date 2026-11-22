#!/usr/bin/env python3
import pygame
import math
import socket
import pickle
import os

# --- CONFIGURATION ---
HOST, PORT = '127.0.0.1', 5005
WIDTH, HEIGHT = 800, 600
MAP_RESOLUTION = 0.0133 
LIDAR_RANGE_PX = int(3.3 / MAP_RESOLUTION)
CIRCUIT_IMAGE_PATH = "image_corridor_widened.png" 

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simu Lidar 50Hz - Arrow Mode")
clock = pygame.time.Clock()

# --- TRACK LOADING ---
if os.path.exists(CIRCUIT_IMAGE_PATH):
    circuit_surface = pygame.image.load(CIRCUIT_IMAGE_PATH).convert()
    circuit_surface = pygame.transform.scale(circuit_surface, (WIDTH, HEIGHT))
else:
    circuit_surface = pygame.Surface((WIDTH, HEIGHT))
    circuit_surface.fill((255, 255, 255))
    pygame.draw.rect(circuit_surface, (0, 0, 0), (50, 50, 700, 500), 5)

# --- SOCKET SERVER ---
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_sock.bind((HOST, PORT))
server_sock.listen(1)
server_sock.setblocking(False)

# --- ROBOT STATE ---
robot_pos = [300.0, 300.0]
robot_theta = 0.0
lidar_conn = None

def draw_robot_with_arrow(surface, pos, theta):
    """ Draws the robot (circle) and a heading arrow (triangle). """
    x, y = int(pos[0]), int(pos[1])
    radius = 12
    arrow_len = 15
    
    # 1. Draw the robot body
    pygame.draw.circle(surface, (0, 0, 255), (x, y), radius)
    
    # 2. Compute the points of the triangle (arrow)
    # Tip of the arrow (front)
    nose = (x + (radius + arrow_len) * math.cos(theta), 
            y + (radius + arrow_len) * math.sin(theta))
    
    # Points of the base of the triangle (rear left and right)
    left_wing = (x + radius * math.cos(theta + 2.5), 
                 y + radius * math.sin(theta + 2.5))
    right_wing = (x + radius * math.cos(theta - 2.5), 
                  y + radius * math.sin(theta - 2.5))
    
    # 3. Draw the triangle
    pygame.draw.polygon(surface, (0, 255, 0), [nose, left_wing, right_wing])

run = True
while run:
    if lidar_conn is None:
        try: lidar_conn, _ = server_sock.accept()
        except BlockingIOError: pass

    for event in pygame.event.get():
        if event.type == pygame.QUIT: run = False

    # --- CONTROLS ---
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:  robot_theta -= 0.02
    if keys[pygame.K_RIGHT]: robot_theta += 0.02
    if keys[pygame.K_UP]:
        robot_pos[0] += 0.5 * math.cos(robot_theta)
        robot_pos[1] += 0.5 * math.sin(robot_theta)
    if keys[pygame.K_DOWN]:
        robot_pos[0] -= 0.5 * math.cos(robot_theta)
        robot_pos[1] -= 0.5 * math.sin(robot_theta)

    # --- RENDU ---
    screen.blit(circuit_surface, (0, 0))
    
    # Lidar simulation (optimised)
    ranges = []
    for angle in range(0, 360, 2):
        rad = math.radians(angle) + robot_theta
        dist_m = 3.3
        for r in range(0, LIDAR_RANGE_PX, 4):
            tx, ty = int(robot_pos[0] + r*math.cos(rad)), int(robot_pos[1] + r*math.sin(rad))
            if 0 <= tx < WIDTH and 0 <= ty < HEIGHT:
                if circuit_surface.get_at((tx, ty))[0] < 100: 
                    dist_m = r * MAP_RESOLUTION
                    # Optional: uncomment to see the Lidar hits
                    # pygame.draw.circle(screen, (255, 0, 0), (tx, ty), 1) 
                    break
            else: break
        ranges.append(dist_m)

    # --- DRAW THE ROBOT AND ITS ARROW ---
    draw_robot_with_arrow(screen, robot_pos, robot_theta)

    pygame.display.flip()

    # --- SEND THE DATA ---
    if lidar_conn:
        try:
            packet = {'ranges': ranges, 'pose': (robot_pos[0], robot_pos[1], robot_theta)}
            lidar_conn.sendall(pickle.dumps(packet))
        except: lidar_conn = None

    clock.tick(50)

pygame.quit()