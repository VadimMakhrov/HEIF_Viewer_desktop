from tkinter import *
from tkinter import filedialog
import os
from sys import argv, exit
from PIL import Image, ImageTk
import pillow_heif

pillow_heif.register_heif_opener()


class App(Tk):
    def __init__(self):
        super().__init__()

        self.title("HEIC Viewer")
        self.state('zoomed')

        # обновляем окно для получения рассчитанных значений высоты и ширины окна
        self.update_idletasks()

        # минимальные и максимальные размеры окна
        min_size = int(self.winfo_width()*0.3) if self.winfo_width() > self.winfo_height() else int(self.winfo_height()*0.3)
        self.minsize(min_size, min_size)
        self.maxsize(self.winfo_screenwidth(), self.winfo_screenheight())
        
        # текущие размеры окна
        self.current_window_width = self.winfo_width()
        self.current_window_height = self.winfo_height()

        # устанавливаем цвет канвы
        self.background = 'black'

        # отобразить меню
        self.show_menu()

        # инициализация пути
        self.path = None

        # tag
        self.tag = 'img'

        # открытие файла
        self.open_file()

        # прослушивание нажатия клавиш с клавиатуры
        self.bind("<KeyPress>", self.keyboard)

        # прослушивание колёсика мышки
        self.bind("<MouseWheel>", self.img_scale)
        
        # перетаскивание картинки мышкой
        self.bind("<B1-Motion>", self.img_drag)
        self.bind("<ButtonPress-1>", self.img_drag_start)

        # прослушивание изменения размера окна
        self.bind("<Configure>", self.resize_window)

    def resize_window(self, event):
        '''событие изменения размера окна'''
        if self.current_window_width == self.winfo_width() and self.current_window_height == self.winfo_height():
            pass
        else:
            self.current_window_width = self.winfo_width()
            self.current_window_height = self.winfo_height()
            self.percent = self.get_scale()
            self.img_draw()

    def img_scale(self, event):
        '''масштабирование колёсиком мыши'''
        if event.delta > 0 and ((self.image_tk.width() <= 5000 and self.image_tk.height() <= 5000) or self.percent < 1 ) and self.percent < 3:
            self.percent += 0.1
            self.percent = round(self.percent, 1)
            self.img_draw()
        elif event.delta < 0 and self.percent > 0.1:
            self.percent -= 0.1
            if self.percent < 0.1:
                self.percent = 0.1
            self.percent = round(self.percent, 1)
            self.img_draw()
        elif event.delta < 0 and self.percent == 0.1 and self.get_scale() < self.percent:
            self.percent = self.get_scale()
            self.img_draw()
            self.percent = 0

    def img_drag_start(self, event):
        '''сохранение текущих координат для перетаскивания'''
        self.canvas.scan_mark(event.x, event.y)

    def img_drag(self, event):
        '''событие перетаскивания'''
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def show_menu(self):
        '''Показывает меню'''        
        self.main_menu = Menu()
        self.file_menu = Menu(self.main_menu,tearoff=0)
        self.background_menu = Menu(self.file_menu,tearoff=0)

        self.main_menu.add_cascade(label='File',menu=self.file_menu)
        self.main_menu.add_command(label='<- q\u0332',command=self.back)
        self.main_menu.add_command(label='e\u0332 ->',command=self.next)

        self.file_menu.add_command(label='Open',command=self.open_file)
        self.file_menu.add_command(label='f\u0332ullscreen',command=self.fullscreen_on)
        self.file_menu.add_command(label='[ s\u0332cale ]',command=self.img_full_window_scale)
        self.file_menu.add_command(label='1\u033200%',command=self.img_original_scale)
        self.file_menu.add_cascade(label='Background',menu=self.background_menu)

        self.background_menu.add_command(label='Black',command=self.bg_black)
        self.background_menu.add_command(label='White',command=self.bg_white)
        self.background_menu.add_command(label='Gray',command=self.bg_gray)

        # отображение меню
        self.config(menu=self.main_menu)

    def hide_menu(self):
        '''Скрывает меню'''
        self.main_menu.destroy()

    def bg_black(self):
        '''кнопка выбора чёрного цвета канвы'''
        self.background = 'black'
        self.create_canvas()
        self.img_draw()

    def bg_white(self):
        '''кнопка выбора белого цвета канвы'''
        self.background = 'white'
        self.create_canvas()
        self.img_draw()

    def bg_gray(self):
        '''кнопка выбора серого цвета канвы'''
        self.background = 'gray'
        self.create_canvas()
        self.img_draw()

    def img_original_scale(self):
        '''обработка кнопки [100%]'''
        self.percent = 1
        self.create_canvas()
        self.img_draw()

    def img_full_window_scale(self):
        '''обработка кнопки []'''
        self.percent = self.get_scale()
        self.create_canvas()
        self.img_draw()

    def dec_open_file(func):
        '''Декоратор для выбора файла'''
        def wrapper(*args, **kwargs):
            if kwargs != {}:
                return func(*args,**kwargs)
            # условие для запуска приложения с параметром (путь картинки)
            elif len(argv) > 1:
                path = argv[-1]
                return func(*args, path = path)
            else:
                path = filedialog.askopenfilename(filetypes=[('All types', '*.*'),('HEIC','.heic'),('PNG','.png'),('JPEG','.jpg .jpeg')]).replace('/','\\')
                if path == '': path = None
                return func(*args, path = path)
        return wrapper

    @dec_open_file
    def open_file(self, **kwargs):
        '''Открывает файл'''
        # Определяем путь из переданного аргумента
        if kwargs['path'] is not None:
            self.path = kwargs['path']
        if self.path == None:
            exit()

        # Получаем название файла
        self.file_name = str(self.path).split('\\')[-1]

        # загрузка изображения 
        self.img = self.img_load()
        
        # отрисовка изображения
        self.percent = self.get_scale()
        self.create_canvas()
        self.img_draw()

    def img_load(self):
        '''Загрузка изображения'''
        with Image.open(self.path) as img:
            img.load()
        return img

    def get_files(self):
        '''Получить список файлов изображений'''
        self.dir_path = '\\'.join(str(self.path).split('\\')[:-1])
        self.files = [_ for _ in os.listdir(self.dir_path) if ('.heic' in _) or ('.png' in _) or ('.jpg' in _) or ('.gif' in _)]

    def create_canvas(self):
        '''Создание канвы'''
        self.canvas = Canvas(self, \
                             height=self.winfo_screenheight(), \
                                width=self.winfo_screenwidth(), \
                                    bg=self.background, \
                                        highlightthickness = 0, \
                                            borderwidth = 0)
        self.canvas.place(x=0,y=0)

    def get_scale(self):
        '''Получение масштаба'''
        return self.winfo_width()/self.img.width \
            if self.winfo_width()/self.img.width < self.winfo_height()/self.img.height \
            else self.winfo_height()/self.img.height

    def img_draw(self):
        '''Отрисовка изображения'''
        self.img_res = self.img.resize([int(self.img.width * self.percent), int(self.img.height * self.percent)])
        self.image_tk = ImageTk.PhotoImage(image=self.img_res)

        self.canvas.create_image(int(self.winfo_width()//2),int(self.winfo_height()//2),image=self.image_tk, tags=self.tag)
        self.show_title()

    def show_title(self):
        '''Сформировать и отобразить название окна'''
        if (round(self.percent * 100, 2) * 100) % 100 == 0:
            self.title(self.file_name + ' ' + str(int(round(self.percent * 100, 2))) + ' %')
        else:
            self.title(self.file_name + ' ' + str(round(self.percent * 100, 2)) + ' %')

    def back(self):
        '''Обработка кнопки <-'''
        self.get_files()
        self.path = '\\'.join([self.dir_path, self.files[int(self.files.index(self.file_name)) - 1]])
        self.open_file(path=self.path)

    def next(self):
        '''Обработка кнопки ->'''
        self.get_files()
        if (self.files.index(self.file_name) == len(self.files) - 1):
            self.path = '\\'.join([self.dir_path, self.files[0]])
        else:
            self.path = '\\'.join([self.dir_path, self.files[int(self.files.index(self.file_name)) + 1]])
        self.open_file(path=self.path)

    def keyboard(self, event):
        '''Обработка клавиш с клавиатуры'''
        if event.keycode == 37 or event.keycode == 81: self.back() # 'Left' or 'q'
        elif event.keycode == 39 or event.keycode == 69: self.next() # 'Right' or 'e'
        elif event.keycode == 70: self.fullscreen_on() # 'F'
        elif event.keycode == 27: self.fullscreen_off() # 'Esc'
        elif event.keycode == 83: self.img_full_window_scale() # 'S'
        elif event.keycode == 49: self.img_original_scale() # '1'

    def fullscreen_on(self):
        '''Включить режим полного экрана'''
        self.hide_menu()
        self.attributes("-fullscreen", True)
        self.percent = self.get_scale()
        self.img_draw()

    def fullscreen_off(self):
        '''Выключить режим полного экрана'''
        if self.attributes("-fullscreen"):
            self.attributes("-fullscreen", False)
            self.show_menu()
            self.percent = self.get_scale()
            self.img_draw()



if __name__ == "__main__":
    viewer = App()
    viewer.mainloop()