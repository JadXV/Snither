import os
import random
import time
import math
import sys
import tty
import termios
import select
from collections import deque

class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    DIM = '\033[2m'
    BG_GREEN = '\033[42m'
    BG_BLUE = '\033[44m'

WIDTH = 32
HEIGHT = 16
SNAKE_HEAD = '●'
SNAKE_BODY = '○'
AI_HEAD = '◆'
AI_BODY = '◇'
AI2_HEAD = '■'
AI2_BODY = '□'
FOOD = '★'
EMPTY = ' '
BORDER_H = '─'
BORDER_V = '│'
CORNER_TL = '┌'
CORNER_TR = '┐'
CORNER_BL = '└'
CORNER_BR = '┘'

def get_key_non_blocking():
    if select.select([sys.stdin], [], [], 0)[0]:
        return sys.stdin.read(1)
    return None

def init_board():
    board = [[EMPTY for _ in range(WIDTH)] for _ in range(HEIGHT)]
    for i in range(WIDTH):
        board[0][i] = BORDER_H
        board[HEIGHT-1][i] = BORDER_H
    for i in range(HEIGHT):
        board[i][0] = BORDER_V
        board[i][WIDTH-1] = BORDER_V
    board[0][0] = CORNER_TL
    board[0][WIDTH-1] = CORNER_TR
    board[HEIGHT-1][0] = CORNER_BL
    board[HEIGHT-1][WIDTH-1] = CORNER_BR
    return board

def is_border(cell):
    return cell in [BORDER_H, BORDER_V, CORNER_TL, CORNER_TR, CORNER_BL, CORNER_BR]

def print_board(board):
    os.system('cls' if os.name == 'nt' else 'clear')
    for row in board:
        line = ''
        for cell in row:
            if cell == SNAKE_HEAD:
                line += f'{Colors.GREEN}{Colors.BOLD}{cell}{Colors.RESET}'
            elif cell == SNAKE_BODY:
                line += f'{Colors.GREEN}{cell}{Colors.RESET}'
            elif cell == AI_HEAD:
                line += f'{Colors.BLUE}{Colors.BOLD}{cell}{Colors.RESET}'
            elif cell == AI_BODY:
                line += f'{Colors.CYAN}{cell}{Colors.RESET}'
            elif cell == AI2_HEAD:
                line += f'{Colors.MAGENTA}{Colors.BOLD}{cell}{Colors.RESET}'
            elif cell == AI2_BODY:
                line += f'{Colors.MAGENTA}{cell}{Colors.RESET}'
            elif cell == FOOD:
                line += f'{Colors.RED}{cell}{Colors.RESET}'
            elif is_border(cell):
                line += f'{Colors.DIM}{cell}{Colors.RESET}'
            else:
                line += cell
        print(line)

def place_food(board):
    while True:
        x = random.randint(2, WIDTH-3)
        y = random.randint(2, HEIGHT-3)
        if board[y][x] == EMPTY:
            board[y][x] = FOOD
            break

def is_opposite_direction(current_direction, new_direction):
    opposite_directions = {
        'w': 's',
        's': 'w',
        'a': 'd',
        'd': 'a'
    }
    return opposite_directions.get(current_direction) == new_direction

def get_best_direction(snake, food, current_direction, board):
    head_y, head_x = snake[0]
    food_y, food_x = food

    directions = ['w', 's', 'a', 'd']
    best_direction = None
    best_score = -float('inf')

    for direction in directions:
        if is_opposite_direction(current_direction, direction):
            continue

        if direction == 'w':
            new_head_y, new_head_x = head_y - 1, head_x
        elif direction == 's':
            new_head_y, new_head_x = head_y + 1, head_x
        elif direction == 'a':
            new_head_y, new_head_x = head_y, head_x - 1
        elif direction == 'd':
            new_head_y, new_head_x = head_y, head_x + 1

        if not is_safe_move(snake, (new_head_y, new_head_x), board):
            continue

        distance_to_food = math.sqrt((food_y - new_head_y) ** 2 + (food_x - new_head_x) ** 2)

        score = -distance_to_food

        if is_trapped_after_move(snake, (new_head_y, new_head_x), board):
            score -= 10

        if score > best_score:
            best_score = score
            best_direction = direction

    return best_direction

def is_safe_move(snake, new_head, board):
    head_y, head_x = new_head

    if head_y < 0 or head_y >= HEIGHT or head_x < 0 or head_x >= WIDTH or (head_y, head_x) in snake:
        return False

    if is_border(board[head_y][head_x]):
        return False

    return True

def is_trapped_after_move(snake, new_head, board):
    new_snake = deque(snake)
    new_snake.appendleft(new_head)

    possible_moves = ['w', 's', 'a', 'd']
    safe_moves = 0

    for direction in possible_moves:
        if direction == 'w':
            test_y, test_x = new_head[0] - 1, new_head[1]
        elif direction == 's':
            test_y, test_x = new_head[0] + 1, new_head[1]
        elif direction == 'a':
            test_y, test_x = new_head[0], new_head[1] - 1
        elif direction == 'd':
            test_y, test_x = new_head[0], new_head[1] + 1

        if is_safe_move(new_snake, (test_y, test_x), board):
            safe_moves += 1
    
    return safe_moves == 0

def is_safe_move_versus(snake, other_snake, new_head, board):
    head_y, head_x = new_head
    if head_y < 0 or head_y >= HEIGHT or head_x < 0 or head_x >= WIDTH:
        return False
    if (head_y, head_x) in snake or (head_y, head_x) in other_snake:
        return False
    if is_border(board[head_y][head_x]):
        return False
    return True

def get_best_direction_versus(snake, other_snake, food, current_direction, board):
    head_y, head_x = snake[0]
    if food is None:
        return current_direction
    food_y, food_x = food

    directions = ['w', 's', 'a', 'd']
    best_direction = None
    best_score = -float('inf')

    for direction in directions:
        if is_opposite_direction(current_direction, direction):
            continue

        if direction == 'w':
            new_head_y, new_head_x = head_y - 1, head_x
        elif direction == 's':
            new_head_y, new_head_x = head_y + 1, head_x
        elif direction == 'a':
            new_head_y, new_head_x = head_y, head_x - 1
        elif direction == 'd':
            new_head_y, new_head_x = head_y, head_x + 1

        if not is_safe_move_versus(snake, other_snake, (new_head_y, new_head_x), board):
            continue

        distance_to_food = math.sqrt((food_y - new_head_y) ** 2 + (food_x - new_head_x) ** 2)
        score = -distance_to_food

        if score > best_score:
            best_score = score
            best_direction = direction

    return best_direction

def versus_mode():
    board = init_board()
    
    player_snake = [(HEIGHT//2, WIDTH//4)]
    player_dir = 'd'
    
    ai_snake = [(HEIGHT//4, 3*WIDTH//4)]
    ai_dir = 'a'
    
    ai2_snake = [(3*HEIGHT//4, 3*WIDTH//4)]
    ai2_dir = 'a'
    
    board[player_snake[0][0]][player_snake[0][1]] = SNAKE_HEAD
    board[ai_snake[0][0]][ai_snake[0][1]] = AI_HEAD
    board[ai2_snake[0][0]][ai2_snake[0][1]] = AI2_HEAD
    
    for _ in range(4):
        place_food(board)
    
    print_board(board)
    print(f" {Colors.MAGENTA}Slither.io Mode{Colors.RESET} - Last snake alive wins! {Colors.YELLOW}WASD{Colors.RESET}=move {Colors.RED}Q{Colors.RESET}=quit")
    
    old_settings = termios.tcgetattr(sys.stdin)
    player_alive = True
    ai_alive = True
    ai2_alive = True
    
    try:
        tty.setcbreak(sys.stdin.fileno())
        
        while player_alive and (ai_alive or ai2_alive):
            time.sleep(0.15)
            
            key = get_key_non_blocking()
            while key:
                key = key.lower()
                if key == 'q':
                    print("\nQuitting...")
                    return
                if key in ['w', 'a', 's', 'd']:
                    if not is_opposite_direction(player_dir, key):
                        player_dir = key
                key = get_key_non_blocking()
            
            other_snakes = player_snake + (ai2_snake if ai2_alive else [])
            ai_food = get_closest_food(ai_snake, board)
            if ai_food and ai_alive:
                new_ai_dir = get_best_direction_versus(ai_snake, other_snakes, ai_food, ai_dir, board)
                if new_ai_dir:
                    ai_dir = new_ai_dir
            
            other_snakes2 = player_snake + (ai_snake if ai_alive else [])
            if ai_food and ai_alive:
                ai2_food = get_closest_food_excluding(ai2_snake, board, ai_food)
            else:
                ai2_food = get_closest_food(ai2_snake, board)
            if ai2_food and ai2_alive:
                new_ai2_dir = get_best_direction_versus(ai2_snake, other_snakes2, ai2_food, ai2_dir, board)
                if new_ai2_dir:
                    ai2_dir = new_ai2_dir
            
            p_head_y, p_head_x = player_snake[0]
            if player_dir == 'w':
                p_head_y -= 1
            elif player_dir == 's':
                p_head_y += 1
            elif player_dir == 'a':
                p_head_x -= 1
            elif player_dir == 'd':
                p_head_x += 1
            
            a_head_y, a_head_x = ai_snake[0]
            if ai_alive:
                if ai_dir == 'w':
                    a_head_y -= 1
                elif ai_dir == 's':
                    a_head_y += 1
                elif ai_dir == 'a':
                    a_head_x -= 1
                elif ai_dir == 'd':
                    a_head_x += 1
            
            a2_head_y, a2_head_x = ai2_snake[0]
            if ai2_alive:
                if ai2_dir == 'w':
                    a2_head_y -= 1
                elif ai2_dir == 's':
                    a2_head_y += 1
                elif ai2_dir == 'a':
                    a2_head_x -= 1
                elif ai2_dir == 'd':
                    a2_head_x += 1
            
            p_new_head = (p_head_y, p_head_x)
            a_new_head = (a_head_y, a_head_x)
            a2_new_head = (a2_head_y, a2_head_x)
            
            player_body = list(player_snake[1:])
            ai_body = list(ai_snake[1:]) if ai_alive else []
            ai2_body = list(ai2_snake[1:]) if ai2_alive else []
            
            player_obstacles = ai_body + ai2_body
            ai_obstacles = player_body + ai2_body
            ai2_obstacles = player_body + ai_body
            
            if is_border(board[p_head_y][p_head_x]) or p_new_head in player_body or p_new_head in player_obstacles:
                player_alive = False
            if ai_alive and (is_border(board[a_head_y][a_head_x]) or a_new_head in ai_snake[1:] or a_new_head in ai_obstacles):
                ai_alive = False
            if ai2_alive and (is_border(board[a2_head_y][a2_head_x]) or a2_new_head in ai2_snake[1:] or a2_new_head in ai2_obstacles):
                ai2_alive = False
            
            if p_new_head == a_new_head and ai_alive:
                player_alive = False
                ai_alive = False
            if p_new_head == a2_new_head and ai2_alive:
                player_alive = False
                ai2_alive = False
            if a_new_head == a2_new_head and ai_alive and ai2_alive:
                ai_alive = False
                ai2_alive = False
            
            if not player_alive:
                break
            
            player_ate = board[p_head_y][p_head_x] == FOOD
            ai_ate = ai_alive and board[a_head_y][a_head_x] == FOOD
            ai2_ate = ai2_alive and board[a2_head_y][a2_head_x] == FOOD
            
            if not player_ate:
                tail_y, tail_x = player_snake.pop()
                board[tail_y][tail_x] = EMPTY
            
            if ai_alive and not ai_ate:
                tail_y, tail_x = ai_snake.pop()
                board[tail_y][tail_x] = EMPTY
            
            if ai2_alive and not ai2_ate:
                tail_y, tail_x = ai2_snake.pop()
                board[tail_y][tail_x] = EMPTY
            
            player_snake.insert(0, (p_head_y, p_head_x))
            if ai_alive:
                ai_snake.insert(0, (a_head_y, a_head_x))
            if ai2_alive:
                ai2_snake.insert(0, (a2_head_y, a2_head_x))
            
            food_count = sum(row.count(FOOD) for row in board)
            if player_ate:
                food_count -= 1
            if ai_ate:
                food_count -= 1
            if ai2_ate:
                food_count -= 1
            while food_count < 4:
                place_food(board)
                food_count += 1
            
            for y in range(1, HEIGHT-1):
                for x in range(1, WIDTH-1):
                    if board[y][x] != FOOD and not is_border(board[y][x]):
                        board[y][x] = EMPTY
            
            board[player_snake[0][0]][player_snake[0][1]] = SNAKE_HEAD
            for y, x in player_snake[1:]:
                board[y][x] = SNAKE_BODY
            
            if ai_alive:
                board[ai_snake[0][0]][ai_snake[0][1]] = AI_HEAD
                for y, x in ai_snake[1:]:
                    board[y][x] = AI_BODY
            
            if ai2_alive:
                board[ai2_snake[0][0]][ai2_snake[0][1]] = AI2_HEAD
                for y, x in ai2_snake[1:]:
                    board[y][x] = AI2_BODY
            
            print_board(board)
            ai1_status = f"{Colors.BLUE}AI1:{Colors.BOLD}{len(ai_snake):2}{Colors.RESET}" if ai_alive else f"{Colors.DIM}AI1:XX{Colors.RESET}"
            ai2_status = f"{Colors.MAGENTA}AI2:{Colors.BOLD}{len(ai2_snake):2}{Colors.RESET}" if ai2_alive else f"{Colors.DIM}AI2:XX{Colors.RESET}"
            print(f" {Colors.GREEN}You:{Colors.BOLD}{len(player_snake):2}{Colors.RESET} | {ai1_status} | {ai2_status} | Last alive wins!")
        
        print()
        print(f"{Colors.DIM}{'─'*36}{Colors.RESET}")
        if not player_alive:
            if ai_alive or ai2_alive:
                print(f"{Colors.RED}{Colors.BOLD}  YOU DIED! AI wins!{Colors.RESET}")
            else:
                print(f"{Colors.YELLOW}{Colors.BOLD}  DRAW! Everyone crashed!{Colors.RESET}")
        else:
            print(f"{Colors.GREEN}{Colors.BOLD}  YOU WIN! Last one standing!{Colors.RESET}")
        print(f"{Colors.DIM}{'─'*36}{Colors.RESET}")
        print(f"  {Colors.GREEN}You:{len(player_snake)}{Colors.RESET} | {Colors.BLUE}AI1:{len(ai_snake)}{Colors.RESET} | {Colors.MAGENTA}AI2:{len(ai2_snake)}{Colors.RESET}")
        print(f"{Colors.DIM}{'─'*36}{Colors.RESET}")
    
    except KeyboardInterrupt:
        print("\nGame interrupted!")
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

def get_closest_food(snake, board):
    head_y, head_x = snake[0]
    closest = None
    min_dist = float('inf')
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if board[y][x] == FOOD:
                dist = abs(head_y - y) + abs(head_x - x)
                if dist < min_dist:
                    min_dist = dist
                    closest = (y, x)
    return closest

def get_closest_food_excluding(snake, board, exclude_pos):
    head_y, head_x = snake[0]
    closest = None
    min_dist = float('inf')
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if board[y][x] == FOOD and (y, x) != exclude_pos:
                dist = abs(head_y - y) + abs(head_x - x)
                if dist < min_dist:
                    min_dist = dist
                    closest = (y, x)
    if closest is None:
        return exclude_pos
    return closest

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Colors.GREEN}{Colors.BOLD}")
    print("  +----------------------------+")
    print("  |     S N A K E   G A M E    |")
    print(f"  +----------------------------+{Colors.RESET}")
    print(f"  {Colors.GREEN}|{Colors.RESET}  {Colors.YELLOW}1.{Colors.RESET} Versus {Colors.MAGENTA}(slither.io){Colors.RESET}   {Colors.GREEN}|{Colors.RESET}")
    print(f"  {Colors.GREEN}|{Colors.RESET}  {Colors.YELLOW}2.{Colors.RESET} Play yourself          {Colors.GREEN}|{Colors.RESET}")
    print(f"  {Colors.GREEN}|{Colors.RESET}  {Colors.YELLOW}3.{Colors.RESET} Watch AI play {Colors.CYAN}(2x){Colors.RESET}     {Colors.GREEN}|{Colors.RESET}")
    print(f"  {Colors.GREEN}{Colors.BOLD}+----------------------------+{Colors.RESET}")
    print()
    
    while True:
        choice = input(f"  {Colors.CYAN}Enter choice (1-3):{Colors.RESET} ").strip()
        if choice in ['1', '2', '3']:
            break
        print(f"  {Colors.RED}Invalid choice.{Colors.RESET}")
    
    if choice == '1':
        versus_mode()
        return
    
    ai_mode = (choice == '3')
    
    board = init_board()
    snake = [(HEIGHT//2, WIDTH//2)]
    direction = 'w'
    board[snake[0][0]][snake[0][1]] = SNAKE_HEAD
    place_food(board)
    print_board(board)
    
    if ai_mode:
        print(f" {Colors.CYAN}AI Mode (2x speed){Colors.RESET} - {Colors.RED}Ctrl+C{Colors.RESET} to quit")
    else:
        print(f" {Colors.GREEN}Manual{Colors.RESET} - {Colors.YELLOW}WASD{Colors.RESET}=move {Colors.RED}Q{Colors.RESET}=quit")
    
    old_settings = termios.tcgetattr(sys.stdin)
    
    try:
        tty.setcbreak(sys.stdin.fileno())
        
        while True:
            if ai_mode:
                time.sleep(0.075)
            else:
                time.sleep(0.15)
                
                key = get_key_non_blocking()
                while key:
                    key = key.lower()
                    if key == 'q':
                        print("\nQuitting...")
                        return
                    if key in ['w', 'a', 's', 'd']:
                        if not is_opposite_direction(direction, key):
                            direction = key
                    key = get_key_non_blocking()

            food_pos = None
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    if board[y][x] == FOOD:
                        food_pos = (y, x)
                        break
                if food_pos:
                    break

            if ai_mode:
                direction = get_best_direction(snake, food_pos, direction, board)

            head_y, head_x = snake[0]
            if direction == 'w':
                head_y -= 1
            elif direction == 's':
                head_y += 1
            elif direction == 'a':
                head_x -= 1
            elif direction == 'd':
                head_x += 1

            if is_border(board[head_y][head_x]) or board[head_y][head_x] == SNAKE_BODY:
                print()
                print(f"{Colors.DIM}{'─'*20}{Colors.RESET}")
                print(f"{Colors.RED}{Colors.BOLD}  GAME OVER!{Colors.RESET}")
                print(f"  Score: {Colors.GREEN}{len(snake) - 1}{Colors.RESET}")
                print(f"{Colors.DIM}{'─'*20}{Colors.RESET}")
                break

            if board[head_y][head_x] == FOOD:   
                place_food(board)
            else:
                tail_y, tail_x = snake.pop()
                board[tail_y][tail_x] = EMPTY

            snake.insert(0, (head_y, head_x))
            board[head_y][head_x] = SNAKE_HEAD
            for y, x in snake[1:]:
                board[y][x] = SNAKE_BODY

            print_board(board)
            mode_text = f"{Colors.CYAN}AI{Colors.RESET}" if ai_mode else f"{Colors.GREEN}Manual{Colors.RESET}"
            print(f" Score: {Colors.YELLOW}{Colors.BOLD}{len(snake) - 1}{Colors.RESET}  |  Mode: {mode_text}")
    
    except KeyboardInterrupt:
        print("\nGame interrupted!")
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


main()
