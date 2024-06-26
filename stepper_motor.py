from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import keyboard
import time
import json

root = Tk()
root.title("Stepper Motor")
root.resizable(width=False, height=False)

tabControl = ttk.Notebook(root) 
positionstab = ttk.Frame(tabControl) 
sequencetab = ttk.Frame(tabControl) 
  
tabControl.add(positionstab, text ='Positions')
tabControl.add(sequencetab, text ='Sequence')
tabControl.grid(row=0, column=0, sticky="nsew")

tree = ttk.Treeview(sequencetab, columns=("X", "Y", "Z", "Delay"), show='headings')
tree.heading("X", text="X")
tree.heading("Y", text="Y")
tree.heading("Z", text="Z")
tree.heading("Delay", text="Delay (s)")

for col in ("X", "Y", "Z", "Delay"):
    tree.column(col, width=100, anchor=CENTER)

tree.grid(row=0, column=0, sticky="nsew")

x, y, z = 0, 0, 0
colorx, colory, colorz = "green", "green", "green"
current_tab = 0
numberofposition = 6
yes_button = False
spinbox_changed = False
running = False
looping = False
after_id = None
current_execution_item = None

spinbox_vars = {
    'X': {},
    'Y': {},
    'Z': {}
}

config = "config.json"
    
def load_positions():
    try:
        with open(config, "r") as file:
            positions = json.load(file)
        return positions
    except FileNotFoundError:
        positions = {}
        
    for i in range(1, 6 + 1):
        if str(i) not in positions:
            positions[str(i)] = (0, 0, 0)
    
    return positions

def save(positions):
    with open(config, "w") as file:
        json.dump(positions, file)

def create_motor_frame(parent, motor, row):
    frame = Frame(parent, width=150)
    frame.grid(row=row, column=0, columnspan=2, sticky="ns")
    Label(frame, text=f'Motor {motor}').grid(row=0, column=0)

    Label(frame, text='Acceleration').grid(row=1, column=1)
    spinbox_vars[motor]['accel'] = IntVar()
    Spinbox(frame, from_=1, to=3000, textvariable=spinbox_vars[motor]['accel']).grid(row=2, column=1)
    Label(frame, text='mm/s²').grid(row=2, column=2)

    Label(frame, text='Speed').grid(row=3, column=1)
    spinbox_vars[motor]['speed'] = IntVar()
    Spinbox(frame, from_=1, to=3000, textvariable=spinbox_vars[motor]['speed']).grid(row=4, column=1)
    Label(frame, text='mm/s').grid(row=4, column=2)

    Label(frame, text='Steps/mm').grid(row=5, column=1)
    column_frame = Frame(frame, width=150)
    column_frame.grid(row=6, column=1, sticky="ns")
    spinbox_vars[motor]['steps'] = IntVar()
    Spinbox(column_frame, from_=1, to=3000, width=5, textvariable=spinbox_vars[motor]['steps']).grid(row=0, column=1)
    Label(column_frame, text='/').grid(row=0, column=2)
    spinbox_vars[motor]['mm'] = IntVar()
    Spinbox(column_frame, from_=1, to=3000, width=5, textvariable=spinbox_vars[motor]['mm']).grid(row=0, column=3)
    Label(column_frame, text='mm').grid(row=0, column=4, columnspan=2)

    return frame

def settings():
    global settings_window
    settings_window = Toplevel(root)
    settings_window.title("Settings")
    settings_window.resizable(width=False, height=False)
    settings_window.grab_set()
    
    motors = ['X', 'Y', 'Z']
    for i, motor in enumerate(motors):
        create_motor_frame(settings_window, motor, i)
    
    Button(settings_window, text='Save', command=save_settings_callback).grid(row=3, column=0, columnspan=2)

def open_settings():
    settings()
    load_settings_callback()

