from flask import Flask
from flask_restful import reqparse, abort, Api, Resource
import subprocess

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
        if app_name == "calmav":
            calmav_path = "%s/calmav" % APP_PATHS
            cmd = "sudo rm -rf %s/Dockerfile || true; sudo mkdir %s || true" % (calmav_path, calmav_path)
            cmd = prefix_cmd(cmd)
            try:
                result = subprocess.check_output([cmd], shell=True)
            except:
                pass

            cmd = prefix_cmd("sudo wget https://nutanixfilesapps.s3-us-west-1.amazonaws.com/calmav/Dockerfile -P %s" % calmav_path)
            result = subprocess.check_output([cmd], shell=True)

            cmd = prefix_cmd("sudo docker build -t calmav %s" % calmav_path)
            result = subprocess.check_output([cmd], shell=True)
            return "Success!"
        elif app_name == "search":
            search_path = "%s/search" % APP_PATHS
            cmd = "sudo rm -rf %s/Dockerfile || true; sudo mkdir %s || true" % (search_path, search_path)
            cmd = prefix_cmd(cmd)
            try:
                result = subprocess.check_output([cmd], shell=True)
            except:
                pass

            cmd = prefix_cmd("sudo wget https://nutanixfilesapps.s3-us-west-1.amazonaws.com/search/Dockerfile -P %s" % search_path)
            result = subprocess.check_output([cmd], shell=True)

            cmd = prefix_cmd("sudo docker build -t search %s" % search_path)
            result = subprocess.check_output([cmd], shell=True)
            return "Success!"

run_parser = reqparse.RequestParser()
run_parser.add_argument("dir_path")
class RunAv(Resource):
    def post(self):
        args = deploy_parser.parse_args()
        dir_path = args["dir_path"]
        cmd = prefix_cmd("clamscan -d /var/lib/clamav/main.cvd -r -i %s" % dir_path)
        result = subprocess.check_output([cmd], shell=True)
        return result

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

        search_prefix = "sudo docker run --rm --name search_data --mount type=bind,source=/data/shares,target=/shares centos:centos7"
        if search_type == "file":
            cmd = prefix_cmd("%s find /shares/%s -name %s" % (search_prefix, share_path, search_keyword))
            result = subprocess.check_output([cmd], shell=True)
        elif search_type == "text":
            cmd = prefix_cmd("%s grep -R /shares/%s search_keyword" % (search_prefix, share_path, search_keyword))
            result = subprocess.check_output([cmd], shell=True)
        return "%s" % result

    def get(self, file_id):
        import json
        cmd = prefix_cmd("sudo cat /root/results/%s" % file_id)
        result = subprocess.check_output([cmd], shell=True)
        return json.loads(result)

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
api.add_resource(Search, '/files_app/search/<file_id>')

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5000,debug=True,use_reloader=True)
