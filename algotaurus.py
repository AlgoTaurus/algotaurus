# -*- coding: utf-8 -*-
"""
AlgoTaurus
==========
An educational game to teach programming.
Write a program to make the AlgoTaurus find the exit.

Copyright, 2015-2017, Attila Krajcsi, Ádám Markója (GUI)

AlgoTaurus is distributed under the terms of the GNU General Public License 3.
"""

import random
import time
import numpy as np
import sys
import os
import appdirs
import ConfigParser
import gettext

# Read config file
dirs = appdirs.AppDirs('algotaurus')
if not os.path.isfile(dirs.user_config_dir+'/algotaurus.ini'):
    import shutil
    if not os.path.exists(dirs.user_config_dir):
        os.makedirs(dirs.user_config_dir)
    shutil.copyfile(os.path.dirname(os.path.abspath(__file__))+'/algotaurus.ini', dirs.user_config_dir+'/algotaurus.ini')
config = ConfigParser.RawConfigParser()
config.read(dirs.user_config_dir+'/algotaurus.ini')
language = config.get('settings', 'language')

# Set language for localization
t = gettext.translation('algotaurus', os.path.dirname(os.path.abspath(__file__))+'/locale/', [language], fallback=True)
_ = t.ugettext
# Only the GUI is localized now, not the TUI
[_('left'), _('right'), _('step'), _('wall?'), _('exit?'), _('quit'), _('goto')]  # for the generate_pot script
local_commands = [_(command) for command in ['left', 'right', 'step', 'wall?', 'exit?', 'quit', 'goto']]

labyr_type_names = [_('Four walls'), _('Depth first')]


class Labyrinth:
    def __init__(self, x=11, y=11, labyr_type=1):
        """Create labyrinth.
        x, y: size of the labyrinth
        the minimum size is 11 x 11
        the size must be odd numbers
        
        returns: numpy array - the map
        0: path
        1: wall
        2: exit
        """

        # x and y should be odd numbers
        x = x if x % 2 else x-1
        y = y if y % 2 else y-1
        
        # Create exits        
        self.labyr = np.ones((y+4, x+4))*2
        self.labyr[2:-2, 2:-2] = 0

        if labyr_type == 0:
            #self.labyr[-3, -3] = 1  # TODO on GUI (not sure about TUI) these are y and x coordinates, not x and y
            self.labyr[5:-5, 3] = 1
            self.labyr[5:-5, -4] = 1
            self.labyr[3, 5:-5] = 1
            self.labyr[-4, 5:-5] = 1
        elif labyr_type == 1:
            def find_new_cell(current_cell):
                """ Depth first search algorithm
                http://en.wikipedia.org/wiki/Maze_generation_algorithm
                This one is building the wall, not carving the path.
                """
                self.labyr[tuple(current_cell)] = 1
                neighb_cells = [[-2, 0], [2, 0], [0, 2], [0, -2]]
                random.shuffle(neighb_cells)
                for pos in neighb_cells:
                    next_cell = current_cell+pos
                    if self.labyr[tuple(next_cell)] == 0:
                        self.labyr[tuple((next_cell+current_cell)/2)] = 1
                        find_new_cell(next_cell)
                return
            find_new_cell(np.array([2, 2]))
        