def load_settings_callback():
    positions = load_positions()
    for motor in ['X', 'Y', 'Z']:
        if motor in positions:
            spinbox_vars[motor]['accel'].set(positions[motor]['acceleration'])
            spinbox_vars[motor]['speed'].set(positions[motor]['speed'])
            spinbox_vars[motor]['steps'].set(positions[motor]['steps'])
            spinbox_vars[motor]['mm'].set(positions[motor]['mm'])

def save_settings_callback():
    global spinbox_changed
    spinbox_changed = True
    positions = load_positions()
    for motor in ['X', 'Y', 'Z']:
        accel_var = spinbox_vars[motor]['accel'].get()
        speed_var = spinbox_vars[motor]['speed'].get()
        steps_var = spinbox_vars[motor]['steps'].get()
        mm_var = spinbox_vars[motor]['mm'].get()
        positions[motor] = {'acceleration': accel_var, 'speed': speed_var, 'steps': steps_var, 'mm': mm_var}
    save(positions)
    settings_window.destroy()
    
def saveStoredPositions(button):
    global x, y, z
    button.coordinates = (x, y, z)
    button.config(text=f'P{button.index}*')
    save_window.destroy()

    positions = load_positions()
    positions[str(button.index)] = button.coordinates 
    save(positions)

def save_position_window(button):
    global save_window
    save_window = Toplevel(root)
    save_window.title("Save")
    save_window.resizable(width=False, height=False)
    Label(save_window, text='Do you wish to save in that position?').grid(row=0, column=0)
    save = Frame(save_window, width=150)
    save.grid(row=1, column=0)
    Button(save, text='Yes', command=lambda: saveStoredPositions(button)).grid(row=0, column=0)
    Button(save, text='No', command=save_window.destroy).grid(row=0, column=1)
    save_window.grab_set()

def on_button_press(event, button):
    button.start_time = time.time()
    button.after_id = button.after(5000, lambda: check_button_press(button))

def check_button_press(button):
    elapsed_time = time.time() - button.start_time
    if elapsed_time >= 5:
        save_position_window(button)

def on_button_release(event, button):
    global x, y, z
    elapsed_time = time.time() - button.start_time
    button.after_cancel(button.after_id)
    if elapsed_time < 5:
        if hasattr(button, 'coordinates'):
            x, y, z = button.coordinates
            update_coordinates()

def create_position_button(parent, row, col, index, positions):
    button = Button(parent, text=f'P{index}', width=16, height=8)
    button.grid(row=row, column=col)
    button.index = index
    button.coordinates = positions.get(str(index), (0, 0, 0))
    button.bind("<ButtonPress>", lambda e, b=button: on_button_press(e, b))
    button.bind("<ButtonRelease>", lambda e, b=button: on_button_release(e, b))
    return button

def move_to_position(position):
    global x, y, z
    positions = load_positions()
    if position in positions:
        x, y, z = positions[position]
        update_coordinates()

def hotkey_position_1():move_to_position('1')
def hotkey_position_2():move_to_position('2')
def hotkey_position_3():move_to_position('3')
def hotkey_position_4():move_to_position('4')
def hotkey_position_5():move_to_position('5')
def hotkey_position_6():move_to_position('6')

def remove_hotkey_safely(key):
    try:
        keyboard.remove_hotkey(key)
    except KeyError:
        pass

def positions_hotkeys():
    keyboard.add_hotkey('ctrl + 1', hotkey_position_1)
    keyboard.add_hotkey('ctrl + 2', hotkey_position_2)
    keyboard.add_hotkey('ctrl + 3', hotkey_position_3)
    keyboard.add_hotkey('ctrl + 4', hotkey_position_4)
    keyboard.add_hotkey('ctrl + 5', hotkey_position_5)
    keyboard.add_hotkey('ctrl + 6', hotkey_position_6)

def remove_positions_hotkeys():
    remove_hotkey_safely('ctrl + 1')
    remove_hotkey_safely('ctrl + 2')
    remove_hotkey_safely('ctrl + 3')
    remove_hotkey_safely('ctrl + 4')
    remove_hotkey_safely('ctrl + 5')
    remove_hotkey_safely('ctrl + 6')
    
