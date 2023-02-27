from manim import *
from manim_mobject_svg import *
from svgpathtools import svg2paths
import os


HTML_STRUCTURE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>%s</title>
</head>
<body>
    <svg id="%s" width="500px" viewbox="0 0 %d %d" style="background-color:%s;"></svg>
    %s
    <script src="%s"></script>
</body>
</html>"""


JAVASCRIPT_STRUCTURE = """function render() {
    svg = document.getElementById("%s");
%s
}"""


JAVASCRIPT_UPDATE_STRUCTURE = """    setTimeout(function() {
        svg.replaceChildren();
        %s
    }, %f)"""


class HTMLParsedVMobject:
    def __init__(self, vmobject: VMobject, scene: Scene):
        self.vmobject = vmobject
        self.scene = scene
        self.filename_base = scene.__class__.__name__
        self.html_filename = self.filename_base + ".html"
        self.js_filename = self.filename_base + ".js"
        self.current_index = 0
        self.final_html_body = ""
        self.html = HTML_STRUCTURE % (
            self.filename_base,
            self.filename_base,
            self.scene.camera.pixel_width,
            self.scene.camera.pixel_height,
            self.scene.camera.background_color,
            self.final_html_body,
            self.js_filename
        )
        self.js_updates = ""
        self.scene.add_updater(self.updater)
    
    def updater(self, dt):
        svg_filename = self.filename_base + str(self.current_index) + ".svg"
        self.vmobject.to_svg(svg_filename)
        html_el_creations = ""
        _, attributes = svg2paths(svg_filename)
        i = 0
        for attr in attributes:
            html_el_creation = f"        var el{i} = document.createElementNS('http://www.w3.org/2000/svg', 'path');\n"            
            for k, v in attr.items():
                html_el_creation += f"       el{i}.setAttribute('{k}', '{v}');\n"
            html_el_creation += f"       svg.appendChild(el{i});\n"
            html_el_creations += html_el_creation
            i += 1
        self.js_updates += JAVASCRIPT_UPDATE_STRUCTURE % (html_el_creations, 1000 * self.scene.renderer.time)
        self.js_updates += "\n"
        self.current_index += 1
        os.remove(svg_filename)
    
    def finish(self):
        self.scene.remove_updater(self.updater)
        self.js_updates.removesuffix("\n")
        with open(self.js_filename, "w") as f:
            f.write(JAVASCRIPT_STRUCTURE % (self.filename_base, self.js_updates))
        with open(self.html_filename, "w") as f:
            f.write(self.html)