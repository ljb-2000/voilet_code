#coding=UTF-8
import datetime
import os
import re
#import md5
import json


from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
import commands,json,yaml
from server_idc.models import  MyForm
from django.views.decorators.csrf import csrf_protect
from django.core.context_processors import csrf
from django.shortcuts import get_object_or_404
from salt_ui.api.salt_token_id import *
from salt_ui.api.salt_https_api import salt_api_jobs
from mysite.settings import  salt_api_pass,salt_api_user, salt_api_url ,pxe_url_api
from server_idc.models import Host

#日志记录
from salt_ui.log_class.api_log_class import salt_log

#songxs add
@login_required
def salt_index(request):
    return render_to_response('saltstack/salt_index.html', context_instance=RequestContext(request))

@login_required
def salt_status(request,id):
    context = {}
    id = int(id)
    node_name_all = []
    node_name_update = []
    user_node_list = []
    node_name = Host.objects.values_list("node_name")
    for test in node_name:
        test = "%s" % (test)
        node_name_all.append(test.encode("utf-8"))
    service_user = request.user.myform_set.all()
    for server_type_node in service_user:
        # type_node = "%s" % (str(server_type_node).encode("utf-8"))
        user_node = server_type_node.host_set.all()
        user_node_list.append({server_type_node:user_node})
    context["node_list"] = user_node_list
    context['service_name'] = service_user
    if id == 1:
        token_api_id = token_id()
        list = salt_api_token(
        {
        "client":'runner',
        "fun":"manage.status",
                   },
        salt_api_url,
        {"X-Auth-Token": token_api_id}
        )
        master_status =list.run()
        master_status = master_status["return"]
        for i in master_status:
            context['down']= i["down"]
            context['up']= i['up']
            context["live"] = len(i['up'])
            context["live_down"] = len(i['down'])
        for node in context['up']:
            if node not in node_name_all:
                node_name_update.append(node)
        context["node_name_update"] = node_name_update
        context.update(csrf(request))
        return render_to_response('saltstack/salt_status.html', context, context_instance=RequestContext(request))
    if id == 2:
        token_api_id = token_id()
        list = salt_api_token(
        {
        "client":'runner',
        "fun":"manage.status",
                   },
        salt_api_url,
        {"X-Auth-Token": token_api_id}
        )
        list = list.run()
        context["salt_key"]=list["return"]
        context.update(csrf(request))
        return render_to_response('saltstack/salt_key.html', context, context_instance=RequestContext(request))
    if id == 3:
        context.update(csrf(request))
        return render_to_response('saltstack/salt_cmd.html', context, context_instance=RequestContext(request))

