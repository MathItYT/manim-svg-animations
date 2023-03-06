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
    <svg id="%s" width="%s" viewBox="0 0 %d %d" style="background-color:%s;"></svg>
    %s
    <script src="%s"></script>
</body>
</html>"""


BASIC_HTML_STRUCTURE = """<div>
    <svg id="%s" width="%s" viewBox="0 0 %d %d" style="background-color:%s;"></svg>
</div>"""


JAVASCRIPT_STRUCTURE = """var rendered = false;
var ready = true;
var timeouts = [];
var %s = document.getElementById("%s");
function render%s() {
    if (!ready) {
        for (var i=0; i<timeouts.length; i++) {
            clearTimeout(timeouts[i]);
        }
        while(timeouts.length > 0) {
            timeouts.pop();
        }
    }
    ready = false;
    rendered = false;
%s
    setTimeout(function() {
        ready = true;
        rendered = true;
    }, %f)
}"""


JAVASCRIPT_UPDATE_STRUCTURE = """    timeouts.push(setTimeout(function() {
        %s.replaceChildren();
        %s
    }, %f))"""


JAVASCRIPT_INTERACTIVE_STRUCTURE = """var combsDict = {%s};
var comb = [%s];
function update(i, val) {
if (!rendered) {
    return
}
var keys = Object.keys(combsDict);
var ithElements = [];
for (let arr of keys) {
    if (Array.isArray(arr[i])) {   
        ithElements.push(arr[i]);
    }
    else {
        ithElements.push(arr);
    }
}
var x = val;
var closest = ithElements.sort( (a, b) => Math.abs(x - a) - Math.abs(x - b))[0];
comb[i] = closest;
combsDict[comb]();
}
"""


class HTMLParsedVMobject:
    def __init__(self, vmobject: VMobject, scene: Scene, width: float = "500px", basic_html=False):
        self.vmobject = vmobject
        self.scene = scene
        self.filename_base = scene.__class__.__name__
        self.html_filename = self.filename_base + ".html"
        self.js_filename = self.filename_base + ".js"
        self.current_index = 0
        self.final_html_body = ""
        self.width = width
        self.basic_html = basic_html
        self.update_html()
        self.js_updates = ""
        self.continue_updating = True
        self.original_frame_width = self.scene.camera.frame_width
        self.original_frame_height = self.scene.camera.frame_height
        self.scene.add_updater(self.updater)
    
    def updater(self, dt):
        if self.continue_updating is False:
            return
        svg_filename = self.filename_base + str(self.current_index) + ".svg"
        self.vmobject.to_svg(svg_filename)
        html_el_creations = ""
        _, attributes = svg2paths(svg_filename)
        i = 0
        for attr in attributes:
            html_el_creation = f"        var el{i} = document.createElementNS('http://www.w3.org/2000/svg', 'path');\n"            
            for k, v in attr.items():
                html_el_creation += f"       el{i}.setAttribute('{k}', '{v}');\n"
            html_el_creation += f"       {self.filename_base.lower()}.appendChild(el{i});\n"
            html_el_creations += html_el_creation
            i += 1
        background_color = color_to_int_rgba(self.scene.camera.background_color, self.scene.camera.background_opacity)
        background_color[-1] = background_color[-1] / 255
        background_color = [str(par) for par in background_color]
        html_el_creations += f"     {self.filename_base.lower()}.style.backgroundColor = 'rgb({', '.join(background_color)})';\n"
        if isinstance(self.scene, MovingCameraScene):
            frame = self.scene.camera.frame
            pixel_width = self.scene.camera.pixel_width * self.scene.camera.frame_width / self.original_frame_width
            pixel_height = self.scene.camera.pixel_height * self.scene.camera.frame_height / self.original_frame_height
            frame_center = frame.get_corner(UL)
            pixel_center = frame_center * self.scene.camera.pixel_width / self.original_frame_width
            pixel_center += self.scene.camera.pixel_width / 2 * RIGHT + self.scene.camera.pixel_height / 2 * DOWN
            pixel_center[1] = -pixel_center[1]
            pixel_center = pixel_center[:2]
            arr = [*pixel_center, pixel_width, pixel_height]
            arr = [str(p) for p in arr]
            html_el_creations += f"     {self.filename_base.lower()}.setAttribute('viewBox', '{' '.join(arr)}');\n"
        self.js_updates += JAVASCRIPT_UPDATE_STRUCTURE % (
            self.filename_base.lower(),
            html_el_creations,
            1000 * self.scene.renderer.time
        )
        self.js_updates += "\n"
        self.current_index += 1
        os.remove(svg_filename)
    
    def update_html(self):
        bg_color = color_to_int_rgba(
            self.scene.camera.background_color,
            self.scene.camera.background_opacity
        )
        bg_color[-1] = bg_color[-1] / 255
        bg_color = [str(c) for c in bg_color]
        bg_color = f"rgb({', '.join(bg_color)})"
        if self.basic_html is False:
            self.html = HTML_STRUCTURE % (
                self.filename_base,
                self.filename_base,
                self.width,
                self.scene.camera.pixel_width,
                self.scene.camera.pixel_height,
                bg_color,
                self.final_html_body,
                self.js_filename
            )
        else:
            self.html = BASIC_HTML_STRUCTURE % (
                self.filename_base,
                self.width,
                self.scene.camera.pixel_width,
                self.scene.camera.pixel_height,
                bg_color
            )
    
    def finish(self):
        self.scene.remove_updater(self.updater)
        self.js_updates.removesuffix("\n")
        if not hasattr(self, "last_t"):
            self.last_t = self.scene.renderer.time
        js_content = JAVASCRIPT_STRUCTURE % (
            self.filename_base.lower(),
            self.filename_base,
            self.filename_base,
            self.js_updates,
            1000 * self.last_t
        )
        if hasattr(self, "interactive_js"):
            js_content += f"\n{self.interactive_js}"
        with open(self.js_filename, "w") as f:
            f.write(js_content)
        with open(self.html_filename, "w") as f:
            f.write(self.html)
    
    def start_interactive(
        self,
        value_trackers: list[ValueTracker],
        linspaces: list[np.ndarray],
        animate_this=True
    ):
        if animate_this is False:
            self.continue_updating = False
            self.last_t = self.scene.renderer.time
        print("This process can be slow, please wait!")
        self.interactive_js = ""
        filename = "update.svg"
        combs = itertools.product(*linspaces)
        combs_dict = ""
        comb_now = ", ".join([str(v.get_value()) for v in value_trackers])
        for comb in combs:
            for vt, val in zip(value_trackers, comb):
                self.scene.wait(1/self.scene.camera.frame_rate)
                vt.set_value(val)
            self.vmobject.to_svg(filename)
            html_el_creations = f"{self.filename_base.lower()}.replaceChildren();\n"
            _, attributes = svg2paths(filename)
            i = 0
            for attr in attributes:
                html_el_creation = f"        var el{i} = document.createElementNS('http://www.w3.org/2000/svg', 'path');\n"            
                for k, v in attr.items():
                    html_el_creation += f"       el{i}.setAttribute('{k}', '{v}');\n"
                html_el_creation += f"       {self.filename_base.lower()}.appendChild(el{i});\n"
                html_el_creations += html_el_creation
                i += 1
            
            combs_dict += "[" + ", ".join([str(v) for v in comb]) + """]: () => {
                %s
            },
            """ % html_el_creations
        self.interactive_js += JAVASCRIPT_INTERACTIVE_STRUCTURE % (combs_dict, comb_now)
        os.remove(filename)