from kivy.app import App
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.clock import Clock
from kivy.properties import StringProperty, ListProperty, ObjectProperty, BooleanProperty
from kivy.animation import Animation
from kivy.uix.image import Image

from functools import partial
import json
import os
import math

TILE_SIZE = (40, 40)
SPEED = 2/0.08  # px/s
#SPEED = 20

Builder.load_file('main.kv')
Window.clearcolor = (1, 1, 1, 1)

class MainLayout(Widget):

    def __init__(self, **kwargs):
        super(MainLayout, self).__init__(**kwargs)
        self.parser = MapParser()
        cols, tiles = self.parser.parse_file("maps/level1.json")
        self.build_map(cols, tiles)

    def build_map(self, cols, tiles):
        # Create tiles and add it to grid
        self.tile_layout.cols = cols
        rows = len(tiles)/cols
        self.tile_layout.width = cols*TILE_SIZE[0]
        self.tile_layout.height = rows*TILE_SIZE[1]
        c = 0
        for tile in tiles:
            if tile == "":
                class_name = "Factory.Empty"
            else:
                class_name = "Factory."+tile
            wid = eval(class_name)()
            wid.name = str(c)
            c+=1
            self.tile_layout.add_widget(wid)

        # Tell every tile it's neighbour
        total = len(self.tile_layout.children)
        cols = float(self.tile_layout.cols)
        for tile in self.tile_layout.children:
            id = int(tile.name)
            row = math.ceil((id+1)/cols)
            next_row = math.ceil((id+2)/cols)
            last_row = math.ceil(id/cols)

            # Top
            if (id - cols) >= 0:
                top = id - cols
            else:
                top = -1

            # Right
            if next_row == row:
                right = id + 1
            else:
                right = -1

            # Bottom
            if (id + cols) <= total-1:
                bottom = id + cols
            else:
                bottom = -1

            # Left
            if last_row == row:
                left = id - 1
            else:
                left = -1

            for _tile in self.tile_layout.children:
                if int(_tile.name) == int(top):
                    tile.neighbour_top = _tile
                elif int(_tile.name) == int(right):
                    tile.neighbour_right = _tile
                elif int(_tile.name) == int(bottom):
                    tile.neighbour_bottom = _tile
                elif int(_tile.name) == int(left):
                    tile.neighbour_left = _tile


class Tile(Widget):

    source = StringProperty("")
    stencil_size = ListProperty([40, 40])
    stencil_pos = ListProperty([0, 0])

    has_product = BooleanProperty(False)

    neighbour_top = ObjectProperty(None)
    neighbour_right = ObjectProperty(None)
    neighbour_bottom = ObjectProperty(None)
    neighbour_left = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(Tile, self).__init__(**kwargs)
        self.product = Factory.Product()
        self.product.tile = self

    def product_enter(self, product=None, insert=None):
        self.has_product = True

    def product_left(self, *kwargs):
        self.has_product = False


class TubeEndBottom(Tile):
    def product_enter(self, product=None, insert=''):
        Clock.schedule_once(self.call_next, 0.6)

    def call_next(self, *kwargs):
        self.neighbour_bottom.product_enter(insert="top")

class TubeCreator(Tile):
    def __init__(self, **kwargs):
        super(TubeCreator, self).__init__(**kwargs)
        Clock.schedule_interval(self.spawn, 1.5)

    def spawn(self, *kwargs):
        self.product_enter()

    def product_enter(self, product=None):
        super(TubeCreator, self).product_enter(product)
        # We don't need to create a product because it is hidden in the tube
        Clock.schedule_once(self.call_next, 1)

    def call_next(self, *kwargs):
        if self.neighbour_bottom.product_enter(insert="top"):
            pass


class ConvCC(Tile):
    def __init__(self, **kwargs):
        super(ConvCC, self).__init__(**kwargs)

    def product_enter(self, product=None, insert=None):
        if self.has_product:
            return False
        super(ConvCC, self).product_enter(product)
        self.stencil_layer.add_widget(self.product)

        if insert == "top":
            self.product.pos = (self.x+(self.width/2)-(19/2), self.y+self.height)
            ani = Animation(y=self.y+10, duration=0.4) + Animation(pos=(self.x-19, self.y+10), duration=(19+20-9.5)/SPEED)
            Clock.schedule_once(self.call_next, ((20-9.5)/SPEED)+0.4+0.05)
        else:
            self.product.pos = (self.x+self.width, self.y+10)
            ani = Animation(pos=(self.x-19, self.y+10), duration=(40+19)/SPEED)
            Clock.schedule_once(self.call_next, 40/SPEED)
        ani.bind(on_complete=self.product_left)
        ani.start(self.product)

    def product_left(self, *kwargs):
        super(ConvCC, self).product_left()
        self.stencil_layer.remove_widget(self.product)
        self.product.left = False

    def call_next(self, *kwargs):
        if self.neighbour_left.product_enter(insert="right"):
            pass


class ConvCCEndLeft(Tile):
    def product_enter(self, product=None, insert=None):
        if self.has_product:
            return False
        super(ConvCCEndLeft, self).product_enter(product)
        self.stencil_layer.add_widget(self.product)

        self.product.pos = (self.x+self.width, self.y+10)
        ani = Animation(x=self.x+20-9.5, duration=(19+20-9.5)/SPEED) + Animation(y=self.y-19, duration=0.5)
        Clock.schedule_once(self.call_next, ((20-9.5)/SPEED)+0.5+0.05)
        ani.bind(on_complete=self.product_left)
        ani.start(self.product)

    def product_left(self, *kwargs):
        super(ConvCCEndLeft, self).product_left()
        self.stencil_layer.remove_widget(self.product)
        self.product.left = False

    def call_next(self, *kwargs):
        if self.neighbour_left.product_enter(insert="right"):
            pass


class ConvCCBoxLeft(Tile):
    def __init__(self, **kwargs):
        super(ConvCCBoxLeft, self).__init__(**kwargs)

    def product_enter(self, product=None, insert=None):
        if self.has_product:
            return False
        super(ConvCCBoxLeft, self).product_enter(product)
        self.stencil_layer.add_widget(self.product)

        self.product.pos = (self.x+self.width, self.y+10)
        ani = Animation(pos=(self.x-19, self.y+10), duration=(40+19)/SPEED)
        Clock.schedule_once(self.call_next, 40/SPEED)
        ani.bind(on_complete=self.product_left)
        ani.start(self.product)

    def product_left(self, *kwargs):
        super(ConvCCBoxLeft, self).product_left()
        self.stencil_layer.remove_widget(self.product)
        self.product.left = False

    def call_next(self, *kwargs):
        if self.neighbour_left.product_enter(insert="right"):
            pass


class ConvCCBoxRight(Tile):

    def product_enter(self, product=None, insert=None):
        if self.has_product:
            return False
        super(ConvCCBoxRight, self).product_enter(product)
        self.stencil_layer.add_widget(self.product)

        self.product.pos = (self.x+self.width, self.y+10)
        ani = Animation(pos=(self.x-19, self.y+10), duration=(40+19)/SPEED)
        Clock.schedule_once(self.call_next, 40/SPEED)
        ani.bind(on_complete=self.product_left)
        ani.start(self.product)

    def product_left(self, *kwargs):
        super(ConvCCBoxRight, self).product_left()
        self.stencil_layer.remove_widget(self.product)
        self.product.left = False

    def call_next(self, *kwargs):
        if self.neighbour_left.product_enter(insert="right"):
            pass


class SwitchTop(Tile):
    vertical_flow = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(SwitchTop, self).__init__(**kwargs)
        self.source = 'images/switch_top_horizontal.png'

    def product_enter(self, product=None, insert=''):
        Clock.schedule_once(self.call_next, 1.5)

    def call_next(self, *kwargs):
        if self.vertical_flow:
            self.neighbour_bottom.product_enter(insert="top")
        else:
            self.neighbour_left.product_enter(insert="right")

    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y):
            self.vertical_flow = not self.vertical_flow
        return super(SwitchTop, self).on_touch_down(touch)

    def on_vertical_flow(self, *kwargs):
        if self.vertical_flow:
            self.source = 'images/switch_top_vertical.png'
        else:
            self.source = 'images/switch_top_horizontal.png'


class Product(Image):
    tile = ObjectProperty(None)
    left = False

    def __init__(self, **kwargs):
        super(Product, self).__init__(**kwargs)


class MapParser(object):

    def parse_file(self, file):
        if not os.path.isfile(file):
            return False
        f = open(file)
        data = json.load(f)
        f.close()

        cols = data['cols']
        tiles = data['tiles']
        return cols, tiles


class FactoryApp(App):
    def build(self):
        #from kivy.uix.scatter import Scatter
        #root = Scatter(size=Window.size)
        #root.add_widget(MainLayout())
        return MainLayout()

FactoryApp().run()