@login_required
@csrf_protect
def salt_cmd(request):
    context = {}
    type_node = ""
    node_list = []
    if request.method == 'POST':
        salt_text = request.POST
        service_type = salt_text.getlist("business_node")
        # for i in service_type:
        #     service_name_type = get_object_or_404(MyForm,service_name = i)
        #     server_list = service_name_type.host_set.all()
        #     for s in server_list:
        #         type_node += "%s," % (s.node_name)
        # context["type_node"] = type_node
        for i in service_type:
            i = '%s' % (i)
            node_list.append(i.encode("utf-8"))
        salt_api_type = salt_text['comm_shell']
        if salt_api_type == "cmd":
            salt_cmd_lr = salt_text['salt_cmd']
            if len(service_type) > 0:
                salt_node_name = node_list
            elif len(salt_text["salt_node_name"]) >0:
                for i in salt_text["salt_node_name"]:
                    i = '%s ' % (i)
                    node_list.append(i.encode("utf-8"))
            else:
                salt_node_name = "*"
            token_api_id = token_id()
            list_all = salt_api_token({'fun': 'cmd.run', 'tgt': salt_node_name, 'arg': salt_cmd_lr, 'expr_form':'list'}, salt_api_url, { 'X-Auth-Token' : token_api_id})
            list_all = list_all.run()
            for i in list_all["return"]:
                context["jid"] =  i["jid"]
                context["minions"] = i["minions"]
            jobs_id = context["jid"]
            jobs_url = salt_api_url + "/jobs/" + jobs_id
            minions_list_all = salt_api_jobs(
            jobs_url,
            {"X-Auth-Token": token_api_id}
            )
            voilet_test = minions_list_all.run()
            for i in voilet_test["return"]:
                context["cmd_run"] = i
            context["cmd_Advanced"] = False
            context["salt_cmd"] = salt_text['salt_cmd']
            context["len_node"] = len(context["minions"])
            context.update(csrf(request))
            # print yaml.dump(context["cmd_run"])
            #日志入库
            salt_log(request.user.username, context["minions"], int(jobs_id), salt_api_type, context["len_node"], salt_cmd_lr, context["cmd_run"])
            return render_to_response('saltstack/salt_cmd_run.html', context, context_instance=RequestContext(request))
            #     #return HttpResponse(json.dumps(cmd))
        elif salt_api_type == "grains" :
            salt_cmd_lr = salt_text['salt_cmd']
            if len(salt_text["salt_node_name"]) >0:
                salt_node_name = salt_text["salt_node_name"]
            else:
                salt_node_name = "*"
            token_api_id = token_id()
            list_all = salt_api_token(
            {
            # 'client': 'local',
            'fun': 'grains.item',
            'tgt':salt_node_name,
            'arg':salt_cmd_lr ,
                           },
            salt_api_url,
            {"X-Auth-Token": token_api_id}
            )
            list_all = list_all.run()
            for i in list_all["return"]:
                context["jid"] =  i["jid"]
                context["minions"] = i["minions"]
            jobs_id = context["jid"]
            jobs_url = salt_api_url + "/jobs/" + jobs_id
            minions_list_all = salt_api_jobs(
            jobs_url,
            {"X-Auth-Token": token_api_id}
            )
            voilet_test = minions_list_all.run()
            for i in voilet_test["return"]:
                print type(i)
                context["cmd_run"] = i
            context["cmd_Advanced"]=False
            context["salt_cmd"]=salt_text['salt_cmd']
            context["len_node"] = len(context["minions"])
            context.update(csrf(request))
            #日志入库
            salt_log(request.user.username, context["minions"], int(jobs_id), salt_api_type, context["len_node"], salt_cmd_lr, context["cmd_run"])
            return render_to_response('saltstack/salt_cmd_grains_run.html', context, context_instance=RequestContext(request))
        elif salt_api_type == "ping":
            salt_cmd_lr = salt_text['salt_cmd']
            if len(salt_text["salt_node_name"]) > 0:
                salt_node_name = salt_text["salt_node_name"]
            else:
                salt_node_name = "*"
            token_api_id = token_id()
            list_all = salt_api_token(
            {
            # 'client': 'local',
            'fun': 'test.ping',
            'tgt':salt_node_name,
                           },
            salt_api_url,
            {"X-Auth-Token": token_api_id}
            )
            list_all = list_all.run()
            for i in list_all["return"]:
                context["jid"] =  i["jid"]
                context["minions"] = i["minions"]
            jobs_id = context["jid"]
            jobs_url = salt_api_url + "/jobs/" + jobs_id
            minions_list_all = salt_api_jobs(
            jobs_url,
            {"X-Auth-Token": token_api_id}
            )
            voilet_test = minions_list_all.run()
            for i in voilet_test["return"]:
                print type(i)
                context["cmd_run"] = i
            context["cmd_Advanced"]=True
            context["salt_cmd"]=salt_text['salt_cmd']
            context["len_node"] = len(context["minions"])
            context.update(csrf(request))
            #日志入库
            salt_log(request.user.username, context["minions"], int(jobs_id), salt_api_type, context["len_node"], salt_cmd_lr, context["cmd_run"])
            return render_to_response('saltstack/test_ping.html', context, context_instance=RequestContext(request))
        else:
            return render_to_response('saltstack/salt_cmd_run.html', context, context_instance=RequestContext(request))