class Robot:
    """Create a robot in the labyrinth.
    The position and the state (direction) of the robot is stored in the
    labyrinth numpy array.

    Operate the robot with various commands.
    """
    def __init__(self, labyr):
        """labyr: Labyrinth object
        """
        self.labyr = labyr.labyr
        
        # Place the robot somewhere in the middle
        while True:
            self.pos = np.array([self.labyr.shape[0]/2 + random.choice([-1, -0, 1]),
                                 self.labyr.shape[1]/2 + random.choice([-1, -0, 1])])
            if self.labyr[tuple(self.pos)] == 0:
                break
        self.previous_pos = self.pos[:]

        # Create a random direction
        self.dir = random.choice(range(4))
        self.dir_vectors = {0: [0, 1], 1: [1, 0], 2: [0, -1], 3: [-1, 0]}  # right, down, left, up
        self.facing_pos = self.pos+self.dir_vectors[self.dir]
        self.update_robot()

    def update_robot(self):
        """Update the robot in the labyr np array.
        """
        self.labyr[tuple(self.previous_pos)] = 0
        self.labyr[tuple(self.pos)] = self.dir+10  # add 10 to have 10-13 codes for the robot
    
    ### Commands ###
    
    def step(self):
        if self.labyr[tuple(self.facing_pos)] == 1:
            return _('Bad news. AlgoTaurus run into wall.')
        elif self.labyr[tuple(self.facing_pos)] == 2:
            return _('Bad news. AlgoTaurus stepped into exit.')
        else:
            self.previous_pos = self.pos[:]
            self.pos = self.facing_pos
            self.facing_pos = self.pos+self.dir_vectors[self.dir]
        self.update_robot()
        return 'go on'
        
    def right(self):
        self.dir = (self.dir+1) % 4
        self.facing_pos = self.pos+self.dir_vectors[self.dir]
        self.update_robot()
        
    def left(self):
        self.dir = (self.dir-1) % 4
        self.facing_pos = self.pos+self.dir_vectors[self.dir]
        self.update_robot()
    
    def robot_quit(self):
        if self.labyr[tuple(self.facing_pos)] == 2:
            return _('Congratulations! AlgoTaurus successfully reached the exit.')
        else:
            return _('Bad news. AlgoTaurus was not in the exit yet.')
    
    def wall(self):
        return True if self.labyr[tuple(self.facing_pos)] == 1 else False
        
    def robot_exit(self):
        return True if self.labyr[tuple(self.facing_pos)] == 2 else False


class Script:
    """Interpret the script.
    """
    def __init__(self, code, robot, max_line=20):
        """
        code: multi line string
        robot: robot object
        max line: maximum length of the code
        """
        self.code = code.splitlines()
        self.code.insert(0, '')  # list index is the row number now
        self.robot = robot
        self.current_line = 1
        self.max_line = max_line
        
    def execute_command(self):
        """Execute a single line.
        """
        
        # Check if we reached the end without a solution
        if self.current_line > self.max_line:
            return _('Bad news. Code ended.')

        # Skip empty line
        if self.code[self.current_line].rstrip() == '':
            self.current_line += 1
            return 'go on'

        command = self.code[self.current_line].split(' ')[0].lower()
        params = self.code[self.current_line].split(' ')[1:]

        # Check if command is correct
        if not (command in local_commands):
            return _('Syntax error. Unknown command.')
        
        # Run the command
        if command == _('step'):
            self.current_line += 1
            return self.robot.step()
        elif command == _('right'):
            self.current_line += 1
            self.robot.right()
            return 'go on'
        elif command == _('left'):
            self.current_line += 1
            self.robot.left()
            return 'go on'
        elif command == _('wall?'):
            if len(params) < 2:
                return _('Syntax error. Wall test needs two parameters.')
            try:
                yes_line = int(params[0])
                no_line = int(params[1])
            except:
                return _('Syntax error. Wall test needs two numbers.')
            self.current_line = yes_line if self.robot.wall() else no_line
            return 'go on'
        elif command == _('exit?'):
            if len(params) < 2:
                return _('Syntax error. Exit test needs two parameters.')
            try:
                yes_line = int(params[0])
                no_line = int(params[1])
            except:
                return _('Syntax error. Exit test needs two numbers.')
            self.current_line = yes_line if self.robot.robot_exit() else no_line
            return 'go on'
        elif command == _('quit'):
            return self.robot.robot_quit()
        elif command == _('goto'):
            if len(params) == 0:
                return _('Syntax error. Goto command needs a parameter.')
            try:
                self.current_line = int(params[0])
            except:
                return _('Syntax error. Goto command needs a number.')
            return 'go on'