def sequence_hotkeys():
    keyboard.add_hotkey('a', add_coordinates)
    keyboard.add_hotkey('e', edit_coordinates)
    keyboard.add_hotkey('enter', run_coordinates)
    keyboard.add_hotkey('ctrl + backspace', clear_coordinates)
    keyboard.add_hotkey('space', stop_coordinates)
    keyboard.add_hotkey('ctrl + s', save_to_json)
    keyboard.add_hotkey('ctrl + l', load_from_json)
    
def remove_sequence_hotkeys():
    remove_hotkey_safely('a')
    remove_hotkey_safely('e')
    remove_hotkey_safely('enter')
    remove_hotkey_safely('ctrl + backspace')
    remove_hotkey_safely('space')
    remove_hotkey_safely('ctrl + s')
    remove_hotkey_safely('ctrl + l')

def handle_tab_change(event):
    global current_tab
    current_tab = tabControl.index(tabControl.select())
    if current_tab == 0:
        positions_hotkeys()
        remove_sequence_hotkeys()
    if current_tab == 1:
        sequence_hotkeys()
        remove_positions_hotkeys()

tabControl.bind("<<NotebookTabChanged>>", handle_tab_change)

def check_number():
    global x, y, z
    try:
        x = int(gotox.get())
    except ValueError:
        char_warning()
        x = 0
    try:
        y = int(gotoy.get())
    except ValueError:
        char_warning()
        y = 0
    try:
        z = int(gotoz.get())
    except ValueError:
        char_warning()
        z = 0

def char_warning():
    warning = Toplevel(root)
    warning.resizable(width=False, height=False)
    Label(warning, text='The value is not a number! Try again.').grid(row=0, column=0)
    Button(warning, text='OK', command=warning.destroy).grid(row=1, column=0)
    warning.grab_set()

def check_limit():
    global x, y, z, colorx, colory, colorz
    limit = 3000

    if int(x) < limit:
        colorx = "green"
    else:
        x = limit
        colorx = "red"
        coordinatesx.config(text=str(x))
        limit_warning()
    limitx.config(fg=colorx)
    if int(x) > -limit:
        colorx = "green"
    else:
        x = -limit
        colorx = "red"
        coordinatesx.config(text=str(x))
        limit_warning()
    limitx.config(fg=colorx)

    if int(y) < limit:
        colory = "green"
    else:
        y = limit
        colory = "red"
        coordinatesy.config(text=str(y))
        limit_warning()
    limity.config(fg=colory)
    if int(y) > -limit:
        colory = "green"
    else:
        y = -limit
        colorz = "red"
        coordinatesy.config(text=str(y))
        limit_warning()
    limity.config(fg=colory)

    if int(z) < limit:
        colorz = "green"
    else:
        z = limit
        colorz = "red"
        coordinatesz.config(text=str(z))
        limit_warning()
    limitz.config(fg=colorz)
    if int(z) > -limit:
        colorz = "green"
    else:
        z = -limit
        colorz = "red"
        coordinatesz.config(text=str(z))
        limit_warning()
    limitz.config(fg=colorz)

def homeMotor(x_target=None, y_target=None, z_target=None):
    global x, y, z
    x = x_target if x_target is not None else x
    y = y_target if y_target is not None else y
    z = z_target if z_target is not None else z
    update_coordinates()

def home_all():
    homeMotor(0, 0, 0)

def limit_warning():
    warning = Toplevel(root)
    warning.resizable(width=False, height=False)
    Label(warning, text='Limit Reached! Changing to Default Value.').grid(row=0, column=0)
    Button(warning, text='OK', command=warning.destroy).grid(row=1, column=0)
    warning.grab_set()

def update_coordinates():
    global x, y, z    
    coordinatesx.config(text=str(x))
    coordinatesy.config(text=str(y))
    coordinatesz.config(text=str(z))
    check_limit()