@login_required
@csrf_protect
def salt_garins(request):
    context = {}
    if request.method == 'POST':
        salt_text = request.POST
        if salt_text['salt_cmd']:
            salt_cmd_lr = salt_text['salt_cmd']
            salt_node_name = salt_text["salt_node_name"]
            token_api_id = token_id()
            list_all = salt_api_token(
            {
            'client': 'local',
            'fun': 'grains.item',
            'tgt':salt_node_name,
            'arg':salt_cmd_lr ,
                           },
            "https://192.168.49.14/",
            {"X-Auth-Token": token_api_id}
            )
            list_all = list_all.run()
            for i in list_all["return"]:
                context["cmd_run"] = i
            context["cmd_Advanced"]=False
            context["salt_cmd"]=salt_text['salt_cmd']
            context.update(csrf(request))
            return render_to_response('saltstack/salt_cmd_grains_run.html', context, context_instance=RequestContext(request))
            #     #return HttpResponse(json.dumps(cmd))

    else:
        context.update(csrf(request))
        return render_to_response('saltstack/salt_garins.html', context, context_instance=RequestContext(request))

#自动化部署
@login_required
@csrf_protect
def salt_nginx(request):
     context = {}
     return render_to_response('saltstack/salt_cmd_run.html', context, context_instance=RequestContext(request))

#系统初始化
@login_required
@csrf_protect
def salt_check_install(request):
     context = {}
     if request.method == 'POST':
        salt_text = request.POST
        return render_to_response('saltstack/salt_check_install.html', context, context_instance=RequestContext(request))
     else:
         server_list = open("/srv/salt/check_install/hostname.jinja","r")
         server = server_list.read()
         server_list.close()
         server_node = open("/etc/salt/roster","r")
         node = server_node.read()
         server_node.close()
         context["server"] = server
         context["node"] = node
         context["cmd_Advanced"]=True
         context.update(csrf(request))
         return render_to_response('saltstack/salt_check_install.html', context, context_instance=RequestContext(request))

#jinja
@login_required
@csrf_protect
def salt_check_jinja(request):
     context = {}
     if request.method == 'POST':
        salt_text = request.POST
        context.update(csrf(request))
        server_list = open("/srv/salt/check_install/hostname.jinja","w")
        server_list.write(salt_text['salt_content_jinja'])
        server_list.close()
        context["cmd_Advanced"] = True
        return render_to_response('saltstack/salt_check_over.html', context, context_instance=RequestContext(request))



#salt_node
@login_required
@csrf_protect
def salt_check_node(request):
     context = {}
     if request.method == 'POST':
        salt_text = request.POST
        context.update(csrf(request))
        server_list = open("/etc/salt/roster","w")
        server_list.write(salt_text['salt_content_node'])
        server_list.close()
        context["server_list"] = server_list
        context["cmd_Advanced"] = True
        return render_to_response('saltstack/salt_check_over.html', context, context_instance=RequestContext(request))

#salt_node_shell
@login_required
@csrf_protect
def salt_check_setup(request):
     context = {}
     if request.method == 'POST':
        salt_text = request.POST
        salt_cmd_lr = salt_text['salt_shell_node']
        cmd = commands.getoutput("salt-ssh " + salt_cmd_lr + " state.sls check_install" )
        context['salt_cmd'] = cmd
        context["cmd_Advanced"] = True
        context.update(csrf(request))
        return render_to_response('saltstack/salt_check_setup.html', context, context_instance=RequestContext(request))


#salt_node_shell
@login_required
@csrf_protect
def salt_state_sls(request):
     context = {}
     if request.method == 'POST':
        salt_text = request.POST
        salt_cmd_lr = salt_text['salt_sls']
        node = salt_text["salt_node"]
        token_api_id = token_id()
        list_all = salt_api_token(
        {
        'client': 'local',
        'fun': 'state.sls',
        'tgt':node,
        'arg':salt_cmd_lr ,
                       },
        "https://192.168.49.14/",
        {"X-Auth-Token": token_api_id}
        )
        list_all = list_all.run()
        test = yaml.dump(list_all["return"])
        context["salt_cmd"] = test
        context["cmd_Advanced"] = True
        context.update(csrf(request))
        #return HttpResponse(json.dumps(context["salt_cmd"]),context_instance=RequestContext(request))
        return render_to_response('saltstack/salt_check_setup.html', context, context_instance=RequestContext(request))
     else:
         context["cmd_Advanced"] = False
         context.update(csrf(request))
         return render_to_response('saltstack/salt_state_sls.html', context, context_instance=RequestContext(request))



