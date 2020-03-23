# -*- coding:utf-8 -*-
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import mimetypes
import shutil
import cgi
from urllib import parse

html_templates = {}


def list_to_json(lst):
    return '[' + ','.join(list(map(lambda x: '"{0}"'.format(x), lst))) + ']'


def dir_to_button(dir_name):
    return '''<button onclick="window.location.href='/images/{1}'">{0}</button>'''.format(dir_name,
                                                                                          parse.quote(dir_name))


def dir_to_option(dir_name):
    return '''<option value = "{0}">{0}</option>'''.format(dir_name)


class FileManager:

    def __init__(self, root="/images"):
        self.root = os.getcwd() + root

    def get_dirs(self):
        return list(filter(lambda d: os.path.isdir(os.path.join(self.root, d)), os.listdir(self.root)))

    def get_files(self, path):
        d = os.path.join(self.root, path)
        return list(filter(lambda f: os.path.isfile(os.path.join(d, f)), os.listdir(d)))


class HtmlGenerator:
    def __init__(self, file_manager):
        self.file_manager = file_manager

    def gen_html(self, key, arg=None):
        all_dirs = self.file_manager.get_dirs()
        if key == '/dirs':
            content = html_templates['dir']
            all_dirs = list(map(dir_to_button, all_dirs))
            all_dirs = ''.join(all_dirs)
            print(all_dirs)
            content = content.format(**{"dirs": all_dirs})
        elif key == '/index':
            content = html_templates['index']
        elif key == '/upload':
            content = html_templates['upload']
            all_dirs = list(map(dir_to_option, all_dirs))
            all_dirs = ''.join(all_dirs)
            content = content.format(**{"dirs": all_dirs})
        elif key == '/images':
            folder = arg
            allfiles = self.file_manager.get_files(folder)
            allfiles = map(parse.quote, allfiles)
            allfiles = map(
                lambda x: "<image max-width=100px max-height=100px src = '/images/" + parse.quote(
                    folder) + "/" + x + "'>",
                allfiles)
            content = "".join(allfiles)
        else:
            with open(os.getcwd() + key, 'r', encoding='utf-8') as reader:
                content = reader.read()

        return content


class RequestHandler(BaseHTTPRequestHandler):
    fm = FileManager()
    hg = HtmlGenerator(fm)

    def do_GET(self):
        try:

            unquote_path = parse.unquote(self.path)

            print(self.path + "\n" + unquote_path)

            if os.path.isfile(os.getcwd() + unquote_path):
                full_path = os.getcwd() + unquote_path
                ext = os.path.splitext(unquote_path)[-1]
                if ext in ['.jpg', '.jpeg', 'png', 'gif']:
                    self.send_file(full_path)
                    return

            if self.path == "/" or self.path == "":
                self.send_content(self.hg.gen_html('/index').encode('utf-8'))
                return

            if self.path == "/dirs":
                self.send_content(self.hg.gen_html('/dirs').encode('utf-8'))
                return

            if self.path == "/upload":
                self.send_content(self.hg.gen_html('/upload').encode('utf-8'))
                return

            if self.path.startswith("/images/"):
                folder = parse.unquote(self.path.split("/")[-1])
                content = self.hg.gen_html('/images', folder)
                self.send_content(content.encode("utf-8"))
                return

            print("not handled" + self.path)
            content = 'page not found'.encode('utf-8')
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        except Exception as e:
            print(e)
        finally:
            pass

    def do_POST(self):
        try:
            form = cgi.FieldStorage(fp=self.rfile,
                                    headers=self.headers,
                                    environ={'REQUEST_METHOD': self.command,
                                             'CONTENT_TYPE': self.headers['Content-Type']})
            folder_name = form["folder"]
            folder_name = folder_name.value
            file_items = form['upload_file']
            if not isinstance(file_items, list):
                file_items = [file_items]
            for item in file_items:
                filename = os.path.basename(item.filename)
                if filename == "":
                    continue
                local_path = os.path.join(self.fm.root, folder_name, filename)
                root, ext = os.path.splitext(local_path)
                i = 1
                while os.path.exists(local_path):
                    local_path = "%s-%d%s" % (root, i, ext)
                    i = i + 1
                with open(local_path, "wb") as fout:
                    shutil.copyfileobj(item.file, fout)
            self.send_content("success".encode("utf-8"))
        except Exception as e:
            print(e)

    def send_content(self, content, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_file(self, local_path):
        with open(local_path, 'rb') as reader:
            self.send_response(200)
            self.send_header("Content-type", mimetypes.guess_type(local_path)[0])
            self.send_header("Content-Length", os.fstat(reader.fileno())[6])
            self.end_headers()
            shutil.copyfileobj(reader, self.wfile)


html_templates['dir'] = '''
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<script language="JavaScript"></script>
<style type="text/css"></style>
</head>
<body>
{dirs}
</body>
</html>
'''

html_templates['index'] = '''
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<script language="JavaScript"></script>
<style type="text/css"></style>
</head>
<body>
<button onclick="window.location.href = '/upload'">Upload</button>
<button onclick="window.location.href = '/dirs'">Dirs</button>
</body>
</html>
'''

html_templates['upload'] = '''
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<title></title>
<style type="text/css"></style>
<script language="JavaScript"></script>
</head>
<body>
<div>
  <div id="form" class="box">
    <form method="post" enctype="multipart/form-data" action="">
      <select name = "folder">
        {dirs}
      </select>
      <input name="upload_file" type="file" multiple="yes">
      <input value="Submit" type="submit">
    </form>
  </div>
</div>
</body>
</html>
'''

if __name__ == '__main__':
    serverAddress = ('', 8080)
    server = HTTPServer(serverAddress, RequestHandler)
    print("start... ")
    server.serve_forever()