def move_delta(dx=0, dy=0, dz=0):
    global x, y, z
    x += dx * int(jogxy.get())
    y += dy * int(jogxy.get())
    z += dz * int(jogz.get())
    update_coordinates()

def moveTo(_x=None, _y=None, _z=None):
    global x, y, z
    try:
        if _x is None and _y is None and _z is None:
            x = int(gotox.get())
            y = int(gotoy.get())
            z = int(gotoz.get())
            check_number()
        else:
            x = _x
            y = _y
            z = _z
    except ValueError:
        char_warning()
        x, y, z = 0, 0, 0
    update_coordinates()

def move_up_left(): move_delta(-1, 1, 0)
def move_xy_up(): move_delta(0, 1, 0)
def move_up_right(): move_delta(1, 1, 0)
def move_left(): move_delta(-1, 0, 0)
def move_right(): move_delta(1, 0, 0)
def move_down_left(): move_delta(-1, -1, 0)
def move_xy_down(): move_delta(0, -1, 0)
def move_down_right(): move_delta(1, -1, 0)
def move_z_up(): move_delta(0, 0, 1)
def move_z_down(): move_delta(0, 0, -1)

def add_coordinates():
    if not running:
        x = gotox.get()
        y = gotoy.get()
        z = gotoz.get()
        delay = delay_spinbox.get()
        
        x = adjust_coordinate(x)
        y = adjust_coordinate(y)
        z = adjust_coordinate(z)
        
        delay = adjust_delay(delay)
        
        tree.insert("", "end", values=(x, y, z, delay))
    else:
        messagebox.showinfo("Info", "Cannot save coordinates while running.")

def edit_coordinates():
    if not running:
        selected_item = tree.selection()
        if selected_item:
            item = selected_item[0]
            x = gotox.get()
            y = gotoy.get()
            z = gotoz.get()
            delay = delay_spinbox.get()
            
            x = adjust_coordinate(x)
            y = adjust_coordinate(y)
            z = adjust_coordinate(z)
            
            delay = adjust_delay(delay)
            
            tree.item(item, values=(x, y, z, delay))
    else:
        messagebox.showinfo("Info", "Cannot edit coordinates while running.")

def clear_coordinates():
    if not running:
        selected_items = tree.selection()
        if selected_items:
            for item in selected_items:
                tree.delete(item)
        else:
            for item in tree.get_children():
                tree.delete(item)
    else:
        messagebox.showinfo("Info", "Cannot clear coordinates while running.")

def adjust_coordinate(coord):
    try:
        coord = int(coord)
        if coord < -3000:
            return -3000
        elif coord > 3000:
            return 3000
        else:
            return coord
    except ValueError:
        return 0

def adjust_delay(delay):
    try:
        delay = float(delay)
        if delay < 0:
            return 0
        elif delay > 31556926:
            return 31556926
        else:
            return delay
    except ValueError:
        return 0

def load_selected_coordinates(event):
    if not running:
        selected_item = tree.selection()
        if selected_item:
            item = selected_item[0]
            x, y, z, delay = tree.item(item, 'values')
            gotox.delete(0, END)
            gotox.insert(0, x)
            gotoy.delete(0, END)
            gotoy.insert(0, y)
            gotoz.delete(0, END)
            gotoz.insert(0, z)
            delay_spinbox.delete(0, END)
            delay_spinbox.insert(0, delay)
    else:
        messagebox.showinfo("Info", "Cannot load coordinates while running.")

def run_coordinates():
    global running, looping, current_index
    if not running:
        coordinates = tree.get_children()
        if coordinates:
            running = True
            looping = loop_checkbox_var.get()
            disable_widgets()
            current_index = 0
            run_next_coordinate(coordinates, current_index)
        else:
            messagebox.showwarning("Warning", "No coordinates to run.")
    else:
        messagebox.showinfo("Info", "Coordinates are already running.")

def stop_coordinates():
    global running, current_execution_item
    running = False
    current_execution_item = None
    if after_id:
        root.after_cancel(after_id)
    enable_widgets()

