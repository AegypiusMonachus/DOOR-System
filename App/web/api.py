'''

    version: 0.3.0
    update: 2019-07-15
    author: Cong

'''
from flask import request, send_from_directory
import os
import App.config as config


web_root = config.WEB_PATH
web_static_root = config.WEB_STATIC_PATH

web_demo_root = config.WEB_DEMO_PATH
web_static_demo_root = config.WEB_STATIC_DEMO_PATH
web_development_root = config.DEVELOPMENT_WEB_PATH
web_development_js_root = config.DEVELOPMENT_WEB_JS_PATH
web_development_css_root = config.DEVELOPMENT_WEB_CSS_PATH

root_web_root = config.ROOT_WEB_PATH


def init_api(app):
    # 检索数据
    @app.route('/', methods=['GET', 'PUT'])
    def mian_index():
        print("当前访问用户：", request.remote_addr)
        return send_from_directory(web_root, "index.html")

    @app.route("/static/"+"<path:filename>")
    def web_static(filename):
        return send_from_directory(web_static_root, filename, as_attachment=False)

    @app.route(os.path.join("/static/", "css") + "<path:filename>")
    def css_static(filename):
        return send_from_directory(os.path.join(web_static_root, "css"), filename, as_attachment=False)

    @app.route(os.path.join("/static/", "js") + "<path:filename>")
    def js_static(filename):
        return send_from_directory(os.path.join(web_static_root, "js"), filename, as_attachment=False)

    @app.route(os.path.join("/static/", "fonts") + "<path:filename>")
    def fonts_static(filename):
        return send_from_directory(os.path.join(web_static_root, "fonts"), filename, as_attachment=False)

    @app.route('/root_web', methods=['GET', 'PUT'])
    def root_web_index():
        print("当前访问用户：", request.remote_addr)
        print("root_webroot_webroot_web")
        print(os.path.join(web_root, "root_web"))
        return send_from_directory(root_web_root, "index.html")

    @app.route("/root_web/" + "<path:filename>")
    def root_web_static(filename):
        print("filename", filename)
        return send_from_directory(root_web_root, filename, as_attachment=False)

    # @app.route(os.path.join("/root_web/", "img") + "<path:filename>")
    # def root_web_img_static(filename):
    #     return send_from_directory(os.path.join(root_web_root, "img"), filename, as_attachment=False)

    # @app.route(os.path.join("/root_web/", "css") + "<path:filename>")
    # def root_web_css_static(filename):
    #     return send_from_directory(os.path.join(root_web_root, "css"), filename, as_attachment=False)
    #
    # @app.route(os.path.join("/root_web/", "js") + "<path:filename>")
    # def root_web_js_static(filename):
    #     return send_from_directory(os.path.join(root_web_root, "js"), filename, as_attachment=False)
    #
    # @app.route(os.path.join("/root_web/", "libs") + "<path:filename>")
    # def root_web_libs_static(filename):
    #     return send_from_directory(os.path.join(root_web_root, "libs"), filename, as_attachment=False)
    #


    '''
    下面是demo，临时用
    '''

    @app.route('/dy', methods=['GET', 'PUT'])
    def demo_index():
        print("当前访问用户：", request.remote_addr)
        return send_from_directory(web_demo_root, "index.html")

    @app.route("/dy/static/" + "<path:filename>")
    def demo_web_static(filename):
        return send_from_directory(web_static_demo_root, filename, as_attachment=False)

    @app.route(os.path.join("/dy/static/", "css") + "<path:filename>")
    def demo_css_static(filename):
        return send_from_directory(os.path.join(web_static_demo_root, "css"), filename, as_attachment=False)

    @app.route(os.path.join("/dy/static/", "js") + "<path:filename>")
    def demo_js_static(filename):
        return send_from_directory(os.path.join(web_static_demo_root, "js"), filename, as_attachment=False)
 
    @app.route(os.path.join("/dy/static/", "fonts") + "<path:filename>")
    def demo_fonts_static(filename):
        return send_from_directory(os.path.join(web_static_demo_root, "fonts"), filename, as_attachment=False)

    '''
    开发人员网站入口
    '''

    @app.route('/development', methods=['GET', 'PUT'])
    def development_index():
        print("当前访问用户：", request.remote_addr)
        print("开发人员网站")
        return send_from_directory(web_development_root, "index.html")

    @app.route("/development/static/" + "<path:filename>")
    def development_web_static(filename):
        return send_from_directory(web_development_root, filename, as_attachment=False)

    @app.route(os.path.join("/development/", "css/") + "<path:filename>")
    def development_css_static(filename):
        print(os.path.join(web_development_root, "css"))
        print("filename", filename)
        return send_from_directory(os.path.join(web_development_root, "css"), filename, as_attachment=False)

    @app.route(os.path.join("/development/", "js/") + "<path:filename>")
    def development_js_static(filename):
        print(os.path.join(web_development_root, "js"))
        print("filename", filename)
        return send_from_directory(os.path.join(web_development_root, "js"), filename, as_attachment=False)