class AlgoTaurusTui:
    """Text UI for the AlgoTaurus game.
    """

    def __init__(self):
        try:
            import curses
            import curses.textpad
        except:
            print 'Cannot import curses module. Install the curses python module.'

        self.curses = curses

        self.stdscr = curses.initscr()
        curses.noecho()
        curses.curs_set(0)
        
        # Size of the terminal
        self.maxy, self.maxx = self.stdscr.getmaxyx()
        # FIXME the help string cannot be printed on the minimum size
        if self.maxx < 50 or self.maxy < 15:
            curses.endwin()
            print 'Too small terminal. Cannot run AlgoTaurus'

        # Code area
        edit_border_win = curses.newwin(self.maxy-5, 17, 0, 0)
        edit_border_win.border()
        edit_border_win.addstr('Code')
        edit_border_win.refresh()
        # Number of lines
        edit_line_win = curses.newwin(self.maxy-7, 3, 1, 1)
        edit_line_win.addstr(''.join([str(i)+'\n' for i in range(1, self.maxy-6)])[:-1])
        edit_line_win.refresh()
        # Sign for the current line processed
        self.edit_current_win = curses.newwin(self.maxy-7, 1, 1, 3)
        # Editing area
        self.edit_win = curses.newwin(self.maxy-7, 12, 1, 4)
        self.edit_win.refresh()
        self.edit_text = curses.textpad.Textbox(self.edit_win)
        self.edit_text.stripspaces = False  # Otherwise empty lines are deleted

        # Labyrinth area
        labyr_border_win = curses.newwin(self.maxy-5, self.maxx-18, 0, 17)
        labyr_border_win.border()
        labyr_border_win.addstr('AlgoTaurus')
        labyr_border_win.refresh()

        self.labyr_win = curses.newwin(self.maxy-7, self.maxx-20, 1, 18)
        self.labyr_win.refresh()
        
        self.result_border_win = curses.newwin(5, self.maxx-22, (self.maxy-18)/2, 19)
        self.result_win = curses.newwin(3, self.maxx-26, (self.maxy-18)/2+1, 21)
        
        # Command area
        self.command_win = curses.newwin(5, self.maxx-1, self.maxy-5, 0)
        self.command_win.border()
        self.command_win.refresh()
        self.command_win.keypad(True)

        self.main_loop()

    def display_labyr(self):
        labyr_char = {0: ' ', 1: '0', 2: '.', 10: '>', 11: 'v', 12: '<', 13: '^'}
        # FIXME is it possible to use unicode chars?

        # Create string
        labyr_str = ''.join([''.join([labyr_char[c] for c in row[1:-1]])+'\n' for row in self.labyr.labyr[1:-1]])
        self.labyr_win.addstr(0, 0, labyr_str[:-1])
        self.labyr_win.refresh()        
    
    def main_loop(self):
        curses = self.curses

        run_timer = 0.0005

        edit_help = 'Ctrl+G: Execute code   Ctrl+O: Insert line'
        edit_help_2 = 'Ctrl+K: Delete line (at the beginning of the line)'
        run_help = 'F5:Run   F6:Step   F7:Stop   +:Faster run   -:Slower run'
        run_help_2 = 'F10: Exit AlgoTaurus'
        command_help = '''Help AlgoTaurus to find the exit.

Available commands:
LEFT       turn left
RIGHT      turn right
STEP       step one square
           ahead of wall and exit it crashes
WALL? x y  is there a wall ahead?
           if yes, continue with line x, otherwise line y
EXIT? x y  is there an exit ahead?
QUIT       leave the labyrinth
           ahead of empty field and wall it crashes
GOTO x     continue with line x'''
        
        while True:
            # Edit the code
            curses.curs_set(1)
            self.command_win.erase()
            self.command_win.border()
            self.command_win.addstr(1, 1, edit_help)
            self.command_win.addstr(2, 1, edit_help_2)
            self.command_win.refresh()
            self.labyr_win.erase()
            self.labyr_win.addstr(0, 0, command_help)
            self.labyr_win.refresh()
            self.edit_win.move(0, 0)
            self.edit_text.edit()
            curses.curs_set(0)
            edited_text = self.edit_text.gather()
            
            # Run the code
            self.labyr = Labyrinth(y=self.maxy-9, x=self.maxx-23)
            self.robot = Robot(self.labyr)
            self.script = Script(edited_text, self.robot, max_line=self.maxy-7)
            self.display_labyr()
            self.command_win.erase()
            self.command_win.addstr(1, 1, run_help)
            self.command_win.addstr(2, 1, run_help_2)
            self.command_win.refresh()
            self.command_win.nodelay(True)
    
            result = 'go on'
            mode = 'step'
            while (result == 'go on') or (mode == 'stop'):
                try:
                    user_key = self.command_win.getkey()
                except:
                    user_key = None
                if user_key is None:
                    pass
                elif user_key == 'KEY_F(5)':
                    mode = 'run'
                elif user_key == 'KEY_F(6)':
                    mode = 'step'
                elif user_key == 'KEY_F(7)':
                    mode = 'stop'
                elif user_key == 'KEY_F(10)':
                    mode = 'quit'
                elif user_key == '+':
                    run_timer /= 2
                elif user_key == '-':
                    run_timer *= 2
                if mode != 'wait':
                    self.command_win.addstr(3, 1, 'Mode: '+mode.ljust(5).capitalize())
                    self.command_win.refresh()
                
                if mode in ['run', 'step']:
                    self.edit_current_win.erase()
                    self.edit_current_win.addstr(self.script.current_line-1, 0, '>')
                    self.edit_current_win.refresh()
                    time.sleep(run_timer)
                    result = self.script.execute_command()
                    self.display_labyr()
                    time.sleep(run_timer)
                if mode == 'step':
                    mode = 'wait'
                if mode == 'stop':
                    result = 'Running stopped.'
                    break
                elif mode == 'quit':
                    break
            
            if mode == 'quit':
                break
            
            # Display result message
            self.result_win.erase()
            self.result_border_win.border()
            self.result_border_win.refresh()
            self.result_win.addstr(0, 0, result)
            self.result_win.refresh()
            while self.command_win.getch() == -1:
                pass
            self.edit_current_win.erase()
            self.edit_current_win.refresh()

        curses.echo()
        curses.curs_set(1)
        curses.endwin()


class AlgoTaurusGui:
    """Graphical User Interface for the AlgoTaurus game.
    Parameters:
    size: size of each squares in the labyrinth in pixels (default:15)
    lines: number of lines in the coder (default:30)
    Set up GUI with custom parameters:
    AlgoTaurusGui(size=__, lines=__)
    """

    def __init__(self, size=15, lines=30):
        import os
        import Tkinter as tk
        import tkFileDialog
        import tkMessageBox
        import ttk

        self.tk = tk
        self.ttk = ttk
        self.tkFileDialog = tkFileDialog
        self.tkMessageBox = tkMessageBox

        # Initial parameters
        self.size = size
        self.lines = lines
        self.x = 27
        self.y = 27
        self.run_timer = 5.0
        self.mode = None
        self.execute = False
        self.exit_flag=False
        self.root = tk.Tk()
        self.root.title('AlgoTaurus')

        # tk limitation for icon use: http://stackoverflow.com/questions/11176638/python-setting-application-icon
        if os.name == 'nt':
            self.root.iconbitmap('maze.ico')
        else:
            img = tk.PhotoImage(file='maze.png')
            self.root.tk.call('wm', 'iconphoto', self.root._w, img)

        self.root.protocol('WM_DELETE_WINDOW', self.exit_command)

        # Build up instruction from smaller strings, so if anything is changed later, only the relevant part should
        # be localized
        command_help = '\n\n'.join([_('Help AlgoTaurus to find the exit.'),
                        _('Available commands:'),
                        _(u'LEFT\t Turn left by 90°'),
                        _(u'RIGHT\t Turn right by 90°'),
                        _('''STEP\t Step one square
\t Ahead of wall and exit it crashes.'''),
                        _('''WALL? m n\t Is there a wall ahead?
\t If yes, continue with line m,
\t otherwise with line n.'''),
                        _('''EXIT? m n\t Is there an exit ahead?
\t If yes, continue with line m,
\t otherwise with line n.'''),
                        _('''QUIT\t Leave the labyrinth
\t Ahead of empty field
\t and wall it crashes.'''),
                        _('''GOTO m\t Continue with line m''')])

        # Create menu for the GUI
        languages = {'Hungarian': 'hu', 'English': 'en'}  # do not localize this, because it could be hard for the ...
        # user to switch back after switching accidently to an unknown language
        self.lang_value = tk.StringVar()
        self.lang_value.set(language)
        self.labyr_type = tk.IntVar()
        self.labyr_type.set(1)
        self.menu = tk.Menu(self.root, relief=tk.FLAT)
        self.root.config(menu=self.menu)
        self.filemenu = tk.Menu(self.menu, tearoff=False)
        self.menu.add_cascade(label=_('Code file'), menu=self.filemenu)
        self.filemenu.add_command(label=_('New'), command=self.new_command, accelerator='Ctrl+N')
        self.filemenu.add_command(label=_('Open...'), command=self.open_command, accelerator='Ctrl+O')
        self.filemenu.add_command(label=_('Save'), command=self.save_command, accelerator='Ctrl+S')
        #self.filemenu.add_separator()
        self.editmenu = tk.Menu(self.menu, tearoff=False)
        self.menu.add_cascade(label=_('Code edit'), menu=self.editmenu)
        self.editmenu.add_command(label=_('Copy'), command=self.copy_command, accelerator='Ctrl+C')
        self.editmenu.add_command(label=_('Cut'), command=self.cut_command, accelerator='Ctrl+X')
        self.editmenu.add_command(label=_('Paste'), command=self.paste_command, accelerator='Ctrl+V')
        self.editmenu.add_separator()
        self.editmenu.add_command(label=_('Select All'), command=self.sel_all, accelerator='Ctrl+A')
        self.labyrmenu = tk.Menu(self.menu, tearoff=False)
        self.menu.add_cascade(label=_('Labyrinth'), menu=self.labyrmenu)
        self.typemenu = tk.Menu(self.labyrmenu, tearoff=False)
        self.labyrmenu.add_cascade(label=_('Type'), menu=self.typemenu)
        for labyr_type in [0, 1]:
            self.typemenu.add_radiobutton(label=labyr_type_names[labyr_type], variable=self.labyr_type, value=labyr_type,
                                          command=self.change_labyr_type)
        self.helpmenu = tk.Menu(self.menu, tearoff=False)
        self.menu.add_cascade(label=_('AlgoTaurus'), menu=self.helpmenu)
        self.languagemenu = tk.Menu(self.helpmenu, tearoff=False)
        self.helpmenu.add_cascade(label=_('Language'), menu=self.languagemenu)
        for lang in sorted(languages.keys()):
            self.languagemenu.add_radiobutton(label=lang, variable=self.lang_value, value=languages[lang],
                                              command = self.change_language)
        self.helpmenu.add_command(label=_('About...'), command=self.about_command)
        self.helpmenu.add_command(label=_('Exit'), command=self.exit_command, accelerator='Ctrl+Q')
        self.rclickmenu = tk.Menu(self.menu, tearoff=False)
        self.rclickmenu.add_command(label=_('Copy'), command=self.copy_command)
        self.rclickmenu.add_command(label=_('Cut'), command=self.cut_command)
        self.rclickmenu.add_command(label=_('Paste'), command=self.paste_command)
        self.root.bind('<Control-n>', self.new_command)
        self.root.bind('<Control-N>', self.new_command)
        self.root.bind('<Control-s>', self.save_command)
        self.root.bind('<Control-S>', self.save_command)
        self.root.bind('<Control-o>', self.open_command)
        self.root.bind('<Control-O>', self.open_command)
        self.root.bind('<Control-q>', self.exit_command)
        self.root.bind('<Control-Q>', self.exit_command)
        self.root.bind('<Control-a>', self.sel_all)
        self.root.bind('<Control-A>', self.sel_all)        
        # Hotkeys
        self.root.bind('<F5>', self.runmode)
        self.root.bind('<F6>', self.stepmode)
        self.root.bind('<F7>', self.stopcommand)
        self.root.bind('<F2>', self.speed_down)
        self.root.bind('<F3>', self.speed_up)
        
        # Creating the two main frames
        self.mainframe = tk.Frame(master=self.root)
        self.controlframe = tk.Frame(master=self.mainframe)
        self.mainframe.pack(fill='both')

        # Creating coder widget
        self.textPad = tk.Text(self.mainframe, width=15, height=self.lines, wrap='none')
        self.textPad.config(bg='white', fg='black')
        numbers = ''.join([str(i).ljust(2)+'\n' for i in range(1, self.lines+1)])
        self.linebox = tk.Text(self.mainframe, width=3, height=self.lines, state='normal')
        self.linebox.insert('1.0', numbers)
        self.linebox.configure(bg='grey', fg='black', state='disabled', relief='flat')
        self.codertitle = ttk.Label(self.mainframe, text=_('Coder'), justify='center')
        self.textPad.bind('<Button-3>', self.rclick)
        self.textPad.bind('<Key>', self.validate_input)        
        # Creating canvas and drawing sample labyrinth
        self.canvas = tk.Canvas(self.mainframe, width=self.size*(self.x+4), height=self.size*(self.y+4))
        samplab = Labyrinth(x=self.x, y=self.y, labyr_type=self.labyr_type.get())
        Robot(samplab)
        self.draw_labyr(samplab.labyr)
        self.instr = ttk.Label(self.mainframe, text=command_help, justify='left', padding=10)
        # Creating buttons
        self.buttstop = ttk.Button(self.controlframe, text=_('Stop code\nexecution (F7)'), command=self.stopcommand, state='disabled')
        self.buttstep = ttk.Button(self.controlframe, text=_('Try the code\nLine by line (F6)'), command=self.stepmode)
        self.buttrun = ttk.Button(self.controlframe, text=_('Try the code\nContinuously (F5)'), command=self.runmode)
        self.buttspdown = ttk.Button(self.controlframe, text=_('Slower (F2)'), command=self.speed_down)
        self.buttspup = ttk.Button(self.controlframe, text=_('Faster (F3)'), command=self.speed_up)
    
        # Placing widgets on the frames with grid geometry manager

        # Widgets in mainframe
        self.codertitle.grid(column=1, row=0, columnspan=2, pady=10)
        self.instr.grid(column=0, row=1, sticky='n')
        self.linebox.grid(column=1, row=1, sticky='en')
        self.textPad.grid(column=2, row=1, sticky='wn')
        self.canvas.grid(column=3, row=1, sticky='ws', padx=20)

        # Widgets in buttonframe

        self.buttspdown.grid(row=1, column=0, padx=5, pady=10)
        self.buttspup.grid(row=1, column=1, padx=5, pady=10)
        self.buttrun.grid(row=0, column=0, columnspan=2, padx=10)
        self.buttstep.grid(row=0, column=2, padx=10)
        self.buttstop.grid(row=0, column=3, padx=10)
        self.controlframe.grid(column=0, row=2, columnspan=3, padx=10, pady=10)
        # Center the window and set the minimal size
        self.root.update()
        w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        winw, winh = self.root.winfo_width(), self.root.winfo_height()
        self.padding = (winw-self.x*(self.size-1), winh-self.y*(self.size-1))
        size = tuple(int(numb)+30 for numb in self.root.geometry().split('+')[0].split('x'))
        x = w/2 - size[0]/2
        y = h/2 - size[1]/2
        self.root.geometry("%dx%d+%d+%d" % (size + (x, y)))
        self.root.update()
        self.root.minsize(self.root.winfo_width(), self.root.winfo_height())
        self.root.mainloop()

    # Building menu and coder options
    def change_labyr_type(self):
        samplab = Labyrinth(x=self.x, y=self.y, labyr_type=self.labyr_type.get())
        Robot(samplab)
        self.draw_labyr(samplab.labyr)

    def change_language(self, event=None):
        if config.get('settings', 'language') != self.lang_value.get():
            cfgfile = open(dirs.user_config_dir + '/algotaurus.ini', 'w')
            config.set('settings', 'language', self.lang_value.get())
            config.write(cfgfile)
            self.tkMessageBox.showinfo(title=_('Info'), message=_('Changes will be applied on the next startup'))

    def validate_input(self, event):
        lines = self.textPad.index('end').split('.')[0]
        if lines > self.lines+2:
            endline = str(self.lines+1)+'.0'
            self.textPad.delete(endline, 'end')

    def new_command(self, event=None):
        if self.textPad.get('1.0', 'end'+'-1c') != '':
            if self.tkMessageBox.askokcancel(_('Warning'),
                                             _('Do you really want to erease the content of the coder?')):
                self.textPad.delete('1.0', 'end')

    def open_command(self, event=None):
        at_file = self.tkFileDialog.askopenfile(parent=self.root, mode='rb', title=_('Select a file'),
                                                filetypes=[(_('AlgoTaurus syntaxes'), '*.lab'), (_('all files'), '.*')])
        if at_file != None:
            contents = at_file.read()
            self.textPad.delete('1.0', 'end')
            self.textPad.insert('1.0', contents)
            at_file.close()

    def save_command(self, event=None):
        at_file = self.tkFileDialog.asksaveasfile(mode='w', defaultextension='.lab',
                                                  filetypes=[(_('AlgoTaurus syntaxes'), '*.lab'), (_('all files'), '.*')],
                                                  initialfile='lab01.lab')
        if at_file != None:
        # slice off the last character from get, as an extra return is added
            data = self.textPad.get('1.0', 'end'+'-1c')
            at_file.write(data)
            at_file.close()

    def exit_command(self, event=None):
        if self.tkMessageBox.askokcancel(_('Quit'), _('Do you really want to quit?')):
            self.exit_flag=True
            self.root.destroy()

    def about_command(self, event=None):
        self.tkMessageBox.showinfo(_('About'), _(u'AlgoTaurus 1.1\nCopyright © 2015-2017 Attila Krajcsi and Ádám Markója'))

    def sel_all(self, event=None):
        self.textPad.tag_add('sel', '1.0', 'end')

    def copy_command(self):
        # try-except to prevent further errors if textpad is empty
        self.textPad.clipboard_clear()
        try:
            text = self.textPad.get('sel.first', 'sel.last')
            self.textPad.clipboard_append(text)
        except:
            pass

    def cut_command(self):
        self.copy_command()
        try:
            self.textPad.delete('sel.first', 'sel.last')
        except:
            pass

    def paste_command(self):
        text = self.textPad.selection_get(selection='CLIPBOARD')
        self.textPad.insert('insert', text)

    def rclick(self, event):
        self.rclickmenu.tk_popup(event.x_root, event.y_root)

    def draw_labyr(self, labyr):
        """Drawing the labyr on the canvas from the numpy array"""
        for col, index in enumerate(labyr):
            for row, element in enumerate(index):            
                if element in [0, 1, 2]:
                    coords = tuple(loc*self.size for loc in (row, col, row+1, col+1))
                    colors = {0: 'white', 1: 'black', 2: 'grey'}
                    self.canvas.create_rectangle(*coords, width=0, fill=colors[element])
                else: 
                    locs = {10: [row, col, row, col+1, row+1, col+0.5],
                            11: [row, col, row+0.5, col+1, row+1, col],
                            12: [row, col+0.5, row+1, col+1, row+1, col],
                            13: [row+0.5, col, row, col+1, row+1, col+1]}
                    coords1 = tuple(loc*self.size for loc in (row, col, row+1, col+1))
                    coords2 = tuple(loc*self.size for loc in locs[element])
                    self.canvas.create_rectangle(*coords1, width=0, fill='white')
                    self.labrobot = self.canvas.create_polygon(*coords2, fill='red')
    
    def move_robot(self, labyr):
        """Moving the robot on the canvas"""
        self.canvas.delete(self.labrobot)
        robot = labyr.max()
        col, row = tuple(int(i) for i in (np.where(labyr == robot)))
        locs = {10: [row, col, row, col+1, row+1, col+0.5],
                11: [row, col, row+0.5, col+1, row+1, col],
                12: [row, col+0.5, row+1, col+1, row+1, col],
                13: [row+0.5, col, row, col+1, row+1, col+1]}
        coords = tuple(loc*self.size for loc in locs[robot])
        self.labrobot = self.canvas.create_polygon(*coords, fill='red')
        self.canvas.update()
    
    # Button commands
    def stopcommand(self, event=None):
        self.mode = 'stop'

    def stepmode(self, event=None):
        self.mode = 'step'
        self.buttrun.configure(state='normal')
        if self.execute == False:
            self.execute_code()

    def runmode(self, event=None):
        self.mode = 'run'
        self.buttrun.configure(state='disabled')
        if self.execute == False:
            self.execute_code()
            
    def speed_up(self, event=None):
        if self.run_timer > 2:
            self.run_timer /= 2
            self.buttspdown.configure(state='enabled')
            if self.run_timer <= 2:
                self.buttspup.configure(state='disabled')

    def speed_down(self, event=None):
        if self.run_timer < 500:
            self.run_timer *= 2
            self.buttspup.configure(state='enabled')
            if self.run_timer >= 500:
                self.buttspdown.configure(state='disabled')

    def execute_code(self):
        """Running the script from the coder"""
        self.execute = True
        self.buttstop.configure(state='normal')
        self.labyrmenu.entryconfig("Type", state="disabled")
        self.textPad.configure(state='disabled', bg='white smoke')
        self.textPad.see('1.0')
        edited_text = self.textPad.get('1.0', 'end'+'-1c')
        edited_text = edited_text.rstrip()
        if edited_text == '':
            result = _('There is no command to execute!')
        else:
            result = 'go on'
        self.canvas.delete('all')
        lines = edited_text.count('\n')+1

        # Resizing labyrinth to fit to the current window size
        self.root.update()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        self.x, self.y = (w-self.padding[0])/self.size, (h-self.padding[1])/self.size
        self.canvas.configure(width=self.size*(self.x+4), height=self.size*(self.y+4))
        self.root.update()
        # Drawing the labyrinth
        lab = Labyrinth(x=self.x, y=self.y, labyr_type=self.labyr_type.get())
        labyr = lab.labyr
        robot = Robot(lab)
        script = Script(edited_text, robot, max_line=lines)
        self.draw_labyr(labyr)
        self.canvas.update()
        self.canvas.after(1000)
        current_pos = 'end'
        while result == 'go on' and not self.exit_flag:
            if self.mode in ['run', 'step']:
                self.linebox.config(state='normal')
                self.linebox.delete(current_pos)
                current_pos = str(script.current_line)+'.2'
                self.linebox.insert(current_pos, '>')
                self.linebox.config(state='disabled')
                result = script.execute_command()
                self.move_robot(labyr)
                if self.mode == 'run':
                    self.canvas.after(int(self.run_timer))
                if self.mode == 'step':
                    self.mode = 'wait'
            elif self.mode == 'wait':
                self.canvas.after(200)
                self.canvas.update()
            elif self.mode == 'stop':
                break
        if not self.exit_flag:
            if not self.mode == 'stop':
                self.tkMessageBox.showinfo('Result', result)
            self.linebox.configure(state='normal')
            self.linebox.delete(current_pos)
            self.linebox.configure(state='disabled')
            self.buttstop.configure(state='disabled')
            self.buttstep.configure(state='normal')
            self.buttrun.configure(state='normal')
            self.textPad.configure(state='normal', bg='white')
            self.labyrmenu.entryconfig("Type", state='normal')
            self.execute = False


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-t', '-tui']:  # Run TUI version
            labyr = AlgoTaurusTui()
        else:
            print '''Use of AlgoTaurus:
algotaurus -t
    run in text user interface mode
algotaurus
    run in graphical user interface mode'''
    else:  # Run GUI version
        root = AlgoTaurusGui()
