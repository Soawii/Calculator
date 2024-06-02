import pygame as pg
from math import e, pi, sin, cos, asin, acos, log, isinf

class OperatorSetting:
    ''' Class handling all operators (+,-...) and their priority '''

    def __init__(self, name: str, priority: int, left_first: bool, function):
        self.name = name
        self.priority = priority
        self.left_first = left_first
        self.function = function


class Expression:
    ''' Class handling the main expression
        Includes methods for solving and displaying it '''
    
    OPERATORS = {'+': OperatorSetting('+', 1, True, lambda a, b: a + b),
                 '-': OperatorSetting('-', 1, True, lambda a, b: a - b),
                 '*': OperatorSetting('*', 2, True, lambda a, b: a * b),
                 '/': OperatorSetting('/', 2, True, lambda a, b: a / b),
                 '^': OperatorSetting('^', 3, False, lambda a, b: pow(a, b))}
    BRACKET_OPERATORS = {'(': OperatorSetting('(', 0, True, None),
                         ')': OperatorSetting(')', 0, True, None)}
    FUNCTIONS = {
        'arccos': acos,
        'arcsin': asin,
        'sin': sin,
        'cos': cos,
        'ln': log}
    CONSTANTS = {'eu': e, 'pi': pi}
    MAX_STACK_LEN = 50
    fonts = []

    def __init__(
            self,
            height: int, top: int,
            BACKGROUND_COLOR: pg.Color, TEXT_COLOR: pg.Color, SMALL_TEXT_COLOR: pg.Color,
            BORDER_COLOR: pg.Color, CURSOR_COLOR: pg.Color, 
            BORDER_WIDTH: int,
            font_path: str, font_size: int,
            cursor_tick_time: int):

        self.rect = pg.Rect(SPACE, top, WIDTH - SPACE * 2, height)

        self.BACKGROUND_COLOR = BACKGROUND_COLOR
        self.TEXT_COLOR = TEXT_COLOR
        self.BORDER_COLOR = BORDER_COLOR
        self.CURSOR_COLOR = CURSOR_COLOR
        self.BORDER_WIDTH = BORDER_WIDTH
        self.SMALL_TEXT_COLOR = SMALL_TEXT_COLOR

        self.expression = []
        self.expression_stack = []
        self.cursor_pointer = 0

        self.font_size = font_size
        self.fonts = [None for i in range(200)]
        for i in range(200):
            self.fonts[i] = pg.font.Font(font_path, i)
        self.font = self.fonts[font_size]

        self.prev_expression = None
        self.precalculated_expression = None
        self.resize(height, top)

        self.last_cursor_tick = pg.time.get_ticks()
        self.cursor_tick_time = cursor_tick_time
        self.draw_cursor = True
        self.error_tick = 0
        self.error_time = 2000


    def resize(self, height: int, top: int) -> None:
        ''' Resize the expression after the window has been resized '''
        self.rect = pg.Rect(SPACE, top, WIDTH - SPACE * 2, height)
        self.small_font = self.fonts[round(height / 4)]
        self.update()


    def add_to_stack(self):
        self.expression_stack.append((self.expression.copy(), self.cursor_pointer))
        if len(self.expression_stack) > self.MAX_STACK_LEN:
            self.expression_stack.pop(0)


    def add_char(self, char_pressed: str) -> None:
        ''' Add chosen sequence to the expression at the cursor pointer '''
        if char_pressed in self.OPERATORS:
            if (self.cursor_pointer > 0 
                    and self.expression[self.cursor_pointer - 1] in self.OPERATORS):
                return
            if (self.cursor_pointer < (len(self.expression) - 1) 
                    and self.expression[self.cursor_pointer + 1] in self.OPERATORS):
                return
            if self.cursor_pointer == 0 and char_pressed != '-':
                return
        if char_pressed == '.' and self.cursor_pointer > 0 and self.expression[self.cursor_pointer - 1] == '.':
            return
        self.add_to_stack()
        self.expression.insert(self.cursor_pointer, char_pressed)
        self.cursor_pointer += 1
        self.update()


    def delete_char(self, to_the_left: bool) -> None:
        ''' Delete sequence from the expression at the cursor pointer '''
        if to_the_left and self.cursor_pointer > 0:
            self.add_to_stack()
            self.expression.pop(self.cursor_pointer - 1)
            self.cursor_pointer -= 1
            self.update()
        if not to_the_left and self.cursor_pointer < len(self.expression):
            self.add_to_stack()
            self.expression.pop(self.cursor_pointer)
            self.update()


    def create_RPN(self) -> list:
        ''' Produces a RPN (Reverse Polish Notation) from the current expression 
            Algorithm used -> https://en.wikipedia.org/wiki/Shunting_yard_algorithm '''
        output = []
        operator_stack = []
        if len(self.expression) > 0 and self.expression[0] == '-':
            output.append(0)
        i = 0
        while i < len(self.expression):
            if ((i > 0) and (self.expression[i - 1] not in self.OPERATORS)
                    and (self.expression[i - 1] != '(') and (self.expression[i] not in self.OPERATORS)
                    and not (self.expression[i] == '(' and self.expression[i - 1] in self.FUNCTIONS)
                    and (self.expression[i] != ')')
                    and not (self.expression[i] == '.' and (self.expression[i - 1].isdigit() or self.expression[i - 1] == '.'))):
                self.expression.insert(i, '*')
                continue
            if self.expression[i].isdigit() or self.expression[i] == '.':
                starting_width_dot = self.expression[i] == '.'
                left = i
                i += 1
                while i < len(self.expression) and self.expression[i].isdigit():
                    i += 1
                if i < len(self.expression) and self.expression[i] == '.':
                    assert not starting_width_dot, "invalid expression"
                    i += 1
                    while i < len(
                            self.expression) and self.expression[i].isdigit():
                        i += 1
                number = 0
                if i < len(self.expression) and self.expression[i] == 'e':
                    right = i + 1
                    j = i + 1
                    if j < len(self.expression) and self.expression[j] in ['-', '+']:
                        j += 1
                    while j < len(self.expression) and self.expression[j].isdigit():
                        j += 1
                    number = float(''.join(
                        self.expression[left:i])) * 10 ** float(''.join(self.expression[right:j]))
                    i = j
                else:
                    number = float(''.join(self.expression[left: i]))
                output.append(number)
                continue

            constant_placed = False
            for constant in self.CONSTANTS:
                if self.expression[i] == constant:
                    constant_placed = True
                    output.append(self.CONSTANTS[constant])
                    i += 1
                    break
            if constant_placed:
                continue

            function_placed = False
            for function in self.FUNCTIONS:
                if self.expression[i] == function:
                    function_placed = True
                    operator_stack.append(function)
                    i += 1
                    if i >= len(self.expression) or self.expression[i] != '(':
                        raise AssertionError(
                            "parentheses after a function absent")
                    break
            if function_placed:
                continue

            if self.expression[i] in self.OPERATORS:
                setting = self.OPERATORS[self.expression[i]]
                while ((len(operator_stack) > 0 and isinstance(operator_stack[-1], OperatorSetting) and operator_stack[-1].name != '(')
                       and ((operator_stack[-1].priority > setting.priority)
                            or (operator_stack[-1].priority == setting.priority
                                and setting.left_first))):
                    output.append(operator_stack[-1])
                    operator_stack.pop()
                operator_stack.append(setting)
            elif self.expression[i] == '(':
                if i + 1 < len(self.expression) and (self.expression[i + 1] in ['-', '+']):
                    output.append(0)
                operator_stack.append(self.BRACKET_OPERATORS['('])
            elif self.expression[i] == ')':
                while len(operator_stack) > 0 and operator_stack[-1].name != '(':
                    output.append(operator_stack[-1])
                    operator_stack.pop()
                assert len(
                    operator_stack) > 0, "parentheses out of order"
                operator_stack.pop()
                if len(operator_stack) > 0 and operator_stack[-1] in self.FUNCTIONS:
                    output.append(operator_stack[-1])
                    operator_stack.pop()
            else:
                raise AssertionError("Unfortunate things might have happenned")
            i += 1

        while len(operator_stack) > 0:
            assert operator_stack[-1].name not in [
                '(', ')'], "parentheses out of order"
            output.append(operator_stack[-1])
            operator_stack.pop()

        while (len(output) > 1 
               and isinstance(output[0], (float, int)) 
               and isinstance(output[1], OperatorSetting) 
               and output[1].name in ['-', '+']):
            new_value = (-1.0 if output[1].name == '-' else 1.0) * output[0]
            output.pop(0)
            output[0] = new_value
    
        return output


    def evaluate_RPN(self) -> float:
        ''' Turns a RPN to a number '''
        RPN = self.create_RPN()
        
        number_stack = []
        for n in RPN:
            if isinstance(n, OperatorSetting):
                assert len(number_stack) >= 2, 'invalid expression'
                left, right = number_stack[-2], number_stack[-1]
                number_stack.pop()
                number_stack.pop()
                number_stack.append(n.function(left, right))
            elif n in self.FUNCTIONS:
                assert len(number_stack) >= 1, 'invalid expression'
                top = number_stack[-1]
                number_stack.pop()
                number_stack.append(self.FUNCTIONS[n](top))
            else:
                number_stack.append(n)

        assert len(number_stack) == 1, 'invalid expression'
        return number_stack[0]

    def evaluate_expression_result(self) -> (float | None):
        ''' Helper expression-evaluating function
            Used for desplaying pre-calculated result in the bottom '''
        if self.prev_expression != None and pg.time.get_ticks() - self.error_tick <= self.error_time:
            return None
        try:
            number = round(float(self.evaluate_RPN()), 10)
            assert not isinf(number), 'number is too big'

        except Exception as e:
            return list(' '.join([str(a) for a in e.args]))

        if (abs(number) <= 10 ** 15) and (number == float(int(number))):
            number = int(number)
        return number

    def evaluate_expression(self) -> (float | None):
        ''' Main expression-evaluating function
            Handles errors and updates the main expression list '''
        result = self.evaluate_expression_result()
        if isinstance(result, list):
            self.prev_expression = self.expression.copy()
            self.error_tick = pg.time.get_ticks()
            self.expression = result
            self.cursor_pointer = len(self.expression)
            self.update()
            return None
        self.add_to_stack()
        self.expression = list(str(result))
        self.cursor_pointer = len(self.expression)
        self.update()
        self.precalculated_expression = None
        return result


    def update_cursor(self) -> None:
        ''' Updates cursors size and position '''
        self.draw_cursor = True
        self.last_cursor_tick = pg.time.get_ticks()
        self.cursor_rect = pg.Rect(0, 0, 1, self.font_size)
        self.cursor_rect.centery = self.text_rect.centery - 4
        self.cursor_rect.right = self.text_rect.right - self.font.size(''.join(
            [('e' if s == 'eu' else s) for s in self.expression][self.cursor_pointer:len(self.expression)]) + ' ')[0] + 1


    def update(self) -> None:
        ''' Updates size and position of main text '''
        self.text_surf = self.font.render(''.join(
            [('e' if s == 'eu' else s) for s in self.expression]) + ' ', True, TEXT_COLOR)
        self.text_rect = self.text_surf.get_rect()

        # Make font smaller while it doesnt fit
        while self.text_rect.width > self.rect.width or self.text_rect.height >= self.rect.height / 2.1:
            self.font = self.fonts[self.font_size - 1]
            self.font_size -= 1
            self.text_surf = self.font.render(''.join(
                [('e' if s == 'eu' else s) for s in self.expression]) + ' ', True, TEXT_COLOR)
            self.text_rect = self.text_surf.get_rect()

        # Make font bigger while it fits
        while True:
            new_font = self.fonts[self.font_size + 1]
            if (new_font.size(''.join([('e' if s == 'eu' else s) for s in self.expression]) + ' ')[0] >= self.rect.width 
                    or new_font.size('1')[1] >= self.rect.height / 2.1):
                break
            self.font = new_font
            self.font_size += 1
            self.text_surf = self.font.render(''.join(
                [('e' if s == 'eu' else s) for s in self.expression]) + ' ', True, TEXT_COLOR)
            self.text_rect = self.text_surf.get_rect()

        calc = self.evaluate_expression_result()
        if calc != None:
            calc = None if isinstance(calc, list) else list(str(calc))
        self.precalculated_expression = calc
        if calc != None:
            self.precalculated_surf = self.small_font.render(''.join(self.precalculated_expression) + ' ', True, self.SMALL_TEXT_COLOR)
            self.precalculated_rect = self.precalculated_surf.get_rect()

        self.text_rect.center = self.rect.center
        self.text_rect.right = self.rect.right
        if calc != None:
            self.precalculated_rect.right = self.text_rect.right
            self.precalculated_rect.centery = self.rect.bottom - self.rect.height // 7

        self.update_cursor()


    def draw(self) -> None:
        ''' Draws the expression onto the window'''
        current_time = pg.time.get_ticks()

        # Update error message
        if self.prev_expression is not None and current_time - \
                self.error_tick > self.error_time:
            self.expression = self.prev_expression
            self.prev_expression = None
            self.cursor_pointer = len(self.expression)
            self.update()

        # Update cursor tick
        if current_time - self.last_cursor_tick >= self.cursor_tick_time:
            self.draw_cursor = not self.draw_cursor
            self.last_cursor_tick = current_time

        pg.draw.rect(screen, self.BACKGROUND_COLOR, self.rect, 0, 5)
        pg.draw.rect(screen, self.BORDER_COLOR, self.rect, self.BORDER_WIDTH, 5)
        screen.blit(self.text_surf, self.text_rect)
        if self.precalculated_expression != None:
            screen.blit(self.precalculated_surf, self.precalculated_rect)
        if self.draw_cursor:
            pg.draw.rect(screen, self.CURSOR_COLOR, self.cursor_rect, 0)


