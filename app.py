from flask import Flask
from flask_restful import reqparse, abort, Api, Resource
import subprocess
import json
import flask

# CONSTANTS
APP_PATHS = "/root/apps"

app = Flask(__name__)
api = Api(app)

def prefix_cmd(cmd):
    cmd = "ssh nutanix@172.17.0.1 '%s'" % cmd
    return cmd

parser = reqparse.RequestParser()
parser.add_argument('app_name')
parser.add_argument('url')

class Docker(Resource):
    def get(self):
        cmd = "ssh nutanix@172.17.0.1 'sudo docker ps -a'"
        result = subprocess.check_output(
                [cmd], shell=True)
        return "Success %s" % result

    def post(self):
        args = parser.parse_args()
        app_name = args['app_name']
        cmd = prefix_cmd("sudo docker pull %s" % app_name)
        result = subprocess.Popen(cmd, shell=True)
        return "pull %s" % result


wget_parser = reqparse.RequestParser()
wget_parser.add_argument("url")

class Wget(Resource):
    def post(self):
        args = wget_parser.parse_args()
        url = args["url"]
        cmd = prefix_cmd("wget %s" % url)
        result = subprocess.Popen(cmd, shell=True)

deploy_parser = reqparse.RequestParser()
deploy_parser.add_argument("app_name")
class Deploy(Resource):
    def post(self):
        args = deploy_parser.parse_args()
        app_name = args["app_name"]
        app_path = "%s/%s" % (APP_PATHS, app_name)
        cmd = "sudo rm -rf %s/Dockerfile || true; sudo mkdir %s || true" % (app_path, app_path)
        cmd = prefix_cmd(cmd)
        try:
            result = subprocess.check_output([cmd], shell=True)
        except:
            pass

        cmd = prefix_cmd("sudo wget https://nutanixfilesapps.s3-us-west-1.amazonaws.com/%s/Dockerfile -P %s" % (app_name, app_path))
        result = subprocess.check_output([cmd], shell=True)

        cmd = prefix_cmd("sudo docker build -t %s %s" % (app_name, app_path))
        if app_name == "anonymize":
            cmd = prefix_cmd("sudo docker build --network host -t %s %s" % (app_name, app_path))

        result = subprocess.check_output([cmd], shell=True)
        return "Success!"

run_parser = reqparse.RequestParser()
run_parser.add_argument("dir_path")
class RunAv(Resource):
    def post(self):
        args = run_parser.parse_args()
        dir_path = args["dir_path"]
        cmd = prefix_cmd("sudo docker run --rm --mount type=bind,source=/data/,target=/data/ -t calmav clamscan -d /var/lib/clamav/main.cvd -r -i %s" % dir_path)

        p = subprocess.Popen([cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = p.communicate()
        json_dict = {}
        json_dict["response"] = "%s" % out
        return flask.jsonify(json_dict)

anon_parser = reqparse.RequestParser()
anon_parser.add_argument("in_path")
anon_parser.add_argument("out_path")
class RunAnon(Resource):
    def post(self):
        args = anon_parser.parse_args()
        in_path = args["in_path"]
        out_path = args["out_path"]
        cmd = prefix_cmd("sudo docker run --rm --network host --mount type=bind,source=/data/,target=/data/ -t anonymize:latest sh anonymize.sh -i %s -o %s" % (in_path, out_path))
        result = ""
        try:
            result = subprocess.check_output([cmd], shell=True)
        except:
            pass
        json_dict = {}
        json_dict["response"] = "%s" % result
        return flask.jsonify(json_dict)

"""
python cleanup.py "path:/home/nutanix/data/binary_logs,age:2"
here age is in hours
python cleanup.py "path:/home/nutanix/data/temp_binary/binary_logs,size:407896064"
here size in bytes
python cleanup.py "path:/home/nutanix/data/temp_binary/binary_logs/"
"""
cleanup_parser = reqparse.RequestParser()
cleanup_parser.add_argument("path")
cleanup_parser.add_argument("age")
cleanup_parser.add_argument("size_bytes")
class RunCleanup(Resource):
    def post(self):
        args = cleanup_parser.parse_args()
        path = args["path"]
        age = args["age"]
        size_bytes = args["size_bytes"]
        cmd = "sudo docker run --rm --network host --mount type=bind,source=/data/,target=/data/ -t cleanup"
        if age:
            cmd = prefix_cmd("%s sudo docker run python cleanup.py 'path:%s,age:%s" % (path, age))
        elif size_bytes:
            cmd = prefix_cmd("%s sudo docker run python cleanup.py 'path:%s,size_bytes:%s" % (path, size_bytes))
        else:
            cmd = prefix_cmd("%s sudo docker run python cleanup.py 'path:%s" % (path))            
        result = ""
        try:
            result = subprocess.check_output([cmd], shell=True)
        except:
            pass
        json_dict = {}
        json_dict["response"] = "%s" % result
        return flask.jsonify(json_dict)

search_parser = reqparse.RequestParser()
search_parser.add_argument("search_keyword")
search_parser.add_argument("share_path")
search_parser.add_argument("share_type")
search_parser.add_argument("file_name")
search_parser.add_argument("file_path")
search_parser.add_argument("search_type")

class Search(Resource):
    def post(self, file_id):
        args = search_parser.parse_args()
        search_keyword = args["search_keyword"]
        share_path = args["share_path"]
        share_type = args["share_type"]
        file_name = args["file_name"]
        file_path = args["file_path"]
        search_type = args["search_type"]

        search_prefix = ("sudo docker run --rm --mount type=bind,source=/data/,target=/data/ -t search")
        if search_type == "file":
            cmd = prefix_cmd("%s python3 search.py file:%s /data/shares/%s /data/%s" % (search_prefix, search_keyword, share_path, file_id))
            result = subprocess.Popen([cmd], shell=True)
        elif search_type == "text":
            cmd = prefix_cmd("%s python3 search.py text:%s /data/shares/%s /data/%s" % (search_prefix, search_keyword, share_path, file_id))
            result = subprocess.Popen([cmd], shell=True)
        json_dict = {}
        json_dict["response"] = "Accepted"
        return flask.jsonify(json_dict), 202

    def get(self, file_id):
        cmd = prefix_cmd("sudo cat /data/%s" % file_id)
        result = subprocess.check_output([cmd], shell=True)
        json_dict = {}
        json_dict["response"] = str(result)
        return flask.jsonify(json_dict)

cmd_parser = reqparse.RequestParser()
cmd_parser.add_argument("cmd")
class Cmd(Resource):
    def post(self):
        args = cmd_parser.parse_args()
        cmd = prefix_cmd(args["cmd"])
        result = subprocess.check_output([cmd], shell=True)
        return "CMD OUTPUT %s" % result

##
## Actually setup the Api resource routing here
##
api.add_resource(Docker, '/docker')
api.add_resource(Cmd, '/cmd')
api.add_resource(Wget, '/wget')
api.add_resource(Deploy, '/deploy')
api.add_resource(RunAv, '/files_app/av')
api.add_resource(RunCleanup, '/files_app/cleanup')
api.add_resource(RunAnon, '/files_app/anon')
api.add_resource(Search, '/files_app/search/<file_id>')

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5000,debug=True,use_reloader=True)
