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

Hooray! You've learned to use this plugin.

## Notes

This plugin is not intended to make a full website, it will only make the SVG animations in HTML. If you want to use this plugin to create a website with Manim animations, you can include the generated HTML and JS files in your website. If you have problems with the size of your animations, you must fix it with CSS.