class Button:
    def __init__(
            self, size: tuple, top_left: tuple,
            NORMAL_COLOR: pg.Color, HOVERED_COLOR: pg.Color,
            PRESSED_COLOR: pg.Color, BORDER_COLOR: pg.Color,
            name: str, expression: Expression, font_path: str, font_size: int):
        self.size, self.top_left = size, top_left
        self.NORMAL_COLOR = NORMAL_COLOR
        self.HOVERED_COLOR = HOVERED_COLOR
        self.PRESSED_COLOR = PRESSED_COLOR
        self.CURRENT_COLOR = NORMAL_COLOR
        self.BORDER_COLOR = BORDER_COLOR
        self.name, self.expression = name, expression
        self.rect = pg.Rect(top_left, size)

        # Make font smaller to fit
        while True:
            self.font = self.expression.fonts[font_size]
            self.text_surf = self.font.render(self.name, True, TEXT_COLOR)
            self.text_rect = self.text_surf.get_rect()
            if (self.text_rect.height >= self.size[1] / 2 
                    or self.text_rect.width >= self.size[0] / 1.2):
                font_size -= 1
                continue
            else:
                self.text_rect.center = self.rect.center
                break

    def press(self):
        global pressed_button
        if self.name == "BACKSPACE":
            self.expression.delete_char(True)
        elif self.name == '=':
            self.expression.evaluate_expression()
        elif self.name in ['<', '>']:
            diff = 1 if self.name == '>' else -1
            self.expression.cursor_pointer += diff
            if self.expression.cursor_pointer < 0:
                self.expression.cursor_pointer = 0
            if self.expression.cursor_pointer > len(self.expression.expression):
                self.expression.cursor_pointer = len(self.expression.expression)
            self.expression.update_cursor()
        elif self.name == 'C':
            self.expression.expression.clear()
            self.expression.cursor_pointer = 0
            self.expression.update()
        elif self.name == 'undo':
            if len(self.expression.expression_stack) == 0:
                return
            self.expression.expression, self.expression.cursor_pointer = self.expression.expression_stack[-1][0].copy(), self.expression.expression_stack[-1][1]
            self.expression.expression_stack.pop() 
            self.expression.update()
        elif self.name == 'x^2':
            self.expression.expression.insert(0, '(')
            self.expression.expression.append(')')
            self.expression.expression.append('^')
            self.expression.expression.append('2')
            self.expression.cursor_pointer = len(self.expression.expression)
            self.expression.update()
        elif self.name == 'e':
            self.expression.add_char('eu')
        else:
            self.expression.add_char(self.name)
            if self.name in self.expression.FUNCTIONS:
                self.expression.add_char('(')
                self.expression.add_char(')')
                self.expression.cursor_pointer -= 1
                self.expression.update_cursor()

        pressed_button = None


    def update(self,
                mouse_pos: tuple, mouse_pressed: bool,
                mouse_pressed_this_frame: bool,
                mouse_released_this_frame: bool):
        global pressed_button
        if not self.rect.collidepoint(mouse_pos) or (
                pressed_button is not None and pressed_button != self):
            self.CURRENT_COLOR = self.NORMAL_COLOR
            return
        if mouse_pressed_this_frame:
            pressed_button = self
        if pressed_button == self:
            if mouse_released_this_frame:
                self.press()
            else:
                self.CURRENT_COLOR = self.PRESSED_COLOR
        else:
            self.CURRENT_COLOR = self.HOVERED_COLOR


    def draw(self):
        pg.draw.rect(screen, self.CURRENT_COLOR, self.rect, 0, 5)
        pg.draw.rect(screen, self.BORDER_COLOR, self.rect, 1, 5)
        screen.blit(self.text_surf, self.text_rect)


buttons = []


def create_buttons():
    ''' Create buttons on creation/resize of the window '''
    buttons.clear()
    expression.resize(NUMBER_BUTTON_SIZE[1] * 3.1 // 2, SPACE)
    for i in range(1, 10):
        buttons.append(Button(NUMBER_BUTTON_SIZE,
                              (((i - 1) % 3 + 2) * (SPACE) + ((i - 1) % 3 + 1) * (NUMBER_BUTTON_SIZE[0]),
                               HEIGHT - NUMBER_BUTTON_SIZE[1] * ((i - 1) // 3 + 2) - ((i - 1) // 3 + 2) * SPACE),
                              NORMAL_BUTTON_COLOR,
                              HOVERED_BUTTON_COLOR,
                              PRESSED_BUTTON_COLOR,
                              BORDER_BUTTON_COLOR,
                              str(i),
                              expression,
                              FONT_PATH,
                              24))

    for i, name in enumerate(['(', ')', 'x^2']):
        buttons.append(Button(BUTTON_SIZE,
                              (SPACE * (i + 2) + BUTTON_SIZE[0] * (i + 1),
                               HEIGHT - NUMBER_BUTTON_SIZE[1] - BUTTON_SIZE[1] * (4 + 1) - (4 + 2) * SPACE),
                              DARKER_NORMAL_BUTTON_COLOR,
                              DARKER_HOVERED_BUTTON_COLOR,
                              DARKER_PRESSED_BUTTON_COLOR,
                              DARKER_BORDER_BUTTON_COLOR,
                              name,
                              expression,
                              FONT_PATH,
                              24))

    for i, operator in enumerate(Expression.OPERATORS.keys()):
        buttons.append(Button(BUTTON_SIZE,
                              (SPACE * 5 + BUTTON_SIZE[0] * 4,
                               HEIGHT - NUMBER_BUTTON_SIZE[1] - BUTTON_SIZE[1] * (i + 1) - (i + 2) * SPACE),
                              DARKER_NORMAL_BUTTON_COLOR,
                              DARKER_HOVERED_BUTTON_COLOR,
                              DARKER_PRESSED_BUTTON_COLOR,
                              DARKER_BORDER_BUTTON_COLOR,
                              str(operator),
                              expression,
                              FONT_PATH,
                              16))

    for i, name in enumerate(['undo', '0', '.', '=']):
        buttons.append(Button(NUMBER_BUTTON_SIZE,
                              (SPACE * (i + 2) + NUMBER_BUTTON_SIZE[0] * (i + 1),
                               HEIGHT - NUMBER_BUTTON_SIZE[1] - SPACE),
                              NORMAL_BUTTON_COLOR,
                              HOVERED_BUTTON_COLOR,
                              PRESSED_BUTTON_COLOR,
                              BORDER_BUTTON_COLOR,
                              name,
                              expression,
                              FONT_PATH,
                              20 if i == 0 else 24))

    for i, name in enumerate(['<', '>', 'C', 'BACKSPACE']):
        buttons.append(Button(BUTTON_SIZE,
                              (SPACE * (i + 2) + BUTTON_SIZE[0] * (i + 1),
                               HEIGHT - NUMBER_BUTTON_SIZE[1] - BUTTON_SIZE[1] * 6 - 7 * SPACE),
                              DARKER_NORMAL_BUTTON_COLOR,
                              DARKER_HOVERED_BUTTON_COLOR,
                              DARKER_PRESSED_BUTTON_COLOR,
                              DARKER_BORDER_BUTTON_COLOR,
                              name,
                              expression,
                              FONT_PATH,
                              16 if i == 3 else 24))

    for i, name in enumerate(['ln', 'arccos', 'arcsin', 'cos', 'sin', 'pi', 'e']):
        buttons.append(Button(
                NUMBER_BUTTON_SIZE if i == 0 else BUTTON_SIZE,
                (SPACE, HEIGHT - NUMBER_BUTTON_SIZE[1] - BUTTON_SIZE[1] * (i) - (i+1) * SPACE),
                DARKER_NORMAL_BUTTON_COLOR,
                DARKER_HOVERED_BUTTON_COLOR,
                DARKER_PRESSED_BUTTON_COLOR,
                DARKER_BORDER_BUTTON_COLOR,
                name,
                expression,
                FONT_PATH,
                20))



pg.init()

WIDTH = 600
HEIGHT = 700
MIN_WIDTH = 200
MIN_HEIGHT = 250
SPACE = 3
NUMBER_BUTTON_SIZE = ((WIDTH - SPACE * 6) // 5, (HEIGHT - SPACE * 8) // 7)
BUTTON_SIZE = ((WIDTH - SPACE * 6) // 5, (NUMBER_BUTTON_SIZE[1] * 3 - SPACE) // 4)

BACKGROUND_COLOR = pg.Color(230, 230, 230)
NORMAL_BUTTON_COLOR = pg.Color(245, 245, 245)
DARKER_NORMAL_BUTTON_COLOR = pg.Color(240, 240, 240)
HOVERED_BUTTON_COLOR = pg.Color(240, 240, 240)
DARKER_HOVERED_BUTTON_COLOR = pg.Color(235, 235, 235)
PRESSED_BUTTON_COLOR = pg.Color(235, 235, 235)
DARKER_PRESSED_BUTTON_COLOR = pg.Color(230, 230, 230)
BORDER_BUTTON_COLOR = pg.Color(220, 220, 220)
DARKER_BORDER_BUTTON_COLOR = pg.Color(215, 215, 215)
TEXT_COLOR = pg.Color(0, 0, 0)
CURSOR_COLOR = pg.Color(20, 20, 20)
FONT_PATH = "calc_font.otf"

expression = Expression(
    NUMBER_BUTTON_SIZE[1] * 3.1 // 2,
    SPACE,
    NORMAL_BUTTON_COLOR,
    TEXT_COLOR,
    pg.Color(200, 200, 200),
    BORDER_BUTTON_COLOR,
    CURSOR_COLOR,
    2,
    FONT_PATH,
    50,
    600)
create_buttons()

screen = pg.display.set_mode((WIDTH, HEIGHT), pg.RESIZABLE)
pg.display.set_caption('Calculator')
pressed_button = None

app_running = True
clock = pg.Clock()

key_to_name = {
    pg.K_LEFT: '<',
    pg.K_RIGHT: '>',
    pg.K_BACKSPACE: 'BACKSPACE',
    pg.K_PERIOD: '.',
    pg.K_0: '0',
    pg.K_MINUS: '-',
    pg.K_SLASH: '/',
    pg.K_RETURN: '='}

shift_key_to_name = {
    pg.K_9: '(',
    pg.K_0: ')',
    pg.K_6: '^',
    pg.K_EQUALS: '+',
    pg.K_8: '*'}

for i in range(1, 10):
    key_to_name[pg.K_1 + i - 1] = str(i)

key_to_button, shift_key_to_button = {}, {}
for key in key_to_name:
    key_to_button[key] = [b for b in buttons if b.name == key_to_name[key]][0]
for key in shift_key_to_name:
    shift_key_to_button[key] = [
        b for b in buttons if b.name == shift_key_to_name[key]][0]

name_to_button = {}
for function in expression.FUNCTIONS:
    name_to_button[function] = [b for b in buttons if b.name == function][0]
name_to_button['e'] = [b for b in buttons if b.name == 'e'][0]
name_to_button['pi'] = [b for b in buttons if b.name == 'pi'][0]

current_string = ''
pg.key.set_repeat(500, 30)

while app_running:
    clock.tick(60)
    screen.fill(BACKGROUND_COLOR)

    mouse_pressed = pg.mouse.get_pressed()[0]
    mouse_pressed_this_frame, mouse_released_this_frame = False, False
    mouse_pos = pg.mouse.get_pos()
    is_shift_pressed = pg.key.get_pressed()[pg.K_LSHIFT]

    if not mouse_pressed:
        pressed_button = None

    for event in pg.event.get():
        if event.type == pg.QUIT:
            app_running = False

        elif event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pressed_this_frame = True
        elif event.type == pg.MOUSEBUTTONUP:
            if event.button == 1:
                mouse_released_this_frame = True
        elif event.type == pg.KEYDOWN:
            if is_shift_pressed:
                if event.key in shift_key_to_button:
                    shift_key_to_button[event.key].press()
            else:
                if event.key in key_to_button:
                    key_to_button[event.key].press()
                elif event.key == pg.K_DELETE:
                    expression.delete_char(False)
                elif event.key == pg.K_z:
                    [b for b in buttons if b.name == 'undo'][0].press()
            current_string += event.unicode
            for name in name_to_button:
                if current_string.endswith(name):
                    name_to_button[name].press()
                    current_string = ''
        elif event.type == pg.VIDEORESIZE:
            WIDTH, HEIGHT = screen.get_size()
            recreate_window = WIDTH < MIN_WIDTH or HEIGHT < MIN_HEIGHT
            if WIDTH < MIN_WIDTH:
                WIDTH = MIN_WIDTH
            if HEIGHT < MIN_HEIGHT:
                HEIGHT = MIN_HEIGHT
            if recreate_window:
                screen = pg.display.set_mode((WIDTH, HEIGHT), pg.RESIZABLE)
            NUMBER_BUTTON_SIZE = (
                (WIDTH - SPACE * 6) // 5,
                (HEIGHT - SPACE * 8) // 7)
            BUTTON_SIZE = (
                (WIDTH - SPACE * 6) // 5,
                (NUMBER_BUTTON_SIZE[1] * 3 - SPACE) // 4)
            create_buttons()

    expression.draw()
    for b in buttons:
        b.update(mouse_pos, mouse_pressed,
                 mouse_pressed_this_frame,
                 mouse_released_this_frame)
        b.draw()

    pg.display.flip()
