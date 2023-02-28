from manim import *
from manim_mobject_svg import *
from svgpathtools import svg2paths
import itertools
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


JAVASCRIPT_STRUCTURE = """var rendered = false;
var ready = true;
var svg = document.getElementById("%s");
function render() {
    if (!ready) {
        return
    }
    ready = false;
    rendered = false;
%s
    setTimeout(function() {
        ready = true;
        rendered = false;
    }, %f)
}"""


JAVASCRIPT_UPDATE_STRUCTURE = """    setTimeout(function() {
        svg.replaceChildren();
        %s
    }, %f)"""


JAVASCRIPT_INTERACTIVE_STRUCTURE = """var combsDict = {%s};
var comb = [%s];
function update(i, val) {
var keys = Object.keys(combDict);
var ithElements = [];
for (let arr of keys) {
    ithElements.push(arr[i])
}
var x = val;
var closest = ithElements.sort( (a, b) => Math.abs(x - a) - Math.abs(x - b))[0];
comb[i] = closest;
combsDict[comb]();
}
"""


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
        js_content = JAVASCRIPT_STRUCTURE % (self.filename_base, self.js_updates, 1000 * self.scene.renderer.time)
        if hasattr(self, "interactive_js"):
            js_content += f"\n{self.interactive_js}"
        with open(self.js_filename, "w") as f:
            f.write(js_content)
        with open(self.html_filename, "w") as f:
            f.write(self.html)
    
    def start_interactive(
        self,
        value_trackers: list[ValueTracker],
        linspaces: list[np.ndarray]
    ):
        self.interactive_js = ""
        filename = "update.svg"
        combs = itertools.product(*linspaces)
        combs_dict = ""
        comb_now = ", ".join([str(v.get_value()) for v in value_trackers])
        for comb in combs:
            for vt, val in zip(value_trackers, comb):
                vt.set_value(val)
            self.vmobject.to_svg(filename)
            html_el_creations = "svg.replaceChildren();\n"
            _, attributes = svg2paths(filename)
            i = 0
            for attr in attributes:
                html_el_creation = f"        var el{i} = document.createElementNS('http://www.w3.org/2000/svg', 'path');\n"            
                for k, v in attr.items():
                    html_el_creation += f"       el{i}.setAttribute('{k}', '{v}');\n"
                html_el_creation += f"       svg.appendChild(el{i});\n"
                html_el_creations += html_el_creation
                i += 1
            
            combs_dict += "[" + ", ".join([str(v) for v in comb]) + """]: () => {
                %s
            },
            """
            os.remove(filename)
        self.interactive_js += JAVASCRIPT_INTERACTIVE_STRUCTURE % (combs_dict, comb_now)