# Manim SVG Animations

This is a plugin for [ManimCE](https://www.manim.community/) to render SVG animations directly with Python.

## Installation
`pip install manim-svg-animations`

## How to use
First of all, you must import Manim and this plugin.
```python
from manim import *
from manim_svg_animations import *
```

Secondly, create your scene. To change the background color to white, you must call `self.camera.background_color = WHITE`. You must create a VGroup which includes the all the VMobjects of the first animation. If the VGroup is called `vg`, then call `parsed = HTMLParsedVMobject(vg, self)` before playing the first animations. If the later animations will include more VMobjects, then simply add them to `vg`. When you finished the animations, don't forget to call `parsed.finish()`. There is an example below.
```python
from manim import *
from manim_svg_animations import *


VMobject.set_default(color=BLACK)


class SceneExample(Scene):
    def construct(self):
        self.camera.background_color = WHITE
        ax = Axes().add_coordinates()
        labels = ax.get_axis_labels("x", "y")
        vg = VGroup(ax, labels)
        parsed = HTMLParsedVMobject(vg, self)
        self.play(Write(VGroup(ax, labels)))
        graph = ax.plot(
            np.log,
            x_range=[np.exp(-4), 7],
            color=RED
        )
        vg.add(graph)
        self.play(Create(graph))
        riemann = ax.get_riemann_rectangles(
            graph,
            x_range=[1, 6],
            dx=1
        )
        vg.add(riemann)
        self.play(Write(riemann))
        dx = ValueTracker(1)
        riemann.add_updater(
            lambda m: m.become(ax.get_riemann_rectangles(
                graph,
                x_range=[1, 6],
                dx=dx.get_value()
            ))
        )
        self.play(dx.animate.set_value(0.1))
        self.wait()
        riemann.clear_updaters()
        self.play(FadeOut(vg))
        banner = ManimBanner(dark_theme=False)
        vg.remove(*vg)
        vg.add(banner)
        self.play(banner.create())
        self.play(banner.expand())
        parsed.finish()
```
Then render your animation with `manim` command in your terminal. It's so important to add the flag `--disable_caching`. You will have an MP4 file with the Manim animation in your media folder and other two files in the directory of your Python file. Those two files are an HTML file and a JS file. Open the HTML file in your browser and open your browser's developer tools. Then go to console and call `render()`. You must see a SVG animation in your browser.

Now you can also make interactive SVG animations, however it's an experimental feature and it may be too slow. Use it by your own risk! `HTMLParsedVMobject` has a method called `start_interactive` and its arguments are value_trackers and linspaces. The argument value_trackers is a list of `ValueTracker`s which represent the parameters to interact (manipulate their values) and linspaces is a list of NumPy linspaces which represent the values that each `ValueTracker` can take. Don't forget to add updaters to the VMobjects that must change when changing each parameter!

There is an example below with interactivity.

```python
from manim import *
from manim_svg_animations import *


VMobject.set_default(color=BLACK)


class SceneExample(Scene):
    def construct(self):
        self.camera.background_color = WHITE
        b = ManimBanner(dark_theme=False)
        vg = VGroup(b)
        parsed = HTMLParsedVMobject(vg, self)
        self.play(b.create())
        self.play(b.expand())
        self.play(FadeOut(b))
        vg.remove(b)
        ax = Axes().add_coordinates()
        labels = ax.get_axis_labels("x", "y")
        vg.add(ax, labels)
        self.play(Write(VGroup(ax, labels)))
        graph = ax.plot(np.log, x_range=[np.exp(-4), 7], color=RED)
        vg.add(graph)
        self.play(Create(graph))
        riemann = ax.get_riemann_rectangles(graph, x_range=[1, 6], dx=1)
        vg.add(riemann)
        self.play(Write(riemann))
        dx = ValueTracker(1)
        riemann.add_updater(lambda m: m.become(ax.get_riemann_rectangles(graph, x_range=[1, 6], dx=dx.get_value())))
        parsed.start_interactive([dx], [np.flip(np.linspace(0.1, 1, 100))])
        parsed.finish()
```
You will have two files. Open the HTML file in your browser and open your browser's developer tools. Then go to console and call `render()`. When the animation finished, you can call `update(0, 0.5)` to change the first parameter to 0.5, `update(1, 1.2)` to change the second parameter to 1.2 (this won't work with the example!), etc. You won't see any range slider to interact, so you must edit the HTML file and add an slider by your own.

For example, you can add to your HTML body the following line:
```html
<input type="range" min="0.1" max="1.0" step="0.01" value="0.1" class="slider" oninput="update(0, this.value)">
```
That line will update your first parameter to the slider value. It won't work if you didn't execute `render()` function.

Hooray! You've learned to use this plugin.

## Notes

This plugin is not intended to make a full website, it will only make the SVG animations in HTML. If you want to use this plugin to create a website with Manim animations, you can include the generated HTML and JS files in your website. If you have problems with the size of your animations, you must fix it with CSS.
