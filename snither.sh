#!/bin/zsh
setopt NO_VERBOSE NO_XTRACE
RESET=$'\033[0m'
BOLD=$'\033[1m'
GREEN=$'\033[92m'
BLUE=$'\033[94m'
RED=$'\033[91m'
YELLOW=$'\033[93m'
CYAN=$'\033[96m'
MAGENTA=$'\033[95m'
DIM=$'\033[2m'
WIDTH=32
HEIGHT=16
SNAKE_HEAD='●'
SNAKE_BODY='○'
AI_HEAD='◆'
AI_BODY='◇'
AI2_HEAD='■'
AI2_BODY='□'
FOOD='★'
EMPTY=' '
typeset -A board
typeset -a snake ai_snake ai2_snake
direction='d'

init_board() {
    local y x
    for ((y=0; y<HEIGHT; y++)); do
        for ((x=0; x<WIDTH; x++)); do
            if ((y == 0 || y == HEIGHT-1)); then
                board[$y,$x]='─'
            elif ((x == 0 || x == WIDTH-1)); then
                board[$y,$x]='│'
            else
                board[$y,$x]=' '
            fi
        done
    done
    board[0,0]='┌'; board[0,$((WIDTH-1))]='┐'
    board[$((HEIGHT-1)),0]='└'; board[$((HEIGHT-1)),$((WIDTH-1))]='┘'
}

is_border() {
    [[ "$1" == '─' || "$1" == '│' || "$1" == '┌' || "$1" == '┐' || "$1" == '└' || "$1" == '┘' ]]
}

print_board() {
    printf '\033[?25l'
    printf '\033[H'
    local y x cell
    for ((y=0; y<HEIGHT; y++)); do
        for ((x=0; x<WIDTH; x++)); do
            cell="${board[$y,$x]}"
            case "$cell" in
                "$SNAKE_HEAD") printf "${GREEN}${BOLD}%s${RESET}" "$cell" ;;
                "$SNAKE_BODY") printf "${GREEN}%s${RESET}" "$cell" ;;
                "$AI_HEAD") printf "${BLUE}${BOLD}%s${RESET}" "$cell" ;;
                "$AI_BODY") printf "${CYAN}%s${RESET}" "$cell" ;;
                "$AI2_HEAD") printf "${MAGENTA}${BOLD}%s${RESET}" "$cell" ;;
                "$AI2_BODY") printf "${MAGENTA}%s${RESET}" "$cell" ;;
                "$FOOD") printf "${RED}%s${RESET}" "$cell" ;;
                '─'|'│'|'┌'|'┐'|'└'|'┘') printf "${DIM}%s${RESET}" "$cell" ;;
                *) printf "%s" "$cell" ;;
            esac
        done
        echo
    done
}

place_food() {
    local x y
    while true; do
        x=$((RANDOM % (WIDTH - 4) + 2))
        y=$((RANDOM % (HEIGHT - 4) + 2))
        if [[ "${board[$y,$x]}" == ' ' ]]; then
            board[$y,$x]="$FOOD"
            break
        fi
    done
}

is_opposite() {
    case "$1$2" in
        ws|sw|ad|da) return 0 ;;
        *) return 1 ;;
    esac
}

get_ai_direction() {
    local hy="$1" hx="$2" fy="$3" fx="$4" cur="$5"
    local other1="$6" other2="$7"
    local best="" best_dist=9999
    local dirs=(w s a d)
    for d in "${dirs[@]}"; do
        is_opposite "$cur" "$d" && continue
        local ny=$hy nx=$hx
        case "$d" in
            w) ny=$((hy - 1)) ;;
            s) ny=$((hy + 1)) ;;
            a) nx=$((hx - 1)) ;;
            d) nx=$((hx + 1)) ;;
        esac
        is_border "${board[$ny,$nx]}" && continue
        [[ "${board[$ny,$nx]}" == "$SNAKE_BODY" ]] && continue
        [[ "${board[$ny,$nx]}" == "$AI_BODY" ]] && continue
        [[ "${board[$ny,$nx]}" == "$AI2_BODY" ]] && continue
        [[ -n "$other1" && "$other1" == "$ny,$nx" ]] && continue
        [[ -n "$other2" && "$other2" == "$ny,$nx" ]] && continue
        local dy=$((fy - ny)) dx=$((fx - nx))
        [[ $dy -lt 0 ]] && dy=$((-dy))
        [[ $dx -lt 0 ]] && dx=$((-dx))
        local dist=$((dy + dx))
        if [[ $dist -lt $best_dist ]]; then
            best_dist=$dist
            best=$d
        fi
    done
    echo "${best:-$cur}"
}

find_food() {
    local exclude_y="${1:--1}" exclude_x="${2:--1}"
    local y x
    for ((y=1; y<HEIGHT-1; y++)); do
        for ((x=1; x<WIDTH-1; x++)); do
            if [[ "${board[$y,$x]}" == "$FOOD" ]]; then
                if [[ $y -ne $exclude_y || $x -ne $exclude_x ]]; then
                    echo "$y $x"
                    return
                fi
            fi
        done
    done
    echo "-1 -1"
}

versus_mode() {
    clear
    printf '\033[?25l'
    init_board
    snake=("$((HEIGHT/2)),$((WIDTH/4))")
    local player_dir='d'
    ai_snake=("$((HEIGHT/4)),$((3*WIDTH/4))")
    local ai_dir='a'
    ai2_snake=("$((3*HEIGHT/4)),$((3*WIDTH/4))")
    local ai2_dir='a'
    local player_alive=1 ai_alive=1 ai2_alive=1
    local py="${snake[1]%,*}" px="${snake[1]#*,}"
    local ay="${ai_snake[1]%,*}" ax="${ai_snake[1]#*,}"
    local a2y="${ai2_snake[1]%,*}" a2x="${ai2_snake[1]#*,}"
    board[$py,$px]="$SNAKE_HEAD"
    board[$ay,$ax]="$AI_HEAD"
    board[$a2y,$a2x]="$AI2_HEAD"
    place_food; place_food; place_food; place_food
    print_board
    echo " ${MAGENTA}Versus Mode${RESET} - WASD to move, Q to quit"
    local old_stty=$(stty -g)
    stty -icanon -echo min 0 time 1
    trap "printf '\033[?25h'; stty '$old_stty'; exit" INT TERM
    while [[ $player_alive -eq 1 ]] && [[ $ai_alive -eq 1 || $ai2_alive -eq 1 ]]; do
        sleep 0.12
        local key=""
        read -t 0.01 -k1 key 2>/dev/null
        key="${key:l}"
        [[ "$key" == "q" ]] && { printf '\033[?25h'; stty "$old_stty"; echo; return; }
        if [[ "$key" == [wasd] ]] && ! is_opposite "$player_dir" "$key"; then
            player_dir="$key"
        fi
        local food_info=($(find_food))
        local fy1=${food_info[1]} fx1=${food_info[2]}
        local food_info2=($(find_food $fy1 $fx1))
        local fy2=${food_info2[1]} fx2=${food_info2[2]}
        if [[ $ai_alive -eq 1 ]]; then
            local ahy="${ai_snake[1]%,*}" ahx="${ai_snake[1]#*,}"
            ai_dir=$(get_ai_direction $ahy $ahx $fy1 $fx1 "$ai_dir")
        fi
        if [[ $ai2_alive -eq 1 ]]; then
            local a2hy="${ai2_snake[1]%,*}" a2hx="${ai2_snake[1]#*,}"
            ai2_dir=$(get_ai_direction $a2hy $a2hx $fy2 $fx2 "$ai2_dir")
        fi
        local phy="${snake[1]%,*}" phx="${snake[1]#*,}"
        case "$player_dir" in
            w) phy=$((phy - 1)) ;; s) phy=$((phy + 1)) ;;
            a) phx=$((phx - 1)) ;; d) phx=$((phx + 1)) ;;
        esac
        local ahy="${ai_snake[1]%,*}" ahx="${ai_snake[1]#*,}"
        if [[ $ai_alive -eq 1 ]]; then
            case "$ai_dir" in
                w) ahy=$((ahy - 1)) ;; s) ahy=$((ahy + 1)) ;;
                a) ahx=$((ahx - 1)) ;; d) ahx=$((ahx + 1)) ;;
            esac
        fi
        local a2hy="${ai2_snake[1]%,*}" a2hx="${ai2_snake[1]#*,}"
        if [[ $ai2_alive -eq 1 ]]; then
            case "$ai2_dir" in
                w) a2hy=$((a2hy - 1)) ;; s) a2hy=$((a2hy + 1)) ;;
                a) a2hx=$((a2hx - 1)) ;; d) a2hx=$((a2hx + 1)) ;;
            esac
        fi
        local pcell="${board[$phy,$phx]}"
        if is_border "$pcell" || [[ "$pcell" == "$SNAKE_BODY" ]] || \
           [[ "$pcell" == "$AI_BODY" ]] || [[ "$pcell" == "$AI2_BODY" ]]; then
            player_alive=0
        fi
        if [[ $ai_alive -eq 1 ]]; then
            local acell="${board[$ahy,$ahx]}"
            if is_border "$acell" || [[ "$acell" == "$AI_BODY" ]] || \
               [[ "$acell" == "$SNAKE_BODY" ]] || [[ "$acell" == "$AI2_BODY" ]]; then
                ai_alive=0
            fi
        fi
        if [[ $ai2_alive -eq 1 ]]; then
            local a2cell="${board[$a2hy,$a2hx]}"
            if is_border "$a2cell" || [[ "$a2cell" == "$AI2_BODY" ]] || \
               [[ "$a2cell" == "$SNAKE_BODY" ]] || [[ "$a2cell" == "$AI_BODY" ]]; then
                ai2_alive=0
            fi
        fi
        [[ "$phy,$phx" == "$ahy,$ahx" ]] && { player_alive=0; ai_alive=0; }
        [[ "$phy,$phx" == "$a2hy,$a2hx" ]] && { player_alive=0; ai2_alive=0; }
        [[ "$ahy,$ahx" == "$a2hy,$a2hx" ]] && { ai_alive=0; ai2_alive=0; }
        [[ $player_alive -eq 0 ]] && break
        local p_ate=0 a_ate=0 a2_ate=0
        [[ "${board[$phy,$phx]}" == "$FOOD" ]] && p_ate=1
        [[ $ai_alive -eq 1 && "${board[$ahy,$ahx]}" == "$FOOD" ]] && a_ate=1
        [[ $ai2_alive -eq 1 && "${board[$a2hy,$a2hx]}" == "$FOOD" ]] && a2_ate=1
        if [[ $p_ate -eq 0 && ${#snake[@]} -gt 0 ]]; then
            local tail="${snake[-1]}"
            board[${tail%,*},${tail#*,}]=' '
            snake=("${snake[@]:0:-1}")
        fi
        if [[ $ai_alive -eq 1 && $a_ate -eq 0 && ${#ai_snake[@]} -gt 0 ]]; then
            local tail="${ai_snake[-1]}"
            board[${tail%,*},${tail#*,}]=' '
            ai_snake=("${ai_snake[@]:0:-1}")
        fi
        if [[ $ai2_alive -eq 1 && $a2_ate -eq 0 && ${#ai2_snake[@]} -gt 0 ]]; then
            local tail="${ai2_snake[-1]}"
            board[${tail%,*},${tail#*,}]=' '
            ai2_snake=("${ai2_snake[@]:0:-1}")
        fi
        snake=("$phy,$phx" "${snake[@]}")
        [[ $ai_alive -eq 1 ]] && ai_snake=("$ahy,$ahx" "${ai_snake[@]}")
        [[ $ai2_alive -eq 1 ]] && ai2_snake=("$a2hy,$a2hx" "${ai2_snake[@]}")
        local food_count=0
        for ((y=1; y<HEIGHT-1; y++)); do
            for ((x=1; x<WIDTH-1; x++)); do
                [[ "${board[$y,$x]}" == "$FOOD" ]] && food_count=$((food_count + 1))
            done
        done
        while [[ $food_count -lt 4 ]]; do
            place_food
            food_count=$((food_count + 1))
        done
        for ((y=1; y<HEIGHT-1; y++)); do
            for ((x=1; x<WIDTH-1; x++)); do
                local c="${board[$y,$x]}"
                [[ "$c" != "$FOOD" ]] && board[$y,$x]=' '
            done
        done
        board[${snake[1]%,*},${snake[1]#*,}]="$SNAKE_HEAD"
        for pos in "${snake[@]:1}"; do
            board[${pos%,*},${pos#*,}]="$SNAKE_BODY"
        done
        if [[ $ai_alive -eq 1 ]]; then
            board[${ai_snake[1]%,*},${ai_snake[1]#*,}]="$AI_HEAD"
            for pos in "${ai_snake[@]:1}"; do
                board[${pos%,*},${pos#*,}]="$AI_BODY"
            done
        fi
        if [[ $ai2_alive -eq 1 ]]; then
            board[${ai2_snake[1]%,*},${ai2_snake[1]#*,}]="$AI2_HEAD"
            for pos in "${ai2_snake[@]:1}"; do
                board[${pos%,*},${pos#*,}]="$AI2_BODY"
            done
        fi
        print_board
        printf ' \033[92mYou:%d\033[0m | ' "${#snake[@]}"
        if [[ $ai_alive -eq 1 ]]; then
            printf '\033[94mAI1:%d\033[0m | ' "${#ai_snake[@]}"
        else
            printf '\033[2mAI1:XX\033[0m | '
        fi
        if [[ $ai2_alive -eq 1 ]]; then
            printf '\033[95mAI2:%d\033[0m\n' "${#ai2_snake[@]}"
        else
            printf '\033[2mAI2:XX\033[0m\n'
        fi
    done
    printf '\033[?25h'
    stty "$old_stty"
    echo
    if [[ $player_alive -eq 0 ]]; then
        if [[ $ai_alive -eq 1 || $ai2_alive -eq 1 ]]; then
            echo "${RED}${BOLD}YOU DIED!${RESET} AI wins!"
        else
            echo "${YELLOW}${BOLD}DRAW!${RESET} Everyone crashed!"
        fi
    else
        echo "${GREEN}${BOLD}YOU WIN!${RESET} Last one standing!"
    fi
}

play_game() {
    local ai_mode=$1
    clear
    printf '\033[?25l'
    init_board
    snake=("$((HEIGHT/2)),$((WIDTH/2))")
    direction='d'
    local hy="${snake[1]%,*}" hx="${snake[1]#*,}"
    board[$hy,$hx]="$SNAKE_HEAD"
    place_food
    print_board
    if ((ai_mode)); then
        echo " ${CYAN}AI Mode${RESET} - Press Ctrl+C to quit"
    else
        echo " ${GREEN}Manual${RESET} - WASD to move, Q to quit"
    fi
    local old_stty=$(stty -g)
    stty -icanon -echo min 0 time 1
    trap "printf '\033[?25h'; stty '$old_stty'; exit" INT TERM
    while true; do
        if ((ai_mode)); then
            sleep 0.08
        else
            sleep 0.12
        fi
        if ((!ai_mode)); then
            local key=""
            read -t 0.01 -k1 key 2>/dev/null
            key="${key:l}"
            [[ "$key" == "q" ]] && { printf '\033[?25h'; stty "$old_stty"; echo; return; }
            if [[ "$key" == [wasd] ]] && ! is_opposite "$direction" "$key"; then
                direction="$key"
            fi
        fi
        local food_y=-1 food_x=-1
        for ((y=1; y<HEIGHT-1; y++)); do
            for ((x=1; x<WIDTH-1; x++)); do
                if [[ "${board[$y,$x]}" == "$FOOD" ]]; then
                    food_y=$y; food_x=$x
                    break 2
                fi
            done
        done
        if ((ai_mode)); then
            local hy="${snake[1]%,*}" hx="${snake[1]#*,}"
            direction=$(get_ai_direction $hy $hx $food_y $food_x "$direction")
        fi
        local head="${snake[1]}"
        local hy="${head%,*}" hx="${head#*,}"
        case "$direction" in
            w) hy=$((hy - 1)) ;;
            s) hy=$((hy + 1)) ;;
            a) hx=$((hx - 1)) ;;
            d) hx=$((hx + 1)) ;;
        esac
        if is_border "${board[$hy,$hx]}" || [[ "${board[$hy,$hx]}" == "$SNAKE_BODY" ]]; then
            printf '\033[?25h'
            stty "$old_stty"
            echo
            echo "${RED}${BOLD}GAME OVER!${RESET} Score: ${GREEN}$((${#snake[@]} - 1))${RESET}"
            return
        fi
        if [[ "${board[$hy,$hx]}" == "$FOOD" ]]; then
            place_food
        else
            local tail="${snake[-1]}"
            board[${tail%,*},${tail#*,}]=' '
            snake=("${snake[@]:0:-1}")
        fi
        snake=("$hy,$hx" "${snake[@]}")
        board[$hy,$hx]="$SNAKE_HEAD"
        for pos in "${snake[@]:1}"; do
            board[${pos%,*},${pos#*,}]="$SNAKE_BODY"
        done
        print_board
        echo " Score: ${YELLOW}${BOLD}$((${#snake[@]} - 1))${RESET}"
    done
}

main() {
    clear
    echo
    printf "  \033[92m\033[1m+----------------------------+\033[0m\n"
    printf "  \033[92m\033[1m|        S N I T H E R       |\033[0m\n"
    printf "  \033[92m\033[1m+----------------------------+\033[0m\n"
    printf "  \033[92m|\033[0m  \033[93m1.\033[0m Versus (slither.io)    \033[92m|\033[0m\n"
    printf "  \033[92m|\033[0m  \033[93m2.\033[0m Play yourself          \033[92m|\033[0m\n"
    printf "  \033[92m|\033[0m  \033[93m3.\033[0m Watch AI play          \033[92m|\033[0m\n"
    printf "  \033[92m\033[1m+----------------------------+\033[0m\n"
    echo
    while true; do
        printf "  \033[96mEnter choice (1-3):\033[0m "
        read -r choice
        case "$choice" in
            1) versus_mode; return ;;
            2) play_game 0; return ;;
            3) play_game 1; return ;;
            *) printf "  \033[91mInvalid choice\033[0m\n" ;;
        esac
    done
}

main