def run_next_coordinate(coordinates, index):
    global current_index, running, current_execution_item
    if index < len(coordinates) and running:
        current_item = coordinates[index]
        if current_item != current_execution_item:
            tree.selection_set(current_item)
            tree.focus(current_item)
            current_execution_item = current_item
            
        for item in tree.selection():
            tree.selection_remove(item)
        
        current_item = coordinates[index]
        tree.selection_add(current_item)
        tree.focus(current_item)
        
        x, y, z, delay = tree.item(current_item, 'values')
        moveTo(x, y, z)
        if running:
            root.after(int(float(delay) * 1000), run_next_coordinate, coordinates, index + 1)
    elif looping and running:
        current_index = 0
        run_next_coordinate(coordinates, current_index)
    else:
        enable_widgets()
        messagebox.showinfo("Info", "Finished running coordinates.")
        running = False

def enable_widgets():
    add_button.config(state="normal")
    edit_button.config(state="normal")
    run_button.config(state="normal")
    clear_button.config(state="normal")
    stop_button.config(state="disabled")
    save_button.config(state="normal")
    load_button.config(state="normal")
    tree.bind("<<TreeviewSelect>>", load_selected_coordinates)

def disable_widgets():
    add_button.config(state="disabled")
    edit_button.config(state="disabled")
    run_button.config(state="disabled")
    clear_button.config(state="disabled")
    stop_button.config(state="normal")
    save_button.config(state="disabled")
    load_button.config(state="disabled")
    tree.unbind("<<TreeviewSelect>>")

def save_to_json():
    filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
    if filename:
        try:
            data = []
            for item in tree.get_children():
                values = tree.item(item, 'values')
                data.append({
                    'X': values[0],
                    'Y': values[1],
                    'Z': values[2],
                    'Delay': values[3]
                })
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save JSON file: {e}")

def load_from_json():
    global running
    if not running:
        filename = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if filename:
            try:
                for item in tree.get_children():
                    tree.delete(item)

                with open(filename, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        x = adjust_coordinate(item['X'])
                        y = adjust_coordinate(item['Y'])
                        z = adjust_coordinate(item['Z'])
                        delay = adjust_delay(item['Delay'])
                        tree.insert("", "end", values=(x, y, z, delay))

                messagebox.showinfo("Success", "Coordinates loaded successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load JSON file: {e}")
    else:
        messagebox.showinfo("Info", "Cannot load coordinates while running.")

def load_jog_speed():
    positions = load_positions()
    jogxy.delete(0, END)
    jogxy.insert(0, positions.get("jogxy", 1))
    speedxy.delete(0, END)
    speedxy.insert(0, positions.get("speedxy", 1))
    jogz.delete(0, END)
    jogz.insert(0, positions.get("jogz", 1))
    speedz.delete(0, END)
    speedz.insert(0, positions.get("speedz", 1))

def save_jog_speed():
    global spinbox_changed
    spinbox_changed = True
    positions = load_positions()
    if positions:
        positions["jogxy"] = jogxy.get()
        positions["speedxy"] = speedxy.get()
        positions["jogz"] = jogz.get()
        positions["speedz"] = speedz.get()
        save(positions)
    else:
        positions = {
            "jogxy": jogxy.get(),
            "speedxy": speedxy.get(),
            "jogz": jogz.get(),
            "speedz": speedz.get()
        }

columnleft = Frame(sequencetab, width=150)
columnleft.grid(row=1, column=0, sticky="ns")

add_button = Button(columnleft, text="Add", command=add_coordinates)
add_button.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

edit_button = Button(columnleft, text="Edit", command=edit_coordinates)
edit_button.grid(row=0, column=2, padx=10, pady=5, sticky="ew")

run_button = Button(columnleft, text="Run", command=run_coordinates)
run_button.grid(row=0, column=3, padx=10, pady=5, sticky="ew")

clear_button = Button(columnleft, text="Clear", command=clear_coordinates)
clear_button.grid(row=0, column=4, padx=10, pady=5, sticky="ew")

loop_checkbox_var = BooleanVar()
loop_checkbox = Checkbutton(columnleft, text="Loop", variable=loop_checkbox_var)
loop_checkbox.grid(row=1, column=2, columnspan=2, padx=10, pady=5, sticky="w")

stop_button = Button(columnleft, text="Stop", command=stop_coordinates, state="disabled")
stop_button.grid(row=2, column=2, columnspan=2, padx=10, pady=5, sticky="ew")

Label(columnleft, text='Delay (s)').grid(row=1, column=6)
delay_spinbox = Spinbox(columnleft, from_=0, to=31556926, textvariable=IntVar())
delay_spinbox.grid(row=0, column=6, padx=10, pady=5)

save_button = Button(columnleft, text="Save", command=save_to_json)
save_button.grid(row=4, column=2, padx=10, pady=5, sticky="ew")

load_button = Button(columnleft, text="Load", command=load_from_json)
load_button.grid(row=4, column=3, padx=10, pady=5, sticky="ew")
    
columnmiddle = Frame(root, width=150)
columnmiddle.grid(row=0, column=3, columnspan=2, sticky="ns")

Button(columnmiddle, text='Go To', command=moveTo).grid(row=3, column=0)

Label(columnmiddle, text='X').grid(row=1, column=1)
Label(columnmiddle, text='Y').grid(row=1, column=2)
Label(columnmiddle, text='Z').grid(row=1, column=3)

columnx = Frame(columnmiddle, width=150)    
columnx.grid(row=2, column=1, sticky="ns")
columny = Frame(columnmiddle, width=150)
columny.grid(row=2, column=2, sticky="ns")
columnz = Frame(columnmiddle, width=150)
columnz.grid(row=2, column=3, sticky="ns")

Button(columnx, text='🏠︎', width=4, command=lambda: homeMotor(0)).grid(row=2, column=1)
keyboard.add_hotkey('home + x', lambda: homeMotor(0))
Button(columny, text='🏠︎', width=4, command=lambda: homeMotor(y_target=0)).grid(row=2, column=1)
keyboard.add_hotkey('home + y', lambda: homeMotor(y_target=0))
Button(columnz, text='🏠︎', width=4, command=lambda: homeMotor(z_target=0)).grid(row=2, column=1)
keyboard.add_hotkey('home + z', lambda: homeMotor(z_target=0))

limitx = Label(columnx, text='⦿', fg=colorx, width=4)
limitx.grid(row=2, column=2)
limity = Label(columny, text='⦿', fg=colory, width=4)
limity.grid(row=2, column=2)
limitz = Label(columnz, text='⦿', fg=colorz, width=4)
limitz.grid(row=2, column=2)

gotox = Spinbox(columnmiddle, from_=-3000, to=3000, textvariable=IntVar())
gotox.grid(row=3, column=1)
gotoy = Spinbox(columnmiddle, from_=-3000, to=3000, textvariable=IntVar())
gotoy.grid(row=3, column=2)
gotoz = Spinbox(columnmiddle, from_=-3000, to=3000, textvariable=IntVar())
gotoz.grid(row=3, column=3)

joystickxy = Frame(columnmiddle, width=150)
joystickxy.grid(row=4, column=1, columnspan=2)

Button(joystickxy, text='◤', width=10, height=5, command=move_up_left).grid(row=0, column=0)
Button(joystickxy, text='▲', width=10, height=5, command=move_xy_up).grid(row=0, column=1)
keyboard.add_hotkey('up', move_xy_up)
Button(joystickxy, text='◥', width=10, height=5, command=move_up_right).grid(row=0, column=2)
Button(joystickxy, text='◀', width=10, height=5, command=move_left).grid(row=1, column=0)
keyboard.add_hotkey('left', move_left)
Label(joystickxy, text='XY', width=10, height=5).grid(row=1, column=1)
Button(joystickxy, text='▶', width=10, height=5, command=move_right).grid(row=1, column=2)
keyboard.add_hotkey('right', move_right)
Button(joystickxy, text='◣', width=10, height=5, command=move_down_left).grid(row=2, column=0)
Button(joystickxy, text='▼', width=10, height=5, command=move_xy_down).grid(row=2, column=1)
keyboard.add_hotkey('down', move_xy_down)
Button(joystickxy, text='◢', width=10, height=5, command=move_down_right).grid(row=2, column=2)

joystickz = Frame(columnmiddle, width=150)
joystickz.grid(row=4, column=3, columnspan=2)

Button(joystickz, text='▲', width=10, height=5, command=move_z_up).grid(row=0, column=0)
keyboard.add_hotkey('page_up', move_z_up)
Label(joystickz, text='Z', width=10, height=5).grid(row=1, column=0)
Button(joystickz, text='▼', width=10, height=5, command=move_z_down).grid(row=2, column=0)
keyboard.add_hotkey('page_down', move_z_down)

Label(columnmiddle, text='Speed').grid(row=7, column=0)
Label(columnmiddle, text='Jog Distance').grid(row=8, column=0)
speedxy = Spinbox(columnmiddle, from_=1, to=3000, textvariable=IntVar())
speedxy.grid(row=7, column=1, columnspan=2)
jogxy = Spinbox(columnmiddle, from_=-3000, to=3000, textvariable=IntVar())
jogxy.grid(row=8, column=1, columnspan=2)
speedz = Spinbox(columnmiddle, from_=1, to=3000, textvariable=IntVar())
speedz.grid(row=7, column=3)
jogz = Spinbox(columnmiddle, from_=-3000, to=3000, textvariable=IntVar())
jogz.grid(row=8, column=3)
Label(columnmiddle, text='mm/s').grid(row=7, column=4)
Label(columnmiddle, text='mm').grid(row=8, column=4)

Button(columnmiddle, text="Load Jog/Speed", command=load_jog_speed).grid(row=9, column=1, columnspan=2)

Button(columnmiddle, text="Save Jog/Speed", command=save_jog_speed).grid(row=9, column=2, columnspan=2)

columnright = Frame(root, width=150)
columnright.grid(row=0, column=5, columnspan=2, sticky="ns")

Label(columnright, text='Coordinates', font=('TkDefaultFont', 16), fg='#353839').grid(row=0, column=0, columnspan=2)
Label(columnright, text='X', font=('TkDefaultFont', 16)).grid(row=1, column=0)
Label(columnright, text='Y', font=('TkDefaultFont', 16)).grid(row=2, column=0)
Label(columnright, text='Z', font=('TkDefaultFont', 16)).grid(row=3, column=0)
coordinatesx = Label(columnright, text=f'{int(x)}', font=('TkDefaultFont', 16, 'bold'), fg='#343434')
coordinatesx.grid(row=1, column=1)
coordinatesy = Label(columnright, text=f'{int(y)}', font=('TkDefaultFont', 16, 'bold'), fg='#343434')
coordinatesy.grid(row=2, column=1)
coordinatesz = Label(columnright, text=f'{int(z)}', font=('TkDefaultFont', 16, 'bold'), fg='#343434')
coordinatesz.grid(row=3, column=1)
Button(columnright, text='Home All', width=18, height=3, command=home_all).grid(row=4, column=0, columnspan=2)
keyboard.add_hotkey('ctrl + home', home_all)
Button(columnright, text='Settings', width=18, height=3, command=open_settings).grid(row=5, column=0, columnspan=2)
keyboard.add_hotkey('s', open_settings)
Button(columnright, text='Stop Motor', width=18, height=3).grid(row=6, column=0, columnspan=2)

positions = load_positions()

for i in range(1, numberofposition + 1):
    create_position_button(positionstab, 0 + (i - 1) // 2, (i - 1) % 2, i, positions=positions)

load_jog_speed()
tree.bind("<<TreeviewSelect>>", load_selected_coordinates)

root.mainloop